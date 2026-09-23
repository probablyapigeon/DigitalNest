# DigitalNest Windows release verification - 2026-09-23

- Fresh repository test run: 31 tests passed in 52.033 seconds.
- PyInstaller 6.22.0 / Python 3.14.6 / Windows 11 x64 build succeeded.
- Actual frozen executable self-test passed: both XC runtimes and program data,
  HTTP web assets, opening progression, new-world creation, construction costs,
  authored offline chat, and exact save reload. The test used an isolated save.
- Frozen Tk launcher widget creation check passed with exit code 0.
- Player saves, QA profiles, virtual environments and generated outputs are excluded
  from Git. Public source was checked for credential patterns and private paths.
- Windows 10 is a build target but has not been separately tested on this machine.
- Browser visual and spoken-reply verification from the local builder release is
  recorded in the project tests and README; these were not rerun inside a new PC.

The following records describe earlier development milestones.

# First playable slice — 2026-09-22

## LonkWorld XC society update

Final `python -m unittest discover -s tests -v`: **16 tests passed** in 48.278 seconds.
`node --check web/app.js` passed.

The social suite covers word learning and associations, actual bird-to-bird teaching,
internal innovation without fabricated external experience, learning-based stages,
multiple reciprocal partnerships, named colonies, independent inherited language,
bounded trait variation, exact combined save/resume with descendants, population limits,
nonlethal automatic nursery construction, and schema-1 migration with a backup.

The real-browser society walkthrough passed teaching six phrases to the flock,
graduation, arranged visits, a reciprocal partnership, colony formation, manual nursery
construction, descendant selection, vocabulary inheritance, reload, and desktop/mobile
layout with no JavaScript exceptions. Both screenshots were visually inspected.
The original opening walkthrough also passed against the social build.

A copy of the actual player save migrated without changing any existing game records
or LUMINA checkpoints; backup creation and an exact reload passed. The original
`LonkWorld.xc` and its vendored copy have identical SHA-256 hashes.

A real local Qwen3 4B reply for Wren used inherited words including "boop", "home",
"moonberry", and "feather" and completed in 6.61 seconds. It also invented a practice
event, so general LLM dialogue is still not a reliable factual narrator. It cannot
change world state; authoritative culture, lineage, and progression remain in the UI.

The browser nursery test initially raced autonomous part consumption. The server
correctly rejected insufficient resources; controls now refresh immediately after
rejection. The deterministic nursery walkthrough pauses the world before construction.

## Original slice checks

Fresh local checks on Windows / Python 3.14.6 / Node 24.19.0:

- `python -m unittest discover -s tests -v`: 10 passing tests. Covers gated repair,
  reward duplication prevention, exact full-brain save/resume and subsequent replay,
  cassette action order changing XC state, song transmission, 100 habitat ticks of
  bounded growth and self-maintenance, corrupt-save preservation, local HTTP origin
  protection, authored progression facts, and offline chat fallback.
- `node --check web/app.js`: passed.
- Chrome headless walkthrough at 1440×1080 and 390×844: opening sequence through
  heater repair, selection, journal, lattice inspector, authored chat, and saved progress
  after reload passed. No JavaScript exceptions or horizontal page overflow.
- Desktop and mobile screenshots were visually inspected.
- Actual Ollama `qwen3:4b-instruct` replies passed through `/api/chat`: Pip answered
  about washers in 15.51 seconds including model startup; Moss answered a construction
  question in 2.54 seconds with the model warm. These are two observations, not a
  representative latency benchmark. Replies remain imperfect and need further character tuning.

The original supplied runtime/core are vendored unchanged. Existing XEMBRA/LUMINA
projects and personal brain files were not edited. Browser verification uses isolated
`.qa` saves, separate from `%LOCALAPPDATA%\LittleFlock\save.json`.

Not verified: Steam packaging, distribution rights, other PCs, long-session performance,
spoken voice, controller support, accessibility with a screen reader, or a complete campaign.
