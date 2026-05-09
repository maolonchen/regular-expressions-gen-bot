import io
import json
import os
import base64
import traceback
import aiohttp
from pathlib import Path
from typing import Union
from app.utils.log_utils import get_logger
from app.conf.config import ChatModelConfig


async def generate_api(session: aiohttp.ClientSession,
                            prompt: str,
                            api_url: str = ChatModelConfig.BASE_URL,
                            api_key: str = ChatModelConfig.API_KEY,
                            timeout: int = 600) -> str:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": ChatModelConfig.NAME,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": getattr(ChatModelConfig, "TEMPERATURE", 0.9),
        "maxtokens": getattr(ChatModelConfig, "MAX_TOKENS", 16384),
        # "max_tokens": getattr(ChatModelConfig, "MAX_TOKENS", 65536),
        # "presence_penalty": 1.5,
        # "chat_template_kwargs": {"enable_thinking": True},
    }
    try:
        async with session.post(api_url, json=payload, headers=headers, timeout=timeout) as resp:
            text = await resp.text()
            if resp.status >= 400:
                raise RuntimeError(f"model call failed status={resp.status}, body={text}")
            # Parse response as JSON
            response_data = json.loads(text)
            # print(response_data)
            content = response_data['choices'][0]['message']['content']
            return content
    except Exception as e:
        # Use traceback.format_exc() for error details
        error_msg = traceback.format_exc()
        print(error_msg)
        raise e