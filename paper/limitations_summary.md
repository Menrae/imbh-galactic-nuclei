# Limitations, modeling choices, and open questions

**Prepared by**: Armeen Shasti-Nazem (University of Washington, <aashasti@uw.edu>) — independent
reimplementation project, not affiliated with the original study.
**Regarding**: Newton, A., Rose, S. C., Kıroğlu, F., Hoang, B.-M., & Rasio, F. A. 2026, *ApJ*,
1006:184, "Intermediate-mass Black Hole Formation from Hierarchical Mergers in Galactic Nuclei"
(hereafter N26).

This is the companion reference for everything the outreach memo summarizes: every place N26's
text was ambiguous, silent, or possibly mistaken, what we chose and why, and how much each choice
matters for the results. The memo (`outreach/technical_memo.md`) is the short version built for a
first read; this document is the complete one. The complete session-by-session working log —
every dead end, every intermediate number, every re-check — lives in `paper/limitations.md`, if
you want the full trail behind any item below.

## At a glance

| # | Item | Type | Our resolution | Confidence | Affects |
| --- | --- | --- | --- | --- | --- |
| 1.1 | Eq. 21 prefactor exponent (1/3 vs 1/2) | Possible erratum | Used 1/2 (Bardeen 1970 source value) | High | Predicted max BH spin |
| 1.2 | Eq. 19–20 $\dot m_{\rm BH}$ vs $\Delta m_{\rm BH}$ | Possible erratum | Read Eq. 20 as using the Eq. 19 rate | High (dimensional necessity) | Captured stellar mass per collision |
| 1.3 | K20 metallicity: "solar" vs Kremer et al.'s $Z=0.1\,Z_\odot$ | Possible erratum | Not resolved; used N26's own Figure 1 histogram regardless | N/A | K20/K20+M mass function |
| 1.4 | Initial $a_\bullet$, $e_\bullet$ sampling | Gap in text | Inherited Rose et al. 2022's convention (thermal $e$, log-uniform $a$); inner bound is our own choice | Low on inner bound specifically | EMRI rate |
| 2.1 | Eq. 22 $\langle M_{\rm avg}\rangle$, $\rho$: star-only vs BH-inclusive | Open ambiguity | Star-only, default; both reported everywhere | **Open — genuinely unresolved** | Nearly every downstream result |
| 2.2 | Coulomb logarithm $\ln\Lambda$ | Unspecified | $\ln(M_\bullet/M_\star)\approx15.2$, from two independent primary sources | High | Relaxation/EMRI timing |
| 2.3 | Eq. 10's "$L$" | Undefined symbol | Solved via Barausse & Rezzolla 2009, verified against their own NR benchmark | High | Merger remnant spin |
| 2.4 | K20 mass function | No closed form | Reconstructed piecewise-uniform sampler from Figure 1's histogram | Medium (by-eye bin reading) | K20/K20+M results |

## 1. Places N26's own text may need a correction or clarification

### 1.1 Eq. 21's prefactor exponent

Eq. 21 (BH spin change from a stellar collision) prints its prefactor as $r_{\rm ISCO}^{1/3}/3$.
The paper attributes the formula to Volonteri, Sikora, Lasota, & Merloni 2013 (ApJ, 775, 94),
whose own Eq. 14 — the Bardeen (1970) thin-disk spin-up result — has exponent $1/2$:
$r_{\rm ISCO}(t)^{1/2}/3$. We confirmed the printed $1/3$ isn't an OCR artifact by cropping the
PDF at high resolution directly. The inner square-root term matches exactly between the two
papers once N26's unsubscripted "$r$" is read as $r_{\rm ISCO}$, so this reads as an isolated
exponent slip rather than a deliberately different formula.

We implemented $1/2$, since it's the long-established result used consistently elsewhere in the
literature (King & Kolb 1999; King, Pringle & Hofmann 2008; Volonteri et al. 2005, 2013) and
Eq. 21's own text attributes it to Volonteri et al. 2013 rather than deriving a new variant. This
has a first-order effect on predicted maximum spins, so we'd value confirmation either way.

### 1.2 Eq. 19–20's rate/mass notation

Eq. 19 defines an accretion **rate**, $\dot m_{\rm BH}$ (units mass/time). Eq. 20 then computes a
captured mass as "$\Delta m_{\rm BH}\times t_{\star,\rm cross}$" — but multiplying a mass by a
time doesn't dimensionally yield a mass, while multiplying a rate by a time does. We read Eq. 20
as using the Eq. 19 rate ($m_{\rm cap}=\min(\dot m_{\rm BH}\times t_{\star,\rm cross},\,1\,
M_\odot)$), since no other reading is dimensionally consistent.

### 1.3 K20's stated metallicity

N26's K20 paragraph states "we assume solar metallicity for all stars," but Kremer et al. 2020
(the paper K20 is based on) runs its own simulations at $Z=0.002=0.1\,Z_\odot$, not solar. We
didn't attempt to resolve which is correct — it may be a loose paraphrase in N26, or N26 may have
re-run Kremer et al.'s setup at a different metallicity than published. Either way, we worked
directly from N26's own Figure 1 histogram (see 2.4 below) rather than trying to reproduce Kremer
et al. 2020 at one metallicity or the other, which sidesteps the question but doesn't answer it.

### 1.4 Initial orbital properties aren't specified in Section 3

Section 2 says BHs' "initial masses, spins, and orbital properties" are drawn "statistically as
described in Section 3" — but Section 3, read in full, covers only mass and spin distributions.
It never states how the initial semimajor axis $a_\bullet$ or eccentricity $e_\bullet$ about the
SMBH are sampled. We confirmed this is a genuine gap by re-reading the full PDF text directly,
not a missed sentence.

Since N26 explicitly presents its dynamical framework as an extension of Rose et al. (2022), we
inherited that paper's stated convention instead: thermal eccentricity ($p(e)\,de=2e\,de$), and
$a_\bullet$ log-uniform out to the outer bound N26 itself states (0.1 pc, the paper's stated focus
region). Neither paper states an *inner* bound for the log-uniform sampling, though — that value
is entirely our own choice, and it directly sets the EMRI rate we get (see 4 below). We picked
$a_{\rm min}=10^{-3}$ pc from an inspiral-time argument: a BH born there takes $\approx1450$ Gyr to
inspiral via quiescent GW decay alone, comfortably longer than the 10 Gyr integration window, so
it doesn't manufacture EMRIs as a pure numerical artifact. (An earlier default of $10^{-4}$ pc
failed this test badly — a BH born there inspirals in $\approx0.15$ Gyr, and a full-scale smoke
test showed 66% of the population became EMRIs from that artifact alone.) If there's a published
or unpublished convention we're missing, we'd want to use it instead.

## 2. Ambiguities we had to resolve ourselves

### 2.1 Eq. 22's $\langle M_{\rm avg}\rangle$ and $\rho$ — the most consequential open item

Eq. 22's two-body relaxation timescale, $t_{\rm relax}=0.34\,\sigma^3/(G^2\rho\langle M_{\rm
avg}\rangle\ln\Lambda)$, depends on an "average object mass" and density that N26's text describes
only generically. We found real textual support for two different readings, with no way to settle
it from the paper's text alone:

- **Star-only** ($\langle M_{\rm avg}\rangle=1\,M_\odot$, $\rho=\rho_\star$): S. C. Rose et al.
  2022 (ApJL, 929, L22) — the paper N26 says this relaxation mechanism is "first developed by" —
  states its own version of this formula (their Eq. 10) is explicitly for a "single-mass system,"
  with $\langle M_*\rangle$ "here assumed to be 1 $M_\odot$." Rose et al. 2022 has no BH-density
  term at all, so their formula can't mean anything else.
- **BH-inclusive** (density-weighted mean over both stars and background BHs, using N26's own
  Eq. 2 BH-density profile): N26's Eq. 22 text drops Rose et al. 2022's "single-mass system"
  qualifier, and N26 introduces a new two-component density apparatus that Rose et al. 2022 never
  had. Most tellingly, Eq. 23 (mass-segregation time) explicitly overrides to star-only for that
  one derived quantity — which only makes sense as a deliberate exception if Eq. 22's own default
  isn't already star-only.

We tested both readings empirically at $N=1000$, H18, 10 Gyr, 3 seeds: star-only gives 34–37% EMRI
and a functioning merger channel (400–580 mergers/run); BH-inclusive gives ~66–69% EMRI and
essentially zero mergers, reproducing what looks like the exact failure mode this relaxation
mechanism exists to avoid — objects diffuse into the SMBH before the merger channel can complete
more than a handful of events. Neither reading reproduces Table 1's exact balance, but only
star-only leaves the merger channel active at meaningful scale, so it's our working default. We
also checked whether a principled multi-species weighting (the textbook Chandrasekhar/Spitzer
generalization, which weights by $\sum n_j m_j^2$ rather than a number-weighted mean) might offer
a middle ground; it doesn't — it's numerically *more* extreme than BH-inclusive, not intermediate.
This is logged as a genuinely open, unresolved choice, not a settled one — it's also, as it turns
out, the single choice that controls both of Section 4's results below.

### 2.2 The Coulomb logarithm

N26's Eq. 22 includes $\ln\Lambda$ with only a generic citation to Binney & Tremaine 2008 and no
numeric value (Rose et al. 2022's own version of this formula gives no number either). We resolved
this from two independent sources specific to the $Q=M_\bullet/m\gg1$ regime (a single, heavy
central mass dominating relaxation of a much lighter population, physically distinct from the
globular-cluster convention $\ln(0.4N)$): Bar-Or, Kupi & Alexander 2013 (ApJ, 764, 52) gives
$\ln\Lambda\sim\log(M_\bullet/m_\star)$ for exactly this regime, and Vasiliev 2017 (ApJ, 848, 10),
a modern multi-component Fokker–Planck code, uses $\ln\Lambda=15$ for a Milky-Way-like nucleus at
the same $M_\bullet=4\times10^6\,M_\odot$ N26 uses. We adopted $\ln\Lambda=\ln(M_\bullet/M_\star)
\approx15.2$ — the two independent sources converge closely (15 vs. 15.2), so we treat this as
resolved with high confidence, distinct in kind from the still-open items above.

### 2.3 Eq. 10's undefined "$L$"

N26 Eq. 10 (final remnant spin) uses a quantity "$L$" (orbital angular momentum) without giving a
formula for it. We traced this to Barausse & Rezzolla 2009 (ApJL, 704, L40), whose aligned-spin
reduction has identical structure to N26's Eq. 10, letting us solve for their script-$\ell$ (N26's
"$L$") from their own fitted formula. We verified the implementation against Barausse & Rezzolla's
own quoted numerical-relativity benchmark ($a_{\rm fin}=0.68646$ for an equal-mass, non-spinning
merger) to 3 decimal places — an independent check, not just internal self-consistency. High
confidence.

### 2.4 K20's mass function isn't a closed-form expression

N26 states its K20 initial condition is "based on" Kremer et al. 2020, which turns out to be a
cluster-collision simulation whose resulting BH mass function is a numerical output, not a
formula — unlike every other distribution in the paper. We read N26's own Figure 1 (left panel)
histogram directly at high resolution and built a piecewise-uniform sampler from the approximate
bin edges and heights, on the grounds that this is the most direct available proxy for what N26
actually sampled from — closer to the source than attempting to reproduce Kremer et al.'s
simulation methodology from text alone. This carries genuine uncertainty from the by-eye bin
reading, on top of the reconstruction itself only approximating whatever smoother distribution
underlies the true simulation output.

## 3. A physical effect worth flagging on its own terms

Beyond the ambiguities above, our H18/H18+M validation runs turned up something that looks like a
genuine feature of the model rather than an implementation bug: a heavy-tailed runaway-growth
regime. Across six H18/H18+M seeds, 44–58 of 1000 BHs exceed 200 $M_\odot$, 13–19 exceed
500 $M_\odot$, and in most runs a single BH reaches into the thousands to tens of thousands of
solar masses over 55–86 successive merger generations — well past Table 1's reported ceiling of
407.3 $M_\odot$ and 12 generations.

We traced the mechanism directly: both growth channels have genuine, paper-documented positive
feedback once a BH is already massive and sitting in the dense inner region — Eq. 18's
gravitational-focusing cross-section scales with BH mass, and Eq. 4's GW-capture cross-section
scales superlinearly with total mass ($t_{\rm GW}\propto m_1^{-12/7}$ once one component
dominates). We re-verified Eqs. 4–7 term-for-term against a high-resolution page-image render of
N26 page 4 and found no transcription error — so if this is a discrepancy, it isn't one of
implementation. Recoil kicks for these late-stage, extreme-mass-ratio mergers are tiny (0.05–6.7
km/s), so the growing BH's orbit barely moves once the runaway starts — it neither escapes to a
safer radius nor decays into the SMBH fast enough to self-terminate within 10 Gyr.

We don't have an explanation for why N26's own Table 1 doesn't show this ceiling being reached —
possibilities include an unstated stellar-depletion or ejection-rate mechanism, a different
Eq. 22 reading (BH-inclusive relaxation does suppress this tail, at the cost of suppressing the
merger channel almost entirely — see 2.1), or something else we haven't identified. We'd
genuinely value your read on whether this matches anything you saw in your own runs.

## 4. Extending the model to Section 5.4's open questions

With validation in hand, we used the same pipeline on the two questions Section 5.4 poses as open
future work. Both results below are reported under **both** readings from 2.1, since that choice
turned out to matter as much here as it did for validation.

### 4.1 Is the critical initial-mass threshold sharp or gradual?

Scanning a log-uniform mass family on $[6,m_{\rm max}]\,M_\odot$ over $m_{\rm max}=16$–$100\,
M_\odot$: under **star-only**, the probability that any BH out of 1000 crosses 100 $M_\odot$ in a
10 Gyr trial rises smoothly from 0% to 75% across roughly $m_{\rm max}\approx20$–$32\,M_\odot$,
without saturating anywhere in that band — a genuine, gradual crossover, not a step function, and
one that sits well below H18's own 100 $M_\odot$ upper limit. Under **BH-inclusive**, no threshold
appears anywhere in the tested range — even at $m_{\rm max}=100$ (H18 exactly), only 0.1–0.3% of
the population crosses 100 $M_\odot$. We also checked N26's own 0%/15% primordial-binary-merger
axis at the same resolution and found no statistically distinguishable effect on the crossover
location (pooled 19/40 vs. 20/40 any-IMBH trials, Fisher's exact $p=1.0$) — the mass-scale of the
initial distribution, not the primordial-pairing fraction, is what drives it.

One methodological note we're flagging deliberately: a first pass at 3 seeds/point made the
transition look sharp, with one grid point appearing fully saturated (3/3 seeds). Rerunning that
point at 8 seeds showed it was actually 6/8 (75%) — not saturated at all. We're surfacing this
correction explicitly because it's exactly the kind of artifact a thin sample can manufacture, and
it's why every location claim from that point on (including 4.2 below) used an 8-seed floor.

### 4.2 Does the result generalize beyond the Milky Way's SMBH mass?

Scanning $m_{\rm smbh}$ over 3 decades (7 points from $1.26\times10^5$ to $1.26\times10^8\,
M_\odot$, 8 seeds each, H18, cluster structure held fixed at the Milky Way's own values): under
**star-only**, all 56 of 56 runs across every mass tested produced at least one IMBH — the
qualitative result doesn't appear to be a Milky Way-specific coincidence. Under **BH-inclusive**,
the mean fraction exceeding 100 $M_\odot$ stayed below 0.5% at every grid point across the full
range — the suppression generalizes just as robustly as the formation effect does. So the answer
is a qualified "yes": the result holds up across SMBH mass, but which side of it you land on
still depends on the Section 2.1 ambiguity.

A more tightly-scoped observation from this same scan: holding cluster structure fixed while
varying only $m_{\rm smbh}$ — a modeling choice on our end, not from N26, made to isolate the pure
dynamical effect of SMBH mass — revealed a non-monotonic runaway-growth regime concentrated
3–10x *below* the Milky Way's own SMBH mass, where individual BHs reached masses of millions of
$M_\odot$, in some runs exceeding the central SMBH itself. We don't read this as a claim about
real lower-mass galactic nuclei (a real one would plausibly have correspondingly lower density
too, which this scan doesn't model) — it's flagged here mainly because it touches the same growth
channels as the Section 3 finding above, at a different corner of parameter space.

## 5. Other modeling choices, briefly

- **Fixed structural profile.** As in N26, $\rho_\star(r)$, $n_{\rm BH}(r)$, and $\sigma(r)$ are
  treated as a static background rather than self-consistently evolved as BHs merge, grow, or are
  ejected. This is inherited directly from N26's own semianalytic approach, not introduced by us.
- **GW inspiral formulas.** N26 cites Peters & Mathews (1963) / Peters (1964) generically without
  giving explicit $da/dt$, $de/dt$ forms. We used the standard orbit-averaged closed forms from
  those papers directly — textbook results, not an ambiguity.
- **EMRI stopping-condition caveat.** N26 itself notes that its EMRI stopping condition may flag
  some plunging/eccentric-orbit BHs as EMRIs prematurely, changing the EMRI rate by "no more than
  a factor of 2." We carried this caveat forward as-is; it's relevant context for the EMRI-rate
  gap noted in the validation memo.
- **Eccentricity dependence sign for BH–star collisions.** Rose et al. 2020 (source of the Eq. 18
  $f_1,f_2$ terms) found collision timescales *decrease* with eccentricity for star–star
  collisions. We find the opposite sign for BH–star collisions specifically, because the
  gravitational-focusing term dominates the geometric term by ~3 orders of magnitude in that
  regime — this is a different regime of the same formula, not a contradiction of Rose et al.'s
  result, and both are well within their own stated "order unity" characterization.

## Where to find more

- **Full working log**, including every intermediate result, dead end, and re-check behind each
  item above: `paper/limitations.md`.
- **Raw scan data and validation runs**: `results/`.
- **Code and tests**: <https://github.com/Menrae/imbh-galactic-nuclei>.

We'd welcome correction, context, or any unpublished detail bearing on the items above — especially
Section 2.1, which is the one choice that ripples furthest through everything else here.
