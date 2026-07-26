import numpy as np
import pytest

from imbh_nuclei.collisions import (
    accreted_mass,
    bh_schwarzschild_radius,
    bondi_hoyle_rate,
    captured_mass,
    collision_timescale,
    f1_eccentricity,
    f2_eccentricity,
    spin_change,
)
from imbh_nuclei.constants import R_SUN_PC


class TestEccentricityFactors:
    @pytest.mark.parametrize("alpha", [0.5, 1.25, 1.75, 1.83, 2.0])
    def test_f1_f2_equal_one_at_zero_eccentricity(self, alpha):
        # 2F1(a,b;c;0) = 1 identically, so f1(0)=f2(0)=1 for any alpha -- recovers the
        # non-eccentric form of Eq. 18
        assert f1_eccentricity(0.0, alpha) == pytest.approx(1.0)
        assert f2_eccentricity(0.0, alpha) == pytest.approx(1.0)

    def test_f1_f2_order_unity_for_moderate_eccentricity(self):
        # Rose et al. 2020 note f(e) is "always of order unity" and the collision-rate
        # change from eccentricity "does not exceed a factor of two"
        for e in [0.1, 0.3, 0.5, 0.7]:
            assert 0.1 < f1_eccentricity(e, 1.25) < 10.0
            assert 0.1 < f2_eccentricity(e, 1.25) < 10.0


class TestSchwarzschildRadius:
    def test_zero_mass_gives_zero_radius(self):
        assert bh_schwarzschild_radius(0.0) == pytest.approx(0.0)

    def test_increases_with_mass(self):
        assert bh_schwarzschild_radius(60.0) > bh_schwarzschild_radius(30.0)

    def test_negligible_compared_to_solar_radius(self):
        # for stellar-mass BHs, R_schwarzschild << R_sun -- confirms the r_c ~ R_sun
        # approximation is reasonable regardless of the BH-radius assumption
        assert bh_schwarzschild_radius(30.0) < 1e-3 * R_SUN_PC


class TestCollisionTimescale:
    def test_positive_and_finite(self):
        t = collision_timescale(m_bh=30.0, n_star=1e6, sigma=100.0, e_bh=0.0, alpha_star=1.25)
        assert np.isfinite(t) and t > 0

    def test_shorter_with_higher_stellar_density(self):
        t_lo = collision_timescale(30.0, n_star=1e4, sigma=100.0, e_bh=0.0, alpha_star=1.25)
        t_hi = collision_timescale(30.0, n_star=1e8, sigma=100.0, e_bh=0.0, alpha_star=1.25)
        assert t_hi < t_lo

    def test_eccentricity_has_weak_order_unity_effect(self):
        # Rose et al. 2020: f1(e), f2(e) are "always of order unity" and change the
        # collision rate by "no more than a factor of two". For BH-star collisions the
        # gravitational-focusing term (weighted by f2) dominates the geometric term
        # (weighted by f1) by ~3 orders of magnitude (2G*m_BH/sigma^2 >> r_c for a
        # stellar-mass BH), so t_coll tracks f2(e) closely -- which is a *weak*,
        # slightly decreasing-with-e function, unlike the star-star case in Rose et al.
        # 2020 Figure 3 where the two terms are comparable and f1 dominates instead.
        # We only assert the "order unity, weak effect" claim, not a specific direction.
        t_circular = collision_timescale(30.0, 1e6, 100.0, e_bh=0.0, alpha_star=1.25)
        t_eccentric = collision_timescale(30.0, 1e6, 100.0, e_bh=0.7, alpha_star=1.25)
        ratio = t_eccentric / t_circular
        assert 0.5 < ratio < 2.0


class TestBondiHoyleAccretion:
    def test_positive(self):
        assert bondi_hoyle_rate(m_i=30.0, sigma=100.0) > 0

    def test_scales_as_mass_squared(self):
        rate_1 = bondi_hoyle_rate(m_i=10.0, sigma=100.0)
        rate_2 = bondi_hoyle_rate(m_i=20.0, sigma=100.0)
        assert rate_2 / rate_1 == pytest.approx(4.0, rel=1e-6)

    def test_decreases_with_velocity_dispersion(self):
        rate_lo_sigma = bondi_hoyle_rate(m_i=30.0, sigma=50.0)
        rate_hi_sigma = bondi_hoyle_rate(m_i=30.0, sigma=500.0)
        assert rate_hi_sigma < rate_lo_sigma


class TestCapturedAndAccretedMass:
    def test_captured_mass_capped_at_one_solar_mass(self):
        # a huge rate should saturate at the 1 Msun cap
        m_cap = captured_mass(mdot_bh=1e20, r_star_pc=R_SUN_PC, sigma=100.0)
        assert m_cap == pytest.approx(1.0)

    def test_captured_mass_positive_for_small_rate(self):
        m_cap = captured_mass(mdot_bh=1e-6, r_star_pc=R_SUN_PC, sigma=100.0)
        assert 0 < m_cap < 1.0

    def test_accreted_mass_less_than_captured_for_realistic_bh_mass(self):
        # radiative feedback (v_esc/(c*eta)) should reduce the captured mass for BHs in
        # the paper's simulated mass range (up to a few hundred Msun)
        m_cap = 0.5
        for m_bh in [1.0, 30.0, 100.0, 500.0]:
            assert accreted_mass(m_cap, m_bh) < m_cap

    def test_accreted_mass_zero_when_captured_mass_zero(self):
        assert accreted_mass(0.0, 30.0) == pytest.approx(0.0)


class TestSpinChange:
    def test_self_consistent_at_zero_mass_growth(self):
        # with (near-)zero mass growth, the Bardeen formula should reproduce the input
        # spin -- a strong internal-consistency check on the implementation
        for chi_i in [0.0, 0.3, 0.5, 0.9]:
            chi_f = spin_change(chi_i=chi_i, m_i=30.0, m_f=30.0 * (1 + 1e-9), prograde=True)
            assert chi_f == pytest.approx(chi_i, abs=1e-6)

    def test_saturates_at_one_for_large_mass_ratio(self):
        # saturation threshold is m_f/m_i >= sqrt(r_ISCO); r_ISCO(chi=0)=6, sqrt(6)~2.449
        chi_f = spin_change(chi_i=0.0, m_i=10.0, m_f=100.0, prograde=True)
        assert chi_f == 1.0

    def test_below_saturation_threshold_gives_value_below_one(self):
        chi_f = spin_change(chi_i=0.0, m_i=10.0, m_f=11.0, prograde=True)
        assert 0 <= chi_f < 1.0

    def test_retrograde_gives_larger_magnitude_spin_change(self):
        # paper Section 5.1: for the same Delta m_BH, retrograde accretion leads to a
        # greater magnitude of spin change than prograde, because the ISCO (and hence
        # accreted angular momentum) is further out for a retrograde disk
        chi_i, m_i, m_f = 0.5, 30.0, 31.0
        chi_f_pro = spin_change(chi_i, m_i, m_f, prograde=True)
        chi_f_retro = spin_change(chi_i, m_i, m_f, prograde=False)
        assert abs(chi_f_retro - chi_i) > abs(chi_f_pro - chi_i)

    def test_vectorized(self):
        chi_f = spin_change(
            chi_i=np.array([0.5, 0.5]),
            m_i=np.array([30.0, 30.0]),
            m_f=np.array([31.0, 31.0]),
            prograde=np.array([True, False]),
        )
        assert chi_f.shape == (2,)
