import os
import argparse
import base64

from openai import AzureOpenAI, OpenAI
import sys
from datetime import datetime
from core.common import debug_print


def invoke_openai(prompt):
    """
    Invoke OpenAI API with the given prompt and parameters.
    Compatible with OpenAI Python SDK v1.0+.
    """
    # Make sure these are set in your environment or .env
    api_key     = os.getenv("OPENAI_API_KEY")
    api_base    = os.getenv("OPENAI_API_BASE")
    api_version = os.getenv("OPENAI_API_VERSION")
    model = os.getenv("OPENAI_DEPLOYMENT_NAME")
    
    if not all([api_key, api_base, api_version]):
        raise RuntimeError("Please set OPENAI_API_KEY, OPENAI_API_BASE and OPENAI_API_VERSION")

    client = AzureOpenAI(
        api_key=api_key,
        api_version=api_version,
        azure_endpoint=api_base
    )

    debug_print("Invoking OpenAI API with model:", model)

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content


def invoke_openai_with_image(prompt, image_path, temperature=0):
    """
    Invoke OpenAI with a prompt and an image using AzureOpenAI.

    Args:
        prompt_text (str): The text prompt to send to OpenAI.
        image_path (str): Path to the image file to include in the request.
        model (str): The OpenAI model to use (default: read from env OPENAI_DEPLOYMENT_NAME).
        temperature (float): Sampling temperature (default: 0).

    Returns:
        dict: The response from OpenAI.
    """
    # Read environment variables
    api_key = os.getenv("OPENAI_API_KEY")
    api_base = os.getenv("OPENAI_API_BASE")
    api_version = os.getenv("OPENAI_API_VERSION")
    model = os.getenv("OPENAI_DEPLOYMENT_NAME")

    if not all([api_key, api_base, api_version, model]):
        raise RuntimeError("Please set OPENAI_API_KEY, OPENAI_API_BASE, OPENAI_API_VERSION, and OPENAI_DEPLOYMENT_NAME")

    client = AzureOpenAI(
        api_key=api_key,
        api_version=api_version,
        azure_endpoint=api_base
    )

    # Read and encode the image as base64
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")

    # Create the input payload
    input_payload = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{img_b64}"
                    }
                }
            ]
        }
    ]

    # Send the request to OpenAI
    response = client.chat.completions.create(
        model=model,
        messages=input_payload
    )

    return response.choices[0].message.content
