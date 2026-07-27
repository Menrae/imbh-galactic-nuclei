"""Phase 3 validation: all four initial conditions, N=1000, 10 Gyr, 3 seeds each,
run in parallel via multiprocessing. Saves a per-run summary CSV and per-run pickled
SimulationResults for later inspection.

Reproduces results/phase3_validation_2026-07-26.md -- see that file and
paper/limitations.md#phase2-emri-rate-high for the full discussion of what this run found.

Takes roughly 30-45 minutes wall-clock on 8 parallel workers (H18/H18+M runs are much
slower than K20/K20+M due to the runaway-growth behavior discussed there).
"""
import os
import pickle
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
import pandas as pd

from imbh_nuclei.config import ClusterConfig, IntegrationConfig, PopulationConfig, SimulationConfig
from imbh_nuclei.simulation import run_simulation
from imbh_nuclei.initial_conditions import get_samplers

ICS = ["K20", "K20+M", "H18", "H18+M"]
SEEDS = [0, 1, 2]
OUTDIR = os.path.join(os.path.dirname(__file__), "..", "results", "phase3_raw")

#: Monte Carlo means (N=2e6) of each IC's actual sampler, not a placeholder -- see
#: paper/limitations.md#mean-bh-mass-placeholder (a prior 20.0-for-everything placeholder
#: was found to be off by up to 40% once actually checked against the samplers).
MEAN_BH_MASS = {
    "K20": 9.718590423573621,
    "K20+M": 9.93733220769189,
    "H18": 33.396222701055834,
    "H18+M": 34.19754582811371,
}


def run_one(ic, seed):
    mass_sampler, spin_sampler = get_samplers(ic)
    config = SimulationConfig(
        cluster=ClusterConfig(),
        population=PopulationConfig(initial_mass_distribution=ic, n_bh=1000, mean_bh_mass=MEAN_BH_MASS[ic]),
        integration=IntegrationConfig(t_max_gyr=10.0, dt0_yr=1.0e6, seed=seed),
    )
    t0 = time.time()
    result = run_simulation(config, mass_sampler, spin_sampler)
    elapsed = time.time() - t0

    with open(f"{OUTDIR}/{ic.replace('+', 'plus')}_seed{seed}.pkl", "wb") as f:
        pickle.dump(result, f)

    pop = result.population
    mass = pop.mass
    n = len(mass)
    n_gt_100 = int(np.sum(mass > 100.0))
    return dict(
        ic=ic,
        seed=seed,
        elapsed_s=elapsed,
        n_steps=result.n_steps,
        n_mergers=len(result.merger_log),
        max_mass=float(mass.max()),
        max_spin=float(pop.chi[np.argmax(mass)]) if n else np.nan,
        p99_mass=float(np.percentile(mass, 99)),
        n_gt_100=n_gt_100,
        pct_gt_100=100.0 * n_gt_100 / n,
        n_emri=len(result.emri_log),
        pct_emri=100.0 * len(result.emri_log) / n,
        n_ejected=int(np.sum(pop.status == "ejected")),
        max_generation=int(pop.generation.max()),
    )


if __name__ == "__main__":
    os.makedirs(OUTDIR, exist_ok=True)
    jobs = [(ic, seed) for ic in ICS for seed in SEEDS]
    rows = []
    with ProcessPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(run_one, ic, seed): (ic, seed) for ic, seed in jobs}
        for fut in as_completed(futures):
            ic, seed = futures[fut]
            try:
                row = fut.result()
                rows.append(row)
                print(f"DONE {ic} seed={seed}: {row}", flush=True)
            except Exception as e:
                print(f"FAILED {ic} seed={seed}: {e}", flush=True)

    df = pd.DataFrame(rows)
    df.to_csv(f"{OUTDIR}/summary.csv", index=False)
    print("ALL DONE")
    print(df)
