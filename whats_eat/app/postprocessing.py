"""Post-processing utilities for the What's Eat LangGraph application."""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any, Callable, Iterable, Optional


JsonSerializer = Callable[[dict[str, Any]], Any]
"""Callable that serialises a JSON payload back to the message format."""


def dedupe_supervisor_output(output: dict[str, Any]) -> dict[str, Any]:
    """Remove duplicate restaurant cards from the supervisor's final message.

    The LangGraph supervisor returns a dictionary containing the message
    history.  The final AI message should be a JSON object that includes a
    ``cards`` array.  When control-flow issues cause upstream agents to emit the
    same place multiple times, duplicates may leak into that array.  This helper
    parses the final message, merges cards with the same identity and writes the
    deduplicated payload back to the message content.

    The function mutates the ``output`` argument in-place (mirroring other
    post-processing helpers in LangChain) and returns it for convenience so it
    can be composed in Runnable pipelines.
    """

    messages = output.get("messages")
    if not isinstance(messages, list) or not messages:
        return output

    last_message = messages[-1]
    content = getattr(last_message, "content", None)

    parsed, serializer = _try_parse_json_content(content)
    if parsed is None or serializer is None:
        return output

    updated_payload, mutated = _dedupe_payload(parsed)
    if not mutated:
        return output

    serialised_content = serializer(updated_payload)
    if content_is_mutable(last_message):
        last_message.content = serialised_content
    else:  # pragma: no cover - defensive branch for frozen message models
        _replace_message_content(messages, serialised_content)

    return output


def _try_parse_json_content(content: Any) -> tuple[Optional[dict[str, Any]], Optional[JsonSerializer]]:
    """Attempt to parse the AI message content as JSON."""

    if isinstance(content, str):
        text = content.strip()

        def _serialiser(payload: dict[str, Any]) -> str:
            return json.dumps(payload, ensure_ascii=False)

        try:
            return json.loads(text), _serialiser
        except json.JSONDecodeError:
            return None, None

    if isinstance(content, list):
        text_parts: list[str] = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                text_parts.append(str(part.get("text", "")))
        text = "".join(text_parts).strip()
        if not text:
            return None, None

        def _serialiser(payload: dict[str, Any]) -> list[Any]:
            dumped = json.dumps(payload, ensure_ascii=False)
            new_parts: list[Any] = []
            replaced = False
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    if not replaced:
                        new_part = dict(part)
                        new_part["text"] = dumped
                        new_parts.append(new_part)
                        replaced = True
                    # Skip additional text parts to avoid duplicate payloads
                    continue
                new_parts.append(part)
            if not replaced:
                new_parts.append({"type": "text", "text": dumped})
            return new_parts

        try:
            return json.loads(text), _serialiser
        except json.JSONDecodeError:
            return None, None

    return None, None


def _dedupe_payload(payload: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    """Return a payload with duplicate cards removed."""

    cards = payload.get("cards")
    if not isinstance(cards, list) or not cards:
        return payload, False

    deduped_cards, mutated = _dedupe_cards(cards)
    if not mutated:
        return payload, False

    updated = dict(payload)
    updated["cards"] = deduped_cards
    return updated, True


def _dedupe_cards(cards: Iterable[Any]) -> tuple[list[Any], bool]:
    """Deduplicate the provided cards list while preserving order."""

    original_cards = list(cards)
    seen: dict[tuple[str, ...], dict[str, Any]] = {}
    deduped: list[Any] = []
    mutated = False

    for card in original_cards:
        if not isinstance(card, dict):
            deduped.append(card)
            continue

        card_copy: dict[str, Any] = deepcopy(card)
        identity = _card_identity(card_copy)

        if identity is None:
            deduped.append(card_copy)
            continue

        existing = seen.get(identity)
        if existing is None:
            seen[identity] = card_copy
            deduped.append(card_copy)
            continue

        mutated = True
        if _merge_card(existing, card_copy):
            mutated = True

    if len(deduped) != len(original_cards):
        mutated = True

    return deduped, mutated


def _card_identity(card: dict[str, Any]) -> Optional[tuple[str, ...]]:
    place_id = card.get("place_id")
    if isinstance(place_id, str) and place_id.strip():
        return ("place_id", place_id.strip())

    name = card.get("name")
    address = card.get("address")
    normalized_name = name.strip().lower() if isinstance(name, str) else ""
    normalized_address = address.strip().lower() if isinstance(address, str) else ""
    if normalized_name or normalized_address:
        return ("name_address", normalized_name, normalized_address)

    return None


def _merge_card(target: dict[str, Any], incoming: dict[str, Any]) -> bool:
    """Merge ``incoming`` card data into ``target`` when new information exists."""

    mutated = False

    for key, value in incoming.items():
        if key not in target:
            target[key] = deepcopy(value)
            mutated = True
            continue

        existing_value = target[key]

        if isinstance(existing_value, list) and isinstance(value, list):
            merged = _merge_lists(existing_value, value, key)
            if merged != existing_value:
                target[key] = merged
                mutated = True
            continue

        if _is_missing(existing_value) and not _is_missing(value):
            target[key] = deepcopy(value)
            mutated = True

    return mutated


def _merge_lists(existing: list[Any], incoming: list[Any], field: str) -> list[Any]:
    """Merge two lists while removing duplicates."""

    if field == "photos":
        seen_names: set[str] = set()
        merged: list[Any] = []
        for item in existing + incoming:
            if isinstance(item, dict):
                name = item.get("name")
                if isinstance(name, str):
                    if name in seen_names:
                        continue
                    seen_names.add(name)
                merged.append(deepcopy(item))
            else:
                if item in merged:
                    continue
                merged.append(deepcopy(item))
        return merged

    merged_list: list[Any] = []
    for item in existing + incoming:
        candidate = deepcopy(item)
        if candidate not in merged_list:
            merged_list.append(candidate)
    return merged_list


def _is_missing(value: Any) -> bool:
    return value in (None, "", [], {})


def content_is_mutable(message: Any) -> bool:
    """Check whether the message content attribute can be reassigned."""

    try:
        original = getattr(message, "content")
        setattr(message, "content", original)
        return True
    except Exception:  # pragma: no cover - triggered only by frozen models
        return False


def _replace_message_content(messages: list[Any], new_content: Any) -> None:
    """Replace the last message in ``messages`` with a shallow copy carrying ``new_content``."""

    last = messages[-1]
    message_cls = last.__class__

    attrs: dict[str, Any]
    if hasattr(last, "model_dump"):
        attrs = last.model_dump()
    elif hasattr(last, "dict"):
        attrs = last.dict()  # type: ignore[assignment]
    else:
        attrs = dict(getattr(last, "__dict__", {}))

    attrs["content"] = new_content
    try:
        messages[-1] = message_cls(**attrs)
    except Exception:  # pragma: no cover - fallback when constructor signature differs
        clone = deepcopy(last)
        setattr(clone, "content", new_content)
        messages[-1] = clone


__all__ = ["dedupe_supervisor_output"]

