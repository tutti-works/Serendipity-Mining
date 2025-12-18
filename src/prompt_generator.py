from __future__ import annotations

import random
from typing import Dict, List, Tuple


AXIS_PLACEHOLDERS: Dict[str, List[str]] = {
    "synesthesia": ["SENSATION", "SUBJECT"],
    "biomimicry": ["OBJECT", "BIO_STRUCTURE"],
    "literal_interpretation": ["IDIOM"],
    "macro_micro": ["SUBJECT"],
    "material_paradox": ["OBJECT", "MATERIAL_OR_STATE"],
    "glitch_contradiction": ["STYLE_A", "STYLE_B", "SUBJECT"],
    "affordance_inversion": ["THING", "WRONG_FUNCTION"],
    "representation_shift": ["SUBJECT"],
    "manufacturing_first": ["OBJECT", "CONSTRAINT"],
    "procedural_rules": ["RULESET", "SUBJECT"],
}


def _sample_hints(domain: dict) -> List[str]:
    hints = domain.get("hints", [])
    if len(hints) < 2:
        raise ValueError(f"Domain {domain.get('domain_id')} must have at least 2 hints")
    return random.sample(hints, 2)


def _select_vocab(placeholders: List[str], vocab: Dict[str, List[str]]) -> Dict[str, str]:
    selected: Dict[str, str] = {}
    for placeholder in placeholders:
        words = vocab.get(placeholder)
        if not words:
            raise ValueError(f"Vocab missing for placeholder {placeholder}")
        selected[placeholder] = random.choice(words)
    return selected


def build_prompt(
    axis_id: str,
    axis_templates: Dict[str, dict],
    domain: dict,
    vocab: Dict[str, List[str]],
) -> Tuple[str, dict]:
    template_info = axis_templates[axis_id]
    template = template_info["template"]
    hints = _sample_hints(domain)
    placeholders = AXIS_PLACEHOLDERS[axis_id]
    vocab_used = _select_vocab(placeholders, vocab)
    prompt = template.format(context=domain["context"], h1=hints[0], h2=hints[1], **vocab_used)
    return prompt, {
        "template_text": template,
        "hints_used": hints,
        "vocab_used": vocab_used,
    }


def _constrain_length(text: str, min_len: int = 500, max_len: int = 800) -> str:
    if len(text) < min_len:
        padding = (
            " Maintain clarity, avoid busy layouts, keep camera still, prioritize legible silhouettes, "
            "focus on structured layering, and keep the context anchored in the domain."
        )
        text = text + padding
    if len(text) > max_len:
        text = text[:max_len]
    return text


def build_mix_prompt(
    axis_pair: List[str],
    axis_templates: Dict[str, dict],
    domain: dict,
    vocab: Dict[str, List[str]],
) -> Tuple[str, dict]:
    hints = _sample_hints(domain)
    vocab_used = {}
    parts = []
    template_texts = []
    for axis_id in axis_pair:
        template_info = axis_templates[axis_id]
        placeholders = AXIS_PLACEHOLDERS[axis_id]
        chosen = _select_vocab(placeholders, vocab)
        vocab_used[axis_id] = chosen
        template_texts.append(template_info["template"])
        filled = template_info["template"].format(
            context=domain["context"],
            h1=hints[0],
            h2=hints[1],
            **chosen,
        )
        parts.append(filled)

    combined = (
        f"Hybrid exploration combining axis {axis_pair[0]} and {axis_pair[1]} inside bundle {domain['bundle']} / {domain['domain_id']}. "
        f"Context: {domain['context']} Hints emphasized: {hints[0]}, {hints[1]}. "
        f"Axis A directive: {parts[0]} Axis B directive: {parts[1]} "
        "Blend the two directives into a single coherent 2K image with controlled chaos, keeping silhouettes readable, "
        "colors harmonized, and micro/macro motifs interlaced. Avoid UI chrome, stick to one scene, and keep depth and lighting consistent."
    )

    prompt = _constrain_length(combined)
    return prompt, {
        "template_text": " | ".join(template_texts),
        "hints_used": hints,
        "vocab_used": vocab_used,
        "axis_pair": axis_pair,
    }
