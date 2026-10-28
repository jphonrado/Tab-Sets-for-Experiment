"""Check the experimental materials independently of the page builder."""
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.stack, self.nodes, self.links, self.tags = [], [], [], []
        self.feed(text)

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        self.tags.append(tag)
        if tag in {"link", "a", "script", "img", "iframe"}:
            self.links.append((tag, attrs))
        if tag not in {"meta", "link", "br", "hr", "img", "input"}:
            self.stack.append({"tag": tag, "attrs": attrs, "text": ""})

    def handle_data(self, text):
        for node in self.stack:
            node["text"] += text

    def handle_endtag(self, tag):
        if self.stack and self.stack[-1]["tag"] == tag:
            self.nodes.append(self.stack.pop())

    def node(self, tag, class_name=None):
        return [node for node in self.nodes if node["tag"] == tag and
                (class_name is None or node["attrs"].get("class") == class_name)]


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def words(text):
    return len(re.findall(r"\b[\w]+(?:[-'][\w]+)*\b", text))


def main():
    manifest = json.loads((ROOT / "materials/manifest.json").read_text(encoding="utf-8"))
    article_data = json.loads((ROOT / "materials/articles.json").read_text(encoding="utf-8"))["sets"]
    check([s["topic"] for s in manifest["sets"]] == ["Sports", "Animals", "Nature", "Science", "History"],
          "Unexpected topic order")
    expected_orders = [[1, 2, 1, 3, 4, 5], [2, 3, 4, 2, 5, 1],
                       [3, 4, 5, 1, 3, 2], [4, 5, 1, 2, 3, 4]]
    all_titles = []
    all_patterns = []
    expected_positions = [[2, 4, 8, 11, 15], [1, 6, 9, 12, 14],
                          [3, 5, 7, 10, 13], [2, 6, 8, 12, 15]]
    baseline = json.loads((ROOT / 'materials/revision-baseline.json').read_text())
    original_pages = {page['path']: page for page in baseline['pages']}
    check(manifest['neutral_position'] == 'last', 'Neutral tab must be last')
    for group, text_data in zip(manifest["sets"], article_data):
        topic = group["topic"]
        records = group["pages"]
        check(len(records) == 15, f"{topic}: not fifteen pages")
        check(len(list((ROOT / f"Content Set {group['number']}").glob("*.html"))) == 15,
              f"{topic}: unexpected HTML files")
        check(len(group["low_load"]) == len(set(group["low_load"])) == 5, f"{topic}: low-load count")
        check(len(group["high_load"]) == len(set(group["high_load"])) == 15, f"{topic}: high-load count")
        check(set(group["low_load"]) < set(group["high_load"]), f"{topic}: low/high relationship")
        check([path for path in group["high_load"] if path in group["low_load"]] == group["low_load"],
              f"{topic}: low-load order changes relative target order")
        for load in ['low_load', 'high_load']:
            check(group['launch_order'][load] == group[load] + [manifest['neutral_page']],
                  f'{topic}: popup sequence must end with Study Start')
        targets = {record["target_id"]: record for record in records if record["target_id"]}
        check(set(targets) == {"P1", "P2", "P3", "P4", "P5"}, f"{topic}: target mapping")
        counts = Counter(trial["target_id"] for trial in group["trials"])
        check(sorted(counts.values()) == [1, 1, 1, 1, 2], f"{topic}: six-trial coverage")
        if group["number"] <= 4:
            actual_order = [int(trial["target_id"][1:]) for trial in group["trials"]]
            check(actual_order == expected_orders[group["number"] - 1], f"{topic}: paper trial schedule changed")
        for trial in group["trials"]:
            record = targets[trial["target_id"]]
            check(trial["path"] == record["path"], f"{topic}: wrong trial answer")
            check(trial["prompt"] == f"Target: {record['title']}.", f"{topic}: prompt must name the exact title without Go")
            check(trial['title'] == record['title'], f"{topic}: trial title mismatch")
            matching = [page for page in records if record["name"].casefold() in page["title"].casefold()]
            check(len(matching) == 1, f"{topic}: ambiguous full-title match for {record['name']}")
        formats = Counter(record["title_format"] for record in records)
        check(formats == {0: 15}, f"{topic}: titles must put the subject first")
        target_formats = Counter(record["title_format"] for record in targets.values())
        check(target_formats == {0: 5}, f"{topic}: target titles must put the subject first")
        positions = sorted(record["high_load_position"] for record in targets.values())
        if group['number'] <= 4:
            check(positions == expected_positions[group['number'] - 1], f'{topic}: agreed position template changed')
            check([(p - 1) // 3 for p in positions] == list(range(5)), f'{topic}: missing position band')
        all_patterns.append(tuple(positions))
        check(positions[0] <= 3 and positions[-1] >= 13, f"{topic}: targets not spread through list")
        for record, item in zip(records, text_data["items"]):
            path = ROOT / record["path"]
            original = original_pages[record['path']]
            check(record['name'] == original['subject'] and record['target_id'] == original['target_id'],
                  f'{path}: original subject or target identity changed')
            check(path.is_file(), f"Missing {path}")
            parsed = Page(path.read_text(encoding="utf-8"))
            check(len(parsed.node("title")) == 1, f"{path}: missing or duplicate title")
            check(parsed.node("title")[0]["text"] == record["title"], f"{path}: wrong title")
            check(3 <= len(record["title"].split()) <= 5, f"{path}: title must be 3-5 words")
            check(25 <= len(record['title']) <= 33, f'{path}: title must be 25-33 characters')
            check(record["title"].startswith(item["name"] + " "), f"{path}: subject is not first")
            check(record["title"] == item["title"], f"{path}: title source mismatch")
            check(len(parsed.node("h1")) == 1 and parsed.node("h1")[0]["text"] == item["name"],
                  f"{path}: wrong heading")
            check(len(parsed.node("li")) == 2, f"{path}: not two key points")
            check(len(parsed.node("p", "summary")) == 1, f"{path}: missing summary")
            check(40 <= words(item["summary"]) <= 50, f"{path}: summary word count")
            check(all(10 <= words(point) <= 16 for point in item["points"]), f"{path}: point word count")
            check(60 <= words(item["summary"]) + sum(map(words, item["points"])) <= 82,
                  f"{path}: article length")
            check(not (set(parsed.tags) & {"a", "button", "script", "iframe", "audio", "video", "form"}),
                  f"{path}: participant navigation, script, or control")
            body = parsed.node("body")[0]["text"]
            check(not re.search(r"\b(?:P[1-5]|distractor|target page|Content Set)\b", body, re.I),
                  f"{path}: research-role label visible")
            for tag, attrs in parsed.links:
                check(tag == "link" and attrs.get("rel") in {"icon", "stylesheet"}, f"{path}: unexpected asset")
                asset = (path.parent / attrs["href"]).resolve()
                check(asset.is_relative_to(ROOT) and asset.is_file(), f"{path}: missing or remote asset")
                if attrs.get("rel") == "icon":
                    check(asset == ROOT / "assets/favicon.svg", f"{path}: icon varies by page")
                if attrs.get("rel") == "stylesheet":
                    check(asset == ROOT / "assets/study.css", f"{path}: stylesheet varies by page")
            check(group["high_load"][record["high_load_position"] - 1] == record["path"],
                  f"{path}: tab rank disagrees with manifest")
            all_titles.append(record["title"])
        check(len(text_data["sources"]) >= 5, f"{topic}: no adequate source record")
        check(all(source["url"].startswith("https://") for source in text_data["sources"]),
              f"{topic}: invalid source URL")
    check(len(all_titles) == len(set(all_titles)) == 75, "Duplicate or missing titles")
    check(len(set(all_patterns)) == 5, "Target-rank pattern repeated across sets")
    check(set(p for pattern in all_patterns[:4] for p in pattern) == set(range(1, 16)),
          'Scored templates do not cover every position')
    for condition in ['H-L', 'H-H', 'V-L', 'V-H']:
        check(sorted(row[condition] for row in manifest['condition_assignments']) == list('ABCD'),
              f'{condition}: templates not counterbalanced')
    check(manifest["sets"][-1]["extra"] and manifest["sets"][-1]["paper_label"] is None,
          "History was included in the scored design")
    neutral = Page((ROOT / manifest["neutral_page"]).read_text(encoding="utf-8"))
    check(neutral.node("title")[0]["text"] == "Study Start", "Neutral tab title")
    check(not (set(neutral.tags) & {"a", "script", "button"}), "Neutral page has interactive aids")
    check('mask disappears' in neutral.node('body')[0]['text'], 'Neutral page must use the visual start cue')
    for group in manifest["sets"]:
        check(len(group["low_load"]) + 1 == 6 and len(group["high_load"]) + 1 == 16,
              f"{group['topic']}: total visible-tab counts")
    report = {
        "result": "PASS", "participant_pages": 75, "topics": 5,
        "targets_per_set": 5, "trials_per_set": 6, "low_visible_tabs": 6,
        "high_visible_tabs": 16,
        "checks": ["unique titles and subject matches", "five targets plus ten additional pages",
                   "unchanged low/high target relationship", "paper trial sequences",
                   "shared icon and styles", "participant role labels absent",
                   "all local assets present", "word-count bounds", "original target-position templates",
                   "original subjects and target identities retained",
                   "25-33 character titles", "exact-title prompts without Go", "neutral-last placement",
                   "popup sequences end with Study Start", "material-to-condition counterbalancing"],
        "limits": "Structural checks do not establish equal task difficulty or actual macOS tab-title visibility.",
    }
    (ROOT / "materials/validation-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
