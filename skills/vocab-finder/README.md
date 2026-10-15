# Vocab finder

An AI skill that finds candidate vocabulary terms for a biodiversity concept and writes a short comparison report.

Example: *"Which vocabulary term could I use for plant height?"*

It searches:

- **Darwin Core (TDWG)**: global standard field names
- **GBIF vocabularies**: global value lists for Darwin Core fields
- **TERN Parameters (via ARDC Research Vocabularies Australia)**: national observable properties

It is a quick search, not a full review. Always check the results before using them.

## Files

| File | Purpose |
|---|---|
| `SKILL.md` | Main instructions for the AI |
| `sources.md` | The sources and how to search them |
| `report.md` | The report layout |

## How to use it

The skill is a folder of plain-text instruction files. Most AI assistants can use it. Pick the option that matches your tool. If unsure, ask your AI assistant: *"How do I install this skill folder?"*

**Claude (claude.ai or Claude desktop app)**
1. Zip the `vocab-finder` folder.
2. Go to *Settings → Capabilities → Skills* and upload the zip.
3. Make sure web access / code execution is on, so it can reach the sources.

**Claude Code**
Copy the `vocab-finder` folder to `~/.claude/skills/` (just for you) or `.claude/skills/` in a project.

**Other AI tools** (e.g. ChatGPT, Copilot, Gemini)
If the tool supports skills, add the folder as a skill. Otherwise, upload or paste the three files and say: *"Follow SKILL.md to answer my question."*

The tool needs internet access to reach the sources listed in `sources.md`.

Then just ask, e.g.:
- *"Find vocabulary terms for plant height."*
- *"What values could I use for establishment means?"*
- *"Is there a standard term for life stage?"*

At the end, it will ask if you want the report saved as a Markdown (.md) file.

## Customising

You can add sources or update versions by editing `sources.md`. Each source needs: what it covers, the web address(es) to call, and where to find the PID.

- **Add another source**, e.g. the BDR vocabularies, Humboldt Extension, or other vocabularies on Research Vocabularies Australia.
- **Add other TERN vocabularies**: this version only includes TERN Parameters (release 2026-02-19). Other TERN vocabularies (e.g. categorical value lists) and later releases are published on [Research Vocabularies Australia](https://vocabs.ardc.edu.au/). Copy the SPARQL endpoint of that release into `sources.md`.

Keep the number of sources small so the skill stays quick.
