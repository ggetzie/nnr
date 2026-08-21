#!/usr/bin/env python
"""Build the frontend assets.

Replaces the gulp pipeline, which pulled in around a thousand npm packages to do
three things: compile one SCSS file, minify eight small JS files, and run a
live-reload server. All of the npm advisories against this repo came from that
tree, none of it ran in production, and the bundle it built from
bootstrap/jquery/popper (vendors.js) was not referenced by any template --
base.html loads Bootstrap and jQuery from a CDN.

Usage:
    uv run --group build scripts/build_assets.py [--check]

--check builds into memory and reports whether the committed output is current,
without writing anything.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import rcssmin
import rjsmin
import sass

ROOT = Path(__file__).resolve().parent.parent
SASS_INPUT = ROOT / "nnr/static/input/sass/project.scss"
JS_INPUT_DIR = ROOT / "nnr/static/input/js"
CSS_OUTPUT_DIR = ROOT / "nnr/static/output/css"
JS_OUTPUT_DIR = ROOT / "nnr/static/output/js"

ROOT_FONT_SIZE = 16

# A declaration whose value contains a rem length, e.g. "  font-size: 1.1rem;"
REM_DECLARATION = re.compile(r"^(?P<indent>\s*)(?P<prop>[\w-]+):\s*(?P<value>[^;]*\d*\.?\d+rem[^;]*);$")
REM_VALUE = re.compile(r"(\d*\.?\d+)rem")


def _px(match: re.Match) -> str:
    px = float(match.group(1)) * ROOT_FONT_SIZE
    # 24.0 -> "24", 17.6 -> "17.6"
    return f"{px:g}px"


def add_rem_fallbacks(css: str) -> str:
    """Emit a px copy of every declaration that uses rem, ahead of it.

    This is what the pixrem postcss plugin did in the gulp pipeline. It only
    matters for browsers with no rem support (IE 8/9), which Bootstrap 4 does not
    support either, but reproducing it keeps this build's output identical to
    what is already committed.
    """
    out = []
    for line in css.split("\n"):
        match = REM_DECLARATION.match(line)
        if match:
            fallback = REM_VALUE.sub(_px, match.group("value"))
            out.append(f"{match.group('indent')}{match.group('prop')}: {fallback};")
        out.append(line)
    return "\n".join(out)


def build_css() -> dict[Path, str]:
    css = sass.compile(filename=str(SASS_INPUT), output_style="expanded")
    css = add_rem_fallbacks(css)
    return {
        CSS_OUTPUT_DIR / "project.css": css,
        CSS_OUTPUT_DIR / "project.min.css": rcssmin.cssmin(css),
    }


def build_js() -> dict[Path, str]:
    built = {}
    for source in sorted(JS_INPUT_DIR.glob("*.js")):
        minified = rjsmin.jsmin(source.read_text())
        built[JS_OUTPUT_DIR / f"{source.stem}.min.js"] = minified
    return built


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="report whether committed output is up to date; write nothing",
    )
    args = parser.parse_args()

    artifacts = {**build_css(), **build_js()}

    if args.check:
        stale = [
            path
            for path, content in artifacts.items()
            if not path.exists() or path.read_text() != content
        ]
        for path in stale:
            print(f"stale: {path.relative_to(ROOT)}")
        if stale:
            print(f"\n{len(stale)} file(s) out of date; run scripts/build_assets.py")
            return 1
        print(f"{len(artifacts)} asset(s) up to date")
        return 0

    for path, content in artifacts.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        print(f"wrote {path.relative_to(ROOT)} ({len(content):,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
