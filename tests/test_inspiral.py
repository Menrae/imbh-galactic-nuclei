import numpy as np
import pytest

from imbh_nuclei.inspiral import da_dt, de_dt, is_emri, r_crit, remaining_merger_time_circular

# Independent SI-unit reference values, computed with scipy.constants directly (not
# derived from this package's pc/Msun/km-s helpers), for m1=m2=30 Msun, a=0.01 pc:
#   da/dt (e=0)   = -2.3241872625973445e-29 pc/yr
#   de/dt (e=0.3) = -1.4475931884207667e-27 /yr
#   tau_circular  =  1.0756448244218414e+26 yr
#   r_crit(4e6)   =  1.5317259349246052e-06 pc
# Small (~0.08%) residuals below come from slightly different Msun/pc constant precision
# between the two independent computations, not a unit-conversion bug.
_REF_DADT_E0 = -2.3241872625973445e-29
_REF_DEDT_E03 = -1.4475931884207667e-27
_REF_TAU_CIRC = 1.0756448244218414e26
_REF_RCRIT = 1.5317259349246052e-06


class TestDaDt:
    def test_matches_independent_si_computation(self):
        value = da_dt(30.0, 30.0, 0.01, e=0.0)
        assert value == pytest.approx(_REF_DADT_E0, rel=2e-3)

    def test_negative_orbit_shrinks(self):
        assert da_dt(30.0, 30.0, 0.01, e=0.0) < 0

    def test_faster_decay_at_smaller_separation(self):
        assert abs(da_dt(30.0, 30.0, 0.001, e=0.0)) > abs(da_dt(30.0, 30.0, 0.01, e=0.0))

    def test_faster_decay_with_higher_eccentricity(self):
        # the (1-e^2)^-7/2 enhancement is the dominant, well-known Peters (1964) effect
        assert abs(da_dt(30.0, 30.0, 0.01, e=0.9)) > abs(da_dt(30.0, 30.0, 0.01, e=0.0))


class TestDeDt:
    def test_matches_independent_si_computation(self):
        value = de_dt(30.0, 30.0, 0.01, e=0.3)
        assert value == pytest.approx(_REF_DEDT_E03, rel=2e-3)

    def test_zero_at_zero_eccentricity(self):
        # a circular orbit stays circular under radiation reaction
        assert de_dt(30.0, 30.0, 0.01, e=0.0) == pytest.approx(0.0)

    def test_negative_orbit_circularizes(self):
        assert de_dt(30.0, 30.0, 0.01, e=0.5) < 0


class TestRemainingMergerTime:
    def test_matches_independent_si_computation(self):
        tau = remaining_merger_time_circular(30.0, 30.0, 0.01)
        assert tau == pytest.approx(_REF_TAU_CIRC, rel=2e-3)

    def test_shorter_for_smaller_separation(self):
        tau_close = remaining_merger_time_circular(30.0, 30.0, 0.001)
        tau_far = remaining_merger_time_circular(30.0, 30.0, 0.01)
        assert tau_close < tau_far

    def test_scales_as_a_fourth_power(self):
        tau_1 = remaining_merger_time_circular(30.0, 30.0, 0.01)
        tau_2 = remaining_merger_time_circular(30.0, 30.0, 0.02)
        assert tau_2 / tau_1 == pytest.approx(2.0**4, rel=1e-6)


class TestRCrit:
    def test_matches_independent_si_computation(self):
        assert r_crit(4.0e6) == pytest.approx(_REF_RCRIT, rel=2e-3)

    def test_scales_linearly_with_smbh_mass(self):
        assert r_crit(8.0e6) / r_crit(4.0e6) == pytest.approx(2.0, rel=1e-6)


class TestIsEmri:
    def test_flags_via_periapsis_condition(self):
        m_smbh = 4.0e6
        rc = r_crit(m_smbh)
        assert is_emri(periapsis=rc * 0.5, m_smbh=m_smbh, remaining_merger_time_yr=1e9)

    def test_flags_via_merger_time_condition(self):
        m_smbh = 4.0e6
        rc = r_crit(m_smbh)
        assert is_emri(periapsis=rc * 100, m_smbh=m_smbh, remaining_merger_time_yr=50.0)

    def test_not_flagged_when_neither_condition_met(self):
        m_smbh = 4.0e6
        rc = r_crit(m_smbh)
        assert not is_emri(periapsis=rc * 100, m_smbh=m_smbh, remaining_merger_time_yr=1e9)

    def test_vectorized(self):
        m_smbh = 4.0e6
        rc = r_crit(m_smbh)
        flags = is_emri(
            periapsis=np.array([rc * 0.5, rc * 100, rc * 100]),
            m_smbh=m_smbh,
            remaining_merger_time_yr=np.array([1e9, 50.0, 1e9]),
        )
        np.testing.assert_array_equal(flags, [True, True, False])
