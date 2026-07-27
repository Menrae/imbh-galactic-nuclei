Run scripts for simulations and parameter scans will live here (Phases 2-6).

- `phase3_validation.py`: runs all four initial conditions (K20, K20+M, H18, H18+M) at
  N=1000, 10 Gyr, 3 seeds each, in parallel. Produces `results/phase3_raw/summary.csv` and
  per-run pickled `SimulationResults`. See `results/phase3_validation_2026-07-26.md` for the
  writeup and `paper/limitations.md#phase2-emri-rate-high` for the full discussion.
