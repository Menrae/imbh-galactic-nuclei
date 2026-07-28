"""Phase 4, pass 1: scan the initial-mass-distribution "upper limit" to look for a
critical-mass threshold separating clusters that form IMBHs from clusters that never do
(N26 Section 5.4: "whether there is a mass distribution between our lower and upper
limits that consistently produces IMBHs").

Design (proposed to and confirmed by the user 2026-07-27, see
paper/limitations.md#phase4-mass-family-scan for the full reasoning):

- Mass family: log-uniform in [6, m_max] Msun (H18's own functional form, generalized --
  H18 itself is the m_max=100 endpoint). Does NOT reproduce K20's true reconstructed
  shape at the low end -- K20/K20+M/H18/H18+M keep their exact Phase 3 results
  (results/phase3_validation_2026-07-26.md) as separate validation anchors.
- Grid: 9 m_max points, log-spaced 16-100 Msun.
- Eq. 22 <M_avg>/rho: BOTH readings (star_only, bh_inclusive) -- required per the
  standing instruction that any Phase 4 threshold conclusion must be checked against
  both, not just the star-only default (paper/limitations.md#average-object-mass).
- 3 seeds per (m_max, reading) point, matching Phase 3's convention.
- Primordial-binary-merger fraction fixed at 0 (deferred to a second, zoomed-in pass
  near wherever this scan finds a threshold -- see paper/limitations.md).
- N=1000 BHs, 10 Gyr, alpha_star=1.25, M_smbh=4e6 Msun (paper fiducial values,
  unchanged from Phase 3).

Total: 9 x 2 x 3 = 54 runs. Estimated ~1.5-2.5 hours wall-clock at 8 parallel workers,
per Phase 3 timing (K20-like runs ~450s, H18-like runs 600-1740s under star_only;
bh_inclusive expected faster since it does not exhibit the runaway-growth tail).

IMBH definition (N26 Section 5.4, confirmed directly from the PDF): mass > 100 Msun.
Primary outcome: % of the N=1000 population exceeding 100 Msun (matches Table 1's own
column exactly). Secondary: a strict binary "did ANY BH cross 100 Msun" indicator, since
Phase 3 found K20 gives exactly 0% across all 6 seeds tested -- the binary indicator may
show a cleaner threshold than the continuous fraction.
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

M_MIN = H18_MASS_MIN  # 6.0 Msun, fixed across the whole scan
M_MAX_GRID = np.geomspace(16.0, 100.0, 9)  # Msun
READINGS = ["star_only", "bh_inclusive"]
SEEDS = [0, 1, 2]
OUTDIR = os.path.join(os.path.dirname(__file__), "..", "results", "phase4_raw")

IMBH_MASS_THRESHOLD = 100.0  # Msun, N26 Section 5.4's own definition


def run_one(m_max, reading, seed):
    mass_sampler, spin_sampler = get_log_uniform_samplers(m_max, m_min=M_MIN)
    mean_bh_mass = log_uniform_mean(M_MIN, m_max)
    config = SimulationConfig(
        cluster=ClusterConfig(),
        population=PopulationConfig(
            initial_mass_distribution="H18",  # nominal label; sampler is the actual family
            n_bh=1000,
            primordial_binary_fraction=0.0,
            mean_bh_mass=mean_bh_mass,
        ),
        integration=IntegrationConfig(
            t_max_gyr=10.0, dt0_yr=1.0e6, seed=seed, relaxation_mass_weighting=reading
        ),
    )
    t0 = time.time()
    result = run_simulation(config, mass_sampler, spin_sampler)
    elapsed = time.time() - t0

    tag = f"mmax{m_max:.2f}_{reading}_seed{seed}"
    with open(f"{OUTDIR}/{tag}.pkl", "wb") as f:
        pickle.dump(result, f)

    pop = result.population
    mass = pop.mass
    n = len(mass)
    n_gt_100 = int(np.sum(mass > IMBH_MASS_THRESHOLD))
    return dict(
        m_max=m_max,
        mean_bh_mass=mean_bh_mass,
        reading=reading,
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
    jobs = [(m_max, reading, seed) for m_max in M_MAX_GRID for reading in READINGS for seed in SEEDS]
    print(f"{len(jobs)} jobs queued: {len(M_MAX_GRID)} m_max points x {len(READINGS)} readings x {len(SEEDS)} seeds")

    rows = []
    with ProcessPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(run_one, m_max, reading, seed): (m_max, reading, seed) for m_max, reading, seed in jobs}
        for fut in as_completed(futures):
            m_max, reading, seed = futures[fut]
            try:
                row = fut.result()
                rows.append(row)
                print(f"DONE m_max={m_max:.2f} reading={reading} seed={seed}: "
                      f"pct_gt_100={row['pct_gt_100']:.1f} n_mergers={row['n_mergers']} "
                      f"max_mass={row['max_mass']:.1f} elapsed={row['elapsed_s']:.0f}s", flush=True)
            except Exception as e:
                print(f"FAILED m_max={m_max:.2f} reading={reading} seed={seed}: {e}", flush=True)

    df = pd.DataFrame(rows)
    df.to_csv(f"{OUTDIR}/summary.csv", index=False)
    print("ALL DONE")
    print(df)
