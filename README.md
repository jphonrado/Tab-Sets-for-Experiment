# Prepared tab sets for the browser-navigation experiment

This folder contains 75 static participant pages: fifteen each for Sports,
Animals, Nature, Science, and History. It preserves the repository's original
Content Set N/content N.M.html filenames.

| Folder | Topic | Use |
| --- | --- | --- |
| Content Set 1 | Sports | Set A in the current four-set schedule |
| Content Set 2 | Animals | Set B |
| Content Set 3 | Nature | Set C |
| Content Set 4 | Science | Set D |
| Content Set 5 | History | Extra set, outside the current scored experiment |

## Open a block

1. Use a separate study browser profile on the study laptop. Keep the version,
   window dimensions, display scaling, zoom, pointer settings, external mouse,
   and expanded vertical-panel width fixed as described in the paper.
2. Open index.html locally or with VS Code Live Server. Select the set and tab
   load. For one-click opening, allow pop-ups for the exact local address and
   click the large **OPEN ALL TABS** button. If only Study Start opens, return to the
   setup tab: the browser blocked the remaining tabs. Click **OPEN ALL TABS**
   again after allowing pop-ups, or use **Open next tab** once per page,
   returning to setup between clicks. The counter must reach 6/6 or 16/16.
   Retrying skips tabs already opened by this setup page.
3. Close the researcher setup tab and unrelated tabs. Put the study tabs in one
   dedicated window. Verify their actual order against the setup list and
   materials/manifest.json; browser settings can affect opening order.
4. Keep Study Start as the first tab in every block and session. Task positions exclude the
   neutral tab. There must be **6 total tabs at low load** and **16 at high load**.
5. Select the required horizontal/vertical orientation. Keep hover previews,
   grouping, pinning, tab search, and other prohibited aids disabled.
6. Activate **Study Start** before every trial. Reset the pointer and tab-list
   scroll position as required by the protocol. Play the prepared auditory
   prompt externally; do not open an additional browser tab for it.

**Close study tabs and reset** closes only the tabs opened by this setup page,
then unlocks the set and load choices. Refreshing setup loses its open-tab
tracking, so close leftover study tabs before preparing again after a refresh.

Live Server is convenient for previewing. For scored sessions, open the files
directly or use a plain static server without live-reload injection. Live
Server adds a reload script and a WebSocket connection to participant pages.
To use a plain local server, open a terminal in this repository and run:

    python -m http.server 5501 --bind 127.0.0.1

Then open http://127.0.0.1:5501/index.html in the study browser. Pop-up
permission is separate for each local address and port.

The setup page, files in materials/, source notes, and answer sheets are for
researchers only. Do not show them to participants. Participant pages contain
only a topic label, subject heading, paragraph, two key points, and a uniform
footer. The authored pages contain no target marks, page numbers, navigation
links, scripts, outside network requests, analytics, or performance
measurements. Development servers such as Live Server can inject their own code.

## Targets and trial scripts

Each set has five targets in files numbered 2, 5, 8, 11, and 14.
Those file numbers are not their high-load display positions. The manifest
provides a different fixed high-load order for each set, spreading targets
through the list and avoiding a common every-third-tab target pattern.
The low-load condition contains those same five pages in the same relative
order, without the ten additional pages. Every target appears once in the six
trials, and one target appears twice.

materials/targets-and-trials.md contains the target mapping and exact spoken
scripts. The first four sets use the six-trial sequences from the paper.
History has an extra suggested sequence. The scripts include the final “Go.”
cue; audio files have **not** been generated. Record and pilot the prompts with
consistent voice, pace, volume, and a consistent pause before the cue.

## What is controlled

- One layout, font, background, text structure, and favicon for all 75 pages.
- Individual 3-5-word titles with the subject at the beginning and concise,
  topic-specific wording. Generic introductory prefixes are not used.
- Similar introductory article lengths, clear subject names, and prompts that
  identify the subject directly without testing background trivia.
- Identical underlying titles, icons, pages, and prompts when a set is assigned
  to different conditions. Browser truncation is allowed to happen naturally.
- Targets spread through the high-load list, with the same low/high page
  relationships and trial counts. Residual position differences are distributed
  across conditions by the paper's content-set counterbalancing.
- Stable local files with no advertisements, changing titles, or external dependencies.

These are **matched draft materials, not demonstrated equivalent stimuli**.
Topics still differ in familiarity, word shapes, name lengths, semantic
similarity, and possibly difficulty. Character counts do not establish equal
rendered width in Chrome's tab bar. The shared favicon limits the task to a
common-icon setting rather than mixtures of website icons.

Before main-study collection, pilot prompt-to-full-title matching, inspect
actual title truncation on the macOS study laptop in all four conditions, and
review confusing items. Check whether errors or difficulty cluster in one set.
Revise material problems rather than tuning titles until one orientation wins
or until the two orientations perform identically. Keep content-set
counterbalancing across conditions. Freeze the final materials, title versions,
tab order, audio, and settings before the main study.

History is an extra pool. If it is later chosen for scored trials, update and
freeze the set-to-condition schedule before data collection. Do not expose any
scored set during practice. This package does not replace the paper's separate
practice materials or revise its four-condition design.

## Files for the group

- start.html: neutral page, with no target information.
- index.html: researcher-only preparation page.
- materials/targets-and-trials.md: answer sheet and spoken prompt scripts.
- materials/stimulus-audit.csv: title lengths, identifier positions, article
  word counts, target IDs, and low/high task positions.
- materials/trial-prompts.csv: one row per scheduled trial.
- materials/manifest.json: complete tab order and target mapping.
- materials/articles.json: editable article text and consulted sources.
- SOURCES.md: primary educational sources used to check introductory facts.
- assets/: shared styles, icon, and setup code.

To rebuild after editing article data, run python tools/build_content_sets.py
from this folder. Run python tools/validate_materials.py to check structure,
links, counts, schedules, and participant-page role leakage.
