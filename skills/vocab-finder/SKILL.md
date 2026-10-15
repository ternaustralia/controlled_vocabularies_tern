---
name: vocab-finder
description: Find candidate vocabulary terms for a biodiversity concept (e.g. "plant height", "establishment means", "life stage") across Darwin Core/TDWG, GBIF and TERN (via ARDC RVA), then compare them in a short plain-language report. Use when someone asks which standard term, field or controlled value list to use, or how a local field maps to a recognised vocabulary.
---

# Vocab finder

Helps biodiversity data officers find suitable vocabulary terms and see how they compare. Users are not software engineers: use plain language and explain jargon briefly the first time (e.g. "PID: a persistent web address that identifies the term").

This is a **quick search**, not a full review. Be fast and use few requests.

## Steps

1. **Understand the request.** In one line, restate what is being looked for and whether it is:
   - a **property / field** (e.g. plant height, establishmentMeans), or
   - a **list of allowed values** (e.g. native, introduced).

   Ask a question only if the request is genuinely ambiguous. Use all sources in [sources.md](sources.md) unless the user names specific ones.

2. **Search each source** using only the calls in [sources.md](sources.md).
   - Fetch at most 20 candidate terms per search.
   - Aim for about 10 requests in total; never more than 15.
   - Never download whole vocabularies or large pages.
   - If a source fails or times out, say so in the report and continue.

3. **Shortlist and compare** the relevant matches. For each, judge:
   - **Fit**: exact, close, broader, narrower or related, based on the definition (not just the label).
   - **Level**: Global (Darwin Core/TDWG, GBIF) or National (TERN). Prefer Global, then National, when the fit is equal.
   - **Machine-readable**: does the term have its own PID, and is it published in a structured format?
   - **Extra signals**: units, existing mappings to other vocabularies, last modified date, deprecated status.

4. **Write the report** in chat using [report.md](report.md).

5. **Offer a file.** At the end, ask: "Would you like this report saved as a Markdown (.md) file?" Only create the file if they say yes.

## Rules

- Every PID/IRI in the report must come from a response received in this session. If you mention a term from your own knowledge, mark it **(not verified)**.
- Suggest, don't decide.
- For TERN, use only the ARDC RVA endpoint in [sources.md](sources.md).
- Always end the report with the disclaimer in [report.md](report.md).
