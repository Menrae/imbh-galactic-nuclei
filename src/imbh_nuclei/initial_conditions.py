"""The four published initial BH mass/spin distributions (Newton et al. 2026, Section 3):
K20, K20+M, H18, H18+M.

See docs/equations.md#initial-conditions for full sourcing and the reconstruction method
used for K20 (Kremer et al. 2020's underlying distribution is a CMC simulation output,
not a closed-form function given in that paper -- reconstructed here from N26's own
Figure 1 histogram instead). H18 is an exact closed form, confirmed directly from
B.-M. Hoang et al. 2018's text.
"""

from __future__ import annotations

import numpy as np

from imbh_nuclei.gw_capture import chi_parallel, final_spin, orbital_ell, remnant_mass

#: H18 base distribution: log-uniform (dN/dm ~ m^-1) between 6-100 Msun, confirmed
#: directly from B.-M. Hoang et al. 2018 ("the mass of each of the BHs is chosen from a
#: distribution uniform in logspace between 6-100 Msun (i.e. dN/dm ~ m^-1)").
H18_MASS_MIN = 6.0
H18_MASS_MAX = 100.0

#: K20 base distribution bin edges/relative weights [Msun], reconstructed by reading
#: N26's own Figure 1 (left panel, green "K20" histogram) directly -- Kremer et al. 2020
#: is a CMC stellar-collision simulation whose output BH mass function is not given as a
#: closed-form expression in that paper, so this is the most direct available
#: reconstruction of what N26 actually sampled from. Approximate, read by eye from the
#: published figure, not exact data extraction -- see paper/limitations.md#k20-reconstruction.
K20_BIN_EDGES = np.array([7.0, 9.25, 11.5, 13.75, 16.0])
K20_BIN_WEIGHTS = np.array([660.0, 120.0, 68.0, 150.0])

#: Primordial-binary-merger prescription (N26 Section 3): 15% of the BH population is
#: considered to be in primordial binaries (i.e. paired up), and one third of those PAIRS
#: undergo a merger (replaced by a single remnant via the Eq. 8-12 formulas); the
#: remaining two thirds of pairs stay as unmerged singles. To hold the sample size fixed
#: at n_bh, the BHs "consumed" by mergers beyond what the remnants replace are backfilled
#: with fresh draws from the base distribution -- N26 does not spell out this bookkeeping
#: explicitly; this is our reasonable, documented interpretation of "15%... a third merged".
PRIMORDIAL_BINARY_FRACTION = 0.15
MERGED_FRACTION_OF_PAIRS = 1.0 / 3.0


def sample_k20_mass(n: int, rng: np.random.Generator) -> np.ndarray:
    """K20 base mass distribution -- see K20_BIN_EDGES docstring note above."""
    probs = K20_BIN_WEIGHTS / K20_BIN_WEIGHTS.sum()
    bin_idx = rng.choice(len(probs), size=n, p=probs)
    lo = K20_BIN_EDGES[bin_idx]
    hi = K20_BIN_EDGES[bin_idx + 1]
    return rng.uniform(lo, hi)


def sample_h18_mass(n: int, rng: np.random.Generator) -> np.ndarray:
    """H18 base mass distribution: log-uniform in [6, 100] Msun."""
    log_m = rng.uniform(np.log10(H18_MASS_MIN), np.log10(H18_MASS_MAX), size=n)
    return 10.0**log_m


def sample_log_uniform_mass(n: int, rng: np.random.Generator, m_min: float, m_max: float) -> np.ndarray:
    """Log-uniform mass distribution in [m_min, m_max] Msun, i.e. dN/dm ~ m^-1 -- the
    same functional form as H18 (`sample_h18_mass` is the special case
    m_min=H18_MASS_MIN, m_max=H18_MASS_MAX), generalized to an arbitrary upper bound.

    Introduced for Phase 4's initial-mass-distribution scan: N26 only gives four
    discrete initial conditions (K20, K20+M, H18, H18+M) and explicitly flags "whether
    there is a mass distribution between our lower and upper limits that consistently
    produces IMBHs" as future work (Section 5.4) without proposing a family to scan.
    This family holds m_min fixed at H18's own value and scans only m_max, so it
    reproduces H18 exactly at m_max=100 -- it does NOT reproduce K20's true
    reconstructed shape (K20_BIN_EDGES/K20_BIN_WEIGHTS is concentrated/non-log-uniform
    in 7-16 Msun, not log-uniform) at the low end; it is an approximate low-mass anchor,
    not a K20 substitute. See paper/limitations.md#phase4-mass-family-scan.
    """
    log_m = rng.uniform(np.log10(m_min), np.log10(m_max), size=n)
    return 10.0**log_m


def log_uniform_mean(m_min: float, m_max: float) -> float:
    """Closed-form mean of the log-uniform distribution on [m_min, m_max]:
    integral of m * (1/m)/ln(m_max/m_min) dm = (m_max - m_min) / ln(m_max/m_min).

    Used as `PopulationConfig.mean_bh_mass` for `sample_log_uniform_mass` draws --
    exact, not a Monte Carlo estimate (unlike K20's reconstructed sampler, which has no
    closed form and needs `PopulationConfig.mean_bh_mass` set from a large-N Monte
    Carlo estimate instead; see paper/limitations.md#mean-bh-mass-placeholder). Sanity
    check: log_uniform_mean(6.0, 100.0) == 33.40..., matching H18's independently
    Monte-Carlo-measured mean (33.396) to within MC noise.
    """
    return (m_max - m_min) / np.log(m_max / m_min)


def zero_spin(n: int, rng: np.random.Generator) -> np.ndarray:
    """K20 and H18 (without mergers) are single, nonspinning from birth (N26 Section 3)."""
    return np.zeros(n)


def apply_primordial_mergers(
    mass: np.ndarray,
    chi: np.ndarray,
    base_mass_sampler,
    rng: np.random.Generator,
    binary_fraction: float = PRIMORDIAL_BINARY_FRACTION,
    merged_fraction: float = MERGED_FRACTION_OF_PAIRS,
) -> tuple[np.ndarray, np.ndarray]:
    """Apply the primordial-binary-merger prescription to a base single-BH population,
    producing the "+M" variant while holding the sample size fixed.

    See PRIMORDIAL_BINARY_FRACTION's docstring note for the bookkeeping interpretation.
    Merger remnant mass/spin use the same Eq. 8-12 machinery as the Phase 2 GW-capture
    channel, with randomly-drawn (isotropic) spin-orientation angles per merger -- both
    progenitors are nonspinning here (K20/H18 base BHs have chi=0), so remnant spin comes
    entirely from orbital angular momentum (Eq. 10's "ell" term), matching N26's own
    observation that "the initial conditions with mergers have a peak around 0.7" for
    exactly this reason.

    Parameters
    ----------
    mass, chi : ndarray
        Base (single, nonspinning) population, length n_bh.
    base_mass_sampler : Callable[[int, np.random.Generator], np.ndarray]
        Used to draw backfill replacements (sample_k20_mass or sample_h18_mass).
    rng : numpy.random.Generator

    Returns
    -------
    mass, chi : ndarray
        Updated population, same length as input.
    """
    mass = mass.copy()
    chi = chi.copy()
    n_bh = len(mass)

    n_paired = int(round(binary_fraction * n_bh))
    n_paired -= n_paired % 2  # must be even to form pairs
    n_pairs = n_paired // 2
    n_merged_pairs = int(round(n_pairs * merged_fraction))
    if n_merged_pairs == 0:
        return mass, chi

    pair_idx = rng.choice(n_bh, size=n_paired, replace=False)
    merge_pairs = pair_idx[: 2 * n_merged_pairs].reshape(n_merged_pairs, 2)

    m_a = mass[merge_pairs[:, 0]]
    m_b = mass[merge_pairs[:, 1]]
    chi_a = chi[merge_pairs[:, 0]]
    chi_b = chi[merge_pairs[:, 1]]

    m1 = np.maximum(m_a, m_b)
    m2 = np.minimum(m_a, m_b)
    q = m2 / m1
    a_is_primary = m_a >= m_b
    chi1 = np.where(a_is_primary, chi_a, chi_b)
    chi2 = np.where(a_is_primary, chi_b, chi_a)

    costheta1 = rng.uniform(-1, 1, n_merged_pairs)
    costheta2 = rng.uniform(-1, 1, n_merged_pairs)
    chi_par_1 = chi1 * costheta1
    chi_par_2 = chi2 * costheta2

    chi_par_combined = chi_parallel(m1, chi_par_1, m2, chi_par_2)
    remnant_m = remnant_mass(m1, m2, chi_par_combined, prograde=True)
    ell = orbital_ell(q, chi_par_1, chi_par_2)
    remnant_chi = final_spin(q, chi_par_1, chi_par_2, ell)

    # replace one slot of each merged pair with the remnant; the other slot is
    # backfilled with a fresh draw from the base distribution (see docstring)
    remnant_slots = merge_pairs[:, 0]
    backfill_slots = merge_pairs[:, 1]
    mass[remnant_slots] = remnant_m
    chi[remnant_slots] = remnant_chi
    mass[backfill_slots] = base_mass_sampler(n_merged_pairs, rng)
    chi[backfill_slots] = 0.0

    return mass, chi


def sample_k20_plus_m(n: int, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """K20+M: K20 base distribution with the primordial-merger prescription applied."""
    mass = sample_k20_mass(n, rng)
    chi = zero_spin(n, rng)
    return apply_primordial_mergers(mass, chi, sample_k20_mass, rng)


def sample_h18_plus_m(n: int, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """H18+M: H18 base distribution with the primordial-merger prescription applied."""
    mass = sample_h18_mass(n, rng)
    chi = zero_spin(n, rng)
    return apply_primordial_mergers(mass, chi, sample_h18_mass, rng)


class _PairedSampler:
    """Shares one joint (mass, chi) draw between two separate mass_sampler/spin_sampler
    calls, as required by population.initialize_population's and
    simulation._apply_gw_captures's interface (both call mass_sampler(n, rng) then
    spin_sampler(n, rng) as two independent calls, always immediately paired, possibly
    many times over a simulation's lifetime with the same rng object threaded through).

    Without this, each call would draw an *independent* merger population, decorrelating
    a remnant's mass from its own spin -- a real bug caught before it shipped, not a
    hypothetical one. An earlier version of this class cached by (n, id(rng)), which
    breaks the moment two different call pairs share the same n with the same rng object
    (e.g. two different timesteps each producing exactly 1 GW-capture event) -- the
    second pair would silently get back the first pair's stale draw. Fixed by using a
    single-slot "pending" cache that mass_sampler always fills and spin_sampler always
    consumes-and-clears, relying only on the strict mass-then-spin call ordering already
    guaranteed by both call sites, not on any properties of n or rng.
    """

    def __init__(self, joint_sampler):
        self._joint_sampler = joint_sampler
        self._pending_chi = None

    def mass_sampler(self, n: int, rng: np.random.Generator) -> np.ndarray:
        mass, chi = self._joint_sampler(n, rng)
        self._pending_chi = chi
        return mass

    def spin_sampler(self, n: int, rng: np.random.Generator) -> np.ndarray:
        if self._pending_chi is None:
            raise RuntimeError(
                "spin_sampler called without a preceding mass_sampler call -- "
                "_PairedSampler requires strict mass-then-spin call pairing."
            )
        chi = self._pending_chi
        self._pending_chi = None
        return chi


def get_log_uniform_samplers(m_max: float, m_min: float = H18_MASS_MIN):
    """Return (mass_sampler, spin_sampler) for the Phase 4 log-uniform mass-scan family
    (see sample_log_uniform_mass), with signature (n, rng) -> ndarray matching
    get_samplers' convention. Nonspinning at birth (chi=0), same as the base K20/H18
    (no "+M" variant) -- Phase 4's first-pass scan defers the primordial-merger axis to
    a follow-up pass (see paper/limitations.md#phase4-mass-family-scan).
    """
    def mass_sampler(n: int, rng: np.random.Generator) -> np.ndarray:
        return sample_log_uniform_mass(n, rng, m_min, m_max)

    return mass_sampler, zero_spin


def get_samplers(name: str):
    """Return (mass_sampler, spin_sampler) callables for one of the four named ICs,
    each with signature (n, rng) -> ndarray, matching population.initialize_population's
    expected interface.

    Parameters
    ----------
    name : str
        One of "K20", "K20+M", "H18", "H18+M" (config.VALID_INITIAL_DISTRIBUTIONS).
    """
    if name == "K20":
        return sample_k20_mass, zero_spin
    if name == "H18":
        return sample_h18_mass, zero_spin
    if name == "K20+M":
        paired = _PairedSampler(sample_k20_plus_m)
        return paired.mass_sampler, paired.spin_sampler
    if name == "H18+M":
        paired = _PairedSampler(sample_h18_plus_m)
        return paired.mass_sampler, paired.spin_sampler
    raise ValueError(f"Unknown initial condition name: {name!r}")
