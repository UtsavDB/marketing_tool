"""Example script that generates a narrated video from rule data."""

import os
import json
from datetime import datetime

from core.common import (
    SCRIPT_OUTPUT_FOLDER,
    today_date_folder,
    BACKGROUND_IMAGE_FOLDER,
    debug_print,
)
from core.generate_script_json import invoke_openai
from core.generate_audio import generate_audio_from_script
from core.generate_video import generate_video_for_paragraphs


def read_prompt_template() -> str:
    """Load the base prompt template from the prompt library."""
    path = os.path.join("prompt_library", "prompt_template.txt")
    with open(path, "r", encoding="utf-8") as f:
        prompt = f.read()
    return prompt


def prepare_prompt(language="english", rule_data=None):
    """
    Prepare the prompt for generating a video script.
    """
    prompt = read_prompt_template()
    prompt = prompt.replace("<<LANGUAGE>>", language)
    prompt = prompt.replace("<<RULE_DATA>>", rule_data)
    return prompt


def generate_audio_for_paragraphs(script_json):
    """
    For each paragraph in the script JSON, generate audio and add the audio file path to the paragraph dict.
    Returns the updated JSON object.
    """
    data = json.loads(script_json)
    for para in data.get("paragraphs", []):
        audio_path = generate_audio_from_script(para["audio_script"])
        para["audio_file_path"] = audio_path
    return data


def main():
    """Build a prompt, call the LLM, then generate audio and video files."""
    rule_data = (
        'Rule name - "Table Game Cashback Bonanza" '
        'Rule criteria - "@RatingTypeID=TableGame AND NOT ((@TableGameType=\"Poker\") OR (@TableGameType=\"Indian\") '
        'OR (@TableGameType=\"Baccarat\") OR (@TableGameType=\"Three Card Poker\") OR (@TableGameType=\"Symphony\") '
        'OR (@TableGameType=\"Ultimate Texas Holdem\") OR (@TableGameType=\"Pai Gow Poker\") and @CoinIN>150'
        'AND (@Property=pokola)" Benefit "@CompDollars = (@CoinIN)/10; '
        'EXECUTE AddPlayerCompDollars'
    )
    prompt = prepare_prompt(language="Gujrati", rule_data=rule_data)
    
    

    # Prepare script JSON
    os.makedirs(SCRIPT_OUTPUT_FOLDER, exist_ok=True)    
    output_dir = os.path.join(SCRIPT_OUTPUT_FOLDER, today_date_folder)
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "script_json_output.json")

    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            script_json = f.read()
    else:
        script_json = invoke_openai(prompt=prompt)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(script_json)
    # Check if audio_file_path already exists in script_json
    script_data = json.loads(script_json)
    audio_exists = any("audio_file_path" in para for para in script_data.get("paragraphs", []))
    if audio_exists:
        audios = script_data
    else:
        # Generate audio files
        audios = generate_audio_for_paragraphs(script_json=script_json)
        # Overwrite the script_json file with the updated audios variable
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(json.dumps(audios, ensure_ascii=False, indent=2))
    debug_print(f"Script JSON loaded from: {output_file}")
    # Generate video
    background_image=os.path.join(BACKGROUND_IMAGE_FOLDER, "bgimage_choctaw.png")
    video_path = generate_video_for_paragraphs(audios,background_image_path=background_image)
    debug_print(f"Video generated at: {video_path}")


if __name__ == "__main__":
    main()
