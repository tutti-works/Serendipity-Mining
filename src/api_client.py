from __future__ import annotations

import time
from typing import Any, Dict, Tuple

from google import genai
from google.genai import types


def init_client(api_key: str) -> genai.Client:
    return genai.Client(api_key=api_key)


def classify_error(exception: Exception) -> Tuple[str, int | None]:
    msg = str(exception).lower()
    if "safety" in msg or "blocked" in msg:
        return ("SAFETY_BLOCKED", 400)
    if "rate" in msg or "quota" in msg or "resource_exhausted" in msg:
        return ("RATE_LIMITED", 429)
    if "authentication" in msg or "permission" in msg or "api_key" in msg:
        return ("AUTH_ERROR", 401)
    if "connection" in msg or "timeout" in msg:
        return ("CONNECTION_ERROR", None)
    if hasattr(exception, "status_code"):
        return ("API_ERROR", getattr(exception, "status_code"))
    if hasattr(exception, "code"):
        return ("API_ERROR", getattr(exception, "code"))
    return ("UNKNOWN_ERROR", None)


def generate_image(client: genai.Client, prompt: str, image_size: str = "2K"):
    # gemini-3-pro-image-preview uses generate_content with IMAGE modality.
    # image_size is kept for metadata but not enforced (model rejects media resolution).
    return client.models.generate_content(
        model="gemini-3-pro-image-preview",
        contents=prompt,
        config=types.GenerateContentConfig(responseModalities=["IMAGE"]),
    )


def generate_with_retry(
    client: genai.Client,
    prompt: str,
    max_retries: int = 3,
    base_delay: float = 2.0,
    image_size: str = "2K",
) -> Tuple[Any | None, Dict[str, Any] | None]:
    last_error: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            response = generate_image(client, prompt, image_size=image_size)
            return response, {"retry_count": attempt}
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            err_type, status = classify_error(exc)
            if err_type in ("SAFETY_BLOCKED", "AUTH_ERROR"):
                return None, {
                    "error": str(exc),
                    "error_type": err_type,
                    "http_status": status,
                    "retry_count": attempt,
                }
            if attempt < max_retries:
                time.sleep(base_delay * (2**attempt))
    err_type, status = classify_error(last_error) if last_error else ("UNKNOWN_ERROR", None)
    return None, {
        "error": str(last_error) if last_error else "Unknown error",
        "error_type": err_type,
        "http_status": status,
        "retry_count": max_retries,
    }
