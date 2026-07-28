Run scripts for simulations and parameter scans will live here (Phases 2-6).

- `phase3_validation.py`: runs all four initial conditions (K20, K20+M, H18, H18+M) at
  N=1000, 10 Gyr, 3 seeds each, in parallel. Produces `results/phase3_raw/summary.csv` and
  per-run pickled `SimulationResults`. See `results/phase3_validation_2026-07-26.md` for the
  writeup and `paper/limitations.md#phase2-emri-rate-high` for the full discussion.
- `phase4_mass_threshold_scan.py`: Phase 4 pass 1 -- scans the log-uniform initial-mass
  distribution's upper bound (16-100 Msun, 9 grid points) x both Eq. 22 <M_avg>/rho readings
  (star_only, bh_inclusive) x 3 seeds = 54 runs, N=1000, 10 Gyr, looking for a critical-mass
  threshold for IMBH formation. Produces `results/phase4_raw/summary.csv` and per-run pickled
  `SimulationResults`. See `paper/limitations.md#phase4-mass-family-scan` for the scan design
  and reasoning (including options considered and not adopted).
