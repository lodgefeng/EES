# -*- coding: utf-8 -*-
"""Ollama vision API helpers for multimodal judgement."""

from __future__ import annotations

import json
from typing import Any, Optional

import requests


def build_judgement_prompt(region_count: int) -> str:
    return (
        "你是光学实验摆放判断助手。"
        "第一张是实时画面（已用编号圆圈标出疑似差异），第二张是标准摆放参考图。"
        f"程序检测到约 {region_count} 处疑似差异。"
        "请对比两张图，说明主要差异在哪里、学生摆放哪里可能不正确，"
        "并给出简短整改建议。使用中文，条理清晰。"
    )


def judge_images_with_ollama(
    *,
    model: str,
    endpoint: str,
    current_b64: str,
    reference_b64: str,
    region_count: int,
    timeout: int = 180,
) -> str:
    prompt = build_judgement_prompt(region_count)
    endpoint = endpoint.rstrip("/")
    model = model.strip() or guess_vision_model(endpoint) or "qwen3-vl:2b"

    app_result = _try_app_ollama_vl(prompt, current_b64, reference_b64, model)
    if app_result:
        return app_result

    errors: list[str] = []
    for caller in (_call_chat_api, _call_generate_api):
        try:
            return caller(
                endpoint=endpoint,
                model=model,
                prompt=prompt,
                images=[current_b64, reference_b64],
                timeout=timeout,
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(str(exc))

    installed = list_installed_models(endpoint)
    hint = ""
    if installed:
        vision_like = [name for name in installed if _looks_like_vision_model(name)]
        if vision_like:
            hint = "已检测到的视觉模型：" + ", ".join(vision_like[:8])
    raise RuntimeError(
        "无法调用 Ollama 视觉接口。\n"
        + "\n".join(errors)
        + (f"\n{hint}" if hint else "")
    )


def list_installed_models(endpoint: str) -> list[str]:
    try:
        response = requests.get(f"{endpoint.rstrip('/')}/api/tags", timeout=10)
        response.raise_for_status()
        data = response.json()
        models = data.get("models", [])
        return [str(item.get("name", "")).strip() for item in models if item.get("name")]
    except Exception:  # noqa: BLE001
        return []


def guess_vision_model(endpoint: str) -> Optional[str]:
    installed = list_installed_models(endpoint)
    preferred = (
        "qwen3-vl:2b",
        "qwen3-vl:8b",
        "qwen2.5-vl",
        "qwen2-vl",
        "llava",
        "llava:13b",
        "gemma3",
    )
    lowered = {name.lower(): name for name in installed}
    for candidate in preferred:
        for name_lower, original in lowered.items():
            if candidate in name_lower:
                return original
    for name in installed:
        if _looks_like_vision_model(name):
            return name
    return installed[0] if installed else None


def _looks_like_vision_model(name: str) -> bool:
    lowered = name.lower()
    return any(token in lowered for token in ("vl", "llava", "vision", "gemma3", "moondream"))


def _call_chat_api(
    *,
    endpoint: str,
    model: str,
    prompt: str,
    images: list[str],
    timeout: int,
) -> str:
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt,
                "images": images,
            }
        ],
        "stream": False,
    }
    response = requests.post(f"{endpoint}/api/chat", json=payload, timeout=timeout)
    response.raise_for_status()
    data = response.json()
    message = data.get("message", {})
    text = str(message.get("content", "")).strip()
    if text:
        return text
    raise RuntimeError("Ollama /api/chat returned empty content.")


def _call_generate_api(
    *,
    endpoint: str,
    model: str,
    prompt: str,
    images: list[str],
    timeout: int,
) -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "images": images,
        "stream": False,
    }
    response = requests.post(f"{endpoint}/api/generate", json=payload, timeout=timeout)
    response.raise_for_status()
    data = response.json()
    text = str(data.get("response", "")).strip()
    if text:
        return text
    raise RuntimeError("Ollama /api/generate returned empty response.")


def _try_app_ollama_vl(prompt: str, current_b64: str, reference_b64: str, model: str) -> Optional[str]:
    try:
        from app import ollama_vl  # type: ignore
    except Exception:  # noqa: BLE001
        return None

    for attr in ("chat_with_images", "compare_images", "analyze_difference", "judge_placement"):
        func = getattr(ollama_vl, attr, None)
        if not callable(func):
            continue
        try:
            result = func(
                prompt=prompt,
                images=[current_b64, reference_b64],
                model=model,
            )
        except TypeError:
            try:
                result = func(current_b64, reference_b64, prompt)
            except Exception:  # noqa: BLE001
                continue
        except Exception:  # noqa: BLE001
            continue
        if isinstance(result, str) and result.strip():
            return result.strip()
        if isinstance(result, dict):
            for key in ("response", "content", "text", "message"):
                value = result.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
            return json.dumps(result, ensure_ascii=False, indent=2)
    return None
