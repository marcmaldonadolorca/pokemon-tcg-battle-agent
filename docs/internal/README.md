# Internal working notes

This folder keeps the project's working log as it was written during the competition
(6–17 August 2026), mostly in Spanish. It is not needed to understand or run the code; the
[root README](../../README.md) is the summary. The work was done with an AI coding assistant
(Claude): the ticket tables name an owner for each step, where «Propietario» is me and «Claude»
is the assistant, which ran many of the measurements and the packaging. The gated decisions
(whether to enter, how much effort to put in, what to submit and under which rule) were mine and
are recorded as such.

**What is here.** [`DECISIONS.md`](DECISIONS.md) holds 18 numbered decisions (`PKM-001` to
`PKM-018`), each with what was measured, what was decided and what was discarded. The most
useful ones: `PKM-014`, where search on top of the larger network wins 0.859 against the
previous agent and the two levers add in log-odds; `PKM-006` and `PKM-012`, where a deck ranking
turns out to measure deck × pilot rather than the deck, and flips when the pilot changes;
`PKM-015`, on the two submitted lists chosen by different criteria (best mean vs best floor);
`PKM-002`, on why the engine is parallelised only with processes; and `PKM-018`, the root cause
of the missed final submission. [`TASKS.md`](TASKS.md) is the ticket table with its checklists.
[`reports/`](reports) has dated session reports: the intake (6 Aug), the search-budget sweep and
the 30-day imitation corpus (14 Aug), the heuristic → policy-clone jump (13 Aug), and the
post-mortem of the missed submission (17 Aug).
[`motor-cabt.md`](motor-cabt.md) documents the engine as verified locally,
[`empaquetado-y-envio.md`](empaquetado-y-envio.md) the submission package contract, and
[`reglas-y-calendario.md`](reglas-y-calendario.md) the rules and calendar of both calls. The
per-experiment lab notes live next to the code in
[`research/notas/`](../../research/notas).

**Reading the figures.** The rank written on 17 August (2,138th of 6,892, score 690.7) was
provisional. The final rank confirmed by the Kaggle API on 3 September, after the leaderboard
was recalculated, is **1,328th of 6,807**, score **773.9** with `c1-grimmsnarl`; notes have been
added where the provisional figure appears. File paths inside these notes refer to the
original layout (for example, `docs/empaquetado-y-envio.md` is now in this folder), and the
`scratchpad/` and `data/` paths they cite were never versioned.
