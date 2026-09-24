## Evolving worlds update (2026-09-23)

Local follow-up: port 8877 reports `evolving-worlds-9`. All 17 deployed runtime
files match the tested source byte for byte. The existing eight birds are present,
the station is unpaused, personal archives contain learned words, and the server
error log is empty. Timestamped pre-update backups are present. The update helper
passes PowerShell parser validation; its failure rollback remains untested.

- Backend coverage: 63 tests, including 11 archive/Heart/world-project tests and
  four ambient-conversation tests. The checkpoint-order fixture now copies the
  matching archive when creating an independent save branch.
- More than 600 words retained while XC stays at 256 active words; older-word
  retrieval and descendant inheritance exercised. Interrupted archive commit
  replays once; missing archives fail without replacing the JSON save.
- Heart recovery over 90 seconds matches nine 10-second updates. Pausing freezes
  dynamics, archive activity and project progress.
- Bird-funded construction spends eight personal parts, reserves them against toy
  spending, creates reciprocal portals and preserves its saved visual identity.
- `node tests/browser-evolving-worlds.mjs`: passed against isolated port 8878.
  Verified differing Canvas pixels for Pip/Moss gardens, deterministic reload,
  selected-bird project controls, natural-conversation toggle, mobile width and no
  JavaScript exceptions. Desktop, mobile and both garden images were inspected.
- JS syntax checks for app, life, worlds and space-art passed; diff whitespace
  checks passed.
- Actual local `qwen3:4b-instruct` returned a parsed two-line reciprocal exchange.
  A separate generated exchange was rejected by the freshness check as intended;
  this is smoke coverage, not a dialogue-quality or latency benchmark.
- Isolated migration of the existing eight-bird save retained exact LUMINA
  checkpoints. Initial archive counts ranged from 256 to 312 words per bird;
  the following simulation tick and reload succeeded.

The artwork is procedural variation within existing themes. Independent kernels
per concept node, long-session growth/performance, new packaged executables, and
publication to GitHub/Steam were not part of this update. Browser/system audio
availability still varies; this pass verified conversation text and delivery,
not audible voice playback.

## Conversation recovery and visible exchanges ? 2026-09-23

- Full Python suite: 48 tests passed in 79.425 seconds; final conversation checks
  also pass after tightening the embedded-catchphrase check.
- Real installed Qwen: three distinct replies to the reported window/poop/shiny
  prompts on an isolated snapshot, approximately 6.0, 2.0, and 2.4 seconds.
- Repetition ledger tested across save/reload, visible-history expiry, case and
  punctuation changes, embedded repeated sentences, and concurrent live admission.
- HTTP tests verify rejected duplicates do not enter chat history or voice events.
- Native automatic conversation pairs restricted to physical room membership;
  cassette tradition continues spreading during actual nearby exchanges.
- Existing eight-bird save roundtrip and ledger migration checked on a copy.
- Browser script added, JavaScript syntax checked. Headless-browser launch was
  rejected by automatic approval review with only 'blocked by policy'; this
  browser execution remains unverified. No request for broader permission made.
- One earlier HTTP test attempt had a Windows connection-aborted error; focused
  rerun and full suite passed. One real cassette-learning regression was fixed.
- Local service verified as conversation-8; published v0.1.0 remains unchanged.

## Chatter repetition fix ? 2026-09-23

Gossip now selects observed topics and occasional real player quotes rather than
recursively quoting generated event memories. Recent six topics are excluded;
topic history persists. Direct-chat instructions discourage habitual recall
openings. Seven Lonk-life tests and three server tests pass. This does not
replace the native word-association generator with an LLM.

# Lonk life integration verification ? 2026-09-23

- Final Python suite: 37 tests passed in 87.762 seconds.
- Browser: selected bird collects, collection renders, local leaf duel sets rivals,
  reload preserves personal state, 390px mobile layout fits, no browser exceptions.
- Existing eight-bird player save: isolated exact roundtrip, new simulation tick,
  and subsequent reload passed.
- 80-tick exploratory run: distinct collections, native emotional impulses,
  autonomous descendant, and exact save roundtrip observed.
- Regression fixed: mature parents reserve nursery supplies instead of spending
  them on other activities. Existing nursery/inheritance test passes.
- Live local service reports lonk-life-6 and all eight player birds.
- Source changes are local; the published v0.1.0 binary has not been rebuilt.

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
