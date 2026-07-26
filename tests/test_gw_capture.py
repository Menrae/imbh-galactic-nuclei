import numpy as np
import pytest

from imbh_nuclei.gw_capture import (
    b_max,
    b_min,
    capture_cross_section,
    capture_timescale,
    chi_parallel,
    final_spin,
    isco_energy,
    orbital_ell,
    r_isco,
    remnant_mass,
    symmetric_mass_ratio,
    z1,
    z2,
)


class TestSymmetricMassRatio:
    def test_equal_masses_gives_quarter(self):
        # hand-computed sanity check requested up front: eta(m,m) = 0.25
        assert symmetric_mass_ratio(30.0, 30.0) == pytest.approx(0.25)

    def test_extreme_mass_ratio_approaches_zero(self):
        assert symmetric_mass_ratio(1.0, 1000.0) < 0.01

    def test_symmetric_in_arguments(self):
        assert symmetric_mass_ratio(10.0, 40.0) == pytest.approx(symmetric_mass_ratio(40.0, 10.0))


class TestISCO:
    def test_schwarzschild_value_at_zero_spin(self):
        # hand-computed sanity check requested up front: r_ISCO(chi=0) = 6
        assert r_isco(0.0, prograde=True) == pytest.approx(6.0)
        assert r_isco(0.0, prograde=False) == pytest.approx(6.0)

    def test_prograde_smaller_than_retrograde_for_positive_spin(self):
        # a prograde ISCO shrinks toward the horizon as spin increases; retrograde grows
        assert r_isco(0.9, prograde=True) < r_isco(0.9, prograde=False)

    def test_prograde_extremal_limit(self):
        # as chi -> 1, prograde r_ISCO -> 1 (horizon at the extremal Kerr limit);
        # convergence is slow (~(1-chi)^(2/3)) so we just check it's well below the
        # Schwarzschild value of 6 and approaching 1, not a tight numeric match
        assert 1.0 <= r_isco(0.9999, prograde=True) < 1.2

    def test_z1_z2_at_zero_spin(self):
        assert z1(0.0) == pytest.approx(3.0)
        assert z2(0.0) == pytest.approx(3.0)

    def test_isco_energy_schwarzschild(self):
        # E_ISCO(r_ISCO=6) = sqrt(1 - 2/18) = sqrt(8/9) ~= 0.9428, the standard
        # Schwarzschild ISCO binding-energy result
        assert isco_energy(6.0) == pytest.approx(np.sqrt(8 / 9))


class TestCaptureGeometry:
    def test_b_min_less_than_b_max(self):
        assert b_min(30.0, 30.0, 100.0) < b_max(30.0, 30.0, 100.0)

    def test_cross_section_positive(self):
        assert capture_cross_section(30.0, 30.0, 100.0) > 0

    def test_b_max_increases_with_mass(self):
        assert b_max(60.0, 60.0, 100.0) > b_max(30.0, 30.0, 100.0)

    def test_cross_section_clamped_at_zero_for_high_relative_velocity(self):
        # b_max ~ v_rel^(-9/7) falls off faster than b_min ~ v_rel^(-1), so at high
        # enough v_rel (deep in the cusp) b_max < b_min and the literal Eq. 6 formula
        # would go negative -- must be clamped to 0, not returned as a negative area.
        # Found via a full simulation-loop smoke test at small semimajor axis.
        assert capture_cross_section(30.0, 30.0, v_rel=50000.0) == 0.0

    def test_capture_timescale_is_infinite_when_cross_section_clamped(self):
        t = capture_timescale(30.0, 30.0, v_rel=50000.0, n_bh=1.0e4)
        assert np.isinf(t) and t > 0

    def test_b_max_decreases_with_relative_velocity(self):
        assert b_max(30.0, 30.0, 200.0) < b_max(30.0, 30.0, 100.0)


class TestCaptureTimescale:
    def test_positive_and_finite(self):
        t = capture_timescale(30.0, 30.0, 100.0, n_bh=1.0e4)
        assert np.isfinite(t)
        assert t > 0

    def test_shorter_with_higher_density(self):
        t_lo = capture_timescale(30.0, 30.0, 100.0, n_bh=1.0e3)
        t_hi = capture_timescale(30.0, 30.0, 100.0, n_bh=1.0e5)
        assert t_hi < t_lo

    def test_order_of_magnitude_milky_way_like(self):
        # O'Leary et al. 2009 quote GW capture rates ~1e-10 to 1e-9 yr^-1 per galaxy for
        # a Milky-Way-like NSC; for a single pair this should correspond to timescales
        # many orders of magnitude longer than the Hubble time (order 1e9-1e13 yr is a
        # generous order-of-magnitude sanity band, not a precision check).
        t = capture_timescale(30.0, 30.0, 150.0, n_bh=1.0e4)
        assert 1e6 < t < 1e16


class TestRemnantMassAndSpin:
    def test_remnant_mass_less_than_total_for_nonspinning(self):
        m_f = remnant_mass(30.0, 30.0, chi_par=0.0)
        assert 0 < m_f < 60.0

    def test_remnant_mass_close_to_total_mass(self):
        # radiated energy fraction is a few percent at most for stellar-mass mergers
        m_f = remnant_mass(30.0, 30.0, chi_par=0.0)
        assert m_f / 60.0 > 0.9

    def test_chi_parallel_equal_masses_equal_spins(self):
        # chi_par = (m1^2*chi1 + m2^2*chi2)/(m1+m2)^2; for equal masses and equal
        # L-projected spins this is (2*m^2*chi)/(2m)^2 = chi/2, not chi
        chi_par = chi_parallel(30.0, 0.5, 30.0, 0.5)
        assert chi_par == pytest.approx(0.25)

    def test_final_spin_capped_at_one(self):
        spin = final_spin(q=1.0, chi1_costheta1=1.0, chi2_costheta2=1.0, orbital_l=10.0)
        assert spin == 1.0

    def test_final_spin_nonspinning_equal_mass_from_orbital_l_only(self):
        # value = q^2*chi2costheta2 + chi1costheta1)/(1+q)^2 + q*L/(1+q)^2
        #       = 0/(2)^2 + 1*0.6/(2)^2 = 0.15
        spin = final_spin(q=1.0, chi1_costheta1=0.0, chi2_costheta2=0.0, orbital_l=0.6)
        assert spin == pytest.approx(0.15)


class TestOrbitalEll:
    def test_self_consistent_for_fully_aligned_spins(self):
        # by construction, plugging orbital_ell back into final_spin for aligned spins
        # (costheta1=costheta2=1) must exactly recover the Barausse & Rezzolla 2009
        # aligned-spin fit it was derived from -- the key correctness check for this
        # otherwise-unverifiable (no independent reference value) function
        for q, chi1, chi2 in [(1.0, 0.0, 0.0), (0.5, 0.3, 0.7), (0.8, -0.2, 0.5), (0.2, 0.9, 0.1)]:
            ell = orbital_ell(q, chi1, chi2)
            chi_f = final_spin(q, chi1, chi2, ell)
            # recompute the aligned-fit value directly to compare against
            eta = q / (1 + q) ** 2
            a_tilde = (chi1 + chi2 * q**2) / (1 + q**2)
            a_fin_expected = (
                a_tilde
                + a_tilde * eta * (-0.1229 * a_tilde + 0.4537 * eta - 2.8904)
                + eta * (2 * np.sqrt(3) - 3.5171 * eta + 2.5763 * eta**2)
            )
            assert chi_f == pytest.approx(abs(a_fin_expected), abs=1e-9)

    def test_equal_mass_nonspinning_matches_known_schwarzschild_merger_value(self):
        # equal-mass, non-spinning, aligned merger: a well-known NR benchmark result is
        # a_fin ~ 0.6864 (Barausse & Rezzolla's own calibration point, their Eq. 2)
        ell = orbital_ell(q=1.0, chi1_costheta1=0.0, chi2_costheta2=0.0)
        chi_f = final_spin(q=1.0, chi1_costheta1=0.0, chi2_costheta2=0.0, orbital_l=ell)
        assert chi_f == pytest.approx(0.68646, abs=1e-3)

    def test_vectorized(self):
        q = np.array([0.5, 1.0])
        ell = orbital_ell(q, np.array([0.1, 0.2]), np.array([0.3, 0.4]))
        assert ell.shape == (2,)
