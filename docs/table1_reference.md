# Table 1 reference (Newton et al. 2026)

Transcribed directly from the published PDF (`references/Newton_2026_ApJ_1006_184.pdf`,
page 7) for use as the Phase 3 validation target. All runs use stellar profile
$\alpha_\star = 1.25$, $N=1000$ BHs, $M_\bullet = 4\times10^6\,M_\odot$, 10 Gyr integration.

| IC | Mergers | Max Mass BH [M☉] | Max Spin BH | BHs > 2×Mᵢ | BHs > 10×Mᵢ | % BHs > 100 M☉ |
| --- | --- | --- | --- | --- | --- | --- |
| K20 | 34 | 28.4 | 0.712 | 8 | 0 | 0% |
| K20+M | 30 | 57.8 | 0.844 | 12 | 0 | 0% |
| H18 | 371 | 407.3 | 0.805 | 79 | 4 | 7.8% |
| H18+M | 535 | 526.0 | 0.855 | 103 | 8 | 14.3% |
| H18* | N/A | 123.7 | 0.196 | 0 | 0 | 2.3% |

**Table note (verbatim, paraphrased for brevity)**: stellar profile $\alpha=1.25$ for all
runs. "Mergers" tallies total BH-BH GW captures over the simulation (some BHs merge
multiple times, i.e. multiple generations); H18* is the exception — it uses H18 initial
conditions but **only stellar collisions, no GW capture** (Section 5.1), so "Mergers" is
N/A for that row. ~4% of the H18+M population were already IMBHs ($>100\,M_\odot$) in the
*initial* conditions (primordial-merger products), so the 14.3% final figure includes that
initial fraction, not just newly-formed IMBHs.

## Other Section 5 numbers likely needed for Phase 3 (rates, not in Table 1 itself)

- K20: ~30 mergers with 1G BHs → merger rate a few $\times10^{-9}\,{\rm yr^{-1}}$ per
  Milky-Way-like galaxy; 2G+ mergers ~ few $\times10^{-10}\,{\rm yr^{-1}}$.
- K20+M: 1G rate ~$2\times10^{-9}\,{\rm yr^{-1}}$; 2G rate ~$5\times10^{-10}\,{\rm yr^{-1}}$;
  3G+ mergers occur (K20 has none).
- H18: ~150 mergers with 1G BHs → merger rate ~$10^{-8}\,{\rm yr^{-1}}$; 2G rate
  ~$5\times10^{-9}\,{\rm yr^{-1}}$.
- H18+M: 1G rate comparable to H18; 2G rate ~$10^{-8}\,{\rm yr^{-1}}$; 3G+ rate for both
  H18/H18+M up to ~$5\times10^{-9}\,{\rm yr^{-1}}$.
- EMRI rate (mass ratio $>5\times10^{-5}$): ~4 Gyr⁻¹ per Milky-Way-like galaxy, predominantly
  after ~2 Gyr. Mass ratio $>1\times10^{-4}$: ~4.8 Gyr⁻¹, predominantly after ~4 Gyr.
- All BHs with final mass $>400\,M_\odot$ become EMRIs; for H18 (H18+M), 70% (55%) of BHs
  $>200\,M_\odot$ become EMRIs.
- Highest-generation progenitor: 16G (H18+M), 12G (H18).
- Most massive BH formed across all simulations: 526 $M_\odot$ (H18+M, Table 1 max).
- IMBHs with mass $>10^4\,M_\odot$ do not form in situ for any initial condition tested.

## Figures referenced (not numeric, but relevant to Phase 3 qualitative comparison)

- Fig. 2: $\chi_f$ vs $\Delta m_{\rm BH}$ scatter + 16 sample random-walk paths, H18*
  only (stellar collisions only). Max collisions per BH: 194; all BHs had $\geq 2$
  collisions.
- Fig. 3: initial (gray) vs final (colored) mass and spin histograms, all four ICs.
- Fig. 4: same as Fig. 3 but for H18* (stellar-collision-only).
- Fig. 5: mass growth from BH-BH capture vs BH-star collisions, per BH; GW capture
  dominates mass growth in all four full (non-*) simulations.
- Fig. 6: mergers by highest-generation progenitor, per IC; primordial binaries increase
  the 2G merger rate by ~factor of 2 in both populations they're present in.
- Fig. 7: total merger mass vs merger time, color-coded by highest-generation progenitor.
- Fig. 8: $\chi_{\rm eff}$ vs primary mass $m_1$, color-coded by generation.
- Fig. 9: $\chi_{\rm eff}$ probability density by generation, per IC.
- Fig. 10 (Appendix): BH number density comparison, Aharon & Perets (2016) power law vs
  Rom et al. (2024a) piecewise Fokker-Planck profile — see `docs/equations.md`'s Appendix
  section for the numeric summary (order-of-magnitude agreement $10^{-3}$–$10^{-2}$ pc,
  diverging up to 3 orders of magnitude by 0.1 pc).
