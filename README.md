# DigitalNest

A playable local prototype about four robot birds and the human who becomes their person.

## Download and play on Windows

[Download the latest Windows release](https://github.com/probablyapigeon/DigitalNest/releases/latest).
Choose **DigitalNest-Windows-x64.zip**, extract the entire archive, and open
**DigitalNest.exe** inside the DigitalNest folder. Keep the `_internal` folder
beside the executable. Python installation is not required for this build.
The launcher opens the local browser game; close its window to stop the server
it started. If your station was already running, it reuses it and leaves it running.

This first build targets Windows 10/11 x64 and is unsigned. Saves stay in
`%LOCALAPPDATA%/LittleFlock/save.json`, so existing Little Flock progress is retained.
No personal saves are included in the download. The game works offline; full LLM
chat optionally uses a separately installed Ollama with `qwen3:4b-instruct`.
Spoken replies use available local browser/system voices.

## Run from source

Double-click **Start Little Flock.cmd**. It starts a hidden Python server and opens
http://127.0.0.1:8877. Python 3.10+ is required; no Python packages or frontend build are needed.
The launcher reuses an already running Little Flock server. The server stays available
after closing the browser, but the habitat rests when the page is inactive.

For a visible server you can stop with Ctrl+C:

```
python server.py --open
```

Follow the project card: wake Pip, inspect his wing, collect the servo, repair him,
open the habitat, recover the cassette, and share the home tune. Choose whether to
reassure Pip before listening. Tune the three channels to 2, 4, 3.

Select Pip, Moss, Zip, Alto, or a descendant to see their relationships and actual LUMINA lattice.
Give parts, whistle, and watch the flock gather, build perches, recharge, and spread
the tune through contact. Sound is opt-in. All controls have button equivalents;
the canvas is not required for interaction. Reduced-motion preferences are respected.

## Language and flock society

Open **Language & flock life** after opening the habitat. Teach a phrase to the
selected bird or everyone. Ordinary chat messages also teach the selected bird.
The original `LonkWorld.xc` procedures learn words, associations, phrase fragments,
origins, and private invented wordplay. Birds teach one another in autonomous
reciprocal conversations; **Arrange a visit** invites a specific pair to converse.

Stages depend on learning, not elapsed age: hatchling → apprentice → storyteller →
graduate. Graduation requires at least 12 learned words and 6 conversations.
Repeated mutual conversations can form reciprocal, nonexclusive partnerships.
Compatible graduates join or found named colonies. The panel shows vocabulary,
origins, associations, thoughts, stages, partners, colony membership, and family.

A graduate in a colony with nest level 2+ and 3 spare parts can **Build a hatchling**.
The parent remains. The child inherits an independent copy of the parent's learned
language, gains varied personality traits, and starts with zero personal conversations
and a new LUMINA brain. Colony membership and parent IDs follow the original XC
inheritance procedure. There are at most eight birds. Parents rest 20 station minutes
between projects. Every 12 ticks the habitat also checks for an eligible autonomous
nursery project, at least 20 ticks after the parent's graduation.

The household's existing maintenance clock supplies time; the original LonkWorld
age-death, violence, and replacement-rebirth loop is not run. Its actual XC language,
reflection, development, society and inheritance procedures are run. Autonomous
conversations also deliver a MusicPulse experience to listeners' LUMINA brains.

## Growing memories and bird-built worlds (source update)

For the existing local `source/little-flock` installation, run **Apply Local Update.cmd**
from this repository. It backs up the current code and save, replaces the local
server, and opens the game. The updated local installation has been verified
running with the existing flock and language archives. Failure rollback has not
been exercised end to end.

Each bird now keeps a personal SQLite language archive with no fixed word-count
ceiling. The 256-word XC vocabulary is a working set; relevant archived words and
experiences are retrieved for conversation using the bird's existing LUMINA node
state. Descendants inherit the larger word/association archive. Chat changes their
memories and prompts, not the weights of Qwen. This does not create independent
kernels per concept node. Storage still depends on available disk space.

The gameplay Heart model responds to interactions and energy, influences rest and
conversation tone, and recovers over simulated time. Its 90-second smoothing uses
elapsed simulation time; pausing freezes it. It is a fictional emotional model.

Select a bird and use **Design your own world** in **A little life of their own**.
They reserve and collect eight personal parts, build a connected world, and head
there. Established graduates can initiate projects themselves after the 48-tick
world-building cooldown. Nursery needs and rest retain priority. The existing
**New world** control spends station supplies for player-created worlds. The
station currently supports 18 connected worlds.

World artwork is procedural: saved palettes, skyline shapes, floor patterns and
creator emblems vary with the creator, local save-folder identity, game instance,
and world identity. Bird traits and remembered words influence the design. Reloads
preserve the artwork. These are variations of the existing illustrated themes,
not unrestricted AI image generation or a cloud account identity.

**Natural conversations** lets nearby birds use the shared local Qwen model for
short reciprocal exchanges. While the page is active, the server checks every 45
seconds; player chat takes priority. Birds that move apart before completion do
not deliver the exchange. Offline learned conversations continue if the model is
unavailable or a generated line repeats. Turn on **Voices** to hear room chatter
when a local browser voice is available.

Back up `save.json` together with its matching `save.<identity>.language.sqlite3`
file in `%LOCALAPPDATA%/LittleFlock`, while the server is stopped. Saves carry a
replayable outbox so interrupted archive commits recover without double-counting.
Missing or mismatched archive files cause startup to stop rather than silently
forget memories. Upgrading imports vocabulary and player messages still retained
by the old save; previously discarded language cannot be reconstructed.

These source features are newer than the published v0.1.0 Windows download.

## Chat and privacy

The optional chat renderer uses local Ollama at 127.0.0.1:11434 with
`qwen3:4b-instruct`. No remote AI service is contacted. If unavailable, authored
offline replies work and all game progression remains available. Critical wing,
repair, and cassette questions use authored game facts. Other model dialogue may
still invent details; it has no tools and cannot change inventory or quest flags.
Player favorite movie/song statements are stored as explicit preferences.

World state, journal, preferences, recent conversations, and complete XC checkpoints
stay in `%LOCALAPPDATA%\LittleFlock\save.json`; growing language archives live in
the matching SQLite file described above. JSON saves use atomic replacement for
the world and every bird's brains. A malformed save is preserved and startup fails
with a diagnostic rather than replacing it. There is no offline neglect mechanic.

Schema-1 saves migrate to schema 2 while preserving existing game records and exact
LUMINA checkpoints. A `save.before-society.json` backup is made before the first
updated save. Schema 2 includes the complete LonkWorld records, RNG state, source
hash, stable bird IDs, colonies, language, genealogy, and per-bird LUMINA checkpoints.
Stored real player chat messages seed the migrated vocabulary; model replies are not
replayed as real player experiences.

## What is real in this prototype

- Each bird has an independent instance of the supplied LUMINA XC runtime and core,
  with a distinct fixed seed. The original matrices, policies, memory, and bounded
  structural morphogenesis execute on every committed bird experience.
- XC-selected actions influence routines; energy and construction needs take priority.
- Nodes and links in the inspector come from the actual persistent runtime graph.
- The habitat is a new discrete game simulation. It does not run the bridge's 600-vertex
  mesh or its expensive research counterfactual suite.
- Relationships, nests, song transmission, energy and inventory are explicit game rules.
  These are developmental and self-maintenance mechanics, not biological life or evidence
  of consciousness. Descendants inherit language and varied traits; this is not a
  claim of open-ended biological evolution or natural selection.
- Six connected illustrated spaces, four founding birds and up to four descendants, one memory cassette,
  procedural canvas art, synthesized chirps.
  Optional local browser speech; no Steam integration, packaged standalone executable, or complete campaign yet.

## Verify

```
python -m unittest discover -s tests -v
node --check web/app.js
```

`tests/browser-smoke.mjs` is an optional Chrome DevTools smoke test for an isolated
test server on port 8878 and a debugging browser on port 9334. It does not touch
the normal player save.
`tests/browser-society.mjs` continues that fixture through teaching, graduation,
visits, partnerships, colony formation, hatchling inheritance, and mobile/reload checks.

## Provenance

`vendor/xc.py` and `vendor/lumina_core.xc` were copied unchanged from the supplied
LUMINA_XC_LIVE_BRIDGE_v0.3.2-coupled-environment archive. See `vendor/PROVENANCE.md`.
`vendor/lonkworld` contains the supplied LonkWorld XC procedure host and application;
its provenance file records the small package-import and in-memory-load adaptations.
This is a local development prototype; redistribution rights for supplied code and
any bundled model must be established before a commercial release.


## Connected worlds

World map opens six habitat cards connected by seven reciprocal portal routes.
Open cards or neighboring portal buttons to browse. Follow tracks the selected
bird; Invite here queues a saved journey, one portal per station tick, followed
by a short stay. Pausing pauses travel too. Pin world adds resident previews below
the habitat; unpin with the close button. The map scrolls on small screens and
supports dragging its background. All room buttons support keyboard navigation.

Room assignment, current journey and last crossing are stored with the same bird
record. Existing saves derive initial rooms from existing activities without
rewriting the LUMINA checkpoints or LonkWorld identities. Birds make autonomous
room visits; the original XC social simulation still operates across the station,
including conversations across rooms. There are eight berths across the whole
flock. This release uses procedural Canvas artwork, not the painted concept art.
No Docker installation or engine is required.

Room regression checks: `python -m unittest discover -s tests -p test_spaces.py -v`.
Browser room checks: `node tests/browser-worlds.mjs` against an isolated server on
8878 and a headless Chrome debugging session on 9334, after the opening smoke test.


## Parts, room objects, and voices

The Parts Tray has Build toy (2 parts) and Share 1 part controls. Toys restore a
little charge and stimulate the bird's saved LUMINA structure. Birds with all five
perches and six or more parts automatically turn spare parts into toys on their
scheduled autonomous turn, so full trays still have a use.

Each world has two labeled clickable objects, with matching accessible buttons in
Things to do together below the habitat. Objects show costs, prerequisites and
cooldowns. Invite the selected bird into the room first. Birds use these same
objects autonomously, at most one bird per station tick. Uses and improvements
persist; nursery hatchlings still require the existing colony and resource rules.

New real XC utterances, saved reflective thoughts, object activity and user chats
appear as habitat bubbles and in the room transcript. Mobile shows one bubble at
a time. The latest 80 events are retained, without replaying old audio on reload.
Existing cross-room XC social exchanges remain possible; the speaker's room is
recorded with each line. Printed phrases retain the latest 20 archive entries.

Voices is an opt-in ambient chatter control separate from synthesized chirps. Direct chat replies are read aloud by default; the checkbox below chat mutes them and remembers your preference. It uses installed
local English browser/OS voices, with different pitch and rate per bird. It does
not clone character voices or require another model. Ambient speech is limited to the viewed room. Direct chat replies speak even while the simulation is paused or the bird is in another room, and take priority over ambient chatter. Thoughts remain silent. Muting replies or hiding the tab stops reply speech; pausing or changing rooms stops ambient chatter. Missing local voices leave text
and chirps available. Browser support: https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesis

Verification adds test_life.py, browser-life.mjs and browser-voice.mjs. The latter
uses a real CDP mouse click to satisfy the browser's speech activation requirement.


## World building

Click Build above the habitat to build or upgrade six permanent structures:
solar canopies, flower terraces, cozy shelters, parts recyclers, story perches,
and wind chimes. Choose station supplies or the selected resident bird's parts.
Each recipe occupies one of six plots per world and supports three levels.
Structures appear in both the habitat and map previews, and become usable room
objects. Solar canopies also passively restore resident charge each tick.

Birds with completed nests use their own parts to build and upgrade during their
scheduled autonomous turn; eligible nursery parents retain priority for breeding.
When their current world is fully improved, full trays can still become toys.

New world creates a named world with one of six scenery/activity themes and a
two-way portal to your chosen existing world. New worlds cost 8 station parts.
The station starts with 24 building parts. Salvage 4 more from the Build panel
on a two-tick cooldown, or donate parts from a bird's tray. Up to 18 worlds fit
in this prototype. The existing eight-bird population limit is unchanged.
Birds explore custom worlds on their own and can be invited to them; long trips
continue to their destination before their visit timer starts.

Every object hotspot now opens an inspector instead of showing a disabled help
cursor. Use myself spends station supplies, operates empty rooms, and can store
charge for arriving birds. Ask bird uses that bird's resources and displays the
specific prerequisite if unavailable. Incubators still need an eligible parent.

Topology, structures, upgrades, builders, supplies, visits and object uses share
the atomic world save. Original LUMINA checkpoints and language identities are
preserved. Invalid saved portal graphs fail safely without replacing the file.

Additional checks: tests/test_building.py and tests/browser-building.mjs.


## Build the Windows program

On Windows with Python 3.14 installed:

```powershell
./build-windows.ps1
```

The script creates an isolated build environment, installs the pinned PyInstaller
build tool, bundles Python, both XC sources and the web assets, and runs an isolated
HTTP/save self-test against the actual executable. Output:
`release/DigitalNest-Windows-x64.zip` and `release/SHA256SUMS.txt`.
GitHub Actions also tests and packages pushes to main and pull requests.

Maintainer checks:

```powershell
python -m unittest discover -s tests -v
python desktop.py --self-test .qa/source-check.json
./dist/DigitalNest/DigitalNest.exe --self-test .qa/exe-check.json
```

The public repository intentionally excludes player saves, QA browser profiles,
logs, local Python environments, and generated release binaries. Vendored XC
provenance is recorded under `vendor/`; no additional license grant is implied.


### Original Lonk life in the habitat

The local source now connects the original XC emotional controller to daily bird
choices. LUMINA policies supply stimuli; Lonk impulses guide exploration, rest,
reflection, and playful contests. Territory visits influence traits. Mature
parents reserve nursery supplies before spending parts on other projects.

Select a bird and look below its parts tray for **A little life of their own**:
find and keep original Lonk items, give a keepsake to a nearby friend, share a
remembered message, dream, hug, or hold a leaf duel. Actions have a two-tick
cooldown; resume a paused world to advance it. Collections, catchphrases, rivals,
feelings, and remembered gifts persist. Friends must share a room for these
social actions. A small gold sparkle marks a bird carrying a favorite treasure.
Chat receives these actual experiences as context; the offline response can
mention a real collected treasure. Ambient speech still uses the Voices control.

This is an adaptation of the original sandbox: leaf duels do not cause injuries,
and nursery descendants coexist with their parents. The old death/rebirth loop
is not enabled. The published v0.1.0 download predates this source update.


### Conversation recovery

Direct chat uses a compact, grounded Qwen prompt and removes repeated assistant
examples from its inference context. Catchphrase-only answers and recycled lines
are rejected, with one clean model retry. A persistent flock-wide phrase ledger
blocks exact repeated sentences despite punctuation/case differences, including
after the visible chat history expires. Existing retained speech is imported;
older discarded history cannot be reconstructed. The check matches wording, not
semantic equivalence, and ordinary words may recur. Explicit Read last reply is
still available when the player wants a replay.

If both model attempts fail and no unused offline response is available, the bird
listens quietly instead of producing another canned response. Automatic learned
conversations now pair birds physically sharing a room. These ambient exchanges
remain native XC word-association speech; Qwen currently serves direct player chat.
