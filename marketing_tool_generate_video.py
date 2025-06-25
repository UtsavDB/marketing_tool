import os
import argparse
import base64
import json
import sys
from datetime import datetime

import openai
from moviepy.editor import TextClip, AudioFileClip, concatenate_videoclips

from core.common import *
from core.generate_script_json import invoke_openai
from core.generate_audio import generate_audio_from_script

# Directories (can be overridden via env vars)
SCRIPT_OUTPUT_FOLDER = os.getenv("SCRIPT_OUTPUT_FOLDER", "output/scripts")
VIDEO_OUTPUT_FOLDER = os.getenv("VIDEO_OUTPUT_FOLDER", "output/videos")


def read_prompt_template():
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


def generate_video_for_paragraphs(audios, output_path=None):
    """
    Generate a vertical video (1080x1920) from the paragraphs JSON with associated audio.
    Each slide displays text_to_be_rendered for the duration of its audio.
    Returns the path to the saved video file.
    """
    os.makedirs(VIDEO_OUTPUT_FOLDER, exist_ok=True)
    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(VIDEO_OUTPUT_FOLDER, f"video_{timestamp}.mp4")

    clips = []
    for para in audios.get("paragraphs", []):
        text = para.get("text_to_be_rendered", "")
        audio_file = para.get("audio_file_path")
        if not audio_file or not os.path.exists(audio_file):
            continue
        # Load audio clip
        audio_clip = AudioFileClip(audio_file)
        duration = audio_clip.duration
        # Create text clip with black background
        txt_clip = (TextClip(text, fontsize=70, color='white', size=(1080, 1920), method='caption')
                    .set_duration(duration)
                    .set_audio(audio_clip)
                    .set_position('center'))
        clips.append(txt_clip)

    if not clips:
        raise RuntimeError("No valid clips to concatenate.")

    final_clip = concatenate_videoclips(clips, method="compose")
    final_clip.write_videofile(output_path, fps=24, codec='libx264', audio_codec='aac')
    return output_path


def main():
    rule_data = (
        'Rule name - "BR - BOL - Comps - Tables 4.5% of Theo = $2.48 Comp" '
        'Rule criteria - "@RatingTypeID=2 AND NOT ((@TableGameType=\"PK\") OR (@TableGameType=\"IN\") '
        'OR (@TableGameType=\"M\") OR (@TableGameType=\"TP\") OR (@TableGameType=\"SY\") '
        'OR (@TableGameType=\"SZ\") OR (@TableGameType=\"MZ\") OR (@TableGameType=\"MY\")) '
        'AND (@Property=13)" Benefit "@CompDollars = (@TheoreticalWin/55.000)*2.480; '
        'EXECUTE AddPlayerCompDollars'
    )
    prompt = prepare_prompt(language="english", rule_data=rule_data)

    # Prepare script JSON
    os.makedirs(SCRIPT_OUTPUT_FOLDER, exist_ok=True)
    output_file = os.path.join(SCRIPT_OUTPUT_FOLDER, "script_json_output.json")

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
    video_path = generate_video_for_paragraphs(audios)
    debug_print(f"Video generated at: {video_path}")


if __name__ == "__main__":
    main()
