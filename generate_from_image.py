"""Generate captioned audio/video from an image, optionally guided by Excel text.

This module orchestrates:
- Building a prompt (image-only or Excel+image)
- Invoking the LLM to get AV-paragraphs JSON
- Generating TTS audio per paragraph
- Rendering a simple video using the image as background

Environment variables required:
- LLM:  OPENAI_API_KEY, OPENAI_API_BASE, OPENAI_API_VERSION, OPENAI_DEPLOYMENT_NAME
- TTS:  OPENAI_TTS_API_KEY, OPENAI_TTS_API_BASE, OPENAI_TTS_DEPLOYMENT_NAME
"""

import os
import json
import re
from typing import Any, Dict, Optional
from datetime import datetime

from core.common import debug_print, SCRIPT_OUTPUT_FOLDER
from core.generate_script_json import invoke_openai_with_image,invoke_openai
from core.generate_audio import generate_audio_from_script
from core.generate_video import generate_video_for_paragraphs
from core.excel_utils import extract_sheet_text, export_sheet_pdf


def read_prompt_template() -> str:
    """Read the base prompt for image-only transcription."""
    path = os.path.join("prompt_library", "EGM_Help_image_to_audio.txt")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def read_prompt_template_excel_image() -> str:
    """Read the prompt for Excel+image guided output."""
    path = os.path.join("prompt_library", "EGM_Help_excel_image_to_audio.txt")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def prepare_prompt(language: str = "english") -> str:
    """Prepare the prompt for image-only mode."""
    prompt = read_prompt_template()
    return prompt.replace("<<LANGUAGE>>", language)


def prepare_prompt_excel_image(language: str, excel_data_json: str) -> str:
    """Prepare the prompt for Excel+image mode with embedded authoritative Excel JSON."""
    prompt = read_prompt_template_excel_image()
    prompt = prompt.replace("<<LANGUAGE>>", language)
    prompt = prompt.replace("<<EXCEL_DATA_JSON>>", excel_data_json)
    return prompt


def add_tts_to_paragraphs(script_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate TTS for each paragraph and add `audio_file_path` in-place.

    Returns the updated dict.
    """
    for para in script_data.get("paragraphs", []):
        text = para.get("audio_script", "")
        if not text:
            continue
        audio_path = generate_audio_from_script(text)
        para["audio_file_path"] = audio_path
    return script_data


def _sanitize_name(value: str) -> str:
    """Make a safe file suffix from a name (sheet/file)."""
    return re.sub(r"[^A-Za-z0-9_-]+", "_", value or "")


def _save_text(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def main(
    image_path: str,
    excel_path: Optional[str] = None,
    sheet_name: Optional[str] = None,
    language: str = "english",
) -> None:
    """Generate per-paragraph audio and a simple video.

    - If `excel_path` and `sheet_name` are provided, uses Excel+image prompt.
    - Otherwise, uses image-only transcription prompt.
    """
    # Output locations
    today_date_folder = datetime.now().strftime("%Y-%m-%d")
    os.makedirs(SCRIPT_OUTPUT_FOLDER, exist_ok=True)
    output_dir = os.path.join(SCRIPT_OUTPUT_FOLDER, today_date_folder)
    os.makedirs(output_dir, exist_ok=True)
    
    if image_path is not None and not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    # Build prompt
    if excel_path and sheet_name:
        excel_data = extract_sheet_text(excel_path=excel_path, sheet_name=sheet_name)
        excel_payload = {
            "sheet_name": excel_data["sheet_name"],
            "flat_text": excel_data["flat_text"],
        }
        # Export the sheet to PDF for auditing
        excel_pdf_output = os.path.join(
            "output",
            "prompts",
            today_date_folder,
            f"excel_sheet_{_sanitize_name(os.path.splitext(os.path.basename(excel_path))[0])}_{_sanitize_name(sheet_name)}.pdf",
        )
        export_sheet_pdf(excel_path=excel_path, sheet_name=sheet_name, output_pdf=excel_pdf_output)
        prompt = prepare_prompt_excel_image(
            language=language,
            excel_data_json=json.dumps(excel_payload, ensure_ascii=False, indent=2),
        )
        suffix = f"{_sanitize_name(os.path.splitext(os.path.basename(excel_path))[0])}_{_sanitize_name(sheet_name)}"
        # Save prompt for audit in all cases
        prompt_output = os.path.join("output", "prompts", today_date_folder, f"prompt_{suffix}.txt")
        _save_text(prompt_output, prompt)
    else:
        prompt = prepare_prompt(language=language)
        suffix = "image_only"
        # Save prompt for audit in all cases
        prompt_output = os.path.join("output", "prompts", today_date_folder, f"prompt_{suffix}.txt")
        _save_text(prompt_output, prompt)


    output_file = os.path.join(output_dir, f"script_json_output_{suffix}.json")

    # Invoke or reuse cached JSON
    if os.path.exists(output_file):
        debug_print(f"Reusing existing script JSON: {output_file}")
        with open(output_file, "r", encoding="utf-8") as f:
            script_json = f.read()
    else:
        if image_path:
            debug_print("Invoking LLM with image context…")
            script_json = invoke_openai_with_image(prompt=prompt, image_path=image_path)
        else:
            debug_print("Invoking LLM with text-only context…")
            script_json = invoke_openai(prompt=prompt)
        _save_text(output_file, script_json)

    # Parse JSON safely
    try:
        script_data: Dict[str, Any] = json.loads(script_json)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Model response was not valid JSON. File: {output_file}") from e

    # Optionally save raw_text for auditing
    raw_text = script_data.get("raw_text")
    if isinstance(raw_text, str) and raw_text.strip():
        _save_text(os.path.join(output_dir, f"raw_text_{suffix}.txt"), raw_text)

    # Generate TTS per paragraph (idempotent if already present)
    audio_exists = any("audio_file_path" in p for p in script_data.get("paragraphs", []))
    if not audio_exists:
        script_data = add_tts_to_paragraphs(script_data)
        _save_text(output_file, json.dumps(script_data, ensure_ascii=False, indent=2))
    debug_print(f"Script JSON ready: {output_file}")


    # Render video with the image as background if provided, else use black background
    if image_path:
        video_path = generate_video_for_paragraphs(script_data, background_image_path=image_path)
    else:
        video_path = generate_video_for_paragraphs(script_data, background_color="black")
    debug_print(f"Video generated at: {video_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate paragraph audio and a simple video from an image; optionally guide content using Excel text."
    )
    parser.add_argument("--image_path", help="Path to the input image.", required=False, default=None)
    parser.add_argument("--excel_path", help="Path to the Excel file (.xls/.xlsx)", default=None)
    parser.add_argument("--sheet_name", help="Sheet name inside the Excel file", default=None)
    parser.add_argument("--language", help="Language for captions/voiceover", default="english")
    args = parser.parse_args()

    main(
        image_path=args.image_path,
        excel_path=args.excel_path,
        sheet_name=args.sheet_name,
        language=args.language,
    )
