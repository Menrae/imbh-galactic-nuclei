"""Phase 4, pass 3: does the primordial-binary-merger prescription shift the
star_only critical-mass crossover located by pass 2
(results/phase4_mass_threshold_scan_2026-07-27.md's "Pass 2" section, m_max in
20.1-31.8 Msun)?

Per the original pass-1 design (paper/limitations.md#phase4-mass-family-scan), the
primordial-binary-fraction axis (0% vs N26's own 15%, the "+M" variants) was
deliberately deferred to "a follow-up pass near the threshold region" rather than
scanned as a second axis from the start -- this is that follow-up, now that pass 2 has
located the region.

Scope, deliberately narrow (mirrors phase4b's own scoping logic):
- reading: star_only ONLY. bh_inclusive's "no threshold in the tested range" finding
  is already saturated evidence (24/24 runs at exact 0.0% in pass 1); this pass tests
  whether a *different* axis shifts the star_only crossover, so bh_inclusive is out of
  scope here too.
- grid: the same 5 m_max points pass 2 used (20.118935, 22.560436, 25.298221,
  28.368246, 31.810829) -- so the new primordial_binary_fraction=0.15 runs compare
  directly, point for point, against pass 2's already-existing primordial_binary_fraction=0.0
  runs (results/phase4b_raw/summary.csv) without needing a new baseline.
- primordial_binary_fraction: 0.15, N26's own prescription (Section 3), applied here
  via initial_conditions.get_log_uniform_samplers' new primordial_binary_fraction
  parameter (added for this pass; extends the log-uniform family with the same
  apply_primordial_mergers machinery already used for K20+M/H18+M).
- seeds: 8 per point (0-7), matching pass 2's convention -- per paper/methodology.md
  Gate 3, this is a location-adjacent comparison, not a bare existence claim, so the
  same >=8-seed bar applies from the start (no separate thin first look this time).
- mean_bh_mass: no closed form for the +M-modified distribution (mergers are a
  nonlinear transform of the base log-uniform draw), so it's Monte-Carlo estimated
  per grid point (N=2e6), same convention as Phase 3's MEAN_BH_MASS dict
  (paper/limitations.md#mean-bh-mass-placeholder) -- computed here rather than
  hardcoded, so it can't silently go stale if the sampler changes.

Total: 5 grid points x 8 seeds = 40 new runs.

Results written to results/phase4c_raw/ (new directory, does not touch pass 1/2's
results/phase4_raw or results/phase4b_raw).
"""
import os
import pickle
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
import pandas as pd

from imbh_nuclei.config import ClusterConfig, IntegrationConfig, PopulationConfig, SimulationConfig
from imbh_nuclei.initial_conditions import H18_MASS_MIN, get_log_uniform_samplers
from imbh_nuclei.simulation import run_simulation

M_MIN = H18_MASS_MIN
READING = "star_only"
PRIMORDIAL_BINARY_FRACTION = 0.15
ALL_SEEDS = list(range(8))  # 0-7, matching pass 2's seed count

# Exact same 5 points as phase4b_threshold_refinement.py's M_MAX_GRID.
_PASS1_GRID = np.geomspace(16.0, 100.0, 9)
_SHARED = _PASS1_GRID[1:4]  # [20.118935, 25.298221, 31.810829]
_NEW_MIDPOINTS = np.array([np.sqrt(_SHARED[0] * _SHARED[1]), np.sqrt(_SHARED[1] * _SHARED[2])])
M_MAX_GRID = np.sort(np.concatenate([_SHARED, _NEW_MIDPOINTS]))

OUTDIR = os.path.join(os.path.dirname(__file__), "..", "results", "phase4c_raw")
IMBH_MASS_THRESHOLD = 100.0
MC_MEAN_N = 2_000_000
MC_MEAN_SEED = 12345  # fixed, independent of the simulation seeds 0-7


def _mc_mean_bh_mass(m_max: float) -> float:
    """Monte Carlo mean of the +M sampler at this m_max."""
    mass_sampler, _ = get_log_uniform_samplers(
        m_max, m_min=M_MIN, primordial_binary_fraction=PRIMORDIAL_BINARY_FRACTION
    )
    rng = np.random.default_rng(MC_MEAN_SEED)
    mass = mass_sampler(MC_MEAN_N, rng)
    return float(mass.mean())


def run_one(m_max, seed, mean_bh_mass):
    mass_sampler, spin_sampler = get_log_uniform_samplers(
        m_max, m_min=M_MIN, primordial_binary_fraction=PRIMORDIAL_BINARY_FRACTION
    )
    config = SimulationConfig(
        cluster=ClusterConfig(),
        population=PopulationConfig(
            initial_mass_distribution="H18+M",
            n_bh=1000,
            primordial_binary_fraction=PRIMORDIAL_BINARY_FRACTION,
            mean_bh_mass=mean_bh_mass,
        ),
        integration=IntegrationConfig(
            t_max_gyr=10.0, dt0_yr=1.0e6, seed=seed, relaxation_mass_weighting=READING
        ),
    )
    t0 = time.time()
    result = run_simulation(config, mass_sampler, spin_sampler)
    elapsed = time.time() - t0

    tag = f"mmax{m_max:.4f}_{READING}_plusM_seed{seed}"
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
        primordial_binary_fraction=PRIMORDIAL_BINARY_FRACTION,
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

    print("Computing Monte Carlo mean_bh_mass per grid point (N=2e6 each)...")
    means = {m_max: _mc_mean_bh_mass(m_max) for m_max in M_MAX_GRID}
    for m_max, mean in means.items():
        print(f"  m_max={m_max:.4f} -> mean_bh_mass={mean:.4f}")

    jobs = [(m_max, seed) for m_max in M_MAX_GRID for seed in ALL_SEEDS]
    print(f"{len(jobs)} jobs queued: {len(M_MAX_GRID)} m_max points x {len(ALL_SEEDS)} seeds, "
          f"reading={READING}, primordial_binary_fraction={PRIMORDIAL_BINARY_FRACTION}")

    rows = []
    with ProcessPoolExecutor(max_workers=8) as ex:
        futures = {
            ex.submit(run_one, m_max, seed, means[m_max]): (m_max, seed) for m_max, seed in jobs
        }
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
