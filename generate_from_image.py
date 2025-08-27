import os
import json
from datetime import datetime
from core.common import debug_print
from core.generate_script_json import invoke_openai_with_image
from core.generate_audio import generate_audio_from_script
from core.generate_video import generate_video_for_paragraphs
import base64

def read_prompt_template():
    path = os.path.join("prompt_library", "EGM_Help_image_to_audio.txt")
    with open(path, "r", encoding="utf-8") as f:
        prompt = f.read()
    return prompt

def encode_file_to_base64(file_path):
    """
    Encode a file to a base64 string.
    """
    import base64
    with open(file_path, "rb") as file:
        return base64.b64encode(file.read()).decode("utf-8")

def prepare_prompt(language="english"):
    """
    Prepare the prompt for generating a video script from an image.
    """
    prompt = read_prompt_template()    
    prompt = prompt.replace("<<LANGUAGE>>", language)    
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

def main(image_path):
    # Prepare the prompt
    prompt = prepare_prompt(language="english")

    # Generate script JSON
    today_date_folder = datetime.now().strftime("%Y-%m-%d")
    script_output_folder = "output/script_json"
    os.makedirs(script_output_folder, exist_ok=True)
    output_dir = os.path.join(script_output_folder, today_date_folder)
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "script_json_output.json")

    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            script_json = f.read()
    else:
        script_json = invoke_openai_with_image(prompt=prompt, image_path=image_path)
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
    import argparse
    parser = argparse.ArgumentParser(description="Generate audio and video from an image.")
    parser.add_argument("image_path", help="Path to the input image.")
    args = parser.parse_args()
    main(image_path=args.image_path)
