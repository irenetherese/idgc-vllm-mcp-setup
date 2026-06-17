import gradio as gr
from openai import OpenAI
import os

VLLM_MODEL = os.environ["VLLM_MODEL"]
VLLM_URL = os.environ["VLLM_URL"]
VLLM_API_KEY = os.environ["VLLM_API_KEY"]

client = OpenAI(
    base_url = VLLM_URL,
    api_key = VLLM_API_KEY
)

def chat(message, history):
    messages = []
    for historical_message in history[-30:]:
        messages.append({"role": historical_message["role"], "content": historical_message["content"]})

    messages.append({"role": "user", "content": message})

    response = client.chat.completions.create(
        model=VLLM_MODEL,
        messages=messages
    )

    return response.choices[0].message.content


gr.ChatInterface(
    fn=chat,
    title="Local vLLM Chat",
).launch(
    server_name="172.21.0.76",
    server_port=5860
)