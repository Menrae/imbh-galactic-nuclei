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

Phase 0 (scaffolding), Phase 1 (core physics, Sections 2 & 4 of the paper), and Phase 2
(the Monte Carlo integration loop) are complete and tested. Phase 3 (validating against
the paper's published Table 1) is in progress — the four initial mass/spin distributions
are implemented, but a calibration issue in the relaxation-driven orbital dynamics is
currently blocking a meaningful full comparison (see `paper/limitations.md` for the
detailed diagnosis). See `docs/equations.md` for the physics reference and
`paper/limitations.md` for the running list of caveats, ambiguities, and assumptions.

## Layout

```
src/imbh_nuclei/          core package: config, constants, physics modules, simulation loop
tests/                    pytest unit tests, one file per module (200+ tests)
scripts/                  run scripts for simulations / parameter scans (no notebooks yet)
config/                   YAML configs specifying full simulation runs
docs/equations.md         single source of truth for every equation, with original citations
docs/table1_reference.md  transcribed Table 1 from the paper, for Phase 3 validation
paper/                    research-note writeup + limitations.md (maintained incrementally)
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

Phase 3 reproduces Table 1 and Figures 2–9 of Newton et al. 2026 as a hard gate before any
extension work (Phases 4–7); results and discrepancies are documented explicitly, not
smoothed over. Currently blocked on a calibration issue (EMRI rate far above the paper's —
see `paper/limitations.md#phase2-emri-rate-high`) before a meaningful full comparison can
be run.
