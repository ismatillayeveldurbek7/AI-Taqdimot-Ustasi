"""
AI Taqdimot Ustasi — Ultra Premium PPTX Generator
Calls the Node.js generator (generate_pptx.js) for beautiful slides with
20+ layouts, Unsplash images, react-icons, and 5 color themes.
"""

import io
import json
import asyncio
import subprocess
import tempfile
import os
from pathlib import Path

# Path to the JS generator (same directory as this file)
_SCRIPT_DIR = Path(__file__).parent
_JS_GENERATOR = _SCRIPT_DIR / "generate_pptx.js"

# Supported color schemes
VALID_SCHEMES = {"Blue", "Black", "White", "Green", "PremiumDark"}


async def generate_pptx(data: dict, color_scheme: str = "Blue") -> bytes:
    """
    Generate a premium .pptx file from presentation data.
    
    Args:
        data: dict with keys: title, slides (list of slide dicts)
        color_scheme: one of "Blue", "Black", "White", "Green", "PremiumDark"
    
    Returns:
        bytes: the .pptx file content
    """
    if color_scheme not in VALID_SCHEMES:
        color_scheme = "Blue"

    # Write data to a temp JSON file
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(data, f, ensure_ascii=False)
        json_path = f.name

    # Output pptx temp file
    pptx_path = json_path.replace(".json", ".pptx")

    try:
        # Run the Node.js generator
        result = await asyncio.to_thread(
            subprocess.run,
            ["node", str(_JS_GENERATOR), json_path, color_scheme, pptx_path],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"PPTX generator failed (code {result.returncode}):\n"
                f"stdout: {result.stdout}\nstderr: {result.stderr}"
            )

        # Read generated file
        with open(pptx_path, "rb") as f:
            return f.read()

    finally:
        # Cleanup temp files
        for path in [json_path, pptx_path]:
            try:
                os.unlink(path)
            except OSError:
                pass


def generate_pptx_sync(data: dict, color_scheme: str = "Blue") -> bytes:
    """Synchronous version of generate_pptx for non-async contexts."""
    if color_scheme not in VALID_SCHEMES:
        color_scheme = "Blue"

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(data, f, ensure_ascii=False)
        json_path = f.name

    pptx_path = json_path.replace(".json", ".pptx")

    try:
        result = subprocess.run(
            ["node", str(_JS_GENERATOR), json_path, color_scheme, pptx_path],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"PPTX generator failed (code {result.returncode}):\n"
                f"stdout: {result.stdout}\nstderr: {result.stderr}"
            )

        with open(pptx_path, "rb") as f:
            return f.read()

    finally:
        for path in [json_path, pptx_path]:
            try:
                os.unlink(path)
            except OSError:
                pass
