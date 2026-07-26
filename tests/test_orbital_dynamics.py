import numpy as np
import pytest

from imbh_nuclei.constants import G_ASTRO
from imbh_nuclei.orbital_dynamics import (
    apply_velocity_kick,
    kepler_state,
    orbital_elements_from_state,
    orbital_period,
    relaxation_kick_sigma,
    solve_kepler_equation,
)


class TestKeplerEquation:
    def test_circular_orbit_eccentric_anomaly_equals_mean_anomaly(self):
        m = np.array([0.0, 1.0, 3.0, 5.0])
        ecc_anomaly = solve_kepler_equation(m, e=0.0)
        np.testing.assert_allclose(ecc_anomaly, m, atol=1e-9)

    def test_satisfies_keplers_equation(self):
        m = np.array([0.1, 1.5, 3.0, 5.5])
        e = 0.6
        ecc_anomaly = solve_kepler_equation(m, e)
        residual = ecc_anomaly - e * np.sin(ecc_anomaly) - m
        np.testing.assert_allclose(residual, 0.0, atol=1e-8)


class TestOrbitalPeriod:
    def test_keplers_third_law(self):
        p1 = orbital_period(a=0.01, m_smbh=4.0e6)
        p2 = orbital_period(a=0.02, m_smbh=4.0e6)
        assert p2 / p1 == pytest.approx(2.0**1.5, rel=1e-6)

    def test_positive(self):
        assert orbital_period(a=0.05, m_smbh=4.0e6) > 0


class TestKeplerState:
    def test_periapsis_distance(self):
        a, e = 0.01, 0.5
        r_vec, v_vec, r = kepler_state(a, e, m_smbh=4.0e6, mean_anomaly=0.0)
        assert r == pytest.approx(a * (1 - e))

    def test_apoapsis_distance(self):
        a, e = 0.01, 0.5
        r_vec, v_vec, r = kepler_state(a, e, m_smbh=4.0e6, mean_anomaly=np.pi)
        assert r == pytest.approx(a * (1 + e))

    def test_circular_orbit_speed(self):
        a, m_smbh = 0.01, 4.0e6
        r_vec, v_vec, r = kepler_state(a, e=0.0, m_smbh=m_smbh, mean_anomaly=1.3)
        speed = np.linalg.norm(v_vec)
        v_circ = np.sqrt(G_ASTRO * m_smbh / a)
        assert speed == pytest.approx(v_circ, rel=1e-6)

    def test_vectorized(self):
        a = np.array([0.01, 0.02, 0.03])
        r_vec, v_vec, r = kepler_state(a, e=0.3, m_smbh=4.0e6, mean_anomaly=np.zeros(3))
        assert r_vec.shape == (3, 2)
        assert v_vec.shape == (3, 2)


class TestRoundTrip:
    @pytest.mark.parametrize("a", [0.001, 0.01, 0.05])
    @pytest.mark.parametrize("e", [0.0, 0.3, 0.7, 0.95])
    @pytest.mark.parametrize("mean_anomaly", [0.0, 1.0, 3.0, 5.0])
    def test_recovers_input_orbital_elements(self, a, e, mean_anomaly):
        # self-consistency: converting (a,e) -> state -> back to (a,e) with no kick
        # must recover the original elements exactly (up to numerical precision)
        m_smbh = 4.0e6
        r_vec, v_vec, _ = kepler_state(a, e, m_smbh, mean_anomaly)
        a_rec, e_rec, bound = orbital_elements_from_state(r_vec, v_vec, m_smbh)
        assert bound
        assert a_rec == pytest.approx(a, rel=1e-6)
        assert e_rec == pytest.approx(e, rel=1e-6, abs=1e-6)


class TestApplyVelocityKick:
    def test_zero_kick_preserves_orbit(self):
        rng = np.random.default_rng(0)
        a_new, e_new, bound = apply_velocity_kick(
            a=0.01, e=0.3, m_smbh=4.0e6, kick_speed=0.0, rng=rng
        )
        assert bound
        assert a_new == pytest.approx(0.01, rel=1e-6)
        assert e_new == pytest.approx(0.3, rel=1e-5, abs=1e-6)

    def test_huge_kick_unbinds_orbit(self):
        rng = np.random.default_rng(0)
        # circular speed at 0.01 pc, 4e6 Msun is a few hundred km/s; a multi-thousand
        # km/s kick should always exceed the local escape speed regardless of phase/angle
        a_new, e_new, bound = apply_velocity_kick(
            a=0.01, e=0.1, m_smbh=4.0e6, kick_speed=5000.0, rng=rng
        )
        assert not bound
        assert np.isinf(a_new)

    def test_vectorized_and_reproducible_with_seed(self):
        rng1 = np.random.default_rng(42)
        rng2 = np.random.default_rng(42)
        n = 20
        a = np.full(n, 0.01)
        e = np.full(n, 0.2)
        kick = np.full(n, 50.0)
        out1 = apply_velocity_kick(a, e, 4.0e6, kick, rng1)
        out2 = apply_velocity_kick(a, e, 4.0e6, kick, rng2)
        for arr1, arr2 in zip(out1, out2):
            np.testing.assert_array_equal(arr1, arr2)


class TestRelaxationKickSigma:
    def test_positive(self):
        assert relaxation_kick_sigma(a=0.01, m_smbh=4.0e6, t_relax_yr=1e9) > 0

    def test_larger_for_shorter_relaxation_time(self):
        sigma_slow = relaxation_kick_sigma(0.01, 4.0e6, t_relax_yr=1e10)
        sigma_fast = relaxation_kick_sigma(0.01, 4.0e6, t_relax_yr=1e8)
        assert sigma_fast > sigma_slow

    def test_scales_as_inverse_sqrt_t_relax(self):
        sigma_1 = relaxation_kick_sigma(0.01, 4.0e6, t_relax_yr=1e8)
        sigma_2 = relaxation_kick_sigma(0.01, 4.0e6, t_relax_yr=4e8)
        assert sigma_1 / sigma_2 == pytest.approx(2.0, rel=1e-6)
