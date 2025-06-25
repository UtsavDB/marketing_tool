import os
import requests
import json
from datetime import datetime
from core.common import VOICE_OUTPUT_FOLDER

def generate_audio_from_script(script, voice="alloy", model="gpt-4o-mini-tts"):
    """
    Generate speech audio from a script using Azure OpenAI's text-to-speech API.
    Returns the path to the saved audio file.
    """

    # Load env variables
    api_key = os.getenv("OPENAI_TTS_API_KEY")
    api_url = os.getenv("OPENAI_TTS_API_BASE")  # full URL already includes deployment and version
    deployment = os.getenv("OPENAI_TTS_DEPLOYMENT_NAME")  # for completeness, but not reused directly

    if not api_key or not api_url:
        raise RuntimeError("Environment variables OPENAI_TTS_API_KEY and OPENAI_TTS_API_BASE must be set.")

    if not os.path.exists(VOICE_OUTPUT_FOLDER):
        os.makedirs(VOICE_OUTPUT_FOLDER)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"audio_{timestamp}.mp3"
    output_path = os.path.join(VOICE_OUTPUT_FOLDER, filename)
    
    if os.path.exists(output_path):
        return output_path

    # Prepare request
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": model,
        "input": script,
        "voice": voice
    }

    response = requests.post(api_url, headers=headers, data=json.dumps(payload))

    if response.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(response.content)
        return output_path
    else:
        raise Exception(f"Error {response.status_code}: {response.text}")
