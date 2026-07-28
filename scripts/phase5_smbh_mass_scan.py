"""Phase 5: does the critical-mass-threshold picture generalize to SMBH masses other
than the Milky Way's? N26's own second open question (Section 5.4, alongside the
sharp-vs-gradual threshold question Phase 4 answered): "does our result generalize to
galaxies with different central black hole masses?"

Design decided with the user (2026-07-28), see paper/limitations.md#phase5-smbh-mass-scan
for the full writeup. Key choice: HOLD the cluster's structural profile (rho0, r0,
n0_bh, r_h, alpha_star, alpha_bh) fixed at N26's Milky-Way-specific values and vary only
m_smbh -- N26 never specifies how these would scale for a different-mass SMBH
(docs/equations.md's Appendix note), so this isolates the pure *dynamical* effect of
m_smbh (velocity dispersion, relaxation time, GW-capture rate, EMRI-stopping physics all
depend on m_smbh directly) from the separate, unresolved question of how a real galaxy's
density profile would differ. Flagged explicitly as our own extension (Gate 1c), not a
claim about real galaxies of other masses.

Grid: 7 m_smbh points, log-spaced across 3 decades centered on N26's own fiducial value
(4e6 Msun is included exactly, as an exact-reproduction anchor against Phase 3/4):
    1.264911e5, 4e5, 1.264911e6, 4e6, 1.264911e7, 4e7, 1.264911e8  [Msun]

Two per-point quantities MUST be recomputed, not held fixed, because they are numerical/
derived rather than structural:
- coulomb_log = ln(m_smbh / 1 Msun) -- ClusterConfig.coulomb_log's own docstring already
  flags this (paper/limitations.md#coulomb-logarithm).
- a_min_pc -- population.A_MIN_PC_DEFAULT (1e-3 pc) was reverse-engineered so quiescent
  GW inspiral from that radius takes >>10 Gyr specifically at m_smbh=4e6; since that
  inspiral time scales roughly as 1/m_smbh^2, holding it fixed across this grid would
  silently reintroduce the exact prompt-EMRI sampling artifact A_MIN_PC_DEFAULT was
  introduced to avoid (see population.a_min_safety_bound's docstring). Generalized via
  that function -- but ONLY as a floor, not applied unconditionally: a_min_pc =
  max(A_MIN_PC_DEFAULT, a_min_safety_bound(m_smbh)). Letting a_min shrink below the
  default at low m_smbh (as a first version of this script did) was tried and found
  broken by an actual smoke-test hang, not just reasoned out: a_min_safety_bound(1.26e5)
  gives ~1.7e-4 pc, and at that radius the held-fixed stellar density profile (rho ~
  r^-alpha, uncapped) has blown up to ~1.25e10 Msun/pc^3 -- ~9000x its r0 calibration
  value and ~9x even the already-extreme MW-anchor density -- which collapses the
  collision timescale and drives the adaptive step count toward the 2e6-step ceiling
  (observed directly: >40 min with no convergence, vs. 27s once clamped). Since inspiral
  is naturally slower at low m_smbh anyway, the default is already a safe margin there;
  the clamp only lets a_min grow (at high m_smbh) and never shrink. This formula reduces
  to exactly A_MIN_PC_DEFAULT at the m_smbh=4e6 anchor, so that point stays bit-for-bit
  reproducible with Phase 3/4 without a separate special case.

Mass distribution held fixed at H18 (0% primordial binaries) -- N26's own literal IC
(Gate 1a, not our own extension like Phase 4's log-uniform family), and the one of the
four ICs that actually produces IMBHs at the Milky-Way mass, so it's the right choice to
show whether *that* result holds up at other m_smbh. Both Eq. 22 readings, per this
project's standing convention (paper/limitations.md#average-object-mass) of never
computing a headline number under only one reading of that still-open ambiguity. 8 seeds
per point from the start (0-7) -- per paper/methodology.md Gate 3, this is directly a
location/magnitude-adjacent comparison against the Phase 3 M_bullet=4e6 anchor, not a
bare existence claim, so the same >=8-seed bar applies immediately.

7 m_smbh points x 2 readings x 8 seeds = 112 runs.

**Timing / non-convergence, decided with the user 2026-07-28**: smoke-testing before this
launch found that low-m_smbh + star_only runs can be dramatically slower than the rest of
the grid -- likely genuine runaway growth becoming more severe at low m_smbh (velocity
dispersion is lower everywhere at fixed density, boosting collision/capture efficiency,
while coulomb_log = ln(m_smbh) also drops, weakening the relaxation process that normally
moderates growth), not a numerical artifact (the a_min/density issue above was a separate,
now-fixed problem). One seed at m_smbh=4e5 did not converge within 15 minutes. Rather than
chase a per-run timeout or narrow the grid, the decision was to run the full grid as
designed and track whether the adaptive loop hits its 2,000,000-step ceiling before
reaching 10 Gyr (`hit_step_ceiling` in the output row) as data in its own right -- "most
seeds at this m_smbh never reach 10 Gyr under star_only" would itself be a real Phase 5
finding about how runaway growth scales with SMBH mass, not a run to discard. Expect
**this script to take substantially longer than Phase 3/4's scans (potentially several
hours total)**, dominated by the low-m_smbh/star_only corner; run in the background.
"""
import os
import pickle
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
import pandas as pd

from imbh_nuclei.config import ClusterConfig, IntegrationConfig, PopulationConfig, SimulationConfig
from imbh_nuclei.initial_conditions import get_samplers
from imbh_nuclei.population import A_MIN_PC_DEFAULT, a_min_safety_bound

M_SMBH_GRID = np.array([1.264911e5, 4e5, 1.264911e6, 4.0e6, 1.264911e7, 4e7, 1.264911e8])
M_SMBH_ANCHOR = 4.0e6  # N26's own fiducial value -- exact Phase 3/4 reproduction point

MEAN_BH_MASS_H18 = 33.396222701055834  # Phase 3's MC-measured H18 mean; m_smbh-independent

READINGS = ["star_only", "bh_inclusive"]
ALL_SEEDS = list(range(8))

OUTDIR = os.path.join(os.path.dirname(__file__), "..", "results", "phase5_raw")
IMBH_MASS_THRESHOLD = 100.0


def _cluster_config(m_smbh: float) -> ClusterConfig:
    coulomb_log = float(np.log(m_smbh / 1.0))
    # a_min only needs to grow BEYOND A_MIN_PC_DEFAULT to stay safe at high m_smbh (where
    # quiescent GW inspiral is faster); at low m_smbh inspiral is naturally slower, so the
    # original default is already a safe (if conservative) margin. Critically, letting
    # a_min_safety_bound shrink it below the default at low m_smbh was tried and is WRONG
    # for a different reason: a_min then samples into a region where the held-fixed
    # stellar density profile (rho ~ r^-alpha) has blown up to ~9000x its r0 calibration
    # value, collapsing the collision timescale and driving the adaptive step count into
    # the step ceiling (found via a real smoke-test hang at m_smbh=1.26e5, >40 min with no
    # convergence -- not a hypothetical concern). Clamping to the default keeps density at
    # or below the already-validated Phase 3/4 anchor value everywhere in the grid. Note
    # this formula already reduces to exactly A_MIN_PC_DEFAULT at m_smbh=M_SMBH_ANCHOR
    # (a_min_safety_bound(4e6) < A_MIN_PC_DEFAULT), so the anchor point stays bit-for-bit
    # reproducible with Phase 3/4 without needing a special case.
    a_min_pc = max(A_MIN_PC_DEFAULT, a_min_safety_bound(m_smbh))
    return ClusterConfig(m_smbh=m_smbh, coulomb_log=coulomb_log, a_min_pc=a_min_pc)


def run_one(m_smbh, reading, seed):
    from imbh_nuclei.simulation import run_simulation  # deferred: cheap fork startup under multiprocessing

    mass_sampler, spin_sampler = get_samplers("H18")
    config = SimulationConfig(
        cluster=_cluster_config(m_smbh),
        population=PopulationConfig(
            initial_mass_distribution="H18", n_bh=1000, primordial_binary_fraction=0.0,
            mean_bh_mass=MEAN_BH_MASS_H18,
        ),
        integration=IntegrationConfig(
            t_max_gyr=10.0, dt0_yr=1.0e6, seed=seed, relaxation_mass_weighting=reading
        ),
    )
    t0 = time.time()
    result = run_simulation(config, mass_sampler, spin_sampler)
    elapsed = time.time() - t0

    tag = f"msmbh{m_smbh:.4e}_{reading}_seed{seed}"
    with open(f"{OUTDIR}/{tag}.pkl", "wb") as f:
        pickle.dump(result, f)

    pop = result.population
    mass = pop.mass
    n = len(mass)
    n_gt_100 = int(np.sum(mass > IMBH_MASS_THRESHOLD))
    # Did the adaptive-timestep loop hit its 2,000,000-step ceiling before reaching
    # t_max_gyr, rather than reaching t_max_gyr or having every BH go terminal early
    # (both legitimate reasons final_time_gyr < t_max_gyr)? Per the user's explicit
    # 2026-07-28 decision, non-convergence at the low-m_smbh/star_only corner (runaway
    # growth appears to become severe enough there that some trajectories may never
    # finish integrating to 10 Gyr within budget) is tracked as data, not treated as a
    # run failure -- see paper/limitations.md#phase5-smbh-mass-scan.
    hit_step_ceiling = bool(result.n_steps >= 2_000_000 and result.final_time_gyr < config.integration.t_max_gyr - 1e-6)
    return dict(
        m_smbh=m_smbh,
        coulomb_log=config.cluster.coulomb_log,
        a_min_pc=config.cluster.a_min_pc,
        reading=reading,
        seed=seed,
        elapsed_s=elapsed,
        n_steps=result.n_steps,
        final_time_gyr=result.final_time_gyr,
        hit_step_ceiling=hit_step_ceiling,
        n_mergers=len(result.merger_log),
        max_mass=float(mass.max()),
        max_spin=float(pop.chi[np.argmax(mass)]) if n else np.nan,
        p99_mass=float(np.percentile(mass, 99)),
        n_gt_100=n_gt_100,
        pct_gt_100=100.0 * n_gt_100 / n,
        any_gt_100=bool(n_gt_100 > 0),
        n_emri=len(result.emri_log),
        pct_emri=100.0 * len(result.emri_log) / n,
        n_ejected=int(np.sum(pop.status == "ejected")),
        max_generation=int(pop.generation.max()),
    )


if __name__ == "__main__":
    os.makedirs(OUTDIR, exist_ok=True)
    jobs = [
        (m_smbh, reading, seed)
        for m_smbh in M_SMBH_GRID
        for reading in READINGS
        for seed in ALL_SEEDS
    ]
    print(f"{len(jobs)} jobs queued: {len(M_SMBH_GRID)} m_smbh points x {len(READINGS)} readings "
          f"x {len(ALL_SEEDS)} seeds")

    rows = []
    with ProcessPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(run_one, *job): job for job in jobs}
        for fut in as_completed(futures):
            m_smbh, reading, seed = futures[fut]
            try:
                row = fut.result()
                rows.append(row)
                ceiling_flag = " HIT_STEP_CEILING" if row["hit_step_ceiling"] else ""
                print(f"DONE m_smbh={m_smbh:.4e} reading={reading} seed={seed}: "
                      f"pct_gt_100={row['pct_gt_100']:.2f} any_gt_100={row['any_gt_100']} "
                      f"n_mergers={row['n_mergers']} elapsed={row['elapsed_s']:.0f}s"
                      f"{ceiling_flag}", flush=True)
            except Exception as e:
                print(f"FAILED m_smbh={m_smbh:.4e} reading={reading} seed={seed}: {e}", flush=True)

    df = pd.DataFrame(rows)
    df.to_csv(f"{OUTDIR}/summary.csv", index=False)
    print("ALL DONE")
    print(df)
