import numpy as np
import pytest

from imbh_nuclei.cluster import bh_number_density, stellar_density, velocity_dispersion


class TestStellarDensity:
    def test_equals_normalization_at_r0(self):
        rho0, r0 = 1.35e6, 0.25
        assert stellar_density(r0, rho0=rho0, r0=r0, alpha=1.25) == pytest.approx(rho0)

    def test_decreasing_with_radius(self):
        r = np.array([0.1, 0.5, 1.0, 5.0])
        rho = stellar_density(r)
        assert np.all(np.diff(rho) < 0)

    def test_power_law_scaling_exact(self):
        # rho(2*r0) / rho(r0) == 2**-alpha, exactly, for a pure power law
        rho0, r0, alpha = 1.35e6, 0.25, 1.25
        ratio = stellar_density(2 * r0, rho0, r0, alpha) / stellar_density(r0, rho0, r0, alpha)
        assert ratio == pytest.approx(2.0 ** (-alpha))

    def test_paper_default_value_at_r0(self):
        # sanity-checks the literal Eq. 3 constants quoted in the paper
        assert stellar_density(0.25) == pytest.approx(1.35e6)


class TestBHNumberDensity:
    def test_equals_normalization_at_r_h(self):
        # paper defaults: n0 = 1e4 pc^-3 at R_h = 1 pc (confirmed against PDF page 3)
        assert bh_number_density(1.0) == pytest.approx(1.0e4)

    def test_equals_normalization_at_r0_custom(self):
        n0, r0 = 10.0, 0.25
        assert bh_number_density(r0, n0=n0, r_h=r0, alpha=1.83) == pytest.approx(n0)

    def test_power_law_scaling_exact(self):
        n0, r0, alpha = 10.0, 0.25, 1.83
        ratio = bh_number_density(2 * r0, n0, r0, alpha) / bh_number_density(r0, n0, r0, alpha)
        assert ratio == pytest.approx(2.0 ** (-alpha))

    def test_steeper_slope_than_stellar_default(self):
        # BH cusp (alpha=1.83) should be steeper than the stellar cusp (alpha=1.25),
        # as expected from mass segregation -- a qualitative cross-check, not a value check.
        r = np.array([0.25, 2.5])
        bh_ratio = bh_number_density(r[1]) / bh_number_density(r[0])
        star_ratio = stellar_density(r[1]) / stellar_density(r[0])
        assert bh_ratio < star_ratio


class TestVelocityDispersion:
    def test_paper_eq1_value_at_1pc(self):
        # sigma(r=1pc) = sqrt(G*M_SMBH / [(alpha+1)*r]) for M_SMBH=4e6 Msun, alpha=1.25:
        # sqrt(4.30091e-3 * 4e6 / (2.25 * 1)) ~= 87.3 km/s -- exact value from confirmed Eq. 1.
        sigma = velocity_dispersion(1.0, 4.0e6, alpha=1.25)
        assert sigma == pytest.approx(np.sqrt(4.30091e-3 * 4.0e6 / 2.25))

    def test_decreases_with_radius(self):
        r = np.array([0.1, 1.0, 10.0])
        sigma = velocity_dispersion(r, 4.0e6, alpha=1.25)
        assert np.all(np.diff(sigma) < 0)

    def test_decreases_with_alpha(self):
        # velocity dispersion "weakly depends on alpha" (paper text) via 1/sqrt(alpha+1)
        sigma_star = velocity_dispersion(1.0, 4.0e6, alpha=1.25)
        sigma_bh = velocity_dispersion(1.0, 4.0e6, alpha=1.83)
        assert sigma_bh < sigma_star

    def test_scales_as_inverse_sqrt_r(self):
        # sigma(4r) / sigma(r) == 1/2 exactly
        ratio = velocity_dispersion(4.0, 4.0e6, alpha=1.25) / velocity_dispersion(
            1.0, 4.0e6, alpha=1.25
        )
        assert ratio == pytest.approx(0.5)

    def test_scales_with_sqrt_mass(self):
        sigma_1 = velocity_dispersion(1.0, 1.0e6, alpha=1.25)
        sigma_2 = velocity_dispersion(1.0, 4.0e6, alpha=1.25)
        assert sigma_2 / sigma_1 == pytest.approx(2.0)
