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


def main():
    data = json.loads((ROOT / "materials" / "articles.json").read_text(encoding="utf-8"))
    manifest = {
        "version": 1, "neutral_page": "start.html", "favicon": "assets/favicon.svg",
        "target_file_numbers": TARGET_SLOTS,
        "notes": [
            "Five task tabs plus one neutral tab at low load; fifteen plus one at high load.",
            "History is an extra set; the paper currently specifies four scored content sets.",
            "Stimulus matching is provisional until pilot testing.",
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
        "and pause before 'Go.' These are scripts, not generated audio recordings.",
        "Use the same recording for an item whenever its set is assigned to another condition.",
        "Return to Study Start and restore the pointer and tab-list scroll position before each trial.",
        "Never open or close task tabs during a scored trial.", "",
        "P1-P5 identify targets in the research record only, never on participant pages.",
        "Low-load pages retain their relative order from the high-load list.", "",
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
            prompt = f"Find the page about {target_page['name']}. Go."
            trial_record = {
                "trial": trial, "target_id": f"P{target_number}", "path": target_page["path"],
                "subject": target_page["name"], "prompt": prompt,
            }
            trial_records.append(trial_record)
            trials_rows.append({"set": set_number, "topic": topic, **trial_record})
            guide.append(f"| {trial} | P{target_number} | {prompt} |")
        guide += ["", "High-load file order: " + ", ".join(map(str, high_order)) + ".",
                  "Low-load file order: " + ", ".join(map(str, TARGET_SLOTS)) + ".",
                  "The neutral start tab is additional to these task-page counts.", ""]
        manifest["sets"].append({
            "number": set_number, "topic": topic,
            "paper_label": chr(64 + set_number) if set_number < 5 else None,
            "extra": set_number == 5, "pages": page_records,
            "high_target_positions": HIGH_TARGET_RANKS[set_number - 1],
            "low_load": [page["path"] for page in target_pages],
            "high_load": [page_records[slot - 1]["path"] for slot in high_order], "trials": trial_records,
        })
        source_lines += [f"## {topic}", ""]
        for source in dataset["sources"]:
            source_lines.append(f"- [{source['title']}]({source['url']})")
        source_lines.append("")
    for filename, rows in [("stimulus-audit.csv", audit_rows), ("trial-prompts.csv", trials_rows)]:
        with (ROOT / "materials" / filename).open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
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
        }
    write(ROOT / "materials" / "construction-summary.json", json.dumps(stats, indent=2) + "\n")
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
