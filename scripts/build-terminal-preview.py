#!/usr/bin/env python3
"""Build dense, animated terminal previews for the GitHub profile README."""

from __future__ import annotations

from copy import deepcopy
from html import escape
from io import BytesIO
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

from PIL import Image


ROOT = Path(__file__).resolve().parent.parent
SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)
FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, Liberation Mono, monospace"
PALETTE = {
    "bg": "#101216",
    "bar": "#1a1d22",
    "border": "#39414b",
    "rule": "#2b3139",
    "text": "#eaedf0",
    "accent": "#aabfd0",
    "muted": "#a9b0b8",
}
ADVISORIES = [
    ("Rack", "CVE-2025-61919", "URL-encoded body parsing DoS"),
    ("Rails Active Storage", "CVE-2026-33174", "Range request DoS"),
    ("Puma", "CVE-2026-47736", "PROXY parser memory exhaustion"),
    ("Nextcloud", "CVE-2026-45157", "Temporary upload file access"),
]
PROJECTS = [
    ("vuln-chaser-core", "IAST + LLM runtime trace analysis"),
    ("caseforge", "OpenAPI test scenario generation"),
]


def text(x: int, y: int, content: str, *, size: int = 14, color: str = "text",
         weight: int | None = None, anchor: str | None = None,
         element_id: str | None = None) -> str:
    attributes = [
        f'x="{x}"', f'y="{y}"', f'fill="{PALETTE[color]}"',
        f'font-family="{FONT}"', f'font-size="{size}"',
    ]
    if weight:
        attributes.append(f'font-weight="{weight}"')
    if anchor:
        attributes.append(f'text-anchor="{anchor}"')
    if element_id:
        attributes.append(f'id="{element_id}"')
    return f'<text {" ".join(attributes)}>{escape(content)}</text>'


def rule(y: int, width: int) -> str:
    margin = 20 if width == 420 else 26
    return f'<path d="M{margin} {y}H{width - margin}" stroke="{PALETTE["rule"]}"/>'


def prompt(y: int, command: str, *, mobile: bool = False,
           animated: bool = False) -> str:
    left = 20 if mobile else 26
    command_x = 202 if mobile else 214
    size = 13 if mobile else 14
    result = text(left, y, "pirikara@github:~$", size=size, color="accent")
    result += text(command_x, y, command, size=size,
                   element_id="demo-command" if animated else None)
    if animated:
        advance = 8 if mobile else 9
        result += (f'<rect id="demo-cursor" x="{command_x + len(command) * advance}" '
                   f'y="{y - size + 2}" width="8" height="{size + 2}" '
                   f'fill="{PALETTE["accent"]}"/>')
    return result


def shell(width: int, height: int) -> list[str]:
    return [
        f'<svg xmlns="{SVG_NS}" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description">',
        '<title id="title">Pirikara security research terminal</title>',
        '<desc id="description">Security engineer profile, four public disclosures, '
        'and two security projects in a compact terminal.</desc>',
        f'<rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="12" '
        f'fill="{PALETTE["bg"]}"/>',
        f'<path d="M14 1H{width - 14}A13 13 0 0 1 {width - 1} 14V44H1V14'
        f'A13 13 0 0 1 14 1Z" fill="{PALETTE["bar"]}"/>',
        f'<path d="M1 44H{width - 1}" stroke="{PALETTE["rule"]}"/>',
        '<circle cx="23" cy="23" r="5" fill="#86919c"/>',
        '<circle cx="41" cy="23" r="5" fill="#6f7a85"/>',
        '<circle cx="59" cy="23" r="5" fill="#59646f"/>',
        text(width // 2, 28, "pirikara@github: ~", size=12, color="muted", anchor="middle"),
    ]


def desktop() -> str:
    width, height = 860, 508
    items = shell(width, height)
    items += [
        prompt(79, "cat profile.txt"),
        text(26, 115, "Pirikara / Tomoya Yamashita", size=20, weight=700),
        text(27, 139, "SECURITY ENGINEER  ·  BUG BOUNTY HUNTER  ·  JAPAN", size=12, color="muted"),
        text(27, 163, "Web application and OSS vulnerability research · security tooling", color="muted"),
        text(27, 183, "Investigating parsers, file handling and access boundaries", color="muted"),
        rule(200, width),
        prompt(226, "ls disclosures/"),
    ]
    for y, (name, cve, detail) in zip((255, 283, 311, 339), ADVISORIES):
        items += [
            text(30, y, name, size=15),
            text(235, y, cve, size=14, color="accent"),
            text(405, y, detail, size=14, color="muted"),
        ]
    items += [rule(357, width), prompt(384, "ls projects/")]
    for y, (name, detail) in zip((414, 442), PROJECTS):
        items += [text(30, y, name, size=15), text(235, y, detail, color="muted")]
    items += [rule(460, width), prompt(487, "help", animated=True)]
    items += [
        f'<rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="12" '
        f'fill="none" stroke="{PALETTE["border"]}" stroke-width="2"/>',
        '</svg>',
    ]
    return "\n".join(items) + "\n"


def mobile() -> str:
    width, height = 420, 625
    items = shell(width, height)
    items += [
        prompt(75, "cat profile.txt", mobile=True),
        text(20, 108, "Pirikara / Tomoya Yamashita", size=18, weight=700),
        text(20, 132, "Security engineer · Bug bounty hunter · Japan", size=12, color="muted"),
        text(20, 156, "Web application + OSS vulnerability research", size=13, color="muted"),
        text(20, 176, "Security tooling · responsible disclosure", size=13, color="muted"),
        rule(194, width),
        prompt(222, "ls disclosures/", mobile=True),
    ]
    for y, (name, cve, detail) in zip((250, 298, 346, 394), ADVISORIES):
        items += [
            text(20, y, name, size=14),
            text(208, y, cve, size=13, color="accent"),
            text(20, y + 20, detail, size=12, color="muted"),
        ]
    items += [rule(432, width), prompt(458, "ls projects/", mobile=True)]
    for y, (name, detail) in zip((486, 534), PROJECTS):
        items += [text(20, y, name, size=14), text(20, y + 20, detail, size=12, color="muted")]
    items += [rule(572, width), prompt(600, "help", mobile=True, animated=True)]
    items += [
        f'<rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="12" '
        f'fill="none" stroke="{PALETTE["border"]}" stroke-width="2"/>',
        '</svg>',
    ]
    return "\n".join(items) + "\n"


def gif_frames(svg: str, *, mobile_size: bool) -> tuple[list[Image.Image], list[int]]:
    converter = shutil.which("rsvg-convert")
    if converter is None:
        raise SystemExit("rsvg-convert is required to build the GIF previews")
    source = ET.fromstring(svg)
    frames: list[Image.Image] = []
    durations: list[int] = []
    states = [
        ("", True, 1000),
        ("h", True, 180),
        ("he", True, 180),
        ("hel", True, 180),
        ("help", True, 850),
        ("help", False, 350),
        ("help", True, 650),
        ("", False, 180),
        ("", True, 500),
    ]
    for command, cursor_on, duration in states:
        frame = deepcopy(source)
        command_text = frame.find(".//*[@id='demo-command']")
        cursor = frame.find(".//*[@id='demo-cursor']")
        assert command_text is not None and cursor is not None
        command_text.text = command
        cursor.set("x", str((202 if mobile_size else 214) + len(command) * (8 if mobile_size else 9)))
        cursor.set("opacity", "1" if cursor_on else "0")
        image_data = subprocess.run(
            [converter, "--format=png"],
            input=ET.tostring(frame, encoding="utf-8"),
            capture_output=True,
            check=True,
        ).stdout
        with Image.open(BytesIO(image_data)) as image:
            frames.append(image.convert("RGB"))
        durations.append(duration)
    return frames, durations


def build(name: str, svg: str, *, mobile_size: bool = False) -> None:
    assets = ROOT / "assets"
    (assets / f"{name}.svg").write_text(svg, encoding="utf-8")
    frames, durations = gif_frames(svg, mobile_size=mobile_size)
    palette = frames[0].quantize(colors=96, method=Image.Quantize.MEDIANCUT)
    indexed = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    destination = assets / f"{name}.gif"
    indexed[0].save(
        destination,
        save_all=True,
        append_images=indexed[1:],
        duration=durations,
        loop=0,
        disposal=2,
        optimize=True,
    )
    print(f"{destination.relative_to(ROOT)}: {len(indexed)} frames, {destination.stat().st_size // 1024} KiB")


if __name__ == "__main__":
    build("terminal", desktop())
    build("terminal-mobile", mobile(), mobile_size=True)
