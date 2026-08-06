Subject: Independent reimplementation of Newton et al. (2026) — validation results and two questions on Eqs. 21/22

Dear Dr. Newton, Prof. Rasio, and coauthors,

Over the past few weeks I independently reimplemented the IMBH-formation model from your recent
paper (Newton et al. 2026, ApJ 1006:184), rebuilding every equation from scratch and validating
against your Table 1. Validation is largely successful — bulk population statistics (including
the fraction of BHs exceeding 100 $M_\odot$) reproduce well across all four initial conditions,
though the heavier H18 family's extreme upper mass tail runs hotter than Table 1 for reasons I
can trace mechanistically but haven't fully resolved.

Along the way I ran into two textual ambiguities, plus one gap, I'd value your take on: Eq. 21's
spin-change prefactor exponent (printed as 1/3, but 1/2 in the Volonteri et al. 2013 formula it
cites), Eq. 22's $\langle M_{\rm avg}\rangle$/$\rho$ definition (star-only vs. BH-inclusive — a
choice that turns out to control nearly every result I get downstream, including both of your
Section 5.4 open questions, which I attempted with the validated pipeline), and where initial
BH orbital properties ($a_\bullet$, $e_\bullet$) should be sampled from, which Section 3 never
actually states.

Full detail on both, plus the validation numbers and the Section 5.4 extensions, is in the
attached memo. Code, tests, and a complete log of every judgment call are public at
https://github.com/Menrae/imbh-galactic-nuclei. I'd very much appreciate your read on the two
ambiguities, and I'm happy to share anything else that would help.

Best regards,
Armeen Shasti-Nazem
University of Washington
aashasti@uw.edu
(425) 919-8596
