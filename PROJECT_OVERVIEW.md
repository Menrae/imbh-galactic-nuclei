# What this project is

Every big galaxy has a supermassive black hole at its center, surrounded by a dense
swarm of stars and stellar-mass black holes called a "nuclear star cluster." This
project asks a specific question about that environment: **can an intermediate-mass
black hole — something in the hundreds-to-thousands of solar masses, a size we rarely
see anywhere in nature — grow up out of that swarm, just through ordinary collisions and
mergers, without needing any exotic physics?**

We're answering that by rebuilding, from scratch, the model in a recent research paper
that tried to answer it:

> Newton, Rose, Kıroğlu, Hoang, & Rasio 2026, *ApJ*, 1006:184, "Intermediate-mass Black
> Hole Formation from Hierarchical Mergers in Galactic Nuclei"

Their model follows 1,000 individual black holes orbiting a supermassive black hole like
the Milky Way's, over 10 billion years, tracking two ways they can grow: **colliding with
nearby stars** (slow, frequent, small nibbles of mass) and **merging with each other**
after close gravitational-wave-radiating encounters (rare, but each one can double a
black hole's mass in one shot). Their headline result: whether this produces an
intermediate-mass black hole or not depends almost entirely on the *starting* mass
distribution of the black hole population — one plausible starting point never produces
one; another, equally plausible, sometimes does.

## Why rebuild someone else's model instead of just reading their paper?

Three reasons, roughly in order of ambition:

1. **Trust, but verify.** Reproducing a result independently, from the equations up, is
   the single best way to know whether it's solid — and it's standard practice before
   building anything new on top of it.
2. **The paper left real questions open.** The authors explicitly flag two things they
   didn't have time to chase down: (a) is there a sharp "critical" starting-mass
   threshold that separates "forms an IMBH" from "never does," or is the transition
   gradual? (b) does their result generalize to galaxies with different supermassive
   black hole masses, or is it a Milky Way-specific coincidence? Once our
   reimplementation is validated, we extend it to answer both.
3. **A rate forecast.** Past that, we want to combine per-galaxy results with how many
   galaxies of each size actually exist in the universe, to get an order-of-magnitude
   estimate of how often gravitational-wave detectors should actually see something
   this model predicts.

## How far we've gotten

The project runs in phases. Roughly:

| Phase | What it is | Status |
|---|---|---|
| 0 | Project scaffolding (code structure, config system) | Done |
| 1 | Core physics, equation by equation, unit-tested | Done |
| 2 | The main simulation loop that ties the physics together | Done, one known calibration issue (see below) |
| 3 | Plugging in the paper's actual starting conditions and checking our numbers against theirs | In progress |
| 4 | The centerpiece: mapping out where the "critical mass" transition actually is | Not started |
| 5 | Does this hold up for supermassive black holes of other sizes? | Not started |
| 6 | Universe-wide detection-rate estimate | Not started |
| 7 | Sensitivity to a cluster-shape assumption (optional, time permitting) | Not started |

Concretely, right now: every equation from the paper's physics sections has been
implemented and independently unit-tested (over 200 tests passing). The full
simulation — initialize a population, run it forward in time, track collisions,
mergers, black holes falling into the central black hole, black holes getting kicked
out of the cluster entirely — runs end to end. We've also built the paper's four
specific starting-condition recipes (see "K20/H18" below) so we can compare our
numbers directly to theirs.

## What we've learned so far

This has been as much a **detective project** as a coding project, because the paper —
like most physics papers — doesn't spell out every equation completely; it leans on
citations to five or six *other* papers for pieces of the puzzle. Chasing those down
directly (not guessing) turned up some genuinely useful findings:

- **We found what looks like a real typo in the paper.** One equation (governing how a
  black hole's spin changes after swallowing a star) has an exponent that doesn't match
  the original 1970s formula it's citing. We're using the original formula's version and
  flagging the discrepancy — it's a small thing, but it could shift the maximum spins we
  predict.
- **We found an actual missing formula.** One equation uses a quantity the paper never
  defines. We traced it two more papers deep and found the real definition — without
  that, this piece of the model literally couldn't have been run correctly.
- **We caught real bugs by stress-testing, not just by reading code.** A few of the
  physics equations, correct in isolation, produced impossible results (like negative
  time) once wired into the full simulation and pushed into extreme corners of parameter
  space — the kind of thing you only find by actually running the thing at scale, not by
  reviewing the formulas on paper. All fixed, with regression tests added so they can't
  silently come back.
- **We've made real progress on the EMRI over-production problem, but it's not fully solved,
  and fixing it exposed a second, new problem.** The over-aggressive "black holes falling
  in" rate (originally ~75% of the population over 10 billion years, vs. a few percent in
  the paper) came down to ~35% after two changes: modeling the random-walk process as
  many smaller updates instead of one big one per timestep, and re-deriving two formula
  inputs from the original underlying papers rather than guessing (see
  `paper/limitations.md#phase2-emri-rate-high` for the full trace). That second re-derivation
  is itself genuinely ambiguous — the paper's text supports two different readings, and we
  picked the one that keeps black hole mergers happening at all, since the other reading
  reintroduces the original problem almost exactly. Picking it, however, exposed a *new*
  issue: in every trial, at least one black hole snowballs to 6,000-9,400 solar masses (the
  paper reports a maximum of about 400), through a growth process the original paper's own
  underlying model acknowledges CAN happen but expects to be kept in check by the same
  random-walk process we just weakened. This is now the top open question before Phase 3+
  results can be trusted, and it's logged in detail, including what we ruled out and why.
- **The paper cites a simulation, not a formula, for one of its four starting
  conditions.** For the "K20" case, we ended up reading the numbers directly off the
  paper's own plotted histogram, since the underlying source is itself a large numerical
  simulation with no simple mathematical description to copy.

None of this is a knock on the original paper — this level of "the details live in
five other papers" is completely normal for how physics research is written. It just
means faithfully reproducing it takes real detective work, not just transcription. Every
one of these decisions, along with our reasoning, is logged in detail in
`paper/limitations.md` and `docs/equations.md` for anyone who wants to check our work.

## What's next

Decide how to handle the new runaway-growth question (documented candidly rather than
resolved, since it's a genuine open question, not a bug), then run the full validation
against the paper's published table of results across all four starting conditions. Once
that's solid, we move to the part of this project that's genuinely new: mapping out whether
there's a sharp dividing line between "this environment makes giant black holes" and "it
never does."

## Where to look for more detail

- `docs/equations.md` — every equation used, its original source, and exactly where the
  paper's presentation was incomplete or ambiguous.
- `paper/limitations.md` — a running log of every judgment call, assumption, and caveat,
  with the reasoning behind each one.
- `docs/table1_reference.md` — the paper's published results, transcribed for
  side-by-side comparison once validation is ready.
- `references/` — the original paper plus every other paper we had to pull in to fill
  in a missing piece.
