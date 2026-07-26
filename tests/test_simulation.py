import numpy as np
import pytest

from imbh_nuclei.config import ClusterConfig, IntegrationConfig, PopulationConfig, SimulationConfig
from imbh_nuclei.simulation import SimulationResults, run_simulation


def _uniform_mass_sampler(n, rng):
    return rng.uniform(10.0, 40.0, n)


def _zero_spin_sampler(n, rng):
    return np.zeros(n)


def _small_config(n_bh=30, t_max_gyr=1.0, seed=0, **overrides):
    cluster_kwargs = {k: v for k, v in overrides.items() if k in ClusterConfig.__dataclass_fields__}
    return SimulationConfig(
        cluster=ClusterConfig(**cluster_kwargs),
        population=PopulationConfig(n_bh=n_bh, mean_bh_mass=25.0),
        integration=IntegrationConfig(t_max_gyr=t_max_gyr, dt0_yr=1.0e6, seed=seed),
    )


class TestRunSimulationBasics:
    def test_returns_simulation_results(self):
        config = _small_config()
        results = run_simulation(config, _uniform_mass_sampler, _zero_spin_sampler)
        assert isinstance(results, SimulationResults)

    def test_population_size_preserved(self):
        config = _small_config(n_bh=25)
        results = run_simulation(config, _uniform_mass_sampler, _zero_spin_sampler)
        assert len(results.population) == 25

    def test_every_bh_has_valid_status(self):
        config = _small_config(n_bh=25)
        results = run_simulation(config, _uniform_mass_sampler, _zero_spin_sampler)
        valid = {"active", "excursion", "emri", "ejected"}
        assert set(np.unique(results.population.status)).issubset(valid)

    def test_time_does_not_exceed_t_max(self):
        config = _small_config(t_max_gyr=0.5)
        results = run_simulation(config, _uniform_mass_sampler, _zero_spin_sampler)
        assert results.final_time_gyr <= 0.5 + 1e-9

    def test_makes_progress(self):
        config = _small_config(t_max_gyr=0.5)
        results = run_simulation(config, _uniform_mass_sampler, _zero_spin_sampler)
        assert results.n_steps > 0
        assert results.final_time_gyr > 0

    def test_reproducible_with_same_seed(self):
        config = _small_config(seed=42)
        r1 = run_simulation(config, _uniform_mass_sampler, _zero_spin_sampler)
        r2 = run_simulation(config, _uniform_mass_sampler, _zero_spin_sampler)
        np.testing.assert_array_equal(r1.population.mass, r2.population.mass)
        np.testing.assert_array_equal(r1.population.status, r2.population.status)
        assert r1.n_steps == r2.n_steps

    def test_different_seeds_give_different_results(self):
        r1 = run_simulation(_small_config(seed=1), _uniform_mass_sampler, _zero_spin_sampler)
        r2 = run_simulation(_small_config(seed=2), _uniform_mass_sampler, _zero_spin_sampler)
        assert not np.array_equal(r1.population.mass, r2.population.mass)


class TestMassAndSpinSanity:
    def test_masses_never_negative(self):
        config = _small_config(n_bh=40, t_max_gyr=2.0)
        results = run_simulation(config, _uniform_mass_sampler, _zero_spin_sampler)
        assert np.all(results.population.mass > 0)

    def test_spin_magnitude_never_exceeds_one(self):
        config = _small_config(n_bh=40, t_max_gyr=2.0)
        results = run_simulation(config, _uniform_mass_sampler, _zero_spin_sampler)
        assert np.all(np.abs(results.population.chi) <= 1.0 + 1e-9)

    def test_generation_starts_at_one_and_never_decreases_below_it(self):
        config = _small_config(n_bh=40, t_max_gyr=2.0)
        results = run_simulation(config, _uniform_mass_sampler, _zero_spin_sampler)
        assert np.all(results.population.generation >= 1)


class TestMergerLog:
    def test_schema_when_present(self):
        # use a larger N and longer time to reliably get at least one merger
        config = _small_config(n_bh=300, t_max_gyr=10.0, seed=1)
        results = run_simulation(config, _uniform_mass_sampler, _zero_spin_sampler)
        if len(results.merger_log) == 0:
            pytest.skip("no mergers occurred in this realization")
        expected_cols = {
            "time_yr", "generation", "m1", "m2", "chi1", "chi2", "chi_eff",
            "remnant_mass", "remnant_chi", "kick_speed_kms", "bound_after_kick",
        }
        assert expected_cols.issubset(results.merger_log.columns)

    def test_remnant_mass_less_than_total_progenitor_mass(self):
        config = _small_config(n_bh=300, t_max_gyr=10.0, seed=1)
        results = run_simulation(config, _uniform_mass_sampler, _zero_spin_sampler)
        if len(results.merger_log) == 0:
            pytest.skip("no mergers occurred in this realization")
        log = results.merger_log
        assert np.all(log["remnant_mass"] < log["m1"] + log["m2"])

    def test_remnant_spin_within_bounds(self):
        config = _small_config(n_bh=300, t_max_gyr=10.0, seed=1)
        results = run_simulation(config, _uniform_mass_sampler, _zero_spin_sampler)
        if len(results.merger_log) == 0:
            pytest.skip("no mergers occurred in this realization")
        assert np.all(results.merger_log["remnant_chi"] <= 1.0 + 1e-9)
        assert np.all(results.merger_log["remnant_chi"] >= 0.0)

    def test_generation_increments_from_progenitor(self):
        config = _small_config(n_bh=300, t_max_gyr=10.0, seed=1)
        results = run_simulation(config, _uniform_mass_sampler, _zero_spin_sampler)
        if len(results.merger_log) == 0:
            pytest.skip("no mergers occurred in this realization")
        assert np.all(results.merger_log["generation"] >= 2)


class TestEmriAndEjectionLogs:
    def test_emri_log_schema_when_present(self):
        config = _small_config(n_bh=50, t_max_gyr=10.0, seed=0)
        results = run_simulation(config, _uniform_mass_sampler, _zero_spin_sampler)
        if len(results.emri_log) == 0:
            pytest.skip("no EMRIs occurred in this realization")
        expected_cols = {"time_yr", "mass", "chi", "a", "e", "generation"}
        assert expected_cols.issubset(results.emri_log.columns)

    def test_emri_flagged_bhs_marked_terminal_in_population(self):
        config = _small_config(n_bh=50, t_max_gyr=10.0, seed=0)
        results = run_simulation(config, _uniform_mass_sampler, _zero_spin_sampler)
        if len(results.emri_log) == 0:
            pytest.skip("no EMRIs occurred in this realization")
        assert (results.population.status == "emri").sum() == len(results.emri_log)

    def test_ejection_log_schema_when_present(self):
        config = _small_config(n_bh=300, t_max_gyr=10.0, seed=1)
        results = run_simulation(config, _uniform_mass_sampler, _zero_spin_sampler)
        if len(results.ejection_log) == 0:
            pytest.skip("no ejections occurred in this realization")
        expected_cols = {"time_yr", "mass", "chi", "generation"}
        assert expected_cols.issubset(results.ejection_log.columns)


class TestExcursionReactivation:
    def test_excursion_bhs_are_not_permanently_stuck(self):
        # Regression test for a real bug found via smoke testing: BHs kicked beyond
        # a_max used to be permanently frozen in 'excursion' status once zero BHs
        # remained 'active', because the old loop condition only checked
        # pop.active.any(). Force many excursions by using a low kick threshold (small
        # a_max) and confirm that, given enough simulation time, BHs do NOT all end up
        # stuck in 'excursion' -- some must have reactivated and moved on to another
        # status (active/emri/ejected).
        config = _small_config(n_bh=60, t_max_gyr=10.0, seed=3, a_max_pc=0.01)
        results = run_simulation(config, _uniform_mass_sampler, _zero_spin_sampler)
        # if the bug were present, once all 60 were kicked into excursion the loop
        # would stop instantly at whatever tiny time that occurred, and n_steps/
        # final_time_gyr would be far below t_max; the fix ensures the loop keeps
        # running (via the fast-forward branch) until t_max or all BHs reach a
        # terminal state.
        assert results.final_time_gyr == pytest.approx(10.0, rel=1e-6) or not np.any(
            results.population.status == "excursion"
        )


class TestCapturePathwayFires:
    def test_at_least_one_merger_across_several_seeds(self):
        # the capture channel is a low-probability-per-step event; check across a
        # handful of seeds that it fires at least once somewhere, confirming the
        # pathway is reachable at all (not asserting a specific rate -- that is a
        # Phase 3 calibration question, see paper/limitations.md#phase2-emri-rate-high)
        total_mergers = 0
        for seed in range(5):
            config = _small_config(n_bh=200, t_max_gyr=10.0, seed=seed)
            results = run_simulation(config, _uniform_mass_sampler, _zero_spin_sampler)
            total_mergers += len(results.merger_log)
        assert total_mergers > 0
