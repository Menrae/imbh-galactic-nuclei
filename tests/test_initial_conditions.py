import numpy as np
import pytest

from imbh_nuclei.initial_conditions import (
    H18_MASS_MAX,
    H18_MASS_MIN,
    apply_primordial_mergers,
    get_log_uniform_samplers,
    get_samplers,
    log_uniform_mean,
    sample_h18_mass,
    sample_h18_plus_m,
    sample_k20_mass,
    sample_k20_plus_m,
    sample_log_uniform_mass,
    zero_spin,
)


class TestK20Mass:
    def test_within_expected_range(self):
        rng = np.random.default_rng(0)
        m = sample_k20_mass(10000, rng)
        assert np.all(m >= 7.0) and np.all(m < 16.0)

    def test_most_mass_in_lowest_bin(self):
        # N26 Figure 1: K20 is dominated by a large peak near 7-9 Msun
        rng = np.random.default_rng(1)
        m = sample_k20_mass(10000, rng)
        assert np.mean(m < 9.25) > 0.5

    def test_zero_spin(self):
        assert np.all(zero_spin(100, np.random.default_rng(0)) == 0.0)


class TestH18Mass:
    def test_within_paper_range(self):
        rng = np.random.default_rng(0)
        m = sample_h18_mass(10000, rng)
        assert np.all(m >= H18_MASS_MIN) and np.all(m <= H18_MASS_MAX)

    def test_log_uniform_not_linear_uniform(self):
        # dN/dm ~ m^-1 -> most draws should cluster toward the low-mass end in linear space
        rng = np.random.default_rng(2)
        m = sample_h18_mass(100000, rng)
        # geometric midpoint of [6,100] is sqrt(600) ~ 24.5; log-uniform puts 2/3 of the
        # decades below that (log10(24.5/6) / log10(100/6) ~ 0.5, so use a direct check
        # against the analytic log-uniform CDF instead of eyeballing a fraction)
        frac_below_24_5 = np.mean(m < np.sqrt(H18_MASS_MIN * H18_MASS_MAX))
        assert frac_below_24_5 == pytest.approx(0.5, abs=0.02)

    def test_matches_paper_qualitative_max(self):
        # N26: "B.-M. Hoang et al.'s (2018) initial mass distribution extends up to ~90 Msun"
        rng = np.random.default_rng(3)
        m = sample_h18_mass(100000, rng)
        assert m.max() < H18_MASS_MAX
        assert m.max() > 80.0  # should get close to the upper bound with 1e5 draws


class TestPrimordialMergers:
    def test_preserves_population_size(self):
        rng = np.random.default_rng(0)
        mass = sample_k20_mass(1000, rng)
        chi = zero_spin(1000, rng)
        new_mass, new_chi = apply_primordial_mergers(mass, chi, sample_k20_mass, rng)
        assert len(new_mass) == 1000
        assert len(new_chi) == 1000

    def test_produces_some_higher_mass_remnants(self):
        # merging two K20 BHs (max ~16 Msun each) should produce some remnants above the
        # base distribution's own max
        rng = np.random.default_rng(0)
        mass = sample_k20_mass(1000, rng)
        chi = zero_spin(1000, rng)
        new_mass, _ = apply_primordial_mergers(mass, chi, sample_k20_mass, rng)
        assert new_mass.max() > mass.max()

    def test_remnant_spin_nonzero_from_orbital_angular_momentum(self):
        # both progenitors are nonspinning (chi=0), but the merger remnant still gets
        # spin from orbital angular momentum (Eq. 10's "ell" term) -- N26 notes this
        # produces "a peak around 0.7" for the +M initial conditions
        rng = np.random.default_rng(0)
        mass = sample_k20_mass(1000, rng)
        chi = zero_spin(1000, rng)
        _, new_chi = apply_primordial_mergers(mass, chi, sample_k20_mass, rng)
        assert np.any(new_chi > 0)

    def test_no_op_for_tiny_population(self):
        # with n_bh small enough that 15% rounds to fewer than 2 (no pairs possible),
        # should return the input unchanged rather than error
        rng = np.random.default_rng(0)
        mass = sample_k20_mass(5, rng)
        chi = zero_spin(5, rng)
        new_mass, new_chi = apply_primordial_mergers(mass, chi, sample_k20_mass, rng)
        np.testing.assert_array_equal(new_mass, mass)
        np.testing.assert_array_equal(new_chi, chi)


class TestKPlusMAndHPlusM:
    def test_k20_plus_m_max_mass_exceeds_k20_max(self):
        rng = np.random.default_rng(0)
        mass, chi = sample_k20_plus_m(1000, rng)
        assert len(mass) == 1000
        assert mass.max() > 16.0  # base K20 max

    def test_h18_plus_m_max_mass_exceeds_h18_max(self):
        rng = np.random.default_rng(0)
        mass, chi = sample_h18_plus_m(1000, rng)
        assert len(mass) == 1000
        assert mass.max() > H18_MASS_MAX


class TestLogUniformMassScan:
    """Phase 4's mass-scale scan family -- see sample_log_uniform_mass's docstring and
    paper/limitations.md#phase4-mass-family-scan.
    """

    def test_reduces_to_h18_at_h18_bounds(self):
        # sample_h18_mass IS sample_log_uniform_mass(m_min=6, m_max=100) -- confirm the
        # generalization reproduces the special case exactly (same rng stream).
        m_h18 = sample_h18_mass(1000, np.random.default_rng(0))
        m_generic = sample_log_uniform_mass(1000, np.random.default_rng(0), H18_MASS_MIN, H18_MASS_MAX)
        np.testing.assert_array_equal(m_h18, m_generic)

    def test_within_bounds(self):
        rng = np.random.default_rng(1)
        m = sample_log_uniform_mass(10000, rng, m_min=6.0, m_max=25.0)
        assert np.all(m >= 6.0) and np.all(m <= 25.0)

    def test_smaller_m_max_gives_smaller_draws_on_average(self):
        rng = np.random.default_rng(2)
        m_low = sample_log_uniform_mass(10000, rng, m_min=6.0, m_max=16.0)
        m_high = sample_log_uniform_mass(10000, rng, m_min=6.0, m_max=100.0)
        assert m_low.mean() < m_high.mean()

    def test_log_uniform_mean_matches_h18_measured_mean(self):
        # Phase 3 measured H18's true Monte Carlo mean as 33.396 (N=2e6) -- the closed
        # form should land within MC noise of that (paper/limitations.md#mean-bh-mass-placeholder).
        assert log_uniform_mean(H18_MASS_MIN, H18_MASS_MAX) == pytest.approx(33.396, abs=0.05)

    def test_log_uniform_mean_matches_empirical_sample_mean(self):
        rng = np.random.default_rng(3)
        m = sample_log_uniform_mass(2_000_000, rng, m_min=6.0, m_max=40.0)
        assert m.mean() == pytest.approx(log_uniform_mean(6.0, 40.0), rel=1e-2)

    def test_get_log_uniform_samplers_signature(self):
        mass_sampler, spin_sampler = get_log_uniform_samplers(m_max=40.0)
        rng = np.random.default_rng(0)
        mass = mass_sampler(100, rng)
        chi = spin_sampler(100, rng)
        assert mass.shape == (100,)
        assert np.all(chi == 0.0)
        assert np.all(mass <= 40.0)

    def test_get_log_uniform_samplers_plus_m_max_mass_exceeds_base_max(self):
        # same "+M" signature as sample_k20_plus_m/sample_h18_plus_m: mergers can push
        # a remnant above the base distribution's own upper bound.
        mass_sampler, spin_sampler = get_log_uniform_samplers(
            m_max=40.0, primordial_binary_fraction=0.15
        )
        rng = np.random.default_rng(0)
        mass = mass_sampler(1000, rng)
        chi = spin_sampler(1000, rng)
        assert mass.shape == (1000,)
        assert mass.max() > 40.0
        assert np.any(chi > 0)

    def test_get_log_uniform_samplers_plus_m_zero_fraction_matches_base(self):
        # primordial_binary_fraction=0.0 must be a true no-op (same sampler as the
        # default), not a merger prescription that happens to merge nothing.
        mass_sampler, spin_sampler = get_log_uniform_samplers(
            m_max=40.0, primordial_binary_fraction=0.0
        )
        rng_a = np.random.default_rng(0)
        rng_b = np.random.default_rng(0)
        mass_base = sample_log_uniform_mass(1000, rng_a, H18_MASS_MIN, 40.0)
        mass_default = mass_sampler(1000, rng_b)
        np.testing.assert_array_equal(mass_base, mass_default)

    def test_get_log_uniform_samplers_plus_m_spin_before_mass_raises(self):
        # _PairedSampler requires mass_sampler called immediately before spin_sampler;
        # calling spin_sampler with no pending draw must raise, not silently return
        # something mismatched.
        mass_sampler, spin_sampler = get_log_uniform_samplers(
            m_max=40.0, primordial_binary_fraction=0.15
        )
        rng = np.random.default_rng(0)
        with pytest.raises(RuntimeError):
            spin_sampler(100, rng)


class TestGetSamplers:
    @pytest.mark.parametrize("name", ["K20", "K20+M", "H18", "H18+M"])
    def test_returns_callables_with_correct_signature(self, name):
        mass_sampler, spin_sampler = get_samplers(name)
        rng = np.random.default_rng(0)
        mass = mass_sampler(100, rng)
        chi = spin_sampler(100, rng)
        assert mass.shape == (100,)
        assert chi.shape == (100,)

    def test_unknown_name_raises(self):
        with pytest.raises(ValueError):
            get_samplers("not-a-real-IC")

    def test_paired_sampler_mass_and_spin_correlated(self):
        # regression test for a real bug: calling mass_sampler and spin_sampler
        # independently for a +M IC used to draw two different populations, so a
        # remnant's logged mass didn't correspond to its own spin. Check that repeated
        # mass/spin pairs (mimicking many timesteps' worth of partner draws with the
        # same rng) stay consistent with each other.
        mass_sampler, spin_sampler = get_samplers("K20+M")
        rng = np.random.default_rng(0)
        for n in [3, 3, 5, 3, 7, 3]:  # deliberately repeat n to stress the old bug
            mass = mass_sampler(n, rng)
            chi = spin_sampler(n, rng)
            assert mass.shape == (n,)
            assert chi.shape == (n,)

    def test_paired_sampler_raises_if_spin_called_without_mass(self):
        mass_sampler, spin_sampler = get_samplers("H18+M")
        rng = np.random.default_rng(0)
        with pytest.raises(RuntimeError):
            spin_sampler(10, rng)
