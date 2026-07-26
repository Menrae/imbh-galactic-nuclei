import numpy as np
import pytest

from imbh_nuclei.relaxation import (
    average_object_mass,
    relaxation_timescale,
    segregation_timescale,
)


class TestAverageObjectMass:
    def test_pure_star_population_gives_star_mass(self):
        m_avg = average_object_mass(n_star=1e6, n_bh=0.0, mean_bh_mass=20.0)
        assert m_avg == pytest.approx(1.0)

    def test_pure_bh_population_gives_bh_mass(self):
        m_avg = average_object_mass(n_star=0.0, n_bh=1e4, mean_bh_mass=20.0)
        assert m_avg == pytest.approx(20.0)

    def test_mixed_population_between_the_two(self):
        m_avg = average_object_mass(n_star=1e6, n_bh=1e4, mean_bh_mass=20.0)
        assert 1.0 < m_avg < 20.0


class TestRelaxationTimescale:
    def test_positive_and_finite(self):
        t = relaxation_timescale(sigma=100.0, rho=1e6, mean_object_mass=1.0, coulomb_log=10.0)
        assert np.isfinite(t) and t > 0

    def test_shorter_with_higher_density(self):
        t_lo = relaxation_timescale(100.0, 1e4, 1.0, 10.0)
        t_hi = relaxation_timescale(100.0, 1e8, 1.0, 10.0)
        assert t_hi < t_lo

    def test_shorter_with_larger_average_mass(self):
        # heavier field objects relax the population faster (more efficient scattering)
        t_light = relaxation_timescale(100.0, 1e6, mean_object_mass=1.0, coulomb_log=10.0)
        t_heavy = relaxation_timescale(100.0, 1e6, mean_object_mass=20.0, coulomb_log=10.0)
        assert t_heavy < t_light

    def test_scales_as_sigma_cubed(self):
        t_1 = relaxation_timescale(100.0, 1e6, 1.0, 10.0)
        t_2 = relaxation_timescale(200.0, 1e6, 1.0, 10.0)
        assert t_2 / t_1 == pytest.approx(2.0**3, rel=1e-6)


class TestSegregationTimescale:
    def test_positive_and_finite(self):
        t = segregation_timescale(m_bh=30.0, sigma=100.0, rho_star=1e6, coulomb_log=10.0)
        assert np.isfinite(t) and t > 0

    def test_shorter_for_more_massive_bh(self):
        # more massive BHs segregate (sink) faster
        t_light = segregation_timescale(10.0, 100.0, 1e6, 10.0)
        t_heavy = segregation_timescale(100.0, 100.0, 1e6, 10.0)
        assert t_heavy < t_light

    def test_scales_inversely_with_bh_mass(self):
        t_1 = segregation_timescale(10.0, 100.0, 1e6, 10.0)
        t_2 = segregation_timescale(20.0, 100.0, 1e6, 10.0)
        assert t_1 / t_2 == pytest.approx(2.0, rel=1e-6)
