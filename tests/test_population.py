import numpy as np
import pytest

from imbh_nuclei.inspiral import remaining_merger_time_circular
from imbh_nuclei.population import (
    A_MAX_PC,
    A_MIN_PC_DEFAULT,
    PopulationState,
    a_min_safety_bound,
    initialize_population,
    sample_log_uniform_semimajor_axis,
    sample_thermal_eccentricity,
)


class TestThermalEccentricity:
    def test_within_bounds(self):
        rng = np.random.default_rng(0)
        e = sample_thermal_eccentricity(10000, rng)
        assert np.all(e >= 0) and np.all(e < 1)

    def test_matches_thermal_cdf(self):
        # CDF(e) = e^2 for a thermal distribution -- check the empirical CDF at a few
        # points against the analytic one with a generous tolerance for sampling noise
        rng = np.random.default_rng(1)
        e = sample_thermal_eccentricity(200000, rng)
        for e0 in [0.2, 0.5, 0.8]:
            empirical = np.mean(e < e0)
            assert empirical == pytest.approx(e0**2, abs=0.01)

    def test_mean_matches_thermal_distribution(self):
        # E[e] = 2/3 for p(e)=2e on [0,1)
        rng = np.random.default_rng(2)
        e = sample_thermal_eccentricity(200000, rng)
        assert np.mean(e) == pytest.approx(2 / 3, abs=0.01)


class TestLogUniformSemimajorAxis:
    def test_within_bounds(self):
        rng = np.random.default_rng(0)
        a = sample_log_uniform_semimajor_axis(10000, rng, a_min=1e-4, a_max=0.1)
        assert np.all(a >= 1e-4) and np.all(a <= 0.1)

    def test_log_uniform_not_linear_uniform(self):
        # a log-uniform sample should have most values clustered at small a (in linear
        # space), since equal probability per decade
        rng = np.random.default_rng(3)
        a = sample_log_uniform_semimajor_axis(100000, rng, a_min=1e-4, a_max=0.1)
        frac_below_midpoint_decade = np.mean(a < 1e-2)  # geometric midpoint of [1e-4,1e-1]
        assert frac_below_midpoint_decade == pytest.approx(2 / 3, abs=0.02)

    def test_default_bounds_match_documented_constants(self):
        assert A_MAX_PC == pytest.approx(0.1)
        assert A_MIN_PC_DEFAULT == pytest.approx(1.0e-3)


class TestAMinSafetyBound:
    """Phase 5's generalization of A_MIN_PC_DEFAULT to other SMBH masses -- see
    a_min_safety_bound's docstring for why holding A_MIN_PC_DEFAULT fixed across a
    SMBH-mass scan would silently reintroduce the prompt-EMRI sampling artifact that
    constant was originally introduced to avoid.
    """

    def test_at_fiducial_mass_close_to_but_not_equal_default(self):
        # 4e6 Msun is N26's own fiducial SMBH mass -- a_min_safety_bound's exact
        # inversion should land close to, but need not exactly equal, the
        # manually-chosen A_MIN_PC_DEFAULT.
        a_min = a_min_safety_bound(4.0e6)
        assert a_min == pytest.approx(9.452e-4, rel=1e-3)
        assert a_min != A_MIN_PC_DEFAULT

    def test_recovers_target_inspiral_time(self):
        # by construction, a BH at a_min_safety_bound(m_smbh) should take exactly the
        # target quiescent GW-inspiral time to merge, for any m_smbh.
        for m_smbh in [1.0e5, 4.0e6, 1.0e8]:
            a_min = a_min_safety_bound(m_smbh)
            tau_yr = remaining_merger_time_circular(20.0, m_smbh, a_min)
            assert tau_yr == pytest.approx(1450.0e9, rel=1e-6)

    def test_increases_with_smbh_mass(self):
        # heavier SMBH -> faster quiescent inspiral at fixed a -> a_min must move
        # outward to preserve the same safety margin.
        a_min_light = a_min_safety_bound(1.0e5)
        a_min_heavy = a_min_safety_bound(1.0e8)
        assert a_min_heavy > a_min_light

    def test_holding_default_fixed_would_break_the_safety_margin_at_high_mass(self):
        # demonstrates the actual bug this function exists to avoid: at a SMBH mass an
        # order of magnitude above N26's fiducial value, the *original* A_MIN_PC_DEFAULT
        # no longer gives a safe (>>10 Gyr) inspiral time.
        tau_yr = remaining_merger_time_circular(20.0, 4.0e7, A_MIN_PC_DEFAULT)
        assert tau_yr / 1e9 < 100.0  # Gyr -- no longer >>10 Gyr safe margin


class TestInitializePopulation:
    def _mass_sampler(self, n, rng):
        return np.full(n, 30.0)

    def _spin_sampler(self, n, rng):
        return np.zeros(n)

    def test_basic_shapes_and_defaults(self):
        rng = np.random.default_rng(0)
        pop = initialize_population(1000, self._mass_sampler, self._spin_sampler, rng)
        assert len(pop) == 1000
        assert np.all(pop.mass == 30.0)
        assert np.all(pop.chi == 0.0)
        assert np.all(pop.generation == 1)
        assert np.all(pop.n_collisions == 0)
        assert np.all(pop.status == "active")
        assert np.all(pop.active)
        assert np.all((pop.a >= A_MIN_PC_DEFAULT) & (pop.a <= A_MAX_PC))
        assert np.all((pop.e >= 0) & (pop.e < 1))

    def test_active_property_reflects_status_changes(self):
        rng = np.random.default_rng(0)
        pop = initialize_population(10, self._mass_sampler, self._spin_sampler, rng)
        pop.status[0] = "emri"
        pop.status[1] = "ejected"
        assert pop.active.sum() == 8
        assert not pop.active[0]
        assert not pop.active[1]

    def test_reproducible_with_seed(self):
        pop1 = initialize_population(
            100, self._mass_sampler, self._spin_sampler, np.random.default_rng(7)
        )
        pop2 = initialize_population(
            100, self._mass_sampler, self._spin_sampler, np.random.default_rng(7)
        )
        np.testing.assert_array_equal(pop1.a, pop2.a)
        np.testing.assert_array_equal(pop1.e, pop2.e)
