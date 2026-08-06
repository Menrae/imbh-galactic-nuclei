# An independent reimplementation of Newton et al. (2026): validation status and open questions

**Prepared by**: Armeen Shasti-Nazem (University of Washington, aashasti@uw.edu) — independent reimplementation project, not affiliated with the original study.
**Date**: 2026-08-05.
**Regarding**: Newton, A., Rose, S. C., Kıroğlu, F., Hoang, B.-M., & Rasio, F. A. 2026, *ApJ*,
1006:184, "Intermediate-mass Black Hole Formation from Hierarchical Mergers in Galactic Nuclei"
(hereafter N26).
**Code**: https://github.com/Menrae/imbh-galactic-nuclei (full history, tests, and a running log
of every modeling judgment call in `paper/limitations.md`).

## Why this memo exists

Over the past several weeks I rebuilt N26's model from its equations up, specifically to (a)
check whether the paper's central claims reproduce under an independent implementation, and (b)
use the validated pipeline to chase down the two open questions N26 poses in Section 5.4. Both of
those questions turn out to have answers under this pipeline — and, tellingly, both hinge on the
same equation ambiguity below (Section 2.2) — which is a large part of why this seemed worth
writing up rather than letting it sit in a private repo. This memo summarizes where validation
stands, three places I ran into genuine ambiguity or gaps in the underlying equations that
materially affect the results, and what my extensions found. I'd welcome your read on all three,
particularly the two ambiguities in Section 2 — in both cases I made a specific choice but neither
is fully settled, and you're the people who'd know.

## Questions for you

1. **Eq. 21's exponent** (§2.1): printed as 1/3, but 1/2 in the Volonteri et al. 2013 formula it
   cites — which was intended?
2. **Eq. 22's $\langle M_{\rm avg}\rangle$/$\rho$** (§2.2): star-only, or BH-inclusive? This
   single choice controls nearly every downstream result below, including both Section 5.4
   extensions.
3. **Initial $a_\bullet$/$e_\bullet$ sampling** (§2.3): Section 3 never states this. Is there a
   convention I'm missing — published or not?

## 1. Validation against Table 1

I ran all four of N26's initial conditions (K20, K20+M, H18, H18+M) at $N=1000$,
$M_\bullet=4\times10^6\,M_\odot$, 10 Gyr, 3 seeds each, and compared against Table 1:

| IC | Mergers (ours, range / Table 1) | Max mass $M_\odot$ (ours, range / Table 1) | % BHs $>100\,M_\odot$ (ours, range / Table 1) | EMRI % (ours) |
|---|---:|---:|---:|---:|
| K20 | 24.0 [14–34] / 34 | 39.1 [30.7–51.4] / 28.4 | 0.0% [0.0–0.0%] / 0% | 29.6% |
| K20+M | 28.7 [19–39] / 30 | 46.2 [38.0–52.2] / 57.8 | 0.0% [0.0–0.0%] / 0% | 31.9% |
| H18 | 1022.0 [923–1102] / 371 | 58,034 [9,181–89,870] / 407.3 | 12.5% [11.7–13.4%] / 7.8% | 34.7% |
| H18+M | 1046.7 [786–1199] / 535 | 11,881 [3,556–16,137] / 526.0 | 12.8% [12.6–13.2%] / 14.3% | 35.0% |

*N26's Table 1 doesn't state whether these are single runs or averages over multiple
realizations — I found no mention of seeds, realizations, or repeated runs anywhere in the
paper's text, so I'm treating them as single runs and showing my own seed-to-seed range for
context, not a like-for-like noise-floor comparison.*

**K20 and K20+M reproduce well** — mergers and max mass both within ~1.3-1.5x of Table 1, which
is well inside the plausible range given seed-to-seed variance and the reconstruction
uncertainty in the K20 mass distribution itself (N26 cites this as drawn from a simulation
(Kremer et al. 2020) rather than a closed-form distribution, so I read the numbers directly off
the published histogram).

**H18 and H18+M are a mixed picture.** The population-level statistic that matters most for the
paper's headline claim — the fraction of BHs exceeding 100 $M_\odot$ — is actually close (12.5%
vs. 7.8% for H18; 12.8% vs. 14.3% for H18+M, the latter within seed noise). But the single
"max mass" order statistic is off by 20-220x, and merger count by ~2.9x. I traced this to a
specific, still-open mechanism: a genuine, moderately broad heavy tail, not a rare fluke — across
the six H18/H18+M seeds, 44-58 of the 1000 BHs exceed 200 $M_\odot$, 13-19 exceed 500 $M_\odot$,
and 6-10 exceed 1000 $M_\odot$, via a runaway positive-feedback loop in which both growth
channels' efficiency scales with the growing BH's own mass. Only the single most extreme BH per
run drives the eye-catching 10,000-90,000 $M_\odot$ figures in the table above, reaching 60-230
successive merger generations along the way (Table 1's own stated maximum is 12-16). I narrowed
one contributing factor (a since-fixed bug in my own `mean_bh_mass` placeholder made the runaway
tail *more* severe once corrected, implicating the GW-capture channel's own mass-dependence, Eqs.
4-7), but the residual is not fully resolved and I am reporting it candidly as an open item rather
than a solved discrepancy. Full trace: `paper/limitations.md#phase2-emri-rate-high`.

**Bottom line**: bulk-population behavior for both mass families is plausible by the metrics
Table 1 reports directly; one bulk statistic Table 1 doesn't report — EMRI fraction — is not: I
get 30-37% over 10 Gyr across all four initial conditions (see table above), versus N26's own
implied rate of roughly 4-5% over the same span, converting from their ~4-4.8 Gyr$^{-1}$
merger-rate figures in Section 5.4 (my conversion, not a fraction N26 states directly). The
extreme upper tail specifically, for the heavier H18 family, runs hotter than Table 1 in my
implementation, for reasons I can point to mechanistically but haven't fully closed the loop on.

## 2. Open questions on the underlying model

The following are cases where my implementation made a specific choice that I believe is
defensible from your own cited sources — but I want to flag them rather than assume I read them
correctly, since each one turns out to matter a great deal for the results below. The first two
are genuine textual ambiguities (I found real support for more than one reading); the third is
different in kind — a place N26's text is silent rather than ambiguous.

### 2.1 — Eq. 21's prefactor exponent: 1/3 as printed, vs. 1/2 in the cited source

Eq. 21 (BH spin evolution from a stellar collision) is presented as extending Volonteri, Sikora,
Lasota, & Merloni 2013 (ApJ, 775, 94). The published Eq. 21 prefactor is
$r_{\rm ISCO}^{1/3}/3$ (I confirmed this isn't an OCR artifact via a high-resolution crop of
the PDF). Volonteri et al. 2013's own Eq. 14 — the Bardeen (1970) thin-disk spin-up result — has
exponent $1/2$: $r_{\rm ISCO}(t)^{1/2}/3$. The inner square-root term is identical between the
two papers once N26's unsubscripted "$r$" is read as $r_{\rm ISCO}$, so this looks like a single
exponent that doesn't match, not a different formula.

I implemented $1/2$, since it's the long-established Bardeen result used consistently across
the literature (King & Kolb 1999; King, Pringle & Hofmann 2008; Volonteri et al. 2005, 2013),
and Eq. 21's text explicitly attributes the formula to Volonteri et al. 2013 rather than
deriving a new variant. My best guess is that this is a typesetting slip rather than an
intentional change — but I haven't confirmed that with you, and it's exactly the kind of thing
that's very easy to miss without going back to Eq. 14 of the cited source directly. Could you
confirm which exponent was intended? It has a direct, first-order effect on predicted maximum
spins.

### 2.2 — Eq. 22's $\langle M_{\rm avg}\rangle$ and $\rho$: star-only, or BH-inclusive?

This is the more consequential of the two ambiguities. Eq. 22's two-body relaxation timescale,
$t_{\rm relax}=0.34\,\sigma^3/(G^2\rho\langle M_{\rm avg}\rangle\ln\Lambda)$, depends on an
"average object mass" $\langle M_{\rm avg}\rangle$ and density $\rho$ that N26's text describes
only generically ("the average object mass," "their mass density"). I found textual support
for two different readings, and — as far as I can tell — no way to settle it from the paper's
text alone:

- **Star-only** ($\langle M_{\rm avg}\rangle=1\,M_\odot$, $\rho=\rho_\star$): S. C. Rose et al.
  2022 (ApJL, 929, L22) — the paper N26 explicitly says this relaxation mechanism is "first
  developed by" — states its own version of this formula (their Eq. 10) is explicitly for "a
  **single-mass system**," with $\langle M_*\rangle$ "here assumed to be 1 $M_\odot$." Rose et
  al. 2022 has no BH-density term at all, so its formula can't mean anything else.
- **BH-inclusive** (density-weighted mean over both stars and background BHs, using N26's own
  Eq. 2 BH-density profile): N26's Eq. 22 text drops Rose et al. 2022's "single-mass system"
  qualifier, and N26 introduces a genuinely new two-component density apparatus that Rose et al.
  2022 never had. Most tellingly, Eq. 23 (mass-segregation time) explicitly writes
  $t_{\rm seg}\approx(M_\star/m_{\rm BH})\times t_{\rm relax}(\langle M_{\rm avg}\rangle=M_\star,
  \rho=\rho_\star)$ — an explicit override to star-only for that one derived quantity, which
  only makes sense as a deliberate exception if Eq. 22's own default isn't already star-only.

I tested both readings empirically (N=1000, H18, 10 Gyr): star-only gives the Section 1 H18
numbers above (34.7% EMRI, 1022 mergers); BH-inclusive gives ~66% EMRI (64.8-67.5% across 3
seeds) and only 1-2 mergers per run, reproducing what looks like the exact early-development
problem this relaxation mechanism was meant to fix — objects get diffused into the SMBH before
the merger channel can ever complete more than a handful of events. Neither reading reproduces
Table 1's exact balance, but only star-only leaves the merger channel functioning at meaningful
scale, so it's my working default. This is logged as an open, unresolved choice, not a settled
one (`paper/limitations.md#average-object-mass`).

I'd be glad to know which reading was intended, or whether Eq. 22 was meant more loosely than
either extreme — because, as it turns out, this single choice controls nearly every downstream
result I describe below.

### 2.3 — Initial orbital properties: a gap, not a discrepancy

Unlike 2.1 and 2.2, this isn't a case where N26 says something and I read it a particular way —
it's a place the text is silent. Section 2 states BHs' initial masses, spins, and orbital
properties are drawn "statistically as described in Section 3," but Section 3, read in full,
covers only mass and spin distributions (K20, H18, the primordial-binary fraction); it never
states how the initial semimajor axis $a_\bullet$ or eccentricity $e_\bullet$ about the SMBH are
sampled. I confirmed this directly against the PDF rather than assuming it from a paraphrase.

Since N26 explicitly presents its dynamical framework as an extension of Rose et al. (2022)'s
model, I inherited that paper's stated convention: thermal eccentricity, and semimajor axis
log-uniform out to $0.1$ pc (N26's own stated focus region for the outer bound). Neither paper
states an inner bound; I picked $a_{\rm min}=10^{-3}$ pc from my own inspiral-time argument (a BH
born there takes far longer than 10 Gyr to inspiral via quiescent GW decay alone, so it doesn't
manufacture EMRIs as a numerical artifact) — but that choice is mine, not N26's or Rose et al.'s,
and it directly sets the EMRI rate I get. If there's a value or derivation I'm missing — from
either paper, or unpublished — I'd want to use it instead; it's the most likely single lever to
close the EMRI-rate gap in Section 1's bottom line.

## 3. Extending the validated model to N26's own Section 5.4 open questions

With validation in hand, I used the same pipeline to pursue the two questions Section 5.4
poses as open future work. Both answers below are reported under **both** readings from Section
2.2, since the choice turned out to matter as much here as it did for validation itself.

### 3.1 — Is there a sharp critical initial-mass threshold, or a gradual one?

Scanning a log-uniform mass family on $[6, m_{\rm max}]\,M_\odot$ over $m_{\rm max}=16$–$100\,
M_\odot$: a first pass at 3 seeds/point (matching the Section 1 validation convention) made the
transition look sharp, with $m_{\rm max}=31.8\,M_\odot$ appearing fully saturated (3/3 seeds
producing an IMBH). That turned out to be a small-sample illusion — rerunning the same point at
8 seeds showed it was actually 6/8 (75%), not saturated at all. I'm surfacing this correction
explicitly because it's exactly the kind of thing a thin sample can manufacture, and it's why I
adopted an 8-seed floor for every location claim from that point on, including the SMBH-mass
scan in 3.2 below.

With that floor applied: under the **star-only** reading, the probability that *any* BH out of
1000 crosses 100 $M_\odot$ in a 10 Gyr trial rises smoothly from 0% to 75% across roughly
$m_{\rm max}\approx20$-$32\,M_\odot$ (mean population mass $\approx12$-$15\,M_\odot$), without
ever fully saturating within that band — a genuine, gradual crossover, not a step function, and
one that sits well below H18's own $100\,M_\odot$ upper limit. Under the **BH-inclusive**
reading, no threshold appears anywhere in the tested range — even at $m_{\rm max}=100$ (H18
exactly), only a marginal 0.1-0.3% of the population crosses 100 $M_\odot$. I also checked N26's
own 0%/15% primordial-binary-merger axis (the "+M" prescription) at the same resolution and
found no statistically distinguishable effect on the crossover (pooled 19/40 vs. 20/40 any-IMBH
trials, Fisher's exact $p=1.0$) — the mass-scale of the initial distribution, not the
primordial-pairing fraction, is what drives it.

### 3.2 — Does the result generalize beyond the Milky Way's SMBH mass?

Scanning $m_{\rm smbh}$ over 3 decades (7 points, $1.26\times10^5$ to $1.26\times10^8\,M_\odot$,
8 seeds each, H18, cluster structure held fixed at the Milky Way's): under **star-only**, all
56/56 runs across every mass tested produced at least one IMBH — the paper's qualitative result
does not appear to be a Milky Way-specific coincidence. Under **BH-inclusive**, the mean
fraction of BHs exceeding $100\,M_\odot$ stayed below 0.5% at every single grid point across the
full 3-decade range — the suppression effect generalizes just as robustly as the formation
effect does. So the generalization answer is a qualified "yes": the paper's claim holds up
across SMBH mass, but which side of the claim you get (forms readily vs. essentially doesn't
form) still depends on the Section 2.2 ambiguity.

One further, more tightly-scoped observation from this scan: holding cluster structure fixed
while varying only $m_{\rm smbh}$ (a modeling choice on my end, not from N26) revealed a
non-monotonic runaway-growth regime concentrated 3-10x *below* the Milky Way's own SMBH mass,
where individual BHs reached masses of millions of $M_\odot$ — in some runs, exceeding the
central SMBH itself. Eleven of the 112 runs in this scan (all star-only, all in the
$4\times10^5$-$1.26\times10^6\,M_\odot$ band where this effect concentrates) didn't reach 10 Gyr
before hitting the integrator's step ceiling — their reported masses reflect partial integration
(roughly 1-9 Gyr), not the full window. I checked this wasn't manufacturing the finding: a seed
that completed *within* the cap at the same mass still reached $1.56\times10^6\,M_\odot$, and the
ceiling-hit rate itself is non-monotonic (0% at the lowest mass tested, 50-87.5% in the band, back
to 0% at and above the Milky Way anchor) — not the shape you'd expect if this were simply
numerical stalling getting worse as the calculation gets harder. That's the basis for my
confidence that it isn't purely an integration artifact, though the partial integration does mean
the true (uncapped) masses in this band are a lower bound, not a final answer. I'm flagging the
whole finding as a consequence of holding the cluster's density profile fixed while shrinking the
SMBH — not a claim about what a real lower-mass galactic nucleus would do — and mention it mainly
because it touches the same growth channels as the Section 1 validation residual.

## Closing

I'd welcome any correction, context, or unpublished detail that bears on any of the three open
items in Section 2 — particularly if one was a known issue, if there's a reading of Eq. 22 I
haven't considered, or a convention for initial orbital sampling I've missed. The full repository
(code, tests, every raw run, and `paper/limitations.md`'s complete log of every judgment call made
along the way) is public and linked above if useful. Happy to share more detail on any of the
above, or to run additional checks if something here looks off.
