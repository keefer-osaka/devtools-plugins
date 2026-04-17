#!/usr/bin/env python3
"""Shared delta-filtering helper for kb-ingest and kb-import."""


def filter_messages_after_uuid(messages, pivot_uuid):
    """Return (filtered, found_pivot).

    messages: list of dicts, each with a 'uuid' key.
    Returns messages strictly after pivot_uuid.
    If pivot_uuid is empty or None, returns (messages, True) — no pivot, full list.
    """
    if not pivot_uuid:
        return messages, True
    found = False
    result = []
    for msg in messages:
        if not found:
            if msg.get("uuid", "") == pivot_uuid:
                found = True
            continue
        result.append(msg)
    return result, found
