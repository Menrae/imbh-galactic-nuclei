# Limitations and caveats (running log)

Maintained incrementally throughout the project — every simplifying assumption,
paper ambiguity, or deliberately-unmodeled effect gets a line here as soon as it comes up,
not retrofitted at the end. Mirrors the "Open items log" in `docs/equations.md` for
equation-specific issues; this file is broader (methodology, validation, scope).

Starting with Phase 4, secondary findings (patterns discovered in our own output, beyond
plain Table 1 agreement/disagreement, especially ones touching an ambiguity or apparent
inconsistency in N26's own text) go through the explicit checklist in
`paper/methodology.md` before being stated as a *result* rather than logged as a
*preliminary observation* here.

As of this pass, the primary source PDF (`references/Newton_2026_ApJ_1006_184.pdf`) is
available directly and has been read page-by-page (including page-image crops for equations
that garble under plain-text extraction). Items below previously flagged as "paper text not
yet available" have been re-resolved against the actual PDF; a few *new* ambiguities turned
up that a paraphrased equation map couldn't have revealed.

## Phase 3 — K20 mass distribution reconstructed from a figure, not a formula {#k20-reconstruction}

N26's K20 initial condition is "based on" Kremer et al. 2020 (arXiv:2006.10771), which turns
out to be a young-massive-star-cluster collision simulation (Kroupa IMF stars, $Z=0.1Z_\odot$)
whose resulting BH mass function is a numerical output, not a closed-form expression given
anywhere in that paper — there was no formula to transcribe, unlike every other equation in
this project so far. **Resolution adopted**: read N26's own Figure 1 (left panel) histogram
directly at high resolution and reconstruct a piecewise-uniform sampler from the approximate
bin edges/heights (`initial_conditions.K20_BIN_EDGES`, `K20_BIN_WEIGHTS`). **Why**: this is
the most direct available proxy for what N26 actually sampled from — closer to the source
than attempting to re-run or approximate Kremer et al.'s simulation methodology from their
paper's text, which isn't reproducible without their actual simulation code/output. **How to
apply**: treat K20 (and by extension K20+M) mass values as approximate, with uncertainty from
both the by-eye bin reading and the fact that a piecewise-uniform-within-bins sampler is
itself a simplification of whatever the true underlying (presumably smoother) distribution
looks like. H18, by contrast, has an exact closed form directly from Hoang et al. 2018's text
("uniform in logspace between 6-100 $M_\odot$") and required no such reconstruction.

Also note a **metallicity inconsistency** worth flagging: N26's K20 paragraph states "we
assume solar metallicity for all stars," but Kremer et al. 2020's own simulations (which K20
is "based on") use $Z=0.002=0.1Z_\odot$, not solar. Not resolved — may be a loose paraphrase
in N26, or may indicate N26 adapted/re-ran Kremer et al.'s setup at a different metallicity
than published, which would also mean the mass function itself could differ from what's
plotted in Kremer et al. 2020's own paper. Another reason the Figure-1-reconstruction
approach (matching what N26 actually plotted) is more defensible than trying to reproduce
Kremer et al. 2020 exactly.

## Resolved (previously flagged as open, now confirmed from the PDF)

- **Velocity dispersion (Eq. 1)**: confirmed exact form is
  $\sigma(r)=\sqrt{GM_\bullet/[(\alpha+1)r]}$ — the earlier placeholder
  $\sqrt{GM_\bullet/r}$ (missing the $(\alpha+1)$ factor) was wrong and has been fixed in
  `cluster.velocity_dispersion`, which now also requires `alpha` as an explicit argument.
- **BH number density normalization (Eq. 2)**: confirmed $n_0=10^4\,{\rm pc}^{-3}$ at
  $R_h=1$ pc are given directly in-text, not free parameters. `cluster.bh_number_density`
  now defaults to these values instead of requiring a caller-supplied `n0`.
- **Holley-Bockelmann et al. 2008 kick constants (A, B, H, K)**: pulled directly from
  arXiv:0707.1334 (the paper's Eq. 2-4): $A=1.2\times10^4$ km/s, $B=-0.93$,
  $H=(7.3\pm0.3)\times10^3$ km/s, $K=(6.0\pm0.1)\times10^4$ km/s.
- **$f_1(e_{\rm BH})$, $f_2(e_{\rm BH})$ in Eq. 18**: pulled directly from S. C. Rose et al.
  2020 (ApJ, 904, 113), Eqs. 20-21 — closed forms in the Gauss hypergeometric function
  ${}_2F_1$, parametrized by the eccentricity $e$ and the density slope $\alpha$ (we use
  $\alpha_\star$, matching Eq. 18's pairing with the stellar profile).

## Velocity-dispersion alpha choice {#velocity-dispersion-alpha-choice}

N26 Eq. 1 depends on a density-profile slope $\alpha$, but the paper uses two different
slopes ($\alpha_\star=1.25$ for stars, $\alpha_{\rm BH}=1.83$ for BHs) and never explicitly
restates which one applies to $\sigma$ in every equation that uses it.

**Resolution adopted**: pair $\sigma$'s $\alpha$ with whichever density equation it's grouped
with in-text: $\alpha_\star$ for the BH-star collision timescale (Eq. 18, which explicitly
cites "Equations (1) and (3)" together), $\alpha_{\rm BH}$ for the GW capture timescale (Eq.
7, paired with $n_{\rm BH}$ from Eq. 2).

**Why**: this is the only textual anchor N26 gives; no other pairing is stated. **How to
apply**: `cluster.velocity_dispersion` takes `alpha` as a required (non-defaulted) argument
specifically so every call site in the Section 4 modules must make this choice explicitly
and visibly, rather than silently inheriting a wrong default.

## Eq. 21 prefactor exponent discrepancy (1/3 vs 1/2) {#eq21-exponent-discrepancy}

N26's published Eq. 21 (BH spin change from a stellar collision) prints the prefactor as
$r_{\rm ISCO}^{1/3}/3$ — confirmed via an ultra-high-resolution crop of the PDF, not an OCR
artifact. The formula is explicitly attributed to M. Volonteri et al. 2013 (ApJ, 775, 94),
whose own Eq. 14 (the Bardeen 1970 thin-disk spin-up formula, confirmed via direct PDF read
of arXiv:1210.1025) has exponent $1/2$: $r_{\rm ISCO}(t)^{1/2}/3$. The inner square-root term
matches exactly between the two papers once N26's unsubscripted "$r$" is identified as
$r_{\rm ISCO}$, so this looks like an isolated typesetting slip in N26 rather than a
different formula.

**Resolution adopted**: implement with the source's exponent, $1/2$.

**Why**: the $1/2$ exponent is the long-established Bardeen (1970) result used consistently
across the accretion-spin-evolution literature (King & Kolb 1999; King, Pringle & Hofmann
2008; Volonteri et al. 2005, 2013); a lone $1/3$ in one equation of one paper, with no
supporting derivation shown, is much more likely to be a transcription slip than an
intentional modification — especially since N26 explicitly says they "use equations from M.
Volonteri et al. (2013)" rather than deriving their own variant.

**How to apply**: `imbh_nuclei.collisions.spin_change` implements the $1/2$ exponent. This
is a genuine, unresolved discrepancy with the *published* N26 text — **flagged explicitly to
the user** (not silently picked) because it changes predicted spin values, and Phase 3
validation (reproducing Table 1's max-spin column) is the first place a wrong choice here
would show up as a discrepancy. Also note N26 states the saturation branch caps spin at
literal $\chi_f=1$, while Volonteri et al. 2013's original formula caps at $a=0.998$ (the
Thorne 1974 equilibrium limit); we follow N26's stated cap of 1 since we're reproducing N26's
model specifically (the difference is $<0.2\%$, immaterial either way).

## ṁ_BH vs "Δm_BH" notation clash in Eqs. 19-20 {#mdot-vs-delta-m-notation}

Eq. 19 explicitly defines an accretion **rate**, $\dot m_{\rm BH}$ (dot notation, units
mass/time). Eq. 20 then computes a captured **mass** as "$\Delta m_{\rm BH} \times
t_{\star,\rm cross}$" (no dot) — multiplying a mass by a time does not dimensionally yield a
mass, whereas multiplying a *rate* by a time does.

**Resolution adopted**: treat Eq. 20 as using the Eq. 19 quantity ($\dot m_{\rm BH}$), i.e.
$m_{\rm cap} = \min(\dot m_{\rm BH}\times t_{\star,\rm cross},\ 1\,M_\odot)$.

**Why**: pure dimensional analysis — no other reading makes Eq. 20 dimensionally consistent.

**How to apply**: `imbh_nuclei.collisions.captured_mass` takes the Eq. 19 rate as input.

## Average object mass in Eq. 22 {#average-object-mass}

**Revised during the Phase 3 EMRI-rate fix (see `#phase2-emri-rate-high` below for the full
diagnostic trail). Revised again at the start of Phase 4 to make this a config choice.**
Default: **star-only**, $\langle M_{\rm avg}\rangle = 1\,M_\odot$, $\rho=\rho_\star$ — adopted
as the default despite a genuine, unresolved textual tension with the BH-inclusive reading,
because it was empirically tested against the alternative and is the one that keeps the merger
channel alive (see below). This is flagged as **open**, not settled — a future pass with more
information (or direct correspondence with N26's authors) could overturn it.

**As of Phase 4**: this is no longer hardcoded. `IntegrationConfig.relaxation_mass_weighting`
(`"star_only"` default or `"bh_inclusive"`) selects between the two readings, resolved by
`imbh_nuclei.simulation._relaxation_mass_and_density` and consumed by both `_timescales` and
`_local_t_relax`. This is a plumbing change only, not a new physics decision — both code paths
already existed and were already empirically tested (see `#phase2-emri-rate-high`); Phase 4's
critical-mass-threshold scan is required to run under both settings and report whether its
conclusions are robust to this choice, per the recommendation at the end of the "searching for
a middle ground" entry below.

**The tension, in full:**

- **For star-only**: S. C. Rose et al. 2022 (ApJL, 929, L22), the paper N26 explicitly says
  it extends for exactly this relaxation mechanism ("a semianalytic model first developed by
  S. C. Rose et al. 2022"), states in their Eq. 10 — confirmed by direct PDF read, not
  paraphrase — "The two-body relaxation timescale for a **single-mass system** is: $t_{\rm
  relax} = 0.34\sigma^3/(G^2\rho\langle M_*\rangle\ln\Lambda_{\rm rlx})$ ... $\langle
  M_*\rangle$ is the average mass of the surrounding objects, **here assumed to be 1
  M$_\odot$**." Rose et al. 2022's own density model is single-component (stars only; no
  BH-density-profile analog of N26's Eq. 2 exists in that paper at all), so their formula
  has nothing else it *could* mean.
- **For BH-inclusive**: N26's own Eq. 22 sentence drops Rose et al. 2022's "single-mass
  system" qualifier entirely — it just says "$\langle M_{\rm avg}\rangle$ is the average
  object mass, and $\rho$ is their mass density" — and N26 introduces a genuinely *new*
  two-component density apparatus (Eq. 2's $n_{\rm BH}(r)$) that Rose et al. 2022 never had,
  specifically to support the new GW-capture channel. Most tellingly: Eq. 23 (mass-segregation
  timescale) explicitly writes $t_{\rm seg}\approx (M_\star/m_{\rm BH})\times t_{\rm
  relax}(\langle M_{\rm avg}\rangle=M_\star,\ \rho=\rho_\star)$ — confirmed via a
  high-resolution page-image re-render (not an OCR artifact) of page 6. Explicitly overriding
  to star-only for this *one* derived quantity only makes sense as a deliberate exception if
  Eq. 22's own default is *not* already star-only — otherwise the override is vacuous.

**Empirical test of both readings** (N=1000, H18, 10 Gyr, seed 0, with the Coulomb-log fix
below and substepping both applied): star-only gives EMRI 34-37% (consistent across 3 seeds),
400-580 mergers, but a systematic (3/3 seeds) runaway to one BH reaching 6000-9400 $M_\odot$
over 55-86 merger generations — Table 1 reports 407.3 $M_\odot$ max, 12G max generation for
H18. BH-inclusive gives EMRI 68.8%, **zero** mergers, max generation 1 — i.e. it reproduces
the original defect (relaxation depletes the population via EMRI before the GW-capture
channel ever completes a single merger) almost exactly. **Neither reproduces Table 1's
balance.** Star-only was kept because it is the only one of the two that leaves the
GW-capture channel functioning at all, which was the original point of this fix; the
runaway-growth residual is logged as a separate, still-open item (see
`#phase2-emri-rate-high`).

**Two other candidate explanations were checked and ruled out as the origin of the
runaway-growth residual specifically** (not as resolutions of the $\langle M_{\rm
avg}\rangle$ tension itself): (1) Rose et al. 2022 explicitly says their model treats
background stars as an undepleted "reservoir," and flags (as an acknowledged, *unimplemented*
limitation of their own model) that real stellar depletion near the SMBH "may reduce the BH
growth in the innermost region" — since this mechanism isn't in Rose et al. 2022's own model
either, its absence here doesn't explain why N26 reports a bounded growth ceiling; (2) N26
gives no numeric ejection-fraction or ejection-rate figure for its fiducial runs to check our
own ejection counts against, so that channel could not be verified or ruled out quickly.

**How to apply**: `imbh_nuclei.simulation._timescales` and `_local_t_relax` both call
`_relaxation_mass_and_density(cq, config)`, which branches on
`config.integration.relaxation_mass_weighting`; `relaxation.average_object_mass` is used
directly for the `"bh_inclusive"` branch (previously flagged as unused — no longer true).
`imbh_nuclei.relaxation.segregation_timescale` (Eq. 23) was star-only from the start,
independent of this config field, and is unaffected by this entry.

---

**Original resolution (2026, pre-Phase-3-validation; superseded above, kept for history)**:
$\langle M_{\rm avg}\rangle(r)$ = the number-density-weighted mean object mass of the local
population at $r$: $[n_\star(r)\cdot 1 M_\odot + n_{\rm BH}(r)\cdot \langle m_{\rm
BH}\rangle] / [n_\star(r)+n_{\rm BH}(r)]$, mirroring how N26 handles the analogous "$m_2$"
placeholder in the GW-capture $\eta$ calculation. This turned out to be the direct cause of
the Phase 2 smoke-test's near-100% EMRI fraction and near-zero merger count (see
`#phase2-emri-rate-high`) — the BH-density term dominates the stellar term by 3-46x at the
radii that matter, once actually run at N=1000/10 Gyr scale rather than the 50-300 BH smoke
tests used when this resolution was first adopted.

## mean_bh_mass placeholder was measurably wrong per-IC {#mean-bh-mass-placeholder}

Found while setting up the Phase 3 4-IC validation runs: `PopulationConfig.mean_bh_mass`
("the average of the initial mass distribution," used as $m_2$ in the GW-capture $\eta$
calculation per N26 Section 4.1's explicit statement) had been carried through Phase 2
smoke-testing as a flat `20.0` placeholder for every initial condition, never actually
checked against the corresponding sampler. A large-N (2e6) Monte Carlo estimate of each
sampler's true mean gives: K20 9.72, K20+M 9.94, H18 33.40, H18+M 34.20 — i.e. `20.0` was
~40% too *high* for K20/K20+M and ~40% too *low* for H18/H18+M.

**Resolution adopted**: `PopulationConfig.mean_bh_mass` default updated to `34.2` (H18+M,
this dataclass's own default IC); Phase 3 runs set it explicitly per IC to the measured
value above.

**Why**: this is a factual, computable property of each sampler (not an interpretive
ambiguity) — no reason to leave it at an unchecked round number once the samplers exist to
check it against.

**How to apply**: any future config construction for a specific IC must set `mean_bh_mass`
to that IC's actual sampler mean, not reuse the dataclass default across ICs.

## Phase 0/1 — Scaffolding & cluster structure (original entries, superseded above)

- **Fixed, static density/dispersion profile.** As in N26, the cluster structure
  ($\rho_\star(r)$, $n_{\rm BH}(r)$, $\sigma(r)$) is treated as a fixed background rather
  than self-consistently evolved as BHs merge, grow, or are ejected over the 10 Gyr
  integration. No full N-body cross-check is planned; this is a semianalytic
  reimplementation, so this limitation is inherited from the original model, not
  introduced by us.

## Phase 4.4 — GW inspiral / EMRI

- N26 does not give explicit $da/dt$, $de/dt$ formulas, citing Peters & Mathews (1963) /
  Peters (1964) generically. We implement the standard, well-established orbit-averaged
  closed forms from those papers directly (not an ambiguity — these are textbook results,
  reproduced identically across the literature).
- N26 explicitly caveats that EMRI stopping conditions may flag some plunging/eccentric-orbit
  BHs as EMRIs, but states this changes their EMRI rate by "no more than a factor of 2" and
  that most flagged BHs have already circularized. Carried forward verbatim as an inherited
  (not introduced) limitation — relevant when comparing our EMRI rate to Table 1/Section 5.4.

## Initial orbital properties (semimajor axis, eccentricity) not stated in N26 {#initial-orbital-properties}

N26 Section 2 says BHs' "initial masses, spins, and orbital properties" are drawn
"statistically as described in Section 3" — but N26's actual Section 3 text only covers
mass/spin distributions (K20, H18, etc.); it never describes how initial semimajor axis
$a_\bullet$ or eccentricity $e_\bullet$ about the SMBH are sampled. Confirmed by direct
re-read of the full PDF text — this is a genuine gap in N26 itself, not a missed sentence.

**Resolution adopted**: N26's own Section 2 states the model is "first developed by S. C.
Rose et al. (2022)" (ApJL, 929, L22; downloaded and confirmed by direct PDF read). That
paper explicitly states its own sampling convention: *"We assume that the orbits of the BHs
follow a thermal eccentricity distribution. We draw their semimajor axes, a_bullet, from a
uniform distribution in log distance, dN/d(log r) being constant."* — i.e. $p(e)\,de = 2e\,de$
for $e\in[0,1)$ (thermal/Ambartsumian 1937 distribution, the standard equilibrium
eccentricity distribution for a relaxed cluster), and $a_\bullet$ log-uniform between some
inner and outer radius. We adopt the same two conventions for N26, since N26 never states a
different one and explicitly inherits the base model from this paper.

**Why**: N26 doesn't re-derive its dynamical framework from scratch — it explicitly presents
itself as an extension of Rose et al. 2022's model (adding GW capture to that paper's
BH-star-collision-only treatment). Silently inheriting unstated methodological choices from
the explicitly-cited base paper is the most defensible reading, much more so than inventing
an unrelated convention.

**Still open**: the exact **radial bounds** for the log-uniform $a_\bullet$ sampling. Rose et
al. 2022 samples across "the inner few parsecs," extending down to within 0.01 pc; N26
instead explicitly restricts its entire study to "the inner 0.1 pc" of the NSC (stated
repeatedly, e.g. in the abstract and Section 2). We adopt $[a_{\min}, 0.1\,{\rm pc}]$ as the
sampling range. $a_{\min}$ is **not pinned to any N26-stated value — still flagged to
user** — but has a concrete, quantitatively-justified default: $a_{\min}=10^{-3}$ pc. An
earlier default of $10^{-4}$ pc (chosen only by the hand-wavy reasoning "safely outside the
EMRI $R_{\rm crit}\sim10^{-6}$ pc scale") turned out not to be safe at all: a full-loop smoke
test (50 BHs, 10 Gyr) showed 66% of the population became EMRIs, wildly above N26's own
implied EMRI fraction ($\sim$4-5% over 10 Gyr, from their $\sim$4-4.8 Gyr$^{-1}$ rate per
1000-BH galaxy). Tracing this down: `remaining_merger_time_circular(20\,M_\odot,
4\times10^6\,M_\odot, 10^{-4}\,{\rm pc}) \approx 0.15$ Gyr — i.e. a BH born near the old
$a_{\min}$ undergoes prompt EMRI from *quiescent* GW inspiral alone (Eq. 4.4/Peters decay),
with no dynamical process needed at all. At $a_{\min}=10^{-3}$ pc the same quantity is
$\approx1450$ Gyr, comfortably ($>100\times$) longer than the 10 Gyr simulation. This is a
much better-justified default than the original guess, but it is still our choice, not N26's
— the paper never states where its BHs are initially sampled from, so any inner bound we pick
shapes the EMRI rate we get. Revisit once real Phase 3 validation data (Table 1's EMRI-rate
figures) is available to check against.

**How to apply**: `imbh_nuclei.population` (Phase 2) draws $e\sim{\rm thermal}$,
$\log_{10}a\sim{\rm Uniform}(\log_{10}a_{\min}, \log_{10}0.1)$, with `a_min` as an explicit,
documented config default ($10^{-3}$ pc).

## Coulomb logarithm not specified {#coulomb-logarithm}

**Resolved (revised during the Phase 3 EMRI-rate fix)**. N26 Eq. 22 includes $\ln\Lambda$,
"the Coulomb logarithm," with no numeric prescription — just a generic citation to Binney &
Tremaine 2008 (as does Rose et al. 2022's Eq. 10, the source of this exact formula, which
also gives no number). Per the user's request, this was investigated independently of the
$\langle M_{\rm avg}\rangle$ question and independently of EMRI-rate matching, starting from
the papers N26/Rose 2022 actually cite plus the specific literature on relaxation around a
dominant central mass:

- **Ben Bar-Or, G. Kupi, & T. Alexander 2013** (ApJ, 764, 52, "Stellar Energy Relaxation
  around a Massive Black Hole" — fetched and read directly, arXiv:1209.4594): for a cusp
  dominated by a central point mass, "$\log\Lambda \sim \log Q$ is typically a large, O(10)
  factor," where $Q = M_\bullet/m_\star$ is the SMBH-to-star mass ratio — explicitly
  distinguished from the general globular-cluster convention.
- **E. Vasiliev 2017** (ApJ, 848, 10, "A New Fokker–Planck Approach for Relaxation-driven
  Evolution of Galactic Nuclei" — fetched and read directly, arXiv:1709.04467): a modern,
  rigorous multi-component (star+BH) Fokker-Planck code explicitly built for exactly this
  problem. States $\ln\Lambda \simeq \ln(M_\bullet/m_\star)$, and for a Milky-Way-like
  nucleus model — **the same $M_\bullet = 4\times10^6\,M_\odot$ as N26's fiducial galaxy** —
  uses $\ln\Lambda = 15$.

This is the **standard, well-established prescription specifically for the $Q=M_\bullet/m\gg1$
regime** (a single, heavy central mass dominating the relaxation of a much lighter
population) — a physically different regime from the $\ln(0.4N)$ convention used for
self-gravitating systems *without* a dominant central mass (globular clusters), which is
therefore the less appropriate of the two candidates previously listed here.

**Resolution adopted**: $\ln\Lambda = \ln(M_\bullet/M_\star) = \ln(4\times10^6/1) \approx
15.2018$, paired with the star-only $\langle M_{\rm avg}\rangle=M_\star=1\,M_\odot$ resolution
above (the two are linked: $Q=M_\bullet/m$ presumes a single relaxing-population mass $m$, so
this specific numeric value is only self-consistent with the star-only reading of $\langle
M_{\rm avg}\rangle$ — if that reading is ever revisited, this value should be too).

**Why**: this is a decisive, converging result from two independent, directly-relevant
sources (one a dedicated N-body calibration study, one a modern multi-component code
explicitly modeling a Milky-Way-mass nucleus), not a single citation or guess. It fully
resolves what was previously an open, undecided placeholder.

**How to apply**: `ClusterConfig.coulomb_log` defaults to `15.201804919084164` (was `10.0`).
If `m_smbh` is changed from its default (e.g. Phase 5's SMBH-mass scan), this value should be
recomputed as $\ln(m_{\rm smbh}/1.0)$, not reused verbatim — flagged in the config field's own
docstring.

**No genuine literature inconsistency found** worth a standalone discussion: unlike the
$\langle M_{\rm avg}\rangle$ question, the two sources checked here agree with each other
(and give a number matching almost exactly, 15 vs 15.2, for the same physical system), and
neither contradicts N26/Rose et al. 2022's generic Binney & Tremaine 2008 citation — they are
simply more specific than N26 bothered to be. Bahcall & Wolf 1976 and Aharon & Perets 2016
(N26's own cited source for the BH density profile) were not directly consulted for their own
$\ln\Lambda$ conventions (both are pre-2015/hard-to-access primary sources not in
`references/`), so it remains possible a closer read of those two specifically would surface
a differing convention — flagged as a loose end, not a finding, given the strong agreement
already found elsewhere.

## Eccentricity dependence of BH-star collision timescale is focusing-dominated

Rose et al. 2020 (source of $f_1,f_2$) show that for *star-star* collisions, eccentricity
*decreases* the collision timescale (Figure 3 there), because in that regime $f_1$ (geometric
term) and $f_2$ (focusing term) are comparable in size and $f_1$ grows with $e$. For the
*BH-star* collisions actually being modeled here, the gravitational-focusing term
($f_2 \cdot r_c \cdot 2G(m_{\rm BH}+M_\odot)/\sigma^2$) exceeds the geometric term ($f_1\cdot
r_c^2$) by roughly 3 orders of magnitude for stellar-mass BHs (verified numerically:
$2Gm_{\rm BH}/\sigma^2 \gg r_c$ since $r_c\approx R_\odot$ is tiny). Since $f_2(e)$ is a weak,
slightly *decreasing* function of $e$, our BH-star collision timescale has a weak *increase*
with eccentricity rather than the decrease seen in Rose et al.'s star-star case. Both are
consistent with Rose et al.'s own characterization of the effect as "order unity" and
"no more than a factor of two" — this is not a contradiction of their result, just a
different regime (focusing- vs geometric-dominated) of the same general formula. Confirmed
numerically in `tests/test_collisions.py::TestCollisionTimescale`.

## Resolved gap: Eq. 10's "L" (orbital angular momentum in the final-spin formula)

N26 Eq. 10 uses a quantity "$L$" without a formula (see `docs/equations.md` for full
detail). Traced to Barausse & Rezzolla 2009 (ApJL, 704, L40): their Eq. 5 aligned-spin
reduction has the identical structure to N26 Eq. 10, letting us solve for their
script-$\ell$ (= N26's "$L$") using their Eq. 1 fitted aligned-spin formula. Implemented as
`gw_capture.orbital_ell`, verified against Barausse & Rezzolla's own quoted NR calibration
benchmark ($a_{\rm fin}=0.68646$ for equal-mass, non-spinning) to 3 decimal places — an
independent check, not just internal self-consistency. This is now considered resolved with
high confidence, unlike most other items in this log.

## Concrete config defaults chosen for previously-flagged-as-required parameters

Two items flagged above as "no default, must be supplied explicitly" now have concrete
defaults in `config.ClusterConfig`/`IntegrationConfig`, needed to make the config system
usable end-to-end for Phase 2. Flagging the specific values chosen, since they were
previously left as pure "caller must decide":

- `coulomb_log = 10.0` (see `#coulomb-logarithm` above). This is a round, order-of-magnitude
  placeholder, not derived from either candidate formula mentioned there
  ($\ln(M_\bullet/\langle m\rangle) \sim 12$-$13$, or $\ln(0.4N)$). Should be revisited once
  Phase 3 validation shows whether relaxation/EMRI-timing results are sensitive to it.
- `timestep_safety_factor = 0.1` — N26 says the timestep is adjusted "to always be less than
  the collision timescale" but doesn't give a specific safety margin below that; we cap
  $\Delta t \le 0.1 \times \min(t_{\rm coll}, t_{\rm GW})$ across all active BHs each step,
  keeping per-step event probabilities $\lesssim 10\%$ (a standard choice for this kind of
  Poisson-probability Monte Carlo scheme, not paper-specified).

## Phase 2/3 EMRI fraction is much higher than N26's implied rate, and a new runaway-growth issue {#phase2-emri-rate-high}

**Status: substantially improved, not fully resolved. Two independent fixes applied, one new
discrepancy discovered and investigated, residual gap documented honestly below.**

### Original symptom (pre-fix)

A full $N=1000$, 10 Gyr run using the H18 initial distribution gave: 757 EMRIs (75.7%), only
3 GW-capture mergers, max final mass 100.3 $M_\odot$. Table 1's H18 row reports 371 mergers,
max mass 407.3 $M_\odot$, implied EMRI count of order tens (few % of 1000) over 10 Gyr. The
merger physics itself was independently verified against a numerical-relativity benchmark
(Barausse & Rezzolla 2009's calibration point, matched to 3 decimals) — the low merger count
looked like a consequence of the EMRI channel depleting the population before BHs could grow,
not an independent bug in the merger equations.

### Fix 1: genuine substepping of the relaxation walk (small effect, ~11pp)

The per-timestep relaxation kick was aggregated as *one* Gaussian evaluated at the timestep's
*starting* $a$, even though a timestep can span $10^5$-$10^6$ real orbits at small $a$ — the
local dynamics (period, $t_{\rm relax}$, $v_{\rm circ}$) implicitly held fixed for the whole
span. `_apply_relaxation_walk` (`simulation.py`) now breaks each timestep into
`IntegrationConfig.relaxation_substeps` (default 20) sub-steps, re-evaluating local dynamics
at the BH's current $a$ between them — see `docs/equations.md#orbital-random-walk-from-relaxation`
for the tradeoff writeup (literal per-orbit substepping is the Rose et al. 2022 prescription
but impractical at N=1000 scale). **Effect measured**: 75.7% → 64.5% EMRI at N=1000. A
follow-up scan of `relaxation_substeps` from 1 to 2000 (2000x range, N=150) moved the result
only between 55-74% with no monotonic trend — i.e. this fix is real and worth keeping (it's
more physically correct regardless), but substep coarseness was **not** the dominant cause of
the original 75.7%.

### Fix 2: <M_avg>/rho and Coulomb log re-derivation from primary sources (large effect)

Traced independently of EMRI-rate matching, per the user's explicit request (see
`#average-object-mass` and `#coulomb-logarithm` above for the full evidence trail):
$\langle M_{\rm avg}\rangle$/$\rho$ switched from a BH-inclusive weighted average to
star-only ($1\,M_\odot$, $\rho_\star$), following Rose et al. 2022 Eq. 10's explicit
"single-mass system" statement; $\ln\Lambda$ recomputed as $\ln(M_\bullet/M_\star)\approx
15.2$ (was a 10.0 placeholder), following Bar-Or, Kupi & Alexander 2013 and Vasiliev 2017.
**Effect measured**: 64.5% → 34-37% EMRI at N=1000 (consistent across 3 seeds), with the
merger channel now genuinely active (400-580 mergers per run, vs. near-zero before).

**This resolution is contested, not settled** — see `#average-object-mass` for the full
back-and-forth: N26's own Eq. 22 phrasing (dropping Rose et al. 2022's "single-mass system"
qualifier) plus Eq. 23's explicit star-only override (redundant if Eq. 22's default were
already star-only) is a real, textually-grounded argument for the *opposite* (BH-inclusive)
reading. Both readings were empirically tested at N=1000/10Gyr/3 seeds; BH-inclusive
reproduces the *original* defect almost exactly (68.8% EMRI, **zero** mergers, max generation
1). Star-only was kept because it's the only one of the two that leaves the GW-capture
channel functioning — but this is a **pragmatic choice under a live, undecided ambiguity**,
not a confirmed resolution.

### New discrepancy found: systematic runaway growth (open, not resolved)

With both fixes applied, EMRI rate is much improved (34-37%, vs. the paper's implied few
percent — still elevated but no longer 75%) but a **new, systematic** problem appeared:
every one of 3 independent seeds (N=1000, H18, 10 Gyr) produces at least one BH that
snowballs to **6000-9400 $M_\odot$** over **55-86 merger generations**, vs. Table 1's 407.3
$M_\odot$ max and stated 12G maximum generation for H18. This is not a rare one-off outlier
(confirmed systematic across seeds 0, 1, 2) but the bulk of the population is much closer to
Table 1's scale (99th-percentile mass 295-543 $M_\odot$ across the three seeds, roughly the
right order for Table 1's "4 BHs $>10\times M_i$" statistic) — so this looks like a
heavy-tailed, rare-catastrophic-trajectory problem specifically, not a uniform miscalibration
of the whole population.

**Mechanism, traced directly** (seed 0's runaway BH: generation 63, mass 9402 $M_\odot$,
sitting at $a=0.0012$ pc, 5221 individual stellar collisions): both growth channels have
genuine, paper-documented positive feedback once a BH is massive and sits in a dense inner
region — Eq. 18's gravitational-focusing collision cross-section scales with BH mass, and
Eq. 4's GW-capture cross-section scales with $M_{\rm tot}^2$. Recoil kicks for these
late-stage mergers are tiny (0.05-6.7 km/s) because the mass ratio is extreme
($m_2\approx$ mean initial mass $\ll m_1$), so the runaway BH's orbit barely moves once it
starts growing — it neither escapes to a safer radius nor decays into the SMBH fast enough to
terminate the runaway within 10 Gyr. Rose et al. 2022 (the base model) explicitly describes
relaxation's role as *not just* causing EMRIs but "impeding the growth of BHs... by allowing
them to diffuse out of the inner region where collisions are efficient," and their own
abstract states the (unmoderated) stellar-collision channel alone can produce IMBHs "as
massive as $10^4\,M_\odot$" — so a $\sim10^4\,M_\odot$ outlier is not unprecedented in the
underlying literature, but Table 1's actual reported ceiling ($\sim400\,M_\odot$) implies
N26's calibration suppresses it far more effectively than ours currently does.

**Time-boxed follow-up investigation (requested by user, completed, did not resolve the
tension)**: (1) tested reverting to BH-inclusive $\langle M_{\rm avg}\rangle$/$\rho$ for Eq.
22's general relaxation usage (keeping Eq. 23's segregation timescale star-only, unchanged) —
this does fix the runaway (max mass back to a sane 100.3 $M_\odot$, since strong relaxation
evicts growing BHs from the efficient zone before they run away) but **recreates the original
defect** (68.8% EMRI, zero mergers) almost exactly, i.e. trades one failure mode for the
other rather than resolving the tension; (2) checked Rose et al. 2022 for a stellar-depletion
mechanism that might explain N26's growth ceiling — found only an explicit acknowledgment that
depletion is *not* included in their own model either, so its absence here doesn't explain the
discrepancy; (3) checked N26's text for a quantitative ejection-rate target to check our own
recoil-kick ejection counts against — none given, so this channel could not be verified or
ruled out.

### Follow-up: GW-capture cross-section mass-dependence, investigated (2026-07-27)

The lead flagged above — that the GW-capture channel's own mass-dependence might be a
separate contributor, not just relaxation — was investigated directly.

**Eq. 4-6 (b_max, b_min, A_cap) re-verified against a direct high-resolution page-image
render of N26 page 4** (not text extraction, which garbles the math): our implementation
matches term-for-term, including the exponents ($\eta^{1/7}$, $(v_{\rm rel}/c)^{-9/7}$ for
$b_{\rm max}$; $(v_{\rm rel}/c)^{-1}$ for $b_{\rm min}$) and the $340\pi/3$ prefactor. **No
transcription error found** — the formulas are correctly implemented.

Given that, the mass-dependence *is* the source of the runaway, but as correctly-implemented
physics, not a bug: $b_{\rm max}\propto M_{\rm tot}\,\eta^{1/7}$, and for $m_1\gg m_2$ (a
tracked BH that has already grown large capturing typical-mass partners), this reduces to
$b_{\rm max}\propto m_1^{6/7}$, giving a capture cross-section $A_{\rm cap}\propto m_1^{12/7}$
and thus $t_{\rm GW}\propto m_1^{-12/7}$ — a **superlinear, positive-feedback runaway** as the
tracked BH's own mass grows (confirmed by the timing data: merger generations accelerate
visibly toward the end of a runaway BH's growth history, e.g. gen 54→63 in ~1.2 Gyr for one
traced lineage, vs. gen 1→22 over the first ~5 Gyr). The stellar-collision channel (Eq. 18)
has an analogous, if gentler, mass-dependence via gravitational focusing. This is the same
double positive-feedback mechanism already described above, now confirmed to originate from
correctly-implemented, verified equations rather than an implementation error.

**The extent of the tail, precisely quantified** (all 6 H18/H18+M seeds, consistent to
within ~30%): 44-58 BHs/1000 exceed 200 $M_\odot$, 13-19 exceed 500 $M_\odot$, 6-10 exceed
1000 $M_\odot$, 3-6 exceed 2000 $M_\odot$, and only 0-3 exceed 5000 $M_\odot$ (with just 0-1
per run reaching the extreme 10,000+ $M_\odot$ tier that dominates the "max mass" statistic).
This revises the earlier "1-3 rare outliers" framing: it is a genuine, robust, moderately
broad heavy tail (tens of BHs undergo substantial hierarchical growth into the hundreds-to-
low-thousands range, consistent across every seed), with only the single most extreme
BH per run responsible for the eye-catching 10,000-90,000 $M_\odot$ figures. Of the BHs
exceeding 500 $M_\odot$ in the traced example, roughly 40% had already been caught by the
EMRI channel by 10 Gyr (8 of 19) — confirming growth and EMRI-driven removal are genuinely
*racing* each other, with growth winning outright for a small, non-negligible fraction of
the population.

**Conclusion, logged honestly**: no additional implementation bug was found in the GW-capture
channel — Eq. 4-7 are correctly implemented and independently verified. The residual
discrepancy is a genuine, currently unresolved tension between two textually-defensible
readings of Eq. 22's $\langle M_{\rm avg}\rangle$ (star-only vs. BH-inclusive), which
controls how effectively relaxation can evict a BH from the runaway-conducive regime (small
$a$, large mass) before both the correctly-implemented, superlinear collision and
GW-capture feedback channels run away with it. This is **not** a coding bug left unfixed — it
is a scientifically genuine open question given what the primary sources actually say, logged
here per this project's standing convention of surfacing ambiguities rather than silently
picking a resolution and moving on. **Recommendation for future work**: if the Phase 4/5
"critical mass" analysis proves sensitive to the extreme upper tail specifically (rather than
the bulk distribution, which is much closer to Table 1's scale), this should be revisited —
most likely by finding a middle-ground resolution of the $\langle M_{\rm avg}\rangle$
question (partial, not all-or-nothing, BH contribution) rather than continuing to treat it as
a binary choice between the two extremes already tested.

### Follow-up: searching for a middle ground, before Phase 4 (2026-07-27) — none found

Before starting Phase 4, two concrete candidate "middle grounds" were tested, specifically
to avoid treating this as a binary choice. Neither worked, and the reasons why are informative
in their own right.

**Candidate 1 — a physically rigorous multi-species weighting, rather than either all-or-
-nothing extreme.** Eq. 22's underlying formula (Binney & Tremaine 2008, Eq. 7.106) is
derived for a *single-mass* population. Its standard textbook generalization to a system with
multiple mass species (Chandrasekhar/Spitzer-style two-body relaxation theory) does not
replace $\rho\langle M_{\rm avg}\rangle$ with our number-weighted mean; it replaces it with
$\sum_j n_j m_j^2$ (the second mass-moment), because heavier field objects contribute to a
test particle's velocity diffusion in proportion to $m^2$, not $m$. This is the textbook-
correct multi-species answer, so it looked like the most principled possible "third reading."
**It isn't a middle ground — it's more extreme than BH-inclusive.** Computed numerically at
$a=10^{-3}$ pc for H18: star-only gives $\rho\langle M_{\rm avg}\rangle \sim 1.3\times10^9$;
our already-tested (and already-too-strong) BH-inclusive number-weighted reading gives
$\sim2.5\times10^{12}$; the rigorous $m^2$-moment gives $\sim3.4\times10^{12}$ — *larger*
still. There is no principled multi-species weighting formula sitting between the two extremes
already tested; the more carefully one applies standard relaxation theory to a population with
a much heavier second species, the *more* that species dominates, not less.

**Candidate 2 — finer substepping specifically under the BH-inclusive reading**, to check
whether the "0 mergers" outcome was itself a numerical-fidelity artifact (as substep coarseness
partially was for the original EMRI-rate problem) rather than a property of the physics.
Scanned `relaxation_substeps` at 20, 200, and 2000 under BH-inclusive with all of today's other
fixes in place (N=150, H18, 10 Gyr, corrected `mean_bh_mass`): EMRI fraction moved only
60.0% → 54.0% → 51.3%, and **mergers stayed at exactly zero at every substep count**, even at
2000 (100x finer than the adopted default). This rules out numerical fidelity as the source of
the BH-inclusive reading's defect — it is a property of the physics at that magnitude, not an
artifact of how finely we integrate it.

**Conclusion**: the tension is a genuine structural fork, not a dial. Both tested resolutions
sit at defensible extremes with no principled interpolation between them found on either the
weighting-formula axis or the numerical-fidelity axis. Star-only remains the adopted choice
(documented above). **Recommendation, revised**: Phase 4 should not treat this as resolved by
further searching for a compromise value. Either (a) explicitly scope Phase 4's results as
contingent on the star-only reading and flag it prominently wherever the extreme upper tail of
the mass distribution matters to a conclusion, or (b) run the critical-initial-mass-threshold
scan under both readings and report whether the *location* of any threshold found is robust to
this choice — which is likely to be more informative than the exact tail statistics anyway,
since the bulk-population behavior (which is what a threshold-detection question mostly
depends on) is far less sensitive to this choice than the extreme maximum is.

**Adopted for Phase 4**: option (b). `IntegrationConfig.relaxation_mass_weighting` is now a
first-class config field (see `#average-object-mass` above); Phase 4's threshold scan runs
under both settings and reports whether the threshold location is robust to this choice.

## Phase 4 — mass-distribution scan family and IMBH definition {#phase4-mass-family-scan}

N26 explicitly leaves open (Section 5.4, confirmed by direct PDF read): "whether there is a
mass distribution between our lower and upper limits that consistently produces IMBHs" — i.e.
a continuous family connecting the K20-like (never produces IMBHs) and H18 (sometimes does)
regimes, which the paper itself never specifies (it only gives the four discrete K20/K20+M/
H18/H18+M points). Designing one is therefore a genuine judgment call, flagged to the user
before committing to it (2026-07-27) rather than picked silently. Options considered and the
resolution chosen:

- **Adopted**: log-uniform mass distribution on $[6, m_{\rm max}]\,M_\odot$ — H18's own stated
  functional form ("uniform in logspace... $dN/dm\sim m^{-1}$"), generalized by scanning only
  the upper bound $m_{\rm max}$ from 16 (K20's rough upper edge) to 100 (exact H18). A single
  scannable parameter that exactly reproduces H18 at the top of the range. **Caveat, explicit**:
  this does *not* reproduce K20's true reconstructed shape (`K20_BIN_EDGES`/`K20_BIN_WEIGHTS`,
  concentrated/non-log-uniform in 7-16 $M_\odot$ — see `#k20-reconstruction`) at the bottom of
  the range; it is an approximate low-mass anchor, not a K20 substitute. The exact K20/K20+M/
  H18/H18+M points keep their Phase 3 results (`results/phase3_validation_2026-07-26.md`) as
  independent validation anchors alongside the scan, not superseded by it.
- **Considered, not adopted**: a mixture blend (draw each BH from the *true* K20 sampler with
  probability $p$, true H18 sampler with probability $1-p$). Would exactly reproduce both real
  endpoints, but produces a bimodal mass function at intermediate $p$ and treats the scan
  parameter as a population-mixture fraction rather than a mass-scale parameter — judged a less
  natural stand-in for "a cluster's initial mass distribution" than a single smooth family.
- **Mean BH mass**: unlike K20 (no closed form, `PopulationConfig.mean_bh_mass` needs a
  large-$N$ Monte Carlo estimate per `#mean-bh-mass-placeholder`), the log-uniform family has
  an exact closed-form mean, $(m_{\rm max}-m_{\rm min})/\ln(m_{\rm max}/m_{\rm min})$
  (`initial_conditions.log_uniform_mean`) — confirmed to match H18's independently
  Monte-Carlo-measured mean (33.396) at $m_{\rm max}=100$, avoiding that whole class of bug.
- **Primordial-binary-merger fraction**: deferred to a follow-up, zoomed-in second pass near
  wherever the first pass finds a threshold, rather than scanned as a second axis in the first
  pass — confirmed with the user given H18 alone (0% primordial mergers) already produces
  IMBHs (Table 1: 7.8%), so this axis is not required to see IMBH formation the way the
  mass-scale axis is, and adding it as a full second axis would double the first pass's compute
  cost for a question that's cheaper to answer locally once the threshold's rough location is
  known.
- **IMBH definition**: N26 Section 5.4's own definition, confirmed directly from the PDF text
  ("defined as a BH with mass > 100 $M_\odot$") — exactly Table 1's "% BHs > 100 $M_\odot$"
  column, so scan results stay directly comparable to the validated Phase 3 numbers. Primary
  outcome: % of the $N=1000$ population exceeding 100 $M_\odot$. Secondary: a strict binary "did
  any BH cross 100 $M_\odot$ at all" indicator per run, since Phase 3 found K20 gives exactly 0%
  across all 6 seeds tested (3 K20 + 3 K20+M) — the binary indicator may show a cleaner
  threshold than the continuous fraction, which can be dominated by seed-to-seed noise at N=1000.
- **Grid/seeds/compute budget**: 9 $m_{\rm max}$ points (log-spaced, 16-100), 3 seeds (0,1,2,
  matching Phase 3's convention), both Eq. 22 readings = 54 runs total. Estimated 1.5-2.5 hours
  wall-clock at 8 parallel workers, based on Phase 3's measured per-run timings (K20-like ~450s,
  H18-like 600-1740s under star-only; bh_inclusive expected faster, since it does not exhibit
  the runaway-growth tail — see `#phase2-emri-rate-high`).

**How to apply**: `scripts/phase4_mass_threshold_scan.py` implements this design;
`initial_conditions.sample_log_uniform_mass`/`log_uniform_mean`/`get_log_uniform_samplers`
implement the mass family. Results and the resulting threshold analysis (or lack thereof) to
be logged in `results/` once the scan completes, per the project's standing convention.

**Results (2026-07-27, `results/phase4_mass_threshold_scan_2026-07-27.md`)**: the scan ran —
54/54 runs completed, 4.3 CPU-hours, ~0.54 hr wall-clock (faster than estimated; `bh_inclusive`
runs were cheap, ~25-33s each, since they never enter the runaway-growth regime). Headline
finding: **a critical-mass threshold exists under `star_only`** (turns on around $m_{\rm
max}\approx25$-$32\,M_\odot$, well below H18's own 100 $M_\odot$, then grows smoothly to H18's
12.7%) **but is essentially absent under `bh_inclusive`** (flat 0.0% for $m_{\rm max}\le79.5$,
only a marginal 0.1-0.3% even at $m_{\rm max}=100$ exactly). This directly falsifies this
entry's own closing hypothesis, immediately below — see the correction there.

**Validation status (per `paper/methodology.md`)**: the threshold's *existence* (a robust
sensitivity to the Eq. 22 reading) graduated to a result immediately — see the worked
scorecard at the end of `methodology.md`. The specific *location* (25-32 $M_\odot$) did not:
it rested on a single 1-of-3 seed flip at $m_{\rm max}=25.3$ (Gate 3 open). A dedicated
follow-up pass (`scripts/phase4b_threshold_refinement.py`, 31 new `star_only` runs, 5 grid
points in the band at 8 seeds each) was run specifically to close that gate before the
location claim is treated as final.

**Outcome, 2026-07-28: Gate 3 closed, and the original location claim was itself corrected,
not just tightened.** With 8 seeds instead of 3, $m_{\rm max}=31.8$ — which pass 1's 3/3
sample made look fully saturated — turned out to produce zero IMBHs in 2 of 8 seeds (75%,
95% CI 41-93%). The "any IMBH forms" probability rises smoothly from 0% ($m_{\rm max}=20.1$)
to 75% (28.4-31.8) without saturating anywhere in the band, with heavily-overlapping Wilson
CIs between adjacent points — i.e. the honest answer is **a gradual crossover region (roughly
20-32 $M_\odot$), not a sharp threshold**, which directly answers the sharper of N26's own two
framings of the open question (is the transition sharp or gradual — Section 5.4, also
`PROJECT_OVERVIEW.md`'s framing). Full data and Wilson CIs:
`results/phase4_mass_threshold_scan_2026-07-27.md`'s "Pass 2" section. This is exactly the
outcome Gate 3 exists to catch — a thin sample (n=3) manufactured an apparently-sharp
transition that more seeds (n=8) showed was actually gradual and unsaturated even at its
upper edge.

**Correction to the "likely more informative... bulk-population behavior... far less sensitive"
claim two paragraphs above**: that claim does not hold for the IMBH-formation question. "% BHs
> 100 $M_\odot$" — a bulk-population statistic, not a single extreme order statistic — swings
from a clear, gradually-developing 0%→12.7% signal under `star_only` to flat zero under
`bh_inclusive` across the *entire* scanned mass range, not just at the specific H18 point
checked during the original investigation. The reason is structural: forming an IMBH by either
channel requires a BH to survive long enough in the dense inner region to grow, and survival
time against EMRI ejection is exactly what this ambiguity controls — so IMBH-formation
questions are about as sensitive to this choice as they could be, not a case where the
ambiguity washes out. Any Phase 4/5 claim about where a critical-mass threshold sits must state
which Eq. 22 reading it assumes.

### Pass 3 (design): does the primordial-binary-fraction axis shift the crossover? (open, in progress)

Per this entry's own original scoping (the "Primordial-binary-merger fraction" bullet above),
the 0%/15% axis was deliberately deferred to "a follow-up pass near the threshold region,"
not scanned from the start, once pass 1 confirmed H18 alone (0% primordial) already produces
IMBHs. Pass 2 has now located that region (~20-32 $M_\odot$), so this is that follow-up,
requested by the user 2026-07-28.

**Design**: `scripts/phase4c_primordial_binary_check.py`. `star_only` only (`bh_inclusive`'s
absence-of-threshold finding is already saturated evidence — see the correction paragraph
above — and this pass asks whether a *different* axis moves the `star_only` crossover, so
testing it under `bh_inclusive` is out of scope here too). Same 5 $m_{\rm max}$ grid points
as pass 2 (20.118935, 22.560436, 25.298221, 28.368246, 31.810829), so the new
`primordial_binary_fraction=0.15` runs compare directly against pass 2's already-existing
`=0.0` runs at identical $m_{\rm max}$ without a new baseline. 8 seeds per point (0-7),
matching pass 2's convention from the start — per `paper/methodology.md` Gate 3 this is a
location-adjacent comparison, not a bare existence claim, so the same $\ge$8-seed bar applies
immediately rather than starting thin and refining. 40 new runs total.

**Extension required**: `initial_conditions.get_log_uniform_samplers` gained a
`primordial_binary_fraction` parameter (default 0.0, backward-compatible with pass 1/2's
calls), applying the same `apply_primordial_mergers` machinery already used for
`sample_k20_plus_m`/`sample_h18_plus_m` to the log-uniform family. `mean_bh_mass` for the
+M-modified distribution has no closed form (mergers are a nonlinear transform of the base
draw, same reason K20/K20+M/H18/H18+M needed Monte Carlo means in Phase 3 — see
`#mean-bh-mass-placeholder`) — estimated here at $N=2\times10^6$ per grid point, computed at
run time rather than hardcoded so it can't go stale.

**Results (2026-07-28)**: 40/40 runs completed. No detectable shift in the crossover from
this axis: point-by-point, every `primordial_binary_fraction=0.15` value falls inside (or
barely outside) the `=0.0` point's own 95% Wilson interval, with no consistent direction
(one grid point even goes down); pooled across all 5 points, 19/40 (0%) vs 20/40 (15%) any-IMBH
runs, Fisher's exact $p=1.0$. The one clean effect is a consistent **+2.3%** `mean_bh_mass`
bump at every grid point, matching Phase 3's real K20/K20+M (+2.2%) and H18/H18+M (+2.4%)
shifts almost exactly — a good Gate 6 cross-check that the new sampler extension behaves like
the already-validated K20+M/H18+M path. Graduated as a result per `paper/methodology.md`'s
gates (mechanism: primordial mergers touch only 2.5% of the population and raise the mean by
~2%, a far smaller perturbation to the growth-rate-controlling mass scale than one $m_{\rm
max}$ grid step, ~12% multiplicative — so a much weaker effect from this axis is physically
expected, not just a null result taken at face value). Bounded, honestly: this rules out an
effect large enough to clear the 8-seed Wilson-CI floor, not an arbitrarily small one — see
`results/phase4_mass_threshold_scan_2026-07-27.md`'s "Pass 3" section and its Caveats entry
for the precise limit and the ~4x-seeds-per-halved-CI cost of tightening it further. Full
data: `results/phase4c_raw/summary.csv`.

## Phase 5 — SMBH-mass scan family {#phase5-smbh-mass-scan}

N26's second explicit open question (Section 5.4, alongside the threshold-shape question
Phase 4 answered): does the result generalize to galaxies with SMBHs of other masses, or is
it a Milky Way-specific coincidence? Answering this requires a genuine judgment call N26
never makes: their cluster's structural profile — $\rho_0=1.35\times10^6\,M_\odot/{\rm
pc}^3$, $r_0=0.25$ pc (Eq. 3), $n_0=10^4\,{\rm pc}^{-3}$, $R_h=1$ pc (Eq. 2),
$\alpha_\star=1.25$, $\alpha_{\rm BH}=1.83$ — is given as fixed numbers specific to the
Milky Way's $M_\bullet=4\times10^6\,M_\odot$ nucleus, with no stated prescription for how
any of them would scale for a different-mass SMBH (`docs/equations.md`'s Appendix note on
this flags it directly). Design decided with the user, 2026-07-28:

- **Adopted**: hold the structural profile fixed at N26's own values, vary only $m_{\rm
  smbh}$. Isolates the pure *dynamical* effect of SMBH mass — velocity dispersion
  ($\sigma\propto\sqrt{M_\bullet}$), the relaxation timescale, GW-capture rate, and the EMRI
  stopping condition all depend on $m_{\rm smbh}$ directly, independent of any assumption
  about how a real galaxy's density profile differs — from the separate, unresolved question
  of realistic profile scaling. **Explicit limitation**: this is our own extension (Gate 1c,
  not from N26), and is *not* a claim that a real galaxy with a different-mass SMBH would
  actually have this exact cluster structure — a genuinely different-mass galaxy's stellar
  and BH densities plausibly scale with $M_\bullet$ too (e.g. via an $M_\bullet$-$\sigma$ or
  $M_\bullet$-$N_\star$ relation), which this scan does not attempt.
- **Considered, not adopted**: sourcing a literature $M_\bullet$-$\sigma$-type relation to
  self-consistently scale $\rho_0$/$r_0$/$R_h$ with $M_\bullet$ — judged a materially bigger
  undertaking (a new reference, a fresh ambiguity-adjudication exercise like Eq. 22's) for a
  first pass at this question; left as a follow-up if the isolated-$M_\bullet$ result
  motivates it.
- **Grid**: 7 $m_{\rm smbh}$ points, log-spaced across 3 decades centered on N26's own
  fiducial value, which is included exactly as an exact-reproduction anchor against Phase
  3/4: $1.264911\times10^5$, $4\times10^5$, $1.264911\times10^6$, $4\times10^6$ (= N26),
  $1.264911\times10^7$, $4\times10^7$, $1.264911\times10^8\,M_\odot$.
- **Mass distribution**: held fixed at H18 (0% primordial) — N26's own literal IC (Gate 1a),
  and the one of the four that actually produces IMBHs at the Milky Way mass, so it's the
  right choice to test whether *that* result survives at other $m_{\rm smbh}$. Not the
  Phase 4 log-uniform family, to keep this scan's IC unambiguously "N26's own," not "ours."
- **Both Eq. 22 readings**, per this project's standing convention of never computing a
  headline number under only one reading of that still-open ambiguity.
- **Seeds**: 8 per point from the start (0-7), not a thin first pass — per
  `paper/methodology.md` Gate 3, this scan is directly comparable to the already-validated
  Phase 3 $m_{\rm smbh}=4\times10^6$ anchor, so the same $\ge$8-seed bar applies immediately
  rather than needing a separate refinement pass later.
- **Two quantities recomputed per grid point, not held fixed** (caught before running, not
  after): `coulomb_log` $=\ln(m_{\rm smbh}/1\,M_\odot)$ (already flagged in
  `ClusterConfig.coulomb_log`'s own docstring, `#coulomb-logarithm`); and `a_min_pc` — the
  inner semimajor-axis sampling bound. `population.A_MIN_PC_DEFAULT` (1e-3 pc) was
  reverse-engineered so a BH born there takes $\gg10$ Gyr to inspiral via quiescent GW decay
  *specifically at $m_{\rm smbh}=4\times10^6$*; since that inspiral time scales roughly as
  $1/m_{\rm smbh}^2$ (from `inspiral.remaining_merger_time_circular`'s mass dependence),
  holding it fixed across this grid would silently reintroduce the exact prompt-EMRI
  numerical artifact `A_MIN_PC_DEFAULT` was originally introduced to fix (checked directly:
  at $m_{\rm smbh}=4\times10^7$, the *original* 1e-3 pc value gives only ~18 Gyr of margin,
  no longer safely $\gg10$ Gyr). Generalized via the new `population.a_min_safety_bound(m_smbh)`
  helper (solves for $a_{\rm min}$ analytically from the closed-form $\tau\propto a^4$
  scaling).
  $a_{\rm max}$ (0.1 pc, N26's stated focus region) is held fixed, consistent with the
  "hold structure fixed" choice above — it's part of the region being studied, not a
  numerical safety margin like $a_{\rm min}$.

**A second, more serious problem found only by actually running the code, not by reasoning
about it in advance**: letting `a_min_safety_bound` *shrink* `a_min_pc` below
`A_MIN_PC_DEFAULT` at low $m_{\rm smbh}$ (the first version of this design) is wrong for a
completely different reason than the one it was designed to fix. `a_min_safety_bound(1.2649
\times10^5)$ gives $\approx1.68\times10^{-4}$ pc — and at that radius, the *held-fixed*
stellar density profile ($\rho\propto r^{-\alpha_\star}$, uncapped at small $r$) evaluates to
$\approx1.25\times10^{10}\,M_\odot/{\rm pc}^3$: about 9236x its own $r_0=0.25$ pc calibration
value, and about 9x even the already-extreme density at the MW-anchor's $a_{\rm min}=10^{-3}$
pc. This collapses the stellar-collision timescale and drives the adaptive-timestep loop
toward its 2,000,000-step ceiling — caught directly as a smoke-test hang (>40 minutes with no
convergence at $t_{\rm max}=10$ Gyr, and even $t_{\rm max}=0.1$ Gyr didn't converge in 5
minutes) before any of the real 112-run scan was launched, not discovered after the fact.

**Fix, verified**: $a_{\rm min}$ should only ever *grow* beyond `A_MIN_PC_DEFAULT` (needed at
high $m_{\rm smbh}$, where quiescent inspiral is faster) and never shrink below it — at low
$m_{\rm smbh}$, inspiral is naturally slower at any fixed $a$, so the original default is
already a safe (if conservative) margin, and shrinking it serves no purpose except sampling
into the density blow-up above. Implemented as `a_min_pc = max(A_MIN_PC_DEFAULT,
a_min_safety_bound(m_smbh))` in `scripts/phase5_smbh_mass_scan.py`'s `_cluster_config` — this
formula happens to reduce to exactly `A_MIN_PC_DEFAULT` at the $m_{\rm smbh}=4\times10^6$
anchor point too (since `a_min_safety_bound(4e6)` $\approx9.45\times10^{-4}<10^{-3}$), so no
separate special case is needed for bit-for-bit Phase 3/4 reproducibility there. Verified
directly: the exact same low-mass point that hung for >40 minutes unclamped completes in 27s
clamped (11,258 steps; 155 mergers; max mass 566 $M_\odot$; 97.9% EMRI — a genuinely
EMRI-dominated regime at low $m_{\rm smbh}$, not a numerical artifact, now that the density
pathology is removed). This is exactly the kind of thing this project's culture of
stress-testing at actual scale (not just deriving formulas on paper) exists to catch —
see the Phase 2 EMRI-rate investigation and the initial-orbital-properties entry
(`#initial-orbital-properties`) for the same pattern occurring once already, at the original
$a_{\rm min}=10^{-4}$ pc choice.

**How to apply**: `scripts/phase5_smbh_mass_scan.py` implements this design;
`population.a_min_safety_bound` implements the generalized inner-bound calculation (tested
in `tests/test_population.py::TestAMinSafetyBound`, including a regression test that
demonstrates the artifact this function avoids). 112 runs total (7 $m_{\rm smbh}$ x 2
readings x 8 seeds). Results to follow in a new `results/phase5_*.md` once complete.

**Status, end of 2026-07-28 session (superseded below)**: design and code complete, not yet
launched. A third, separate timing issue turned up in smoke-testing (after the $a_{\rm
min}$/density fix above): a single seed at $m_{\rm smbh}=4\times10^5$ under `star_only` did
not converge within 15 minutes, well outside Phase 3's known 600-1740s spread for
H18/`star_only`. Likely mechanism (not yet confirmed as thoroughly as the $a_{\rm min}$ issue
was): holding density fixed while lowering $m_{\rm smbh}$ makes velocity dispersion lower
*everywhere* in the cluster ($\sigma\propto\sqrt{M_\bullet}$, not just at $a_{\rm min}$),
boosting gravitational-focusing collision efficiency throughout, while `coulomb_log`$=\ln(m_{\rm
smbh})$ also drops, weakening the relaxation process that normally moderates runaway growth
— both effects push toward more severe runaway growth, not a numerical artifact this time.
**Decided with the user**: rather than narrow the grid or chase a timeout, run the full
grid as designed and record whether each run hits the adaptive loop's 2,000,000-step
ceiling before reaching 10 Gyr (`hit_step_ceiling` column, added to `run_one`'s output row)
as data in its own right.

**Results (2026-07-28, `results/phase5_smbh_mass_scan_2026-07-28.md`)**: the full 112-run grid
completed (no exceptions; wall-clock dominated by the low-$m_{\rm smbh}$/`star_only` corner as
anticipated, ~4 hours). 11/112 runs (all `star_only`, all at $m_{\rm smbh}\in\{4\times10^5,\
1.264911\times10^6\}$) hit the 2,000,000-step ceiling before 10 Gyr.

**Finding 1 — the qualitative Eq. 22 dependence generalizes across all 3 decades of SMBH mass
tested**: under `star_only`, **every one of the 56 runs** (all 7 grid points $\times$ 8 seeds)
produced at least one IMBH — a fully saturated existence claim. Under `bh_inclusive`, the mean
% of the population exceeding 100 $M_\odot$ stays below 0.5% at **every single grid point**
across the full range. This is a direct, conditional answer to N26's own second Section 5.4
open question: the paper's result is not a Milky Way-specific coincidence — it generalizes
across 3 decades of SMBH mass, contingent on the same still-open Eq. 22 ambiguity already
documented in `#average-object-mass`. The $m_{\rm smbh}=4\times10^6$ anchor point reproduces
Phase 3's H18 validation **bit-for-bit** for seeds 0-2 (Gate 6 pass).

**Finding 2 — a severe, non-monotonic runaway-growth "sweet spot" 3-10x below the anchor mass,
tightly scoped to this scan's fixed-cluster-structure design choice**: the step-ceiling rate
under `star_only` is 0% at $m_{\rm smbh}=1.264911\times10^5$ (the *lowest* mass tested), jumps
to 50% at $4\times10^5$ and 87.5% at $1.264911\times10^6$, then drops back to 0% at and above
the $4\times10^6$ anchor. In this band, mean maximum BH mass reaches into the **millions of
solar masses** — in several runs literally exceeding the central SMBH's own mass. Mechanism:
two $m_{\rm smbh}$-dependent effects compete — relaxation-driven EMRI removal weakens
($t_{\rm relax}\propto\sigma^3\propto M_\bullet^{1.5}$) as $m_{\rm smbh}$ drops, while
growth-channel efficiency (Eq. 18 focusing, Eq. 4-7 GW-capture) simultaneously strengthens; at
the very lowest mass tested, relaxation still wins outright (97.7% EMRI, cutting off growth
early), but in the $4\times10^5$-$1.264911\times10^6$ band the balance tips just enough to let
the already-documented (`#phase2-emri-rate-high`) superlinear growth mechanism run
uncontested. **Explicitly scoped, not a claim about real lower-mass galactic nuclei**: this
result depends entirely on holding the cluster's structural density fixed while shrinking
$m_{\rm smbh}$ (Gate 1c) — a real lower-mass nucleus plausibly has correspondingly lower
density too, which this scan does not model. Full gate scorecard, per-seed detail, and the
falsification pass (ruling out a step-ceiling artifact or a numerical bug) in
`results/phase5_smbh_mass_scan_2026-07-28.md`.

## Still to resolve before Phase 1 (Section 4) is considered fully complete

- Confirm the Eq. 21 exponent discrepancy resolution (1/2 vs printed 1/3) doesn't need
  revisiting once Phase 3 validation runs against Table 1's max-spin column.
- Confirm the $\langle M_{\rm avg}\rangle$ assumption doesn't need revisiting once Phase 3
  validation runs against EMRI timing/rate figures (Section 5.4 timing claims).
