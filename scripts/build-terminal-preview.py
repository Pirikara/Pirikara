#!/usr/bin/env python3
"""Render the terminal SVG previews as compact animated GIFs."""

from __future__ import annotations

from copy import deepcopy
from io import BytesIO
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

from PIL import Image


ROOT = Path(__file__).resolve().parent.parent
SVG_NS = "{http://www.w3.org/2000/svg}"
RSVG = shutil.which("rsvg-convert")
if RSVG is None:
    raise SystemExit("rsvg-convert is required to build the previews")


def text_at(root: ET.Element, x: int, y: int) -> ET.Element:
    for element in root.iter(f"{SVG_NS}text"):
        if element.get("x") == str(x) and element.get("y") == str(y):
            return element
    raise ValueError(f"Missing SVG text at {x},{y}")


def hide_text_y(root: ET.Element, y: int) -> None:
    for element in root.iter(f"{SVG_NS}text"):
        if element.get("y") == str(y):
            element.set("opacity", "0")


def render_frame(source: ET.Element, config: dict, state: dict) -> Image.Image:
    frame = deepcopy(source)
    text_at(frame, *config["first_command"]).text = state["first_text"]
    if not state["show_files"]:
        for y in config["file_lines"]:
            hide_text_y(frame, y)
    if not state["show_second_prompt"]:
        text_at(frame, *config["second_prompt"]).set("opacity", "0")
    text_at(frame, *config["second_command"]).text = state["second_text"]
    for index, y in enumerate(config["result_lines"]):
        if index >= state["results_count"]:
            hide_text_y(frame, y)
    if not state["show_bottom"]:
        text_at(frame, *config["bottom_prompt"]).set("opacity", "0")
    for rectangle in frame.iter(f"{SVG_NS}rect"):
        if rectangle.get("x") == str(config["cursor"][0]) and rectangle.get("y") == str(config["cursor"][1]):
            if not state["show_bottom"] or not state["cursor_on"]:
                rectangle.set("opacity", "0")
            break
    else:
        raise ValueError("Missing SVG cursor")

    svg = ET.tostring(frame, encoding="utf-8", xml_declaration=True)
    result = subprocess.run([RSVG, "--format=png"], input=svg, capture_output=True, check=True)
    with Image.open(BytesIO(result.stdout)) as rendered:
        return rendered.convert("RGB")


def states_for(second_command: str, result_count: int) -> list[tuple[dict, int]]:
    state = {
        "first_text": "",
        "show_files": False,
        "show_second_prompt": False,
        "second_text": "",
        "results_count": 0,
        "show_bottom": False,
        "cursor_on": True,
    }
    frames: list[tuple[dict, int]] = []

    def add(milliseconds: int, **changes: object) -> None:
        state.update(changes)
        frames.append((state.copy(), milliseconds))

    add(1100)  # A useful first frame if the viewer has disabled GIF autoplay.
    add(180, first_text="l")
    add(250, first_text="ls")
    add(850, show_files=True)
    add(260, show_second_prompt=True)
    for letter_count in range(1, len(second_command) + 1):
        add(90, second_text=second_command[:letter_count])
    for count in range(1, result_count + 1):
        add(350 if count < result_count else 650, results_count=count)
    add(550, show_bottom=True)
    add(360, cursor_on=False)
    add(1600, cursor_on=True)
    return frames


def build(source_name: str, output_name: str, config: dict) -> None:
    source = ET.parse(ROOT / "assets" / source_name).getroot()
    states = states_for(config["typed_command"], len(config["result_lines"]))
    frames = [render_frame(source, config, state) for state, _ in states]
    palette = frames[-1].quantize(colors=96, method=Image.Quantize.MEDIANCUT)
    indexed = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    destination = ROOT / "assets" / output_name
    indexed[0].save(
        destination,
        save_all=True,
        append_images=indexed[1:],
        duration=[duration for _, duration in states],
        loop=0,
        disposal=2,
        optimize=True,
    )
    print(f"{destination.relative_to(ROOT)}: {len(indexed)} frames, {destination.stat().st_size // 1024} KiB")


build(
    "terminal.svg",
    "terminal.gif",
    {
        "first_command": (269, 310),
        "file_lines": [342],
        "second_prompt": (38, 389),
        "second_command": (269, 389),
        "typed_command": "disclosures",
        "result_lines": [424, 453, 480],
        "bottom_prompt": (38, 523),
        "cursor": (258, 508),
    },
)
build(
    "terminal-mobile.svg",
    "terminal-mobile.gif",
    {
        "first_command": (235, 276),
        "file_lines": [306, 331],
        "second_prompt": (20, 378),
        "second_command": (235, 378),
        "typed_command": "help",
        "result_lines": [409, 434],
        "bottom_prompt": (20, 492),
        "cursor": (235, 477),
    },
)
