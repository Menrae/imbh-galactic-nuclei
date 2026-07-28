"""Phase 4, pass 2: refine the star_only critical-mass threshold located by pass 1
(scripts/phase4_mass_threshold_scan.py) between m_max=20.1 and m_max=31.8, where the
"any BH crosses 100 Msun" indicator flipped from 0/3 to 3/3 seeds, with the m_max=25.3
point sitting on a 1/3-seed coin flip.

Per the user's explicit request (2026-07-27): before treating the threshold LOCATION as
a reportable result, firm up the statistics that currently rest on a single seed flip.
Deliberately narrow in scope, not a repeat of the full pass-1 scan:

- reading: star_only ONLY. bh_inclusive's "no threshold in the tested range" finding is
  already exact 0.0% across 24 runs (8 m_max points x 3 seeds) -- already saturated
  evidence for "no threshold here," not the part that needs firming up.
- grid: the 3 m_max points pass 1 already ran in the band (20.118935, 25.298221,
  31.810829), PLUS 2 new points at the exact geometric midpoints (22.560436,
  28.368246), for finer x-resolution across the transition. 5 points total.
- seeds: 8 per point (0-7), up from pass 1's 3 -- reuses pass 1's existing seed-0/1/2
  runs for the 3 shared m_max points (skipped here, not rerun) and adds seeds 3-7 fresh;
  the 2 new points get all 8 seeds fresh. Total new runs: 3*5 + 2*8 = 31.

See paper/methodology.md for why this specific design (more seeds concentrated on the
already-observed transition, not a blind wider scan) is the right way to firm up a
threshold-location claim, and paper/limitations.md#phase4-mass-family-scan for the
original pass-1 design writeup.

Results are written to results/phase4b_raw/ (new files only, does not touch pass 1's
results/phase4_raw/). Analysis combines both directories' rows for the 3 shared m_max
points.
"""
import os
import pickle
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
import pandas as pd

from imbh_nuclei.config import ClusterConfig, IntegrationConfig, PopulationConfig, SimulationConfig
from imbh_nuclei.initial_conditions import H18_MASS_MIN, get_log_uniform_samplers, log_uniform_mean
from imbh_nuclei.simulation import run_simulation

M_MIN = H18_MASS_MIN

# Exact float match to pass 1's grid indices [1, 2, 3] (np.geomspace(16, 100, 9)) so the
# 3 shared points' existing pass-1 rows merge cleanly with these new ones.
_PASS1_GRID = np.geomspace(16.0, 100.0, 9)
_SHARED = _PASS1_GRID[1:4]  # [20.118935, 25.298221, 31.810829]
_NEW_MIDPOINTS = np.array([np.sqrt(_SHARED[0] * _SHARED[1]), np.sqrt(_SHARED[1] * _SHARED[2])])
M_MAX_GRID = np.sort(np.concatenate([_SHARED, _NEW_MIDPOINTS]))

READING = "star_only"
ALL_SEEDS = list(range(8))  # 0-7

PASS1_SUMMARY = os.path.join(os.path.dirname(__file__), "..", "results", "phase4_raw", "summary.csv")
OUTDIR = os.path.join(os.path.dirname(__file__), "..", "results", "phase4b_raw")

IMBH_MASS_THRESHOLD = 100.0


def _already_done(m_max, seed):
    """Skip (m_max, star_only, seed) combos pass 1 already ran (its 3 shared points'
    seeds 0-2)."""
    if not os.path.exists(PASS1_SUMMARY):
        return False
    df = pd.read_csv(PASS1_SUMMARY)
    match = df[
        (np.isclose(df["m_max"], m_max, rtol=1e-9))
        & (df["reading"] == READING)
        & (df["seed"] == seed)
    ]
    return len(match) > 0


def run_one(m_max, seed):
    mass_sampler, spin_sampler = get_log_uniform_samplers(m_max, m_min=M_MIN)
    mean_bh_mass = log_uniform_mean(M_MIN, m_max)
    config = SimulationConfig(
        cluster=ClusterConfig(),
        population=PopulationConfig(
            initial_mass_distribution="H18",
            n_bh=1000,
            primordial_binary_fraction=0.0,
            mean_bh_mass=mean_bh_mass,
        ),
        integration=IntegrationConfig(
            t_max_gyr=10.0, dt0_yr=1.0e6, seed=seed, relaxation_mass_weighting=READING
        ),
    )
    t0 = time.time()
    result = run_simulation(config, mass_sampler, spin_sampler)
    elapsed = time.time() - t0

    tag = f"mmax{m_max:.4f}_{READING}_seed{seed}"
    with open(f"{OUTDIR}/{tag}.pkl", "wb") as f:
        pickle.dump(result, f)

    pop = result.population
    mass = pop.mass
    n = len(mass)
    n_gt_100 = int(np.sum(mass > IMBH_MASS_THRESHOLD))
    return dict(
        m_max=m_max,
        mean_bh_mass=mean_bh_mass,
        reading=READING,
        seed=seed,
        elapsed_s=elapsed,
        n_steps=result.n_steps,
        n_mergers=len(result.merger_log),
        max_mass=float(mass.max()),
        max_spin=float(pop.chi[np.argmax(mass)]) if n else np.nan,
        p99_mass=float(np.percentile(mass, 99)),
        n_gt_100=n_gt_100,
        pct_gt_100=100.0 * n_gt_100 / n,
        any_gt_100=bool(n_gt_100 > 0),
        n_emri=len(result.emri_log),
        pct_emri=100.0 * len(result.emri_log) / n,
        n_ejected=int(np.sum(pop.status == "ejected")),
        max_generation=int(pop.generation.max()),
    )


if __name__ == "__main__":
    os.makedirs(OUTDIR, exist_ok=True)
    jobs = []
    skipped = []
    for m_max in M_MAX_GRID:
        for seed in ALL_SEEDS:
            if _already_done(m_max, seed):
                skipped.append((m_max, seed))
            else:
                jobs.append((m_max, seed))
    print(f"{len(jobs)} new jobs queued ({len(skipped)} skipped, already in pass 1): "
          f"{len(M_MAX_GRID)} m_max points x up to {len(ALL_SEEDS)} seeds, reading={READING}")

    rows = []
    with ProcessPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(run_one, m_max, seed): (m_max, seed) for m_max, seed in jobs}
        for fut in as_completed(futures):
            m_max, seed = futures[fut]
            try:
                row = fut.result()
                rows.append(row)
                print(f"DONE m_max={m_max:.4f} seed={seed}: pct_gt_100={row['pct_gt_100']:.2f} "
                      f"any_gt_100={row['any_gt_100']} n_mergers={row['n_mergers']} "
                      f"elapsed={row['elapsed_s']:.0f}s", flush=True)
            except Exception as e:
                print(f"FAILED m_max={m_max:.4f} seed={seed}: {e}", flush=True)

    df = pd.DataFrame(rows)
    df.to_csv(f"{OUTDIR}/summary.csv", index=False)
    print("ALL DONE")
    print(df)
