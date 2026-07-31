# An independent reimplementation of Newton et al. (2026): validation status and two open questions

**Prepared by**: Armeen Shasti-Nazem (University of Washington) — independent reimplementation project, not affiliated with the original study.
**Regarding**: Newton, A., Rose, S. C., Kıroğlu, F., Hoang, B.-M., & Rasio, F. A. 2026, *ApJ*,
1006:184, "Intermediate-mass Black Hole Formation from Hierarchical Mergers in Galactic Nuclei"
(hereafter N26).
**Code**: https://github.com/Menrae/imbh-galactic-nuclei (full history, tests, and a running log
of every modeling judgment call in `paper/limitations.md`).

## Why this memo exists

Over the past several weeks we rebuilt N26's model from its equations up — every collision,
spin-change, relaxation, and GW-capture formula independently implemented and unit-tested —
specifically to (a) check whether the paper's central claims reproduce under an independent
implementation, and (b) use the validated pipeline to chase down the two open questions N26
poses in Section 5.4. We got far enough on both fronts that it seemed worth writing up rather
than letting it sit in a private repo. This memo summarizes where validation stands, two textual
ambiguities we ran into that materially affect the results, and what our extensions found. We'd
genuinely welcome your read on the two ambiguities in particular — in both cases we made a
specific, documented choice, but neither is fully settled, and you're the people best positioned
to say whether we read it right.

## 1. Validation against Table 1

We ran all four of N26's initial conditions (K20, K20+M, H18, H18+M) at $N=1000$,
$M_\bullet=4\times10^6\,M_\odot$, 10 Gyr, 3 seeds each, and compared against Table 1:

| IC | Mergers (ours / Table 1) | Max mass $M_\odot$ (ours / Table 1) | % BHs $>100\,M_\odot$ (ours / Table 1) |
|---|---:|---:|---:|
| K20 | 24.0 / 34 | 39.1 / 28.4 | 0.0% / 0% |
| K20+M | 28.7 / 30 | 46.2 / 57.8 | 0.0% / 0% |
| H18 | 1022.0 / 371 | 58,034 / 407.3 | 12.5% / 7.8% |
| H18+M | 1046.7 / 535 | 11,881 / 526.0 | 12.8% / 14.3% |

**K20 and K20+M reproduce well** — mergers and max mass both within ~1.3-1.5x of Table 1, which
is well inside the plausible range given seed-to-seed variance and the reconstruction
uncertainty in the K20 mass distribution itself (N26 cites this as drawn from a simulation
(Kremer et al. 2020) rather than a closed-form distribution, so we read the numbers directly off
the published histogram).

**H18 and H18+M are a mixed picture.** The population-level statistic that matters most for the
paper's headline claim — the fraction of BHs exceeding 100 $M_\odot$ — is actually close (12.5%
vs. 7.8% for H18; 12.8% vs. 14.3% for H18+M, the latter within seed noise). But the single
"max mass" order statistic is off by 20-220x, and merger count by ~2.9x. We traced this to a
specific, still-open mechanism: in every run, 1-3 of the 1000 BHs undergo 60-230 successive
merger generations (Table 1's own stated maximum is 12-16 generations) via a runaway
positive-feedback loop in which both growth channels' efficiency scales with the growing BH's
own mass. We narrowed one contributing factor (a since-fixed bug in our own `mean_bh_mass`
placeholder made the runaway tail *more* severe once corrected, implicating the GW-capture
channel's own mass-dependence, Eqs. 4-7), but the residual is not fully resolved and we are
reporting it candidly as an open item rather than a solved discrepancy. Full trace:
`paper/limitations.md#phase2-emri-rate-high`.

**Bottom line**: bulk-population behavior for both mass families is plausible; the extreme
upper tail specifically, for the heavier H18 family, runs hotter than Table 1 in our
implementation, for reasons we can point to mechanistically but haven't fully closed the loop
on.

## 2. Two open questions on the underlying equations

Both of the following are cases where our implementation made a specific, documented choice
that we believe is defensible from your own cited sources — but we want to flag them rather
than assume we read them correctly, since each one turns out to matter a great deal for the
results below.

### 2.1 — Eq. 21's prefactor exponent: 1/3 as printed, vs. 1/2 in the cited source

Eq. 21 (BH spin evolution from a stellar collision) is presented as extending Volonteri, Sikora,
Lasota, & Merloni 2013 (ApJ, 775, 94). The published Eq. 21 prefactor is
$r_{\rm ISCO}^{1/3}/3$ (we confirmed this isn't an OCR artifact via a high-resolution crop of
the PDF). Volonteri et al. 2013's own Eq. 14 — the Bardeen (1970) thin-disk spin-up result — has
exponent $1/2$: $r_{\rm ISCO}(t)^{1/2}/3$. The inner square-root term is identical between the
two papers once N26's unsubscripted "$r$" is read as $r_{\rm ISCO}$, so this looks like a single
exponent that doesn't match, not a different formula.

We implemented $1/2$, since it's the long-established Bardeen result used consistently across
the literature (King & Kolb 1999; King, Pringle & Hofmann 2008; Volonteri et al. 2005, 2013),
and Eq. 21's text explicitly attributes the formula to Volonteri et al. 2013 rather than
deriving a new variant. Our best guess is that this is a typesetting slip rather than an
intentional change — but we haven't confirmed that with you, and it's exactly the kind of thing
that's very easy to miss without going back to Eq. 14 of the cited source directly. Could you
confirm which exponent was intended? It has a direct, first-order effect on predicted maximum
spins.

### 2.2 — Eq. 22's $\langle M_{\rm avg}\rangle$ and $\rho$: star-only, or BH-inclusive?

This is the more consequential of the two. Eq. 22's two-body relaxation timescale,
$t_{\rm relax}=0.34\,\sigma^3/(G^2\rho\langle M_{\rm avg}\rangle\ln\Lambda)$, depends on an
"average object mass" $\langle M_{\rm avg}\rangle$ and density $\rho$ that N26's text describes
only generically ("the average object mass," "their mass density"). We found textual support
for two different readings, and — as far as we can tell — no way to settle it from the paper's
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

We tested both readings empirically (N=1000, H18, 10 Gyr): star-only gives EMRI fractions of
34-37% and 400-580 mergers (with the runaway tail from Section 1); BH-inclusive gives an EMRI
fraction of 68.8% and **zero** mergers in every trial, reproducing what looks like the exact
early-development problem this relaxation mechanism was meant to fix — objects get diffused
into the SMBH before the merger channel can ever complete a single event. Neither reading
reproduces Table 1's exact balance, but only star-only leaves the merger channel functioning at
all, so it's our working default. This is logged as an open, unresolved choice, not a settled
one (`paper/limitations.md#average-object-mass`).

We'd be glad to know which reading was intended, or whether Eq. 22 was meant more loosely than
either extreme — because, as it turns out, this single choice controls nearly every downstream
result we describe below.

## 3. Extending the validated model to N26's own Section 5.4 open questions

With validation in hand, we used the same pipeline to pursue the two questions Section 5.4
poses as open future work. Both answers below are reported under **both** readings from Section
2.2, since the choice turned out to matter as much here as it did for validation itself.

### 3.1 — Is there a sharp critical initial-mass threshold, or a gradual one?

Scanning a log-uniform mass family on $[6, m_{\rm max}]\,M_\odot$ over $m_{\rm max}=16$–$100\,
M_\odot$ (8 seeds/point in the region of interest, to guard against small-sample noise): under
the **star-only** reading, the probability that *any* BH out of 1000 crosses 100 $M_\odot$ in a
10 Gyr trial rises smoothly from 0% to 75% across roughly $m_{\rm max}\approx20$-$32\,M_\odot$
(mean population mass $\approx12$-$15\,M_\odot$), without ever fully saturating within that
band — a genuine, gradual crossover, not a step function, and one that sits well below H18's own
$100\,M_\odot$ upper limit. Under the **BH-inclusive** reading, no threshold appears anywhere in
the tested range — even at $m_{\rm max}=100$ (H18 exactly), only a marginal 0.1-0.3% of the
population crosses 100 $M_\odot$. We also checked N26's own 0%/15% primordial-binary-merger
axis (the "+M" prescription) at the same resolution and found no statistically distinguishable
effect on the crossover (pooled 19/40 vs. 20/40 any-IMBH trials, Fisher's exact $p=1.0$) — the
mass-scale of the initial distribution, not the primordial-pairing fraction, is what drives it.

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
while varying only $m_{\rm smbh}$ (a modeling choice on our end, not from N26) revealed a
non-monotonic runaway-growth regime concentrated 3-10x *below* the Milky Way's own SMBH mass,
where individual BHs reached masses of millions of $M_\odot$ — in some runs, exceeding the
central SMBH itself. We can trace the mechanism (competing scalings between relaxation-driven
EMRI removal and both growth channels' efficiency, both $\propto\sigma$-dependent), and we're
confident it isn't an integration artifact, but we're flagging it explicitly as a consequence of
holding the cluster's density profile fixed while shrinking the SMBH — not a claim about what a
real lower-mass galactic nucleus would do. We mention it mainly because it touches the same
growth channels as the Section 1 validation residual, and thought it might be of independent
interest.

## Closing

We'd welcome any correction, context, or unpublished detail that bears on either of the two
open items in Section 2 — particularly if either was a known issue, or if there's a reading of
Eq. 22 we haven't considered. The full repository (code, tests, every raw run, and
`paper/limitations.md`'s complete log of every judgment call made along the way) is public and
linked above if useful. Happy to share more detail on any of the above, or to run additional
checks if something here looks off.
