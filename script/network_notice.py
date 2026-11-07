#!/usr/bin/env python3
"""Render the dated wireless-data notice into existing static support pages."""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
import re

ANCHOR = "wireless-data-notice"
START = "<!-- mowyns-network-notice:start -->"
END = "<!-- mowyns-network-notice:end -->"
APPLE_DISCUSSION = "https://developer.apple.com/forums/thread/822198"
ISSUE = "r.183584353"
LOCALES = {"zh-Hans", "zh-Hant", "en-US", "es-ES", "de-DE", "fr-FR", "ru", "ja", "ko", "tr", "it"}
FIELDS = {"heading", "updatedLabel", "summary", "paragraphs", "appleLinkLabel", "detailsLinkLabel"}
CSS = "#wireless-data-notice{margin:24px 0 32px;padding:18px 20px;border:1px solid #aaa;border-left-width:3px;border-radius:8px}#wireless-data-notice h2{margin:0 0 10px}#wireless-data-notice p{font-size:16px}#wireless-data-notice .date{font-size:14px}"


def load_notice(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("appleDiscussionURL") != APPLE_DISCUSSION or data.get("appleInternalIssue") != ISSUE:
        raise ValueError("Review the official source URL and issue identifier")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", data.get("updatedAt", "")):
        raise ValueError("Notice requires an ISO update date")
    if set(data.get("localizations", {})) != LOCALES:
        raise ValueError("Expected all 11 published locales")
    for locale, copy in data["localizations"].items():
        if set(copy) != FIELDS:
            raise ValueError(f"Incomplete notice fields for {locale}")
        if not isinstance(copy["paragraphs"], list) or len(copy["paragraphs"]) != 4:
            raise ValueError(f"Expected four complete paragraphs for {locale}")
        if any(not isinstance(value, str) or not value.strip() for key, value in copy.items() if key != "paragraphs"):
            raise ValueError(f"Empty notice label for {locale}")
        if any(not isinstance(value, str) or not value.strip() for value in copy["paragraphs"]):
            raise ValueError(f"Empty notice paragraph for {locale}")
        if ISSUE not in copy["paragraphs"][2] or "1.0.39" not in copy["paragraphs"][3] or "1.0.39" not in copy["summary"]:
            raise ValueError(f"Missing issue/version guidance for {locale}")
    return data


def render_notice(data: dict, locale: str, *, detailed: bool, index: bool = False) -> str:
    copy = data["localizations"][locale]
    paragraphs = copy["paragraphs"] if detailed else [copy["summary"]]
    links = []
    if not detailed:
        target = (locale + "/" if index else "") + "support.html#" + ANCHOR
        links.append('<a href="' + target + '">' + html.escape(copy["detailsLinkLabel"]) + "</a>")
    links.append('<a href="' + APPLE_DISCUSSION + '">' + html.escape(copy["appleLinkLabel"]) + " · " + ISSUE + "</a>")
    return (START + '<section id="' + ANCHOR + '" aria-labelledby="wireless-data-heading">'
            + '<h2 id="wireless-data-heading">' + html.escape(copy["heading"]) + '</h2>'
            + '<p class="date"><time datetime="' + data["updatedAt"] + '">' + html.escape(copy["updatedLabel"]) + '</time></p>'
            + "".join("<p>" + html.escape(paragraph) + "</p>" for paragraph in paragraphs)
            + "<p>" + " · ".join(links) + "</p></section>" + END)


def render_notice_markdown(data: dict, locale: str) -> str:
    copy = data["localizations"][locale]
    return ("## " + copy["heading"] + "\n\n" + copy["updatedLabel"] + "\n\n" + copy["summary"]
            + "\n\n[" + copy["detailsLinkLabel"] + "](support.html#" + ANCHOR + ") · ["
            + copy["appleLinkLabel"] + " · " + ISSUE + "](" + APPLE_DISCUSSION + ")\n\n")


def inject_notice(page: str, data: dict, locale: str, *, detailed: bool, index: bool = False) -> str:
    if page.count(START) != page.count(END) or page.count(START) > 1:
        raise ValueError("Unexpected existing notice markers")
    page = re.sub(re.escape(START) + r".*?" + re.escape(END), "", page, flags=re.S)
    page = re.sub(r'<style id="network-notice-style">.*?</style>', "", page, flags=re.S)
    if page.count("</head>") != 1:
        raise ValueError("Expected one HTML head")
    page = page.replace("</head>", '<style id="network-notice-style">' + CSS + "</style></head>")
    position = r"(<h1\b[^>]*>.*?</h1>)" if index else r'(<h1\b[^>]*>.*?</h1>\s*<p class="date">.*?</p>)'
    if len(list(re.finditer(position, page, flags=re.S))) != 1:
        raise ValueError("Cannot locate the page introduction")
    return re.sub(position, lambda match: match[1] + render_notice(data, locale, detailed=detailed, index=index), page, count=1, flags=re.S)


def update_site(site: Path, data: dict, *, check: bool = False) -> list[str]:
    paths = [(site / locale / name, locale, name == "support.html", False)
             for locale in sorted(LOCALES) for name in ("privacy.html", "support.html")]
    paths.append((site / "index.html", "zh-Hans", False, True))
    updates = []
    for path, locale, detailed, index in paths:
        old = path.read_text(encoding="utf-8")
        new = inject_notice(old, data, locale, detailed=detailed, index=index)
        if old != new:
            updates.append((path, new))
    # Validate every page before writing any page.
    if not check:
        for path, content in updates:
            path.write_text(content, encoding="utf-8")
    return [str(path.relative_to(site)) for path, _ in updates]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-dir", type=Path, required=True)
    parser.add_argument("--notice-file", type=Path, required=True)
    parser.add_argument("--check", action="store_true", help="Fail if generated notices are missing or stale")
    args = parser.parse_args()
    updates = update_site(args.site_dir, load_notice(args.notice_file), check=args.check)
    print(json.dumps({"check": args.check, "changedPages": updates}, ensure_ascii=False))
    return 1 if args.check and updates else 0


if __name__ == "__main__":
    raise SystemExit(main())
