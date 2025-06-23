import os
import argparse
import base64

import openai
import sys
from datetime import datetime
from core.common import debug_print


def invoke_openai(prompt, model="gpt-4o", temperature=0.7):
    """
    Invoke OpenAI API with the given prompt and parameters.
    """
    # Make sure these four are set in your shell or .env
    openai.api_key    = os.getenv("OPENAI_API_KEY")
    openai.api_type   = "azure"
    openai.api_base   = os.getenv("OPENAI_API_BASE")
    openai.api_version= os.getenv("OPENAI_API_VERSION")
    if not all([openai.api_key, openai.api_base, openai.api_version]):
        raise RuntimeError("Please set OPENAI_API_KEY, OPENAI_API_BASE and OPENAI_API_VERSION")
    
    debug_print("Invoking OpenAI API with model:", model, "and temperature:", temperature)
    response = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature
    )
    
    if response.choices[0].message['role'] != 'assistant':
        raise ValueError("Unexpected response from OpenAI API")
    
    return response.choices[0].message['content']
    