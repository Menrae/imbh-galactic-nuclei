# Limitations and caveats (running log)

Maintained incrementally throughout the project — every simplifying assumption,
paper ambiguity, or deliberately-unmodeled effect gets a line here as soon as it comes up,
not retrofitted at the end. Mirrors the "Open items log" in `docs/equations.md` for
equation-specific issues; this file is broader (methodology, validation, scope).

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

N26 describes $\langle M_{\rm avg}\rangle$ in the relaxation-time formula (Eq. 22) only as
"the average object mass," with no formula given. The single-population analog in Rose et
al. 2020 (Eq. 17 there) just uses $\langle M_\star\rangle$, but N26's cluster is explicitly
two-component (BHs + 1 M☉ stars), and N26's own Section 4.3 text describes relaxation as
proceeding through interactions with "other objects" generically, not just stars.

**Resolution adopted**: $\langle M_{\rm avg}\rangle(r)$ = the number-density-weighted mean
object mass of the local population at $r$: $[n_\star(r)\cdot 1 M_\odot + n_{\rm BH}(r)\cdot
\langle m_{\rm BH}\rangle] / [n_\star(r)+n_{\rm BH}(r)]$, with $\langle m_{\rm BH}\rangle$ the
mean of the initial BH mass distribution in use for that run.

**Why**: mirrors how N26 itself handles the analogous "$m_2$" placeholder in the GW-capture
$\eta$ calculation (Section 4.1: "we take $m_2$ in $\eta$ to be the average of the initial
mass distribution") — using a population mean where an individual encounter partner isn't
tracked is already N26's own convention elsewhere in the paper.

**How to apply**: `imbh_nuclei.relaxation.relaxation_timescale` takes this as a computed
input; **flagged to user** as a best-guess resolution, not a textual certainty — open to
correction if it visibly affects Phase 3 reproduction of relaxation-driven quantities (e.g.
EMRI timing).

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

N26 Eq. 22 includes $\ln\Lambda$, "the Coulomb logarithm," with no numeric prescription
given — just a generic citation to Binney & Tremaine 2008. Common choices in this subfield
for a cusp dominated by a central SMBH include $\ln\Lambda \sim \ln(M_\bullet/\langle
m\rangle)$ or $\ln(0.4N)$ for $N$ objects within the relevant radius; these give
substantially different numeric values (typically $\ln\Lambda \sim 10$-$20$ either way, but
not identical).

**Resolution adopted**: none — `relaxation_timescale` requires `coulomb_log` as an explicit
argument with no default, forcing this choice to be made visibly at the call site (in the
Phase 2 integration loop) rather than buried in this module.

**Why**: unlike $\langle M_{\rm avg}\rangle$, there isn't a clear textual anchor elsewhere in
N26 to base a best-guess resolution on, so we defer the choice rather than guess.

**How to apply**: whoever wires up the Phase 2 loop must pick a value/formula for
$\ln\Lambda$ and document the choice here when that happens.

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

## Phase 2 smoke-test EMRI fraction is much higher than N26's implied rate {#phase2-emri-rate-high}

**Updated with real data.** A full $N=1000$, 10 Gyr run using the actual H18 initial
distribution (`initial_conditions.py`, Phase 3) gives: 757 EMRIs (75.7%), only 3 GW-capture
mergers, and a maximum final mass of 100.3 $M_\odot$. Table 1's H18 row instead reports 371
mergers, max mass 407.3 $M_\odot$, and (from Section 5.4's rate figures) an implied EMRI
count of order tens over 10 Gyr, not hundreds. The GW-capture merger channel itself is not
obviously broken (an equal-mass, non-spinning test merger gave remnant $\chi_f\approx0.685$,
matching the independently-verified Schwarzschild benchmark to 3 decimals) -- the low merger
count looks like a *consequence* of the EMRI channel removing BHs from the pool before they
have time to grow via collisions/captures, not an independent bug.

**Root cause, narrowed down**: direct inspection of the timescales (`t_relax` vs. orbital
period, vs. `dt`) shows the relaxation-kick aggregation is internally consistent with the
*definition* of $t_{\rm relax}$ (velocity randomizes by order-of-itself over one relaxation
time) -- at $\Delta t = 0.1\,t_{\rm relax}$ (our `timestep_safety_factor`), the aggregated
kick naturally comes out to $\sim\sqrt{0.1}\approx32\%$ of the local circular velocity, which
is large but not unphysical for that definition. Testing sensitivity to `coulomb_log` (10 vs.
30 vs. 100) shows the EMRI fraction is *not* strongly parameter-sensitive in that range (all
three gave 70-85% of a 300-BH test sample reaching excursion/EMRI/ejected) -- ruling out
`coulomb_log`'s specific placeholder value as the primary cause. This points to something more
structural in the per-timestep aggregation itself: treating a timestep spanning
$10^5$-$10^6$ orbits as *one* Gaussian kick evaluated at the *starting* radius's kick-scale
does not capture that the local dynamics (period, $t_{\rm relax}$, $v_{\rm circ}$) should
themselves evolve *during* that walk in a true diffusion process -- our one-shot aggregation
implicitly assumes they stay fixed at the pre-timestep values for the whole span, which stops
being a good approximation once the walk is large enough to be interesting (i.e. always, at
these radii, given how much shorter orbital periods are than any reasonable global timestep).

**Not resolved in this pass.** The most promising concrete next step: replace the one-shot
aggregated-kick approximation with genuine per-orbit (or coarser but still sub-timestep)
substepping of the relaxation walk, so the local dynamics update *during* a timestep rather
than only at its start and end. This is real implementation work, not a parameter tweak, and
is the top blocker for a meaningful Phase 3 comparison against Table 1 -- **Phase 3's other
deliverable, the four initial mass/spin distributions (`initial_conditions.py`), is complete
and tested independently of this issue** (see `docs/equations.md#initial-conditions`), so
that work is not blocked, only the full validation run against Table 1's numbers is.

## Still to resolve before Phase 1 (Section 4) is considered fully complete

- Confirm the Eq. 21 exponent discrepancy resolution (1/2 vs printed 1/3) doesn't need
  revisiting once Phase 3 validation runs against Table 1's max-spin column.
- Confirm the $\langle M_{\rm avg}\rangle$ assumption doesn't need revisiting once Phase 3
  validation runs against EMRI timing/rate figures (Section 5.4 timing claims).
