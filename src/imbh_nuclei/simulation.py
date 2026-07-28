"""The Phase 2 Monte Carlo integration loop (Newton et al. 2026, Section 4).

Wires together every Section 4 physics module into the per-timestep probabilistic update
described in the paper: draw collision/capture probabilities from Delta_t/t_timescale,
roll random numbers, apply mass/spin/orbit updates, check EMRI/ejection stopping
conditions, track merger generation per BH. See docs/equations.md and
paper/limitations.md for citations and flagged ambiguities in each physics piece; this
module's own modeling choices (documented inline) are:

- GW-capture partners are drawn fresh from the initial mass/spin distribution each time
  (not from the tracked N-BH sample) -- explicitly stated by N26 ("we draw a mass and
  spin for the second BH from the initial distribution").
- Mass ratio convention q = m_secondary/m_primary <= 1 (m1 = larger mass) for all
  Eq. 8-10, 13-16 calls -- N26 doesn't pin down q's numerator/denominator, but this is
  the near-universal convention in the cited sources.
- Spin orientation angles (cos theta_i relative to the merger's orbital angular
  momentum) are drawn fresh, isotropically, at each merger event rather than tracked as
  persistent 3D vector state -- consistent with N26's own statement that recoil-kick
  angles are "chosen according to a uniform distribution" for each merger.
- GW-capture recoil kicks use eccentricity=1 in Eq. 13's (1+e) factor, representing
  O'Leary et al. 2009's finding that GW-capture binaries form and merge promptly at high
  eccentricity (N26 does not give a specific value) -- flagged, see
  paper/limitations.md.
- The relaxation velocity kick (Rose et al. 2022's per-orbit Gaussian prescription) is
  applied as `IntegrationConfig.relaxation_substeps` aggregated Gaussian kicks per
  *timestep* rather than one per *orbit* (literally 10^5-10^6 kicks per timestep at
  small radii -- impractical at N=1000 scale) or one aggregated kick for the whole
  timestep (an earlier version of this code; see
  paper/limitations.md#phase2-emri-rate-high). Each sub-step still aggregates its
  dt/n_sub/P_orbit orbits into one Gaussian draw (valid: a sum of iid Gaussian kicks is
  itself Gaussian), but the local dynamics (period, t_relax, v_circ -- all functions of
  the current semimajor axis) are *recomputed* at the start of each sub-step rather than
  held fixed for the entire timestep. This is a deliberate middle ground, not the literal
  per-orbit prescription: it lets the walk's own drift in `a` feed back into the kick
  amplitude partway through a timestep (letting the diffusion accelerate or decelerate as
  the BH's radius changes), at the cost of `relaxation_substeps` times more work per
  timestep instead of dt/P times more. See docs/equations.md for the tradeoff reasoning
  and why a fixed substep count (not literally per-orbit) was chosen.
- A kicked BH that ends up bound but beyond a_max is marked 'excursion' and skips
  collision/capture/relaxation processing until it sinks back to a_max after one
  mass-segregation timescale (computed at its new mass/orbit) -- N26 describes this
  qualitatively ("we allow it to sink back... over a mass-segregation timescale")
  without giving the exact re-entry mechanics.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from imbh_nuclei import cluster, collisions, gw_capture, inspiral, orbital_dynamics, recoil, relaxation
from imbh_nuclei.config import SimulationConfig
from imbh_nuclei.constants import R_SUN_PC
from imbh_nuclei.population import PopulationState, initialize_population

#: Eccentricity used in the (1+e) recoil-kick amplification factor (Eq. 13) for
#: GW-capture mergers -- see module docstring and paper/limitations.md.
GW_CAPTURE_KICK_ECCENTRICITY = 1.0


@dataclass
class SimulationResults:
    population: PopulationState
    merger_log: pd.DataFrame
    emri_log: pd.DataFrame
    ejection_log: pd.DataFrame
    n_steps: int
    final_time_gyr: float


def _cluster_quantities(a: np.ndarray, config: SimulationConfig) -> dict:
    c = config.cluster
    rho_star = cluster.stellar_density(a, c.rho0, c.r0, c.alpha_star)
    n_star = rho_star / 1.0
    n_bh_density = cluster.bh_number_density(a, c.n0_bh, c.r_h, c.alpha_bh)
    sigma_star = cluster.velocity_dispersion(a, c.m_smbh, c.alpha_star)
    sigma_bh = cluster.velocity_dispersion(a, c.m_smbh, c.alpha_bh)
    return dict(
        rho_star=rho_star,
        n_star=n_star,
        n_bh_density=n_bh_density,
        sigma_star=sigma_star,
        sigma_bh=sigma_bh,
    )


def _relaxation_mass_and_density(cq: dict, config: SimulationConfig) -> tuple[np.ndarray | float, np.ndarray]:
    """Eq. 22's <M_avg>/rho, resolved per `IntegrationConfig.relaxation_mass_weighting`.

    Two textually-defensible readings, both empirically tested and neither a clean match
    to Table 1 -- see paper/limitations.md#average-object-mass and
    config.IntegrationConfig.relaxation_mass_weighting's docstring for the full trace.
    Does NOT apply to Eq. 23 (segregation_timescale), which N26 explicitly writes as
    star-only regardless of this choice.
    """
    weighting = config.integration.relaxation_mass_weighting
    if weighting == "star_only":
        return 1.0, cq["rho_star"]
    if weighting == "bh_inclusive":
        mean_bh_mass = config.population.mean_bh_mass
        mean_object_mass = relaxation.average_object_mass(cq["n_star"], cq["n_bh_density"], mean_bh_mass)
        rho_total = cq["rho_star"] + cq["n_bh_density"] * mean_bh_mass
        return mean_object_mass, rho_total
    raise ValueError(f"Unknown relaxation_mass_weighting: {weighting!r}")


def _timescales(pop: PopulationState, mask: np.ndarray, config: SimulationConfig) -> dict:
    c = config.cluster
    a = pop.a[mask]
    e = pop.e[mask]
    mass = pop.mass[mask]
    cq = _cluster_quantities(a, config)

    t_coll = collisions.collision_timescale(mass, cq["n_star"], cq["sigma_star"], e, c.alpha_star)
    t_gw = gw_capture.capture_timescale(
        mass, config.population.mean_bh_mass, cq["sigma_bh"], cq["n_bh_density"]
    )
    mean_object_mass, rho = _relaxation_mass_and_density(cq, config)
    t_relax = relaxation.relaxation_timescale(cq["sigma_star"], rho, mean_object_mass, c.coulomb_log)
    t_seg = relaxation.segregation_timescale(mass, cq["sigma_star"], cq["rho_star"], c.coulomb_log)
    tau_gw_circular = inspiral.remaining_merger_time_circular(mass, c.m_smbh, a)

    return dict(
        t_coll=t_coll,
        t_gw=t_gw,
        t_relax=t_relax,
        t_seg=t_seg,
        tau_gw_circular=tau_gw_circular,
        cluster_quantities=cq,
    )


def _mass_ratio_ordered(m_a: np.ndarray, m_b: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return q = m_secondary/m_primary <= 1 given two mass arrays (order-independent)."""
    m1 = np.maximum(m_a, m_b)
    m2 = np.minimum(m_a, m_b)
    return m1, m2 / m1


def run_simulation(
    config: SimulationConfig,
    mass_sampler,
    spin_sampler,
) -> SimulationResults:
    """Run one full Monte Carlo simulation per config.

    Parameters
    ----------
    config : SimulationConfig
    mass_sampler, spin_sampler : Callable[[int, np.random.Generator], np.ndarray]
        Initial (and GW-capture partner) mass/spin samplers -- see population.py and the
        module docstring for the partner-sampling convention.

    Returns
    -------
    SimulationResults
    """
    rng = np.random.default_rng(config.integration.seed)
    c = config.cluster
    pop = initialize_population(
        config.population.n_bh,
        mass_sampler,
        spin_sampler,
        rng,
        a_min=c.a_min_pc,
        a_max=c.a_max_pc,
    )

    t_global_yr = 0.0
    t_max_yr = config.integration.t_max_gyr * 1.0e9
    n_steps = 0
    #: Defensive hard cap so an unforeseen stall (e.g. a future bug reintroducing a
    #: zero/negative-progress loop) fails loudly instead of hanging forever.
    max_steps = 2_000_000

    merger_rows: list[dict] = []
    emri_rows: list[dict] = []
    ejection_rows: list[dict] = []

    def _pending(p: PopulationState) -> bool:
        # "pending" = not yet in a terminal state (emri/ejected). Excursion BHs are not
        # terminal -- they must eventually get a chance to reactivate and resume, so the
        # loop must not stop just because zero BHs are *currently* 'active'.
        return bool(p.active.any() or (p.status == "excursion").any())

    while t_global_yr < t_max_yr and _pending(pop) and n_steps < max_steps:
        active = pop.active
        n_active_now = int(active.sum())

        if n_active_now == 0:
            # everyone left is 'excursion': nothing to do but fast-forward to the next
            # reactivation event (no collision/capture/relaxation/inspiral to process).
            excursion_mask = pop.status == "excursion"
            next_time = np.min(pop.reactivation_time_yr[excursion_mask])
            t_global_yr = max(t_global_yr, min(next_time, t_max_yr))
            n_steps += 1
            _check_excursion_reentry(pop, t_global_yr, c)
            continue

        ts = _timescales(pop, active, config)

        # t_relax must also cap dt: the relaxation kick is applied as an aggregate of
        # dt/P_orbit independent per-orbit kicks (see _apply_relaxation_walk), which is
        # only a valid approximation while dt stays well below t_relax itself -- omitting
        # this let dt span enormous numbers of orbits at small radii and produced
        # unphysically large aggregated kicks (found via a full-loop smoke test showing
        # an implausibly high EMRI fraction).
        dt_cap = config.integration.timestep_safety_factor * np.min(
            np.concatenate([ts["t_coll"], ts["t_gw"], ts["tau_gw_circular"], ts["t_relax"]])
        )
        dt = min(config.integration.dt0_yr, dt_cap, t_max_yr - t_global_yr)
        if dt <= 0:
            break
        t_global_yr += dt
        n_steps += 1

        active_idx = np.flatnonzero(active)
        n_active = active_idx.size

        # --- collision channel ---
        p_coll = dt / ts["t_coll"]
        collision_event = rng.uniform(0, 1, n_active) <= p_coll
        _apply_collisions(pop, active_idx[collision_event], ts["cluster_quantities"], collision_event, rng)

        # --- GW capture channel ---
        p_capture = dt / ts["t_gw"]
        capture_event = rng.uniform(0, 1, n_active) <= p_capture
        _apply_gw_captures(
            pop, active_idx[capture_event], mass_sampler, spin_sampler, rng, c, t_global_yr, merger_rows
        )

        # --- relaxation random walk (all still-active BHs) ---
        still_active_mask = pop.status[active_idx] == "active"
        _apply_relaxation_walk(pop, active_idx, still_active_mask, dt, config, rng, t_global_yr)

        # --- GW inspiral decay (Peters), all still-active BHs ---
        still_active_mask = pop.status[active_idx] == "active"
        _apply_gw_inspiral_decay(pop, active_idx[still_active_mask], c, dt)

        # --- excursion re-entry check ---
        _check_excursion_reentry(pop, t_global_yr, c)

        # --- EMRI stopping condition ---
        _check_emri(pop, c, t_global_yr, emri_rows)

        # --- ejection was already applied inside relaxation/GW-capture kick handling;
        #     log any newly-ejected BHs from this step ---
        _log_new_ejections(pop, active_idx, t_global_yr, ejection_rows)

    merger_log = pd.DataFrame(merger_rows)
    emri_log = pd.DataFrame(emri_rows)
    ejection_log = pd.DataFrame(ejection_rows)

    return SimulationResults(
        population=pop,
        merger_log=merger_log,
        emri_log=emri_log,
        ejection_log=ejection_log,
        n_steps=n_steps,
        final_time_gyr=t_global_yr / 1.0e9,
    )


def _apply_collisions(pop, idx, cq_active, collision_event_mask, rng):
    if idx.size == 0:
        return
    sigma_star = cq_active["sigma_star"][collision_event_mask]
    mass = pop.mass[idx]
    chi_i = pop.chi[idx]

    mdot = collisions.bondi_hoyle_rate(mass, sigma_star)
    m_cap = collisions.captured_mass(mdot, R_SUN_PC, sigma_star)
    delta_m = collisions.accreted_mass(m_cap, mass)
    new_mass = mass + delta_m

    prograde = rng.uniform(0, 1, idx.size) < 0.5
    new_chi = collisions.spin_change(chi_i, mass, new_mass, prograde)

    pop.mass[idx] = new_mass
    pop.chi[idx] = new_chi
    pop.n_collisions[idx] += 1


def _apply_gw_captures(
    pop, idx, mass_sampler, spin_sampler, rng, cluster_cfg, t_global_yr, merger_rows
):
    if idx.size == 0:
        return
    n = idx.size
    partner_mass = np.asarray(mass_sampler(n, rng), dtype=float)
    partner_chi = np.asarray(spin_sampler(n, rng), dtype=float)

    tracked_mass = pop.mass[idx]
    tracked_chi = pop.chi[idx]

    costheta_tracked = rng.uniform(-1, 1, n)
    costheta_partner = rng.uniform(-1, 1, n)
    chi_par_tracked = tracked_chi * costheta_tracked
    chi_par_partner = partner_chi * costheta_partner
    sintheta_tracked = np.sqrt(np.clip(1 - costheta_tracked**2, 0, None))
    sintheta_partner = np.sqrt(np.clip(1 - costheta_partner**2, 0, None))
    chi_perp_tracked = tracked_chi * sintheta_tracked
    chi_perp_partner = partner_chi * sintheta_partner

    m1, q = _mass_ratio_ordered(tracked_mass, partner_mass)
    tracked_is_primary = tracked_mass >= partner_mass
    chi_par_1 = np.where(tracked_is_primary, chi_par_tracked, chi_par_partner)
    chi_par_2 = np.where(tracked_is_primary, chi_par_partner, chi_par_tracked)
    chi_perp_1 = np.where(tracked_is_primary, chi_perp_tracked, chi_perp_partner)
    chi_perp_2 = np.where(tracked_is_primary, chi_perp_partner, chi_perp_tracked)

    chi_par_combined = gw_capture.chi_parallel(m1, chi_par_1, m1 * q, chi_par_2)
    remnant_m = gw_capture.remnant_mass(m1, m1 * q, chi_par_combined, prograde=True)
    ell = gw_capture.orbital_ell(q, chi_par_1, chi_par_2)
    remnant_chi = gw_capture.final_spin(q, chi_par_1, chi_par_2, ell)

    theta = rng.uniform(0, 2 * np.pi, n)
    theta_0 = rng.uniform(0, 2 * np.pi, n)
    xi = rng.uniform(0, 2 * np.pi, n)
    v_kick_vec = recoil.kick_velocity(
        q, chi_par_1, chi_par_2, chi_perp_1, chi_perp_2, theta, theta_0, xi,
        eccentricity=GW_CAPTURE_KICK_ECCENTRICITY,
    )
    kick_speed = np.linalg.norm(v_kick_vec, axis=-1)

    a_new, e_new, bound = orbital_dynamics.apply_velocity_kick(
        pop.a[idx], pop.e[idx], cluster_cfg.m_smbh, kick_speed, rng
    )

    chi_eff = (m1 * chi_par_1 + m1 * q * chi_par_2) / (m1 * (1 + q))

    for k in range(n):
        merger_rows.append(
            dict(
                time_yr=t_global_yr,
                generation=pop.generation[idx[k]] + 1,
                m1=m1[k],
                m2=m1[k] * q[k],
                chi1=chi_par_1[k],
                chi2=chi_par_2[k],
                chi_eff=chi_eff[k],
                remnant_mass=remnant_m[k],
                remnant_chi=remnant_chi[k],
                kick_speed_kms=kick_speed[k],
                bound_after_kick=bool(bound[k]),
            )
        )

    pop.generation[idx] += 1
    pop.mass[idx] = remnant_m
    pop.chi[idx] = remnant_chi
    _finalize_orbit_after_kick(pop, idx, a_new, e_new, bound, cluster_cfg, t_global_yr)


def _finalize_orbit_after_kick(pop, idx, a_new, e_new, bound, cluster_cfg, t_global_yr):
    ejected = ~bound
    pop.status[idx[ejected]] = "ejected"

    still_bound = bound
    excursion = still_bound & (a_new > cluster_cfg.a_max_pc)
    within_region = still_bound & ~excursion

    pop.a[idx[within_region]] = a_new[within_region]
    pop.e[idx[within_region]] = e_new[within_region]

    if np.any(excursion):
        exc_idx = idx[excursion]
        seg_sigma = cluster.velocity_dispersion(cluster_cfg.a_max_pc, cluster_cfg.m_smbh, cluster_cfg.alpha_star)
        seg_rho = cluster.stellar_density(cluster_cfg.a_max_pc, cluster_cfg.rho0, cluster_cfg.r0, cluster_cfg.alpha_star)
        t_seg = relaxation.segregation_timescale(
            pop.mass[exc_idx], seg_sigma, seg_rho, cluster_cfg.coulomb_log
        )
        pop.status[exc_idx] = "excursion"
        pop.a[exc_idx] = a_new[excursion]
        pop.e[exc_idx] = e_new[excursion]
        pop.reactivation_time_yr[exc_idx] = t_global_yr + t_seg


def _local_t_relax(a: np.ndarray, config: SimulationConfig) -> np.ndarray:
    """Relaxation timescale (Eq. 22) evaluated fresh at the given semimajor axis/axes --
    used to re-derive the relaxation-kick amplitude partway through a substepped walk
    (see _apply_relaxation_walk), mirroring exactly the t_relax calculation in
    _timescales but callable at an arbitrary (mid-walk) `a` rather than only the
    start-of-timestep value. <M_avg>/rho resolved per
    `config.integration.relaxation_mass_weighting` -- see the matching helper in
    _timescales (_relaxation_mass_and_density) and paper/limitations.md#average-object-mass.
    """
    c = config.cluster
    cq = _cluster_quantities(a, config)
    mean_object_mass, rho = _relaxation_mass_and_density(cq, config)
    return relaxation.relaxation_timescale(cq["sigma_star"], rho, mean_object_mass, c.coulomb_log)


def _apply_relaxation_walk(pop, active_idx, still_active_mask, dt, config, rng, t_global_yr):
    """Apply the relaxation random walk to BHs that are still 'active' after the
    collision/capture channels this step, broken into `relaxation_substeps` sub-steps
    (see module docstring and paper/limitations.md#phase2-emri-rate-high) so the local
    dynamics get re-evaluated at the BH's *current* semimajar axis partway through the
    walk, rather than only at the start of the (potentially huge, in orbit count)
    timestep. `still_active_mask` is a boolean mask over `active_idx`'s positions.
    """
    c = config.cluster
    idx = active_idx[still_active_mask]
    if idx.size == 0:
        return

    n_sub = config.integration.relaxation_substeps
    dt_sub = dt / n_sub

    a = pop.a[idx].copy()
    e = pop.e[idx].copy()
    bound_final = np.ones(idx.size, dtype=bool)
    #: still being substepped this timestep -- drops out (frozen a/e/bound_final) as
    #: soon as a BH is kicked unbound (ejected) or beyond a_max (excursion), matching the
    #: original one-shot code's behavior of not processing those further this step.
    alive = np.ones(idx.size, dtype=bool)

    for _ in range(n_sub):
        live_pos = np.flatnonzero(alive)
        if live_pos.size == 0:
            break
        a_live = a[live_pos]

        t_relax_live = _local_t_relax(a_live, config)
        period = orbital_dynamics.orbital_period(a_live, c.m_smbh)
        per_orbit_sigma = orbital_dynamics.relaxation_kick_sigma(a_live, c.m_smbh, t_relax_live)
        n_orbits = np.maximum(dt_sub / period, 1.0)  # at least one "orbit" of kick per sub-step
        aggregated_sigma = per_orbit_sigma * np.sqrt(n_orbits)
        kick_speed = np.abs(rng.normal(0, aggregated_sigma))

        a_new, e_new, bound = orbital_dynamics.apply_velocity_kick(
            a_live, e[live_pos], c.m_smbh, kick_speed, rng
        )
        a[live_pos] = a_new
        e[live_pos] = e_new
        bound_final[live_pos] = bound
        alive[live_pos] = bound & (a_new <= c.a_max_pc)

    _finalize_orbit_after_kick(pop, idx, a, e, bound_final, c, t_global_yr)


def _apply_gw_inspiral_decay(pop, idx, cluster_cfg, dt):
    if idx.size == 0:
        return
    a = pop.a[idx]
    e = pop.e[idx]
    mass = pop.mass[idx]
    da = inspiral.da_dt(mass, cluster_cfg.m_smbh, a, e)
    de = inspiral.de_dt(mass, cluster_cfg.m_smbh, a, e)
    new_a = np.maximum(a + da * dt, 1e-12)
    new_e = np.clip(e + de * dt, 0, 0.999999)
    pop.a[idx] = new_a
    pop.e[idx] = new_e


def _check_excursion_reentry(pop, t_global_yr, cluster_cfg):
    excursion = pop.status == "excursion"
    ready = excursion & (t_global_yr >= pop.reactivation_time_yr)
    pop.status[ready] = "active"
    pop.a[ready] = cluster_cfg.a_max_pc


def _check_emri(pop, cluster_cfg, t_global_yr, emri_rows):
    active = pop.status == "active"
    if not np.any(active):
        return
    idx = np.flatnonzero(active)
    a = pop.a[idx]
    e = pop.e[idx]
    mass = pop.mass[idx]
    periapsis = a * (1 - e)
    tau = inspiral.remaining_merger_time_circular(mass, cluster_cfg.m_smbh, a)
    flags = inspiral.is_emri(periapsis, cluster_cfg.m_smbh, tau)
    for k in np.flatnonzero(flags):
        bh_idx = idx[k]
        emri_rows.append(
            dict(
                time_yr=t_global_yr,
                mass=pop.mass[bh_idx],
                chi=pop.chi[bh_idx],
                a=pop.a[bh_idx],
                e=pop.e[bh_idx],
                generation=pop.generation[bh_idx],
            )
        )
    pop.status[idx[flags]] = "emri"


def _log_new_ejections(pop, active_idx, t_global_yr, ejection_rows):
    newly_ejected = pop.status[active_idx] == "ejected"
    for bh_idx in active_idx[newly_ejected]:
        ejection_rows.append(
            dict(
                time_yr=t_global_yr,
                mass=pop.mass[bh_idx],
                chi=pop.chi[bh_idx],
                generation=pop.generation[bh_idx],
            )
        )
