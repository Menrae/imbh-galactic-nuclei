# imbh-nuclei

Python reimplementation and extension of the semianalytic dynamical-formation model in:

> Newton, A., Rose, S. C., Kıroğlu, F., Hoang, B.-M., & Rasio, F. A. 2026, ApJ, 1006:184,
> "Intermediate-mass Black Hole Formation from Hierarchical Mergers in Galactic Nuclei"

The model evolves a population of stellar-mass black holes embedded in a nuclear star
cluster around a supermassive black hole over a Hubble time, tracking BH–star collisions
and BH–BH GW-capture mergers to see whether the population produces an intermediate-mass
black hole (>100 M☉).

**New to this project?** Start with [`PROJECT_OVERVIEW.md`](PROJECT_OVERVIEW.md) — a
plain-language summary of what this is, why it exists, and what we've found so far. This
README is the technical/setup reference.

## Project status

Phases 0-5 are complete. Phase 3 validated all four of the paper's initial mass/spin
distributions against its published Table 1; Phase 4 mapped out whether the paper's
critical initial-mass threshold is sharp or gradual (gradual, under one reading of a
still-open equation ambiguity); Phase 5 tested whether the paper's result generalizes to
supermassive black holes of other masses (it does, under the same reading) — together
answering both of the open questions the paper poses in its own Section 5.4. Phases 6
(universe-wide detection-rate forecast) and 7 (cluster-shape sensitivity) haven't been
started. Outreach materials for the paper's authors, covering validation status and the
project's open questions, are drafted in `outreach/`. See `docs/equations.md` for the
physics reference, `paper/limitations_summary.md` for a readable summary of every
modeling ambiguity and caveat, and `paper/limitations.md` for the complete running log
behind it.

## Layout

```
src/imbh_nuclei/          core package: config, constants, physics modules, simulation loop
tests/                    pytest unit tests, one file per module (200+ tests)
scripts/                  run scripts for simulations / parameter scans (no notebooks yet)
config/                   YAML configs specifying full simulation runs
docs/equations.md         single source of truth for every equation, with original citations
docs/table1_reference.md  transcribed Table 1 from the paper, for Phase 3 validation
paper/                    research-note writeup + limitations.md (running log, maintained
                          incrementally) and limitations_summary.md (readable digest)
references/               the source paper plus every other paper pulled in to fill gaps
figures/                  output figures
results/                  output data (dataframes, logs)
PROJECT_OVERVIEW.md        plain-language project summary — start here
```

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Config system

A full simulation run is specified by a single `SimulationConfig` (see
`src/imbh_nuclei/config.py`), covering cluster structure, initial BH population, and
integration parameters. Configs can be loaded from / saved to YAML (see
`config/default.yaml`).

## Validation

Phase 3 reproduces Table 1 of Newton et al. 2026 across all four initial conditions
(K20, K20+M, H18, H18+M); results and discrepancies are documented explicitly, not
smoothed over. Bulk-population statistics (e.g. fraction of BHs exceeding 100 M☉)
reproduce well; the EMRI rate and the extreme upper mass tail for the heavier H18 family
remain open items — see `paper/limitations_summary.md` for the readable version and
`paper/limitations.md#phase2-emri-rate-high` for the full diagnostic trail.
