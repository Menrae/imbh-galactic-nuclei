import numpy as np
import pytest

from imbh_nuclei.recoil import HOLLEY_BOCKELMANN_2008, kick_velocity, v_m, v_parallel, v_perp


class TestConstants:
    def test_paper_values(self):
        # exact values pulled from arXiv:0707.1334 Eq. 2-4 (Holley-Bockelmann et al. 2008)
        assert HOLLEY_BOCKELMANN_2008.A == pytest.approx(1.2e4)
        assert HOLLEY_BOCKELMANN_2008.B == pytest.approx(-0.93)
        assert HOLLEY_BOCKELMANN_2008.H == pytest.approx(7.3e3)
        assert HOLLEY_BOCKELMANN_2008.K == pytest.approx(6.0e4)


class TestVm:
    def test_zero_at_equal_mass(self):
        # q=1 (equal mass) gives zero mass-asymmetry kick component: (1-q) term vanishes
        assert v_m(1.0) == pytest.approx(0.0)

    def test_zero_at_zero_mass_ratio(self):
        assert v_m(0.0) == pytest.approx(0.0)

    def test_nonzero_for_unequal_masses(self):
        assert v_m(0.36) != 0.0

    def test_hb2008_benchmark_order_of_magnitude(self):
        # HB2008 (Gonzalez et al. 2006) find a maximum non-spinning kick of ~175 km/s
        # near q~0.36; v_m alone (no spin contribution) should be the same
        # order of magnitude as that benchmark.
        q = np.linspace(0.01, 1.0, 500)
        vm_max = np.max(np.abs(v_m(q)))
        assert 50.0 < vm_max < 500.0


class TestVPerpVParallel:
    def test_v_perp_zero_for_equal_aligned_spins(self):
        assert v_perp(q=1.0, chi_par_2=0.5, chi_par_1=0.5) == pytest.approx(0.0)

    def test_v_perp_nonzero_for_unequal_spins(self):
        assert v_perp(q=1.0, chi_par_2=0.8, chi_par_1=0.2) != 0.0

    def test_v_parallel_zero_for_equal_perp_spins(self):
        v = v_parallel(q=1.0, chi_perp_2=0.3, chi_perp_1=0.3, theta=0.0, theta_0=0.0)
        assert v == pytest.approx(0.0)

    def test_v_parallel_depends_on_angle(self):
        v_aligned = v_parallel(q=1.0, chi_perp_2=0.5, chi_perp_1=0.0, theta=0.0, theta_0=0.0)
        v_perp_angle = v_parallel(
            q=1.0, chi_perp_2=0.5, chi_perp_1=0.0, theta=np.pi / 2, theta_0=0.0
        )
        assert v_aligned != pytest.approx(v_perp_angle)


class TestKickVelocity:
    def test_shape(self):
        v = kick_velocity(
            q=0.5,
            chi_par_1=0.1,
            chi_par_2=0.2,
            chi_perp_1=0.0,
            chi_perp_2=0.0,
            theta=0.3,
            theta_0=0.1,
            xi=0.5,
        )
        assert v.shape == (3,)

    def test_vectorized_over_mergers(self):
        n = 10
        v = kick_velocity(
            q=np.full(n, 0.5),
            chi_par_1=np.zeros(n),
            chi_par_2=np.zeros(n),
            chi_perp_1=np.zeros(n),
            chi_perp_2=np.zeros(n),
            theta=np.zeros(n),
            theta_0=np.zeros(n),
            xi=np.zeros(n),
        )
        assert v.shape == (n, 3)

    def test_eccentricity_scales_kick_linearly(self):
        kwargs = dict(
            q=0.5,
            chi_par_1=0.3,
            chi_par_2=0.1,
            chi_perp_1=0.2,
            chi_perp_2=0.05,
            theta=0.4,
            theta_0=0.1,
            xi=0.7,
        )
        v_circular = kick_velocity(**kwargs, eccentricity=0.0)
        v_eccentric = kick_velocity(**kwargs, eccentricity=1.0)
        np.testing.assert_allclose(v_eccentric, 2 * v_circular)

    def test_zero_spin_unequal_mass_gives_pure_in_plane_kick(self):
        v = kick_velocity(
            q=0.5,
            chi_par_1=0.0,
            chi_par_2=0.0,
            chi_perp_1=0.0,
            chi_perp_2=0.0,
            theta=0.0,
            theta_0=0.0,
            xi=0.0,
        )
        assert v[2] == pytest.approx(0.0)  # no z-component without spin
        assert v[0] != 0.0  # nonzero in-plane component from mass asymmetry
