from __future__ import annotations

import base64
from typing import Dict, Iterable

THINKING_RULE = "Use the last image part as final. If only one part exists, treat it as final."


def iter_image_parts(response) -> Iterable:
    if getattr(response, "parts", None):
        return response.parts
    if getattr(response, "candidates", None):
        candidates = response.candidates or []
        if candidates and getattr(candidates[0], "content", None):
            return candidates[0].content.parts or []
    return []


def extract_images_from_response(response) -> Dict[str, object]:
    images = []
    for part in iter_image_parts(response):
        inline = getattr(part, "inline_data", None)
        data = getattr(inline, "data", None)
        mime = getattr(inline, "mime_type", None)
        if not data or not mime or not str(mime).startswith("image/"):
            continue
        if isinstance(data, str):
            data = base64.b64decode(data)
        images.append(data)

    if not images:
        raise ValueError("No image data in response")

    final_idx = 0 if len(images) == 1 else len(images) - 1
    return {
        "final_image": images[final_idx],
        "final_image_index": final_idx,
        "thought_images": images[:final_idx],
        "total_parts": len(images),
    }


def extract_response_metadata(response) -> Dict[str, object]:
    meta = {"finish_reason": None, "safety_ratings": None, "model_version": None}
    candidate = response.candidates[0] if getattr(response, "candidates", None) else None
    if candidate:
        if getattr(candidate, "finish_reason", None):
            meta["finish_reason"] = str(candidate.finish_reason)
        if getattr(candidate, "safety_ratings", None):
            meta["safety_ratings"] = [
                {
                    "category": str(r.category if not hasattr(r.category, "name") else r.category.name),
                    "probability": str(r.probability if not hasattr(r.probability, "name") else r.probability.name),
                }
                for r in candidate.safety_ratings
            ]
    if getattr(response, "model_version", None):
        meta["model_version"] = response.model_version
    return meta
