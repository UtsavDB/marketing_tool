import os
import argparse
import base64
import json

import openai
import sys
from datetime import datetime
from core.common import debug_print
from core.generate_script_json import invoke_openai
from core.generate_audio import generate_audio_from_script

def read_prompt_template():
    path = os.path.join("Prompt_template", "generate_video_prompt_template.txt")
    with open(path, "r", encoding="utf-8") as f:
        prompt = f.read()
    return prompt
        
def prepare_prompt(language="english", rule_data=None):
    """
    Prepare the prompt for generating a video script.
    """
    prompt = read_prompt_template()
    prompt = prompt.replace("<<language>>", language)
    prompt = prompt.replace("<<rule_data>>", rule_data)
    
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
    rule_data = """Rule name - "BR - BOL - Comps - Tables 4.5% of Theo = $2.48 Comp"	 Rule criteria - "@RatingTypeID=2  AND NOT    ((@TableGameType="PK") OR   (@TableGameType="IN") OR   (@TableGameType="M") OR   (@TableGameType="TP")OR   (@TableGameType="SY") OR (@TableGameType="SZ")  OR (@TableGameType="MZ")  OR (@TableGameType="MY")) AND   (@Property=13 )" Benefit "@CompDollars =   (@TheoreticalWin/55.000)*2.480;  EXECUTE AddPlayerCompDollars" """
    prompt = prepare_prompt(language="english", rule_data=rule_data)

    script_json = invoke_openai(prompt=prompt)
    audios = generate_audio_for_paragraphs(script_json=script_json)
    debug_print(audios)

if __name__ == "__main__":
    main()
