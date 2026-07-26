# Equations reference

Single source of truth for every equation used in this model. Code references this file by
anchor (e.g. `# see docs/equations.md#stellar-density-profile`) instead of re-deriving or
re-explaining physics in comments. This document is written to be usable directly as the
"Methods" section of the eventual `paper/` writeup.

**Primary source**, cited throughout as **N26**:

> Newton, A., Rose, S. C., Kıroğlu, F., Hoang, B.-M., & Rasio, F. A. 2026, ApJ, 1006:184,
> "Intermediate-mass Black Hole Formation from Hierarchical Mergers in Galactic Nuclei"
> (`references/Newton_2026_ApJ_1006_184.pdf`)

Every equation below has been read directly from the PDF (page images, not just OCR text
extraction, which garbles subscripts/exponents in several places — see ambiguity notes) and
traces back, where N26 itself cites a source, to the original publication rather than
stopping at N26. Where N26's presentation is incomplete, ambiguous, or appears to contain a
typo relative to its own cited source, that is flagged explicitly under **Ambiguity note**
rather than silently patched — see `paper/limitations.md` for the full reasoning on each.

## Units and conventions

Unless stated otherwise, this package uses:

| Quantity | Unit |
| --- | --- |
| length | pc |
| mass | M☉ |
| velocity | km/s |
| time | yr (relaxation-type timescales quoted in Gyr for readability) |

Gravitational constant: `G = 4.30091e-3 pc M☉⁻¹ (km/s)²` (`imbh_nuclei.constants.G_ASTRO`),
the standard value used throughout galactic dynamics work at these scales. Natural units
($c=G=1$) are used locally in Section 4.1's ISCO/spin equations, as in the source papers.

---

## Section 2 — Cluster structure

### Stellar density profile

**Status: implemented and confirmed against PDF (page 3).**

$$
\rho_\star(r) = \rho_0 \left( \frac{r}{r_0} \right)^{-\alpha_\star}
$$

- $\rho_\star(r)$: stellar mass density at radius $r$ [M☉ pc⁻³]
- $\rho_0 = 1.35 \times 10^6\ M_\odot\,\mathrm{pc}^{-3}$: normalization at $r_0$
- $r_0 = 0.25$ pc: normalization radius
- $\alpha_\star = 1.25$ (default): power-law cusp slope

**Source**: N26 Eq. 3. Normalization from R. Genzel, F. Eisenhauer, & S. Gillessen 2010,
RvMP, 82, 3121. N26 use $\alpha_\star = 1.25$ as a deliberately conservative value (a lower
stellar density can only *understate* the star–BH collision rate), noting Milky Way NSC
observations indicate $\alpha \in [1.1, 1.4]$ (M. Habibi et al. 2019; R. Schödel et al.
2020) — relevant to the Phase 7 sensitivity scan.

**Implementation**: `imbh_nuclei.cluster.stellar_density`.

**Ambiguity note**: none — fully specified, no discrepancy found.

---

### BH number density profile

**Status: implemented and confirmed against PDF (page 2-3).**

$$
n_{\rm BH}(r) = n_0 \left( \frac{r}{R_h} \right)^{-\alpha_{\rm BH}}
$$

- $n_{\rm BH}(r)$: BH number density at radius $r$ [pc⁻³]
- $n_0 = 10^4\ \mathrm{pc}^{-3}$: normalization constant
- $R_h = 1$ pc: the SMBH's sphere of influence (normalization radius — **distinct from the
  stellar profile's $r_0 = 0.25$ pc**, do not conflate the two)
- $\alpha_{\rm BH} \approx 1.83$ (default): BH cusp slope

**Source**: N26 Eq. 2. Profile shape from a Fokker-Planck calculation for a four-component
population (main-sequence stars, BHs, white dwarfs, neutron stars) in D. Aharon & H. B.
Perets 2016, ApJL, 830, L1 (their Figure 1, left panel), which N26 note is comparable to the
analytic two-component-population result of B. Rom, I. Linial, K. Kaur, & R. Sari 2024a, ApJ,
977, 7 within the inner 0.1 pc (see the Appendix comparison, below). This profile yields
$\gtrsim 1000$ BHs within the inner 0.1 pc, consistent with N26's choice to sample 1000 BHs.

**Implementation**: `imbh_nuclei.cluster.bh_number_density`.

**Ambiguity note**: previously flagged as unresolved (normalization $n_0$ "not given") —
this was an error in an earlier pass that worked from a paraphrased equation map rather than
the paper itself. Reading the PDF directly resolved it fully: $n_0$ and $R_h$ are both given
as explicit numeric constants in-text, not derived quantities.

---

### Velocity dispersion profile

**Status: implemented and confirmed against PDF (page 2).**

$$
\sigma(r) = \sqrt{\frac{G M_{\bullet}}{(\alpha + 1)\, r}}
$$

- $\sigma(r)$: velocity dispersion at radius $r$ [km/s]
- $M_{\bullet}$: SMBH mass [M☉]
- $\alpha$: slope of the *relevant population's* density profile (see ambiguity note)
- $G$: gravitational constant (`imbh_nuclei.constants.G_ASTRO`)

**Source**: N26 Eq. 1. The paper states this "also weakly depends on $\alpha$, the slope of
the density profile" — confirmed the $(\alpha+1)$ denominator is the mechanism (a factor of
order unity, hence "weakly").

**Implementation**: `imbh_nuclei.cluster.velocity_dispersion(r, m_smbh, alpha)` — `alpha` is
a required argument (no silent default), forcing every call site to make an explicit choice.

**Ambiguity note** (see `paper/limitations.md#velocity-dispersion-alpha-choice`): N26 uses
Eq. 1 in at least two contexts with two different density slopes in play ($\alpha_\star$ for
stars, $\alpha_{\rm BH}$ for BHs), and never restates which $\alpha$ governs $\sigma$ in each
one. Our resolution, based on textual pairing in each context:

- **Eq. 18** (BH–star collision timescale) explicitly says "$n$ and $\sigma$ are calculated
  from Equations (1) and (3)" — Eq. 3 is the *stellar* density, so we pair $\sigma$ with
  $\alpha = \alpha_\star$ here.
- **Eq. 7** (GW capture timescale) evaluates "$n_{\rm BH}$ and $\sigma$" together, where
  $n_{\rm BH}$ comes from Eq. 2 (BH density, $\alpha_{\rm BH}$). By the same pairing logic —
  and because the relevant relative velocity for BH–BH capture is that of the BH population
  itself — we use $\alpha = \alpha_{\rm BH}$ here.

This is an interpretation, not a textual certainty, since N26 never says "use $\alpha_{\rm
BH}$ in Eq. 7" explicitly. Flagged for the user; open to correction.

---

### Initial orbital properties (semimajor axis, eccentricity)

**Status: not in N26 itself; resolved via the explicitly-inherited base model.**

$$
p(e)\,de = 2e\,de,\ e\in[0,1) \qquad\qquad \frac{dN}{d(\log_{10} a_\bullet)} = {\rm const},\ a_\bullet\in[a_{\min}, 0.1\,{\rm pc}]
$$

**Source**: not stated in N26's own text (see `paper/limitations.md#initial-orbital-properties`
for the full reasoning); adopted from S. C. Rose, S. Naoz, R. Sari, & I. Linial 2022, ApJL,
929, L22 (arXiv:2201.00022), the paper N26 explicitly says its semianalytic model is "first
developed by," which states this thermal-eccentricity / log-uniform-semimajor-axis
convention directly.

**Implementation**: `imbh_nuclei.population` (Phase 2).

**Ambiguity note**: the outer bound (0.1 pc) matches N26's stated focus region; the inner
bound $a_{\min}$ is not pinned to any N26-stated value — flagged to user, see
`paper/limitations.md#initial-orbital-properties`.

---

## Section 3 — Initial BH Mass/Spin Distributions {#initial-conditions}

**Status: implemented; H18 exact, K20 reconstructed from N26's own figure (see below).**

Four initial conditions: K20, K20+M, H18, H18+M.

**H18** (exact closed form, confirmed directly from B.-M. Hoang et al. 2018,
arXiv:1706.09896): each BH mass drawn independently, log-uniform (i.e. $dN/dm\propto
m^{-1}$) between 6 and 100 $M_\odot$; single, zero initial spin.

**K20**: N26 describes this as "based on Cluster Monte Carlo (CMC) globular cluster
simulations by K. Kremer et al. (2020)," extending up to $\sim$15 $M_\odot$. Kremer et al.
2020 (arXiv:2006.10771, downloaded and read directly) turns out to be a simulation of
**young massive star clusters** (Kroupa-IMF stars, 0.08-150 $M_\odot$, low metallicity
$Z=0.1Z_\odot$) undergoing runaway stellar collisions that feed into BH formation — a
numerical-simulation output, not a closed-form mass function given anywhere in that paper.
There is consequently no formula to transcribe. Instead, **K20's mass distribution was
reconstructed by reading bin edges/heights directly off N26's own Figure 1** (left panel,
green histogram) — the closest available representation of what N26 actually sampled from,
since it's literally their own plot of the distribution in use. Approximate (read by eye off
the published figure at high resolution, not exact numeric data extraction) — see
`initial_conditions.K20_BIN_EDGES`/`K20_BIN_WEIGHTS` and
`paper/limitations.md#k20-reconstruction`.

**+M variants** (K20+M, H18+M): N26 describes accounting for primordial-binary-merger
products as "15% of the BH population... a third of the primordial binary systems merged."
Interpreted as: pair up 15% of the base single-BH population (by count), and of those pairs,
1/3 undergo a merger (replaced by a single remnant computed via the same Eq. 8-12 machinery
already implemented for the Phase 2 GW-capture channel — reused directly, not
reimplemented); the remaining 2/3 of pairs stay as unmerged singles. To hold the sample size
fixed, BHs "consumed" beyond what the remnants replace are backfilled with fresh draws from
the base distribution. N26 does not spell out this bookkeeping explicitly — a documented,
reasonable interpretation of the stated 15%/one-third figures, not a textual certainty.
Confirmed to reproduce N26's own qualitative observation that "+M" initial spin
distributions "have a peak around 0.7" — see `tests/test_initial_conditions.py` (both
progenitors are nonspinning, so remnant spin comes entirely from orbital angular momentum,
the same mechanism underlying the Barausse & Rezzolla $\ell$ term, Section 4.1 above).

**Implementation**: `imbh_nuclei.initial_conditions.{sample_k20_mass, sample_h18_mass,
apply_primordial_mergers, sample_k20_plus_m, sample_h18_plus_m, get_samplers}`.

---

## Section 4.1 — GW Capture between Single Black Holes

**Status: implemented and confirmed against PDF (page 4).**

Symmetric mass ratio (standard definition, used throughout):

$$
\eta = \frac{m_1 m_2}{(m_1+m_2)^2}
$$

Maximum impact parameter to produce a capture (Eq. 4):

$$
b_{\rm max} = \left(\frac{340\pi\eta}{3}\right)^{1/7} \frac{G M_{\rm tot}}{c^2} \left(\frac{v_{\rm rel}}{c}\right)^{-9/7}
$$

Minimum impact parameter, below which the encounter is a direct collision rather than a GW
capture (Eq. 5):

$$
b_{\rm min} = \frac{4 G M_{\rm tot}}{c^2} \left(\frac{v_{\rm rel}}{c}\right)^{-1}
$$

GW capture cross section (Eq. 6):

$$
A_{\rm cap} = \pi\left(b_{\rm max}^2 - b_{\rm min}^2\right)
$$

GW capture timescale (Eq. 7):

$$
t_{\rm GW} = \left(A_{\rm cap}\, n_{\rm BH}\, \sigma\right)^{-1}
$$

- $M_{\rm tot} = m_1+m_2$; $v_{\rm rel}$ is taken to be $\sigma(r)$ (Eq. 1) at the BH's
  semimajor axis, with $\alpha=\alpha_{\rm BH}$ (see ambiguity note above)
- $m_2$ in $\eta$ is taken to be the mean of the initial BH mass distribution (per-BH
  timescales are computed for BH 1 against a notional "average" BH 2)
- $n_{\rm BH}$ from Eq. 2, evaluated at the same semimajor axis

**Source**: R. M. O'Leary, B. Kocsis, & A. Loeb 2009, MNRAS, 395, 2127 (cross section and
capture-timescale formalism); also cited alongside L. Gondán et al. 2018 and B.-M. Hoang
et al. 2020 in N26.

**Implementation**: `imbh_nuclei.gw_capture.{symmetric_mass_ratio, b_max, b_min,
capture_cross_section, capture_timescale}`.

### Remnant mass, spin, and ISCO

Final remnant mass (Eq. 8):

$$
\frac{m_f}{M_{\rm tot}} = 1 - \eta(1-4\eta)(1-E_{\rm ISCO}) - 16\eta^2\left(p_0 + 4p_1\,\chi_\parallel(\chi_\parallel+1)\right)
$$

$$
E_{\rm ISCO} = \sqrt{1 - \frac{2}{3\, r_{\rm ISCO}}}, \qquad p_0 = 0.04827,\ \ p_1 = 0.01707
$$

Parallel spin component (Eq. 9), for BHs of mass/spin $(m_1,\chi_1)$, $(m_2,\chi_2)$ and unit
orbital angular momentum vector $\hat L$:

$$
\chi_\parallel = \frac{m_1^2 \chi_1 + m_2^2 \chi_2}{(m_1+m_2)^2} \cdot \hat L
$$

Final spin magnitude (Eq. 10), with mass ratio $q$, $\cos\theta_1 = \chi_1\cdot\hat L$,
$\cos\theta_2=\chi_2\cdot\hat L$:

$$
\chi_f = \min\left(1,\ \left|\frac{q^2\chi_2\cos\theta_2 + \chi_1\cos\theta_1}{(1+q)^2} + \frac{qL}{(1+q)^2}\right|\right)
$$

ISCO radius (Eq. 11) and its $\chi$-dependent parameters (Eq. 12), in natural units
($c=G=1$), upper/lower sign for prograde/retrograde:

$$
r_{\rm ISCO} = 3 + Z_2 \mp \sqrt{(3-Z_1)(3+Z_1+2Z_2)}
$$

$$
Z_1 = 1 + (1-\chi^2)^{1/3}\left[(1+\chi)^{1/3} + (1-\chi)^{1/3}\right], \qquad Z_2 = \left[3\chi^2+Z_1^2\right]^{1/2}
$$

**Source**: N26 attributes these to "the same equations as the CMC Code (C. L. Rodriguez
et al. 2022, ApJS, 258, 22), drawn from numerical relativity and other studies": the
$r_{\rm ISCO}(\chi)$/$Z_1$/$Z_2$ form originates in J. M. Bardeen, W. H. Press, & S. A.
Teukolsky 1972, ApJ, 178, 347 (Kerr ISCO); the remnant-mass fit and $p_0,p_1$ constants trace
to E. Barausse & L. Rezzolla 2009, ApJL, 704, L40 and E. Barausse, V. Morozova, & L. Rezzolla
2012, ApJ, 758, 63, with $p_0,p_1$ specifically from C. Reisswig et al. 2009, PhRvD, 80,
124026 (as refit/tabulated in Barausse et al. 2012 and used by C. L. Rodriguez et al. 2018,
PhRvL, 120, 151101). The $\chi_\parallel$ normalization convention ($J/M^2$) follows Z. Li &
C. Bambi 2014, JCAP, 2014, 041.

**Implementation**: `imbh_nuclei.gw_capture.{remnant_mass, isco_energy, chi_parallel,
final_spin, r_isco, z1, z2, orbital_ell}`.

**Ambiguity note**: Eqs. 8-12 as coded match the PDF exactly. **Test anchor**:
$r_{\rm ISCO}(\chi=0) = 3 + \sqrt{3}\cdot\sqrt{3} = 6$, the Schwarzschild value, and
$\eta(m_1=m_2)=0.25$ — both checked directly in `tests/test_gw_capture.py`.

**Resolved gap — "$L$" in Eq. 10**: N26's Eq. 10 uses a quantity "$L$, the orbital angular
momentum" without giving its formula (distinct from the unit-vector $\hat L$ used to project
spins onto in Eq. 9 — in Eq. 10, "$L$" is added directly inside a magnitude expression, so it
must itself be a dimensionless scalar, not a vector). Traced to E. Barausse & L. Rezzolla
2009, ApJL, 704, L40 (arXiv:0904.2577; downloaded, confirmed by direct PDF read): their Eq. 1
gives the aligned-spin final-spin fit (coefficients $s_4,s_5,t_0,t_2,t_3$, refit to 72 NR
binaries) and their Eq. 5 gives the aligned-spin reduction $a_{\rm fin} = [a_1+a_2q^2+\ell
q]/(1+q)^2$ — matching N26's Eq. 10 structure exactly once "$L$" is identified as their
script-$\ell$. Solving Eq. 5 for $\ell$ using Eq. 1's fit gives a closed-form expression for
N26's "$L$" — implemented in `orbital_ell`. Self-consistency verified two ways in
`tests/test_gw_capture.py`: (1) for fully-aligned spins, `orbital_ell` fed back into
`final_spin` exactly reproduces the aligned fit by construction; (2) for the equal-mass,
non-spinning case, it reproduces Barausse & Rezzolla's own calibration benchmark
$a_{\rm fin}=0.68646$ (their Eq. 2, from Scheel et al. 2009 NR data) to 3 decimal places —
an independent numerical check, not just internal consistency.

---

## Section 4.1.1 — Recoil Kicks

**Status: implemented; A/B/H/K pulled from the original source via web search (not in N26).**

$$
v_{\rm kick} = (1+e)\left[\hat x(v_m + v_\perp\cos\xi) + \hat y\, v_\perp\sin\xi + \hat z\, v_\parallel\right]
$$

$$
v_m = A\frac{q^2(1-q)}{(1+q)^5}\left(1 + B\frac{q}{(1+q)^2}\right) \qquad \text{(Eq. 13)}
$$

$$
v_\perp = H\frac{q^2}{(1+q)^5}\left(\chi_{\parallel,2} - q\chi_{\parallel,1}\right) \qquad \text{(Eq. 15)}
$$

$$
v_\parallel = K\cos(\Theta-\Theta_0)\frac{q^2}{(1+q)^5}\left(\chi_{\perp,2} - q\chi_{\perp,1}\right) \qquad \text{(Eq. 16)}
$$

$\Theta$: angle of the merger direction; $\Theta_0$: angle of the initial direction of
motion; $\xi$: angle from unequal mass/spin contributions — all drawn from a uniform
distribution per merger. $e$ is the orbital eccentricity at merger (N26 assumes prompt,
high-eccentricity GW-capture mergers, so $e$ is not the negligible-eccentricity limit).

**Fitting constants** (N26 states these "can be found in K. Holley-Bockelmann et al.
2008" without tabulating them; pulled directly from that source, arXiv:0707.1334 /
ApJ, 686, 829, Eqs. 2-4 — confirmed via direct PDF read, not a secondary citation):

$$
A = 1.2\times10^4\ {\rm km\,s^{-1}}, \quad B = -0.93, \quad H = (7.3\pm0.3)\times10^3\ {\rm km\,s^{-1}}, \quad K = (6.0\pm0.1)\times10^4\ {\rm km\,s^{-1}}
$$

**Source**: K. Holley-Bockelmann, K. Gültekin, D. Shoemaker, & N. Yunes 2008, ApJ, 686, 829.
That paper itself adopts the parameterized numerical-relativity fit of M. Campanelli, C.
Lousto, Y. Zlochower, & D. Merritt 2007, ApJL, 659, L5 (N26's own "see also" list for this
section), adding the $(1+e)$ eccentric-orbit factor from C. F. Sopuerta, N. Yunes, & P.
Laguna 2007, ApJL, 656, L9. We cite Holley-Bockelmann et al. 2008 as the source, per N26,
while noting Campanelli et al. 2007 as the further-upstream origin of A, B, H, K.

**Implementation**: `imbh_nuclei.recoil.{kick_velocity, v_m, v_perp, v_parallel}`; constants
in `imbh_nuclei.recoil.HOLLEY_BOCKELMANN_2008`.

**Ambiguity note**: none for the formula itself. The *point along the orbit* at which the
kick is applied, and the resulting new bound/unbound orbit calculation, is Phase 2 loop
logic (statistically weighted by time spent per orbital phase, per N26 text) — deferred to
that phase, not a Section 4.1.1 equation-level ambiguity.

---

## Section 4.2 — Direct Collisions with Stars

**Status: implemented and confirmed against PDF (page 5); f₁/f₂ traced to source.**

Collision timescale, geometric form (Eq. 17):

$$
t_{\rm coll} = \frac{1}{n_\star A \sigma}
$$

Full form with gravitational focusing and eccentricity dependence (Eq. 18):

$$
t_{\rm coll}^{-1} = \pi n \sigma \left[f_1(e_{\rm BH})\, r_c^2 + f_2(e_{\rm BH})\, r_c\, \frac{2G(m_{\rm BH}+M_\odot)}{\sigma^2}\right]
$$

- $r_c$ = sum of the radii of the BH (0, point mass) and a 1 M☉ star
- $n = n_\star = \rho_\star/M_\odot$ (Eq. 3), $\sigma$ from Eq. 1 with $\alpha=\alpha_\star$
  (see cluster-structure ambiguity note), both evaluated at the BH's semimajor axis
- $\Delta t / t_{\rm coll}$ is the per-timestep collision probability; timestep starts at
  $10^6$ yr and adaptively shrinks below $t_{\rm coll}$

**Eccentricity factors** $f_1(e_{\rm BH})$, $f_2(e_{\rm BH})$ — N26 states these are "as
described in S. C. Rose et al. (2020)" without giving the functional form. Located directly
in that source (S. C. Rose, S. Naoz, A. K. Gautam, et al. 2020, ApJ, 904, 113, Eqs. 20-21;
downloaded via NSF PAR, confirmed by direct PDF read):

$$
f_1(e) = \frac{(1-e)^{\frac12-\alpha}}{2}\ {}_2F_1\!\left(\tfrac12, \alpha-\tfrac12; 1; \tfrac{2e}{e-1}\right) + \frac{(1+e)^{\frac12-\alpha}}{2}\ {}_2F_1\!\left(\tfrac12, \alpha-\tfrac12; 1; \tfrac{2e}{e+1}\right)
$$

$$
f_2(e) = \frac{(1-e)^{\frac32-\alpha}}{2}\ {}_2F_1\!\left(\tfrac12, \alpha-\tfrac32; 1; \tfrac{2e}{e-1}\right) + \frac{(1+e)^{\frac32-\alpha}}{2}\ {}_2F_1\!\left(\tfrac12, \alpha-\tfrac32; 1; \tfrac{2e}{e+1}\right)
$$

where ${}_2F_1$ is the Gauss hypergeometric function and $\alpha$ is the density-profile
slope of the perturbing population — here $\alpha_\star$, consistent with Eq. 18's use of
the stellar profile. **Sanity check**: at $e=0$ (circular orbit), ${}_2F_1(a,b;c;0)=1$
identically, so $f_1(0)=f_2(0)=1$, recovering the non-eccentric form of Eq. 18 — verified in
`tests/test_collisions.py`.

**Implementation**: `imbh_nuclei.collisions.{f1_eccentricity, f2_eccentricity,
collision_timescale}`.

### 4.2.1 — Mass Growth through Collisions

Bondi-Hoyle accretion rate (Eq. 19):

$$
\dot m_{\rm BH} = \frac{4\pi G^2 m_i^2 \rho_\star}{(c_s^2+\sigma^2)^{3/2}}, \qquad \rho_\star = \frac{3 M_\odot}{4\pi R_\odot^3}, \qquad c_s = 600\ {\rm km\,s^{-1}}
$$

Captured mass (Eq. 20):

$$
m_{\rm cap} = \min\left(\dot m_{\rm BH} \times t_{\star,\rm cross},\ 1\,M_\odot\right), \qquad t_{\star,\rm cross}\sim R_\star/\sigma
$$

Accreted mass after feedback losses:

$$
\Delta m_{\rm BH} = m_{\rm cap} \times \frac{v_{\rm esc}}{c\,\eta}, \qquad v_{\rm esc} = \sqrt{2 G m_{\rm BH}/R_\odot},\ \ \eta = 0.1
$$

**Source**: H. Bondi & F. Hoyle 1944, MNRAS, 104, 273; H. Bondi 1952, MNRAS, 112, 195 (Bondi-
Hoyle accretion); sound-speed value from J. Christensen-Dalsgaard et al. 1996, Sci, 272,
1286; feedback/efficiency prescription from S. C. Rose et al. 2022, ApJL, 929, L22.

**Implementation**: `imbh_nuclei.collisions.{bondi_hoyle_rate, captured_mass,
accreted_mass}`.

**Ambiguity note** (see `paper/limitations.md#mdot-vs-delta-m-notation`): Eq. 19 in the PDF
defines the accretion **rate** as $\dot m_{\rm BH}$ (dot notation), but Eq. 20 multiplies
"$\Delta m_{\rm BH}$" (no dot) by a crossing **time** to get a mass. Multiplying a mass
difference by a time is dimensionally wrong; multiplying a *rate* by a time is not. We treat
this as a notation inconsistency in the published PDF and implement Eq. 20 using the Eq. 19
rate, i.e. $m_{\rm cap} = \min(\dot m_{\rm BH}\times t_{\star,\rm cross}, 1 M_\odot)$ —
resolved by dimensional analysis, not guessed.

### 4.2.2 — Spin Change through Collisions

Final spin after a collision (Eq. 21; $m_f/m_i$ is the BH's mass ratio after/before the
collision, $r_{\rm ISCO}$ from Eq. 11 evaluated at the *new* spin):

$$
\chi_f = \begin{cases}
\dfrac{r_{\rm ISCO}^{1/2}}{3}\cdot\dfrac{m_i}{m_f}\left(4 - \sqrt{3\left(\dfrac{m_i}{m_f}\right)^2 r_{\rm ISCO} - 2}\right), & \dfrac{m_f}{m_i} \le r_{\rm ISCO}^{1/2} \\[2ex]
1, & \dfrac{m_f}{m_i} \ge r_{\rm ISCO}^{1/2}
\end{cases}
$$

**Source**: M. Volonteri, M. Sikora, J.-P. Lasota, & A. Merloni 2013, ApJ, 775, 94, Eqs.
14-15 (the Bardeen 1970 thin-disk spin-up formula; downloaded from arXiv:1210.1025 and
confirmed by direct PDF read). Originally J. M. Bardeen 1970, Nature, 226, 64.

**Implementation**: `imbh_nuclei.collisions.spin_change`.

**Ambiguity note** (see `paper/limitations.md#eq21-exponent-discrepancy` — **flagged to
user, not silently resolved**): N26's printed Eq. 21 (confirmed via ultra-high-resolution
crop of the PDF) shows the prefactor as $r_{\rm ISCO}^{1/3}/3$, exponent **1/3**. The
original Volonteri et al. 2013 source (Eq. 14 of that paper, confirmed by direct PDF read)
has exponent **1/2**: $r_{\rm ISCO}(t)^{1/2}/3$. The inner square-root term matches exactly
between the two papers once N26's unsubscripted "$r$" is identified as $r_{\rm ISCO}$, so
this is not a wholesale different formula — just one exponent that differs from the cited
source. We implement the source's $1/2$ exponent (physically the standard, widely-used
Bardeen spin-up result), treating N26's $1/3$ as a probable typesetting error, but this has
**not been confirmed with the authors** and materially affects predicted spin values, so
Phase 3 validation should watch for this specifically if our peak spins disagree from
Table 1. Additionally, Volonteri et al. 2013's saturation branch caps spin at $a=0.998$ (the Thorne
1974 equilibrium limit), while N26 states a literal cap of $\chi_f=1$; we follow N26's stated
cap of 1 since we are reproducing N26's model, not Volonteri et al.'s (the numerical
difference is $<0.2\%$ and does not affect any qualitative conclusion).

---

## Section 4.3 — Relaxation and Dynamical Friction

**Status: implemented and confirmed against PDF (page 5-6); ⟨M_avg⟩ resolved by assumption.**

Two-body relaxation timescale (Eq. 22):

$$
t_{\rm relax} = 0.34\, \frac{\sigma^3}{G^2\rho\langle M_{\rm avg}\rangle\ln\Lambda}
$$

Mass-segregation timescale (Eq. 23):

$$
t_{\rm seg} \approx \frac{M_\star}{m_{\rm BH}} \times t_{\rm relax}\big(\langle M_{\rm avg}\rangle = M_\star,\ \rho=\rho_\star\big)
$$

**Source**: N26 Eqs. 22-23, citing J. Binney & S. Tremaine 2008, *Galactic Dynamics* (2nd
ed.) for the relaxation-time form, and L. Spitzer 1987; J. M. Fregeau et al. 2002, ApJ, 570,
171; D. Merritt 2006, RPPh, 69, 2513 for the mass-segregation form. The same two-body
relaxation formalism (with a single-population $\langle M_*\rangle$) appears as Eq. 17 of S.
C. Rose et al. 2020, ApJ, 904, 113 (the same collision-timescale paper used for $f_1,f_2$
above), confirming the numerical prefactor 0.34 and citing Binney & Tremaine 2008, Eq.
(7.106) specifically.

**Implementation**: `imbh_nuclei.relaxation.{relaxation_timescale, segregation_timescale}`.

**Ambiguity note** (see `paper/limitations.md#coulomb-logarithm`): N26 gives no numeric
prescription for $\ln\Lambda$, citing Binney & Tremaine 2008 generically. `coulomb_log` is
therefore a required argument with no default in `relaxation_timescale` — deliberately not
silently filled in.

**Ambiguity note** (see `paper/limitations.md#average-object-mass`): N26 describes
$\langle M_{\rm avg}\rangle$ in Eq. 22 only as "the average object mass," with no formula.
Rose et al. 2020's single-population analog uses $\langle M_\star\rangle$ (i.e., just the
mass of the field population under consideration). N26's cluster, however, is explicitly
two-component (BHs + 1 M☉ stars), and Section 4.3 states relaxation proceeds through "weak
gravitational interactions with **other objects**" generically — not just stars. Our
resolution: $\langle M_{\rm avg}\rangle(r)$ is the number-density-weighted mean object mass
of the *local* population at radius $r$,
$$
\langle M_{\rm avg}\rangle(r) = \frac{n_\star(r)\cdot 1\,M_\odot + n_{\rm BH}(r)\cdot \langle m_{\rm BH}\rangle}{n_\star(r) + n_{\rm BH}(r)},
$$
with $\langle m_{\rm BH}\rangle$ the mean of the initial BH mass distribution (mirroring how
N26 handles "$m_2$" in the GW-capture $\eta$, Section 4.1). This is a best-guess resolution,
not a textual certainty — flagged to the user.

### Orbital random walk from relaxation

**Status: implemented as a simplified approximation — exact source equations not yet pulled.**

N26 states relaxation is modeled "by simulating a random walk in the semimajor axis and
eccentricity parameter space (for the full equations, see S. Naoz et al. 2022; S. C. Rose
et al. 2022)" — again deferring the exact formula. S. C. Rose et al. 2022 (ApJL, 929, L22;
the paper N26's whole model derives from) states its own version explicitly:

> "We apply a small instantaneous velocity kick to the BH, denoted as $\Delta v$. We draw
> $\Delta v$ from a Gaussian distribution with average of zero and a standard deviation of
> $\Delta v_{\rm rlx}/\sqrt3$, where $\Delta v_{\rm rlx} = v_\bullet\sqrt{P_\bullet/t_{\rm
> rlx}}$ ... The new orbital parameters can be calculated following Lu & Naoz (2019), and
> see Naoz et al. (2022) for the full set of equations."

i.e. once per orbital period $P_\bullet$, perturb the BH's orbital velocity $v_\bullet$ by a
3D Gaussian kick with per-component standard deviation $\Delta v_{\rm rlx}/\sqrt3$, then
recompute the orbit. We implement the kick using standard, unambiguous two-body Kepler
mechanics: draw the orbital phase via a mean anomaly uniform in $[0,2\pi)$ (equivalent to
"weighted by time spent," since mean anomaly is uniform in time by definition), solve
Kepler's equation for position/velocity at that phase, add a kick vector of magnitude
$|\Delta v|$ drawn per the formula above with an **isotropic random 3D orientation** relative
to the local orbital frame (a simplification — the real geometry may correlate kick
direction with the orbital velocity direction, which our isotropic choice does not capture),
then recompute $(a,e)$ from the perturbed specific energy and angular momentum.

Lu & Naoz 2019 (MNRAS, 484, 1506, arXiv:1805.06897) and Naoz et al. 2022 (ApJL, 927, L18,
arXiv:2202.12303) have both since been pulled and read directly. Lu & Naoz 2019 derives new
post-kick orbital elements from the *same* underlying physics we already use —
energy/angular-momentum conservation given a velocity perturbation at a known orbital phase
(their Eqs. 9-19) — just expressed via an angle-parametrized closed form ($\theta,\alpha$
relative to the position/velocity vectors) rather than our direct vector approach. This
confirms our `orbital_dynamics` machinery is methodologically consistent with the cited
literature, not an ad hoc substitute. What Lu & Naoz 2019 does *not* resolve is our specific
simplification: their $\theta,\alpha$ are physical parameters tied to a known kick mechanism
(supernova natal kicks, with a specific direction relative to the binary), not a stochastic
ensemble with no preferred direction — so there is no "correct" value to look up for our
case. The isotropic-orientation choice remains a deliberate, reasonable simplification for a
kick source (many-body relaxation encounters, or an unknown-orientation GW-capture merger
plane) with no preferred direction, not an unresolved lookup.

**Source**: S. C. Rose et al. 2022, ApJL, 929, L22 (arXiv:2201.00022) for $\Delta v_{\rm rlx}$;
standard two-body orbital mechanics (vis-viva + angular momentum), cross-checked against
Lu & Naoz 2019's equivalent derivation, for the position/velocity and new-orbital-element
calculations.

**Implementation**: `imbh_nuclei.orbital_dynamics.{kepler_state, apply_velocity_kick,
relaxation_kick_sigma}`.

**Ambiguity note / flagged simplification**: the isotropic-kick-orientation assumption is
ours, not from any cited source — a placeholder pending a pass through Lu & Naoz 2019 /
Naoz et al. 2022 for the exact geometry. Likely a second-order effect on aggregate
statistics (many kicks over many orbits should average out orientation-dependent details),
but not verified. The same `apply_velocity_kick` machinery is reused for GW recoil kicks
(Eq. 13), where the orientation angles ($\Theta,\Theta_0,\xi$) *are* explicitly drawn
uniformly by N26 itself, so that application is not a simplification.

---

## Section 4.4 — Gravitational Wave Inspiral into the Supermassive Black Hole

**Status: implemented (standard Peters 1964 forms); stopping conditions confirmed against PDF (page 6).**

Orbit-averaged GW decay of semimajor axis and eccentricity (standard Peters & Mathews 1963 /
Peters 1964 result; N26 cites these papers for "changes to the orbital eccentricity and
semimajor axis due to GW emission" without restating the equations, so the well-established
closed forms are used directly):

$$
\left\langle\frac{da}{dt}\right\rangle = -\frac{64}{5}\frac{G^3 m_1 m_2 (m_1+m_2)}{c^5 a^3 (1-e^2)^{7/2}}\left(1 + \frac{73}{24}e^2 + \frac{37}{96}e^4\right)
$$

$$
\left\langle\frac{de}{dt}\right\rangle = -\frac{304}{15}\frac{G^3 m_1 m_2 (m_1+m_2)}{c^5 a^4 (1-e^2)^{5/2}}\, e\left(1 + \frac{121}{304}e^2\right)
$$

**Source**: P. C. Peters & J. Mathews 1963, PhRv, 131, 435 (GW luminosity of an eccentric
binary); P. C. Peters 1964, PhRv, 136, 1224 (orbit-averaged $da/dt$, $de/dt$, Eqs. 5.6-5.7 of
that paper).

**Stopping conditions** (confirmed exact from PDF):

- EMRI flag 1: orbital periapsis falls within $R_{\rm crit} = 8 G M_{\rm SMBH}/c^2$
- EMRI flag 2: remaining GW merger time with the SMBH is $< 100$ yr

**Implementation**: `imbh_nuclei.inspiral.{da_dt, de_dt, r_crit, remaining_merger_time,
is_emri}`.

**Ambiguity note**: N26 states the majority of BHs flagged as EMRIs "have already
circularized" and that excluding eccentric orbits changes the EMRI rate by "no more than a
factor of 2" — an explicit, quantified caveat from the authors themselves, carried into
`paper/limitations.md` verbatim rather than re-derived.

---

## Appendix (N26) — Comparison of BH Number Densities

Relevant to Phase 5 (SMBH mass scan): N26's Appendix compares the D. Aharon & H. B. Perets
2016 power-law BH density (adopted as Eq. 2, above) against the four-part piecewise Fokker-
Planck profile of B. Rom et al. 2024a. The two agree within an order of magnitude from
$10^{-3}$–$10^{-2}$ pc but diverge by up to three orders of magnitude by $0.1$ pc, where the
Rom et al. profile breaks and steepens — the break location depends on the assumed BH-to-
star number ratio $f_{\rm BH}$ (Rom et al. consider $10^{-4}$ and $10^{-3}$; N26 use $10^{-4}$
for their comparison plot, and note $f_{\rm BH}=10^{-3}$ would push the break outward, making
Rom et al.'s profile look more like Aharon & Perets'). N26 justify using the simpler power
law because dynamical timescales are $\gg 10$ Gyr outside 0.1 pc, so the disagreement there
doesn't affect their results. **Relevance to Phase 5**: the fixed numeric normalization
$n_0=10^4\,{\rm pc}^{-3}$ at $R_h=1$ pc is specific to the Milky Way's $M_\bullet=4\times10^6\,
M_\odot$ cluster; scaling to other SMBH masses requires either (a) assuming $n_0, R_h$ scale
with some literature $M_\bullet$–$R_h$ or $M_\bullet$–$N_{\rm BH}$ relation, or (b)
re-deriving the profile from the same Fokker-Planck approach at each mass — this is exactly
the kind of cited-relation choice Phase 5 needs to make explicit and source (see
`paper/limitations.md`).

---

## Open items log

Mirrors `paper/limitations.md` for anything that affects equation fidelity specifically.
**Resolved** items (confirmed directly from the PDF or a traced primary source) are kept
here for the historical record; only genuinely open interpretive choices remain live.

1. ~~BH number density normalization $n_0$~~ — **RESOLVED**: $n_0=10^4\,{\rm pc}^{-3}$,
   $R_h=1$ pc, given explicitly in N26 text (page 3).
2. ~~Velocity dispersion functional form~~ — **RESOLVED**: $\sigma=\sqrt{GM_\bullet/[(\alpha+1)r]}$,
   confirmed from PDF (page 2). **Still open**: which $\alpha$ to use in which context (see
   note under "Velocity dispersion profile" above) — resolved by interpretation, flagged.
3. ~~Holley-Bockelmann et al. 2008 kick constants~~ — **RESOLVED** via direct read of
   arXiv:0707.1334: $A=1.2\times10^4$, $B=-0.93$, $H=7.3\times10^3$, $K=6.0\times10^4$ km/s.
4. ~~$f_1(e_{\rm BH})$, $f_2(e_{\rm BH})$ functional form~~ — **RESOLVED** via direct read of
   Rose et al. 2020 (ApJ 904, 113), Eqs. 20-21 (hypergeometric functions).
5. **OPEN**: "Average object mass" $\langle M_{\rm avg}\rangle$ definition in Eq. 22 —
   resolved by assumption (number-weighted local mean of star + BH population masses), not
   confirmed textually.
6. **OPEN — new, high-priority**: Eq. 21 prefactor exponent. N26 prints $r_{\rm
   ISCO}^{1/3}$; the cited source (Volonteri et al. 2013) has $r_{\rm ISCO}^{1/2}$. We
   implement $1/2$. Flagged to user; could change Phase 3 max-spin reproduction.
7. **OPEN — new**: Eq. 19/20 notation clash ($\dot m_{\rm BH}$ vs. "$\Delta m_{\rm BH}$")
   resolved via dimensional analysis (rate $\times$ time).
