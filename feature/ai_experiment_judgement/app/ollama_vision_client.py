# -*- coding: utf-8 -*-
"""Ollama vision API helpers for multimodal judgement."""

from __future__ import annotations

import base64
import json
from typing import Any, Optional

import requests

try:
    import cv2
    import numpy as np
except ImportError:  # pragma: no cover - runtime dependency in app venv
    cv2 = None
    np = None


def judge_images_with_ollama(
    *,
    model: str,
    endpoint: str,
    current_b64: str,
    reference_b64: str,
    region_count: int,
    timeout: int = 180,
) -> str:
    endpoint = endpoint.rstrip("/")
    model = model.strip() or guess_vision_model(endpoint) or "qwen3-vl:2b"
    composite_b64 = _compose_comparison_b64(current_b64, reference_b64)
    prompt = build_judgement_prompt(region_count, single_image=True)

    app_result = _try_app_ollama_vl(prompt, current_b64, reference_b64, model)
    if app_result:
        return app_result

    errors: list[str] = []
    strategies = (
        ("chat-single-composite", lambda: _call_chat_api(
            endpoint=endpoint, model=model, prompt=prompt,
            images=[composite_b64], timeout=timeout,
        )),
        ("chat-single-current", lambda: _call_chat_api(
            endpoint=endpoint, model=model, prompt=prompt,
            images=[current_b64], timeout=timeout,
        )),
        ("chat-two-turn", lambda: _call_chat_two_turn_api(
            endpoint=endpoint, model=model, prompt=prompt,
            reference_b64=reference_b64, current_b64=current_b64, timeout=timeout,
        )),
        ("generate-single-composite", lambda: _call_generate_api(
            endpoint=endpoint, model=model, prompt=prompt,
            images=[composite_b64], timeout=timeout,
        )),
    )
    for name, caller in strategies:
        try:
            result = caller()
            _log_attempt(name, True)
            return result
        except Exception as exc:  # noqa: BLE001
            _log_attempt(name, False, exc)
            errors.append(f"{name}: {exc}")

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
        + "\n提示：qwen3-vl 通常一次只支持 1 张图片，程序已自动拼接对比图重试。"
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
                "images": images[:1],
            }
        ],
        "stream": False,
    }
    response = requests.post(f"{endpoint}/api/chat", json=payload, timeout=timeout)
    if not response.ok:
        raise RuntimeError(_format_http_error("chat", response))
    data = response.json()
    message = data.get("message", {})
    text = str(message.get("content", "")).strip()
    if text:
        return text
    raise RuntimeError("Ollama /api/chat returned empty content.")


def _call_chat_two_turn_api(
    *,
    endpoint: str,
    model: str,
    prompt: str,
    reference_b64: str,
    current_b64: str,
    timeout: int,
) -> str:
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": "这是标准摆放参考图，请先记住它。",
                "images": [reference_b64],
            },
            {
                "role": "user",
                "content": prompt,
                "images": [current_b64],
            },
        ],
        "stream": False,
    }
    response = requests.post(f"{endpoint}/api/chat", json=payload, timeout=timeout)
    if not response.ok:
        raise RuntimeError(_format_http_error("chat-two-turn", response))
    data = response.json()
    message = data.get("message", {})
    text = str(message.get("content", "")).strip()
    if text:
        return text
    raise RuntimeError("Ollama two-turn /api/chat returned empty content.")


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
        "images": images[:1],
        "stream": False,
    }
    response = requests.post(f"{endpoint}/api/generate", json=payload, timeout=timeout)
    if not response.ok:
        raise RuntimeError(_format_http_error("generate", response))
    data = response.json()
    text = str(data.get("response", "")).strip()
    if text:
        return text
    raise RuntimeError("Ollama /api/generate returned empty response.")


def _compose_comparison_b64(current_b64: str, reference_b64: str) -> str:
    if cv2 is None or np is None:
        return current_b64
    current = _b64_to_image(current_b64)
    reference = _b64_to_image(reference_b64)
    if current is None or reference is None:
        return current_b64

    target_h = max(current.shape[0], reference.shape[0])

    def resize_to_height(image: np.ndarray) -> np.ndarray:
        scale = target_h / max(1, image.shape[0])
        width = max(1, int(image.shape[1] * scale))
        return cv2.resize(image, (width, target_h))

    left = resize_to_height(current)
    right = resize_to_height(reference)
    gap = np.full((target_h, 24, 3), 255, dtype=np.uint8)
    combined = np.hstack([left, gap, right])
    ok, encoded = cv2.imencode(".jpg", combined, [int(cv2.IMWRITE_JPEG_QUALITY), 88])
    if not ok:
        return current_b64
    return base64.b64encode(encoded.tobytes()).decode("ascii")


def _b64_to_image(image_b64: str) -> Optional["np.ndarray"]:
    if np is None or cv2 is None:
        return None
    try:
        raw = base64.b64decode(image_b64)
        arr = np.frombuffer(raw, dtype=np.uint8)
        return cv2.imdecode(arr, cv2.IMREAD_COLOR)
    except Exception:  # noqa: BLE001
        return None


def _format_http_error(api_name: str, response: requests.Response) -> str:
    body = response.text.strip()
    if len(body) > 300:
        body = body[:300] + "..."
    return f"{response.status_code} {api_name} error: {body or response.reason}"


def _log_attempt(name: str, ok: bool, exc: Exception | None = None) -> None:
    pass


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
