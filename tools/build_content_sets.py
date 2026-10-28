"""Build offline study pages: python tools/build_content_sets.py."""
from pathlib import Path
import csv
import html
import json
import re
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
TARGET_SLOTS = [2, 5, 8, 11, 14]
HIGH_TARGET_RANKS = [
    [2, 4, 8, 11, 15], [1, 6, 9, 12, 14], [3, 5, 7, 10, 13],
    [2, 6, 8, 12, 15], [1, 4, 7, 11, 14],
]
TITLE_FORMATS = [0] * 15
TRIAL_ORDERS = [
    [1, 2, 1, 3, 4, 5], [2, 3, 4, 2, 5, 1],
    [3, 4, 5, 1, 3, 2], [4, 5, 1, 2, 3, 4],
    [5, 1, 2, 3, 5, 4],
]
TITLE_NAMES = ["subject first"]


def word_count(text):
    return len(re.findall(r"\b[\w]+(?:[-'][\w]+)*\b", text))


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def render_article(topic, item, title):
    esc = html.escape
    points = "\n".join(f"        <li>{esc(point)}</li>" for point in item["points"])
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <link rel="icon" type="image/svg+xml" href="../assets/favicon.svg">
  <link rel="stylesheet" href="../assets/study.css">
</head>
<body>
  <main class="article">
    <p class="eyebrow">{esc(topic)}</p>
    <h1>{esc(item["name"])}</h1>
    <p class="summary">{esc(item["summary"])}</p>
    <section aria-labelledby="key-points">
      <h2 id="key-points">Key points</h2>
      <ul>
{points}
      </ul>
    </section>
    <footer>Study reference page</footer>
  </main>
</body>
</html>
"""


def write_revision_report(manifest):
    baseline = json.loads((ROOT / "materials/revision-baseline.json").read_text(encoding="utf-8"))
    old = {page["path"]: page for page in baseline["pages"]}
    lines = [
        "# Title changes and audio recording checklist", "",
        f"Compared with GitHub commit `{baseline['commit']}`.", "",
        "All 20 scored target recordings (and five extra History targets, if used) must",
        "use the exact current title. Earlier subject-only recordings ending in 'Go'",
        "need replacement even when the tab title is unchanged. Record each unique",
        "target once and reuse that file for its repeated trial and across assignments.", "",
        "Start searching when the mask disappears. Do not record an auditory Go cue.", "",
        "## Changed scored target titles", "",
        "| Set | Target | File | Previous tab title | Current tab title |",
        "| --- | --- | --- | --- | --- |",
    ]
    for group in manifest["sets"][:4]:
        for page in group["pages"]:
            before = old[page["path"]]
            if page["target_id"] and before["title"] != page["title"]:
                lines.append(f"| {group['topic']} | {page['target_id']} | {page['path']} | {before['title']} | {page['title']} |")
    lines += ["", "## Exact current recording scripts", "",
              "| Set | Target | Subject | Exact recording script |",
              "| --- | --- | --- | --- |"]
    for group in manifest["sets"]:
        for page in group["pages"]:
            if page["target_id"]:
                lines.append(f"| {group['topic']}" + (" (extra)" if group["extra"] else "") +
                             f" | {page['target_id']} | {page['name']} | Target: {page['title']}. |")
    lines += ["", "## All changed page titles (including distractors)", "",
              "| File | Role | Previous title | Current title |", "| --- | --- | --- | --- |"]
    for group in manifest["sets"]:
        for page in group["pages"]:
            before = old[page["path"]]
            if before["title"] != page["title"]:
                lines.append(f"| {page['path']} | {page['target_id'] or 'Distractor'} | {before['title']} | {page['title']} |")
    lines += ["", "## Original subjects and positions retained", "",
              "This revision standardizes titles while retaining each original article,",
              "file, subject, target identity, six-trial sequence and task-tab position.",
              "Animal P1 remains Red Panda and P2 remains Fennec Fox. Capybara and",
              "Cheetah remain distractors; no articles or target subjects are swapped.",
              "The earlier proposed replacement position templates and animal target",
              "reassignments are superseded. Study Start is last (browser tab 6 or 16),",
              "so task position j now equals browser tab j rather than j+1.", ""]
    write(ROOT / "materials/audio-update-checklist.md", "\n".join(lines))


def write_position_tables(manifest):
    rows = [f"{group['paper_label']} ({group['topic']}) & " +
            " & ".join(map(str, group['high_target_positions'])) + r" \\"
            for group in manifest['sets'] if not group['extra']]
    assignments = [str(row['group']) + " & " +
                   " & ".join(row[key] for key in ['H-L', 'H-H', 'V-L', 'V-H']) + r" \\"
                   for row in manifest['condition_assignments']]
    text = r"""% Generated by tools/build_content_sets.py. Standard LaTeX; no extra packages.
\begin{table}[t]
\centering
\caption{Proposed target-tab positions in the high-load condition.}
\label{tab:target-positions}
\small
\begin{tabular}{lccccc}
\hline
Template (content set) & P1 & P2 & P3 & P4 & P5 \\
\hline
""" + "\n".join(rows) + r"""
\hline
\end{tabular}
\medskip
\begin{minipage}{\linewidth}
\footnotesize
\textit{Note.} P1--P5 identify target pages. Study Start is last: browser
tab 6 at low load or 16 at high load. Task position $j$ equals browser
tab $j$. Low load retains P1--P5 in positions 1--5; high load adds ten
distractors in predetermined positions. Tab order remains fixed within
each block. Each high-load template includes one unique target in each
band: 1--3, 4--6, 7--9, 10--12, and 13--15. Repeated-target trials add
another observation at the repeated target's position.
\end{minipage}
\end{table}

\begin{table}[t]
\centering
\caption{Proposed rotation of content sets and position templates across conditions.}
\label{tab:template-assignment}
\small
\begin{tabular}{ccccc}
\hline
Group & H--L & H--H & V--L & V--H \\
\hline
""" + "\n".join(assignments) + r"""
\hline
\end{tabular}
\medskip
\begin{minipage}{\linewidth}
\footnotesize
\textit{Note.} H--L = horizontal-low; H--H = horizontal-high;
V--L = vertical-low; V--H = vertical-high. Low load has five task
tabs plus Study Start; high load has fifteen plus Study Start. Allocate
participants equally across groups (four per group if $N=16$). This
table specifies material assignments, not chronological condition order.
Coordinate condition order and target-prompt schedules separately.
\end{minipage}
\end{table}
"""
    write(ROOT / 'materials/tab-position-tables.tex', text)


def main():
    data = json.loads((ROOT / "materials" / "articles.json").read_text(encoding="utf-8"))
    manifest = {
        "version": 2, "neutral_page": "start.html", "neutral_position": "last",
        "favicon": "assets/favicon.svg",
        "target_file_numbers": TARGET_SLOTS,
        "condition_assignments": [
            {"group": n + 1, **dict(zip(["H-L", "H-H", "V-L", "V-H"], row))}
            for n, row in enumerate([list("ABCD"), list("BCDA"), list("CDAB"), list("DABC")])
        ],
        "notes": [
            "Five task tabs plus one neutral tab at low load; fifteen plus one at high load.",
            "History is an extra set; the paper currently specifies four scored content sets.",
            "Stimulus matching is provisional until pilot testing.",
            "Study Start is last: browser tab 6 at low load or 16 at high load.",
            "Task positions equal browser tab numbers in a dedicated study window.",
            "Mask disappearance is the start cue; prompts contain the exact title and no Go.",
        ], "sets": [],
    }
    audit_rows, trials_rows = [], []
    source_lines = [
        "# Sources for the prepared pages", "",
        "The pages contain original summaries of stable, introductory facts. These primary",
        "educational sources were consulted during preparation. Sources are kept here for",
        "researchers rather than linked from participant pages, so the retrieval task",
        "cannot navigate away to outside sites.", "",
    ]
    guide = [
        "# Targets and six-trial prompt scripts", "",
        "**Researcher material: keep this document and the setup page out of view during trials.**", "",
        "Record each complete prompt in advance using the same voice, pace, volume,",
        "and a fixed pause after the exact-title cue. Do not include 'Go'.",
        "Mask disappearance is the sole start cue. These scripts are not audio recordings.",
        "Use the same recording for an item whenever its set is assigned to another condition.",
        "Return to Study Start and restore the pointer and tab-list scroll position before each trial.",
        "Never open or close task tabs during a scored trial.", "",
        "P1-P5 identify targets in the research record only, never on participant pages.",
        "Low-load pages retain their relative order from the high-load list.", "",
        "Study Start is last (browser tab 6 or 16); task positions equal browser tab numbers.",
        "Any controller that previously selected tab 1 for reset must be updated.", "",
    ]
    for set_number, dataset in enumerate(data["sets"], 1):
        topic = dataset["topic"]
        if len(dataset["items"]) != 15:
            raise ValueError(f"{topic} must contain fifteen articles")
        high_order = [None] * 15
        for file_number, rank in zip(TARGET_SLOTS, HIGH_TARGET_RANKS[set_number - 1]):
            high_order[rank - 1] = file_number
        additional_pages = iter(slot for slot in range(1, 16) if slot not in TARGET_SLOTS)
        high_order = [next(additional_pages) if slot is None else slot for slot in high_order]
        high_position = {slot: rank for rank, slot in enumerate(high_order, 1)}
        page_records = []
        guide += [
            f"## Set {set_number}: {topic}" + (" (extra)" if set_number == 5 else ""), "",
            "| Target | Subject | File | High-load task position | Low-load task position |",
            "| --- | --- | --- | --- | --- |",
        ]
        for slot, item in enumerate(dataset["items"], 1):
            format_id = TITLE_FORMATS[slot - 1]
            title = item["title"]
            relative = f"Content Set {set_number}/content {set_number}.{slot}.html"
            target_id = f"P{TARGET_SLOTS.index(slot) + 1}" if slot in TARGET_SLOTS else None
            low_rank = TARGET_SLOTS.index(slot) + 1 if target_id else None
            record = {
                "slot": slot, "path": relative, "name": item["name"], "title": title,
                "title_format": format_id, "target_id": target_id,
                "low_load_position": low_rank, "high_load_position": high_position[slot],
            }
            page_records.append(record)
            write(ROOT / relative, render_article(topic, item, title))
            lengths = [word_count(item["summary"])] + [word_count(p) for p in item["points"]]
            audit_rows.append({
                "set": set_number, "topic": topic, "path": relative, "subject": item["name"],
                "target": target_id or "", "title": title, "title_characters": len(title),
                "identifier_characters": len(item["name"]), "title_format": TITLE_NAMES[format_id],
                "identifier_start_character": title.index(item["name"]) + 1,
                "summary_words": lengths[0], "point_1_words": lengths[1],
                "point_2_words": lengths[2], "article_words": sum(lengths),
                "high_load_task_position": high_position[slot], "low_load_task_position": low_rank or "",
            })
            if target_id:
                guide.append(f"| {target_id} | {item['name']} | {relative} | {high_position[slot]} | {low_rank} |")
        target_pages = [page_records[slot - 1] for slot in TARGET_SLOTS]
        trial_records = []
        guide += ["", "| Trial | Target | Exact spoken prompt |", "| --- | --- | --- |"]
        for trial, target_number in enumerate(TRIAL_ORDERS[set_number - 1], 1):
            target_page = target_pages[target_number - 1]
            prompt = f"Target: {target_page['title']}."
            trial_record = {
                "trial": trial, "target_id": f"P{target_number}", "path": target_page["path"],
                "subject": target_page["name"], "title": target_page["title"], "prompt": prompt,
            }
            trial_records.append(trial_record)
            trials_rows.append({"set": set_number, "topic": topic, **trial_record})
            guide.append(f"| {trial} | P{target_number} | {prompt} |")
        guide += ["", "High-load file order: " + ", ".join(map(str, high_order)) + ".",
                  "Low-load file order: " + ", ".join(map(str, TARGET_SLOTS)) + ".",
                  "Study Start follows all task tabs and is the last browser tab.", ""]
        manifest["sets"].append({
            "number": set_number, "topic": topic,
            "paper_label": chr(64 + set_number) if set_number < 5 else None,
            "extra": set_number == 5, "pages": page_records,
            "high_target_positions": HIGH_TARGET_RANKS[set_number - 1],
            "position_template": chr(64 + set_number) if set_number < 5 else "extra",
            "low_load": [page["path"] for page in target_pages],
            "high_load": [page_records[slot - 1]["path"] for slot in high_order], "trials": trial_records,
            "launch_order": {
                "low_load": [page["path"] for page in target_pages] + ["start.html"],
                "high_load": [page_records[slot - 1]["path"] for slot in high_order] + ["start.html"],
            },
        })
        source_lines += [f"## {topic}", ""]
        for source in dataset["sources"]:
            source_lines.append(f"- [{source['title']}]({source['url']})")
        source_lines.append("")
    for filename, rows in [("stimulus-audit.csv", audit_rows), ("trial-prompts.csv", trials_rows)]:
        with (ROOT / "materials" / filename).open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
    write(ROOT / "materials" / "manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    write(ROOT / "assets" / "manifest.js", "window.STUDY_MATERIALS = " + json.dumps(manifest, ensure_ascii=False, indent=2) + ";\n")
    write(ROOT / "materials" / "targets-and-trials.md", "\n".join(guide) + "\n")
    write(ROOT / "SOURCES.md", "\n".join(source_lines) + "\n")
    stats = {}
    for dataset in data["sets"]:
        rows = [row for row in audit_rows if row["topic"] == dataset["topic"]]
        stats[dataset["topic"]] = {
            "pages": len(rows), "targets": sum(bool(row["target"]) for row in rows),
            "article_words": [min(row["article_words"] for row in rows), max(row["article_words"] for row in rows)],
            "title_characters": [min(row["title_characters"] for row in rows), max(row["title_characters"] for row in rows)],
            "mean_title_characters": round(mean(row["title_characters"] for row in rows), 1),
            "mean_target_title_characters": round(mean(row["title_characters"] for row in rows if row["target"]), 1),
            "mean_distractor_title_characters": round(mean(row["title_characters"] for row in rows if not row["target"]), 1),
        }
    write(ROOT / "materials" / "construction-summary.json", json.dumps(stats, indent=2) + "\n")
    write_revision_report(manifest)
    write_position_tables(manifest)
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
