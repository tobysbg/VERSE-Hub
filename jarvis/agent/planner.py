"""Lightweight intent classification and planning helpers.

The heavy lifting (deciding which tools to call) is done by the LLM via tool
calling. This module provides a cheap, dependency-free intent classifier used
for status display, logging, and to let the app behave sensibly even when no
LLM is configured.
"""
from __future__ import annotations

import enum
import re


class Intent(str, enum.Enum):
    CHITCHAT = "chitchat"
    FILE_TASK = "file_task"
    APP_TASK = "app_task"
    WEB_TASK = "web_task"
    EMAIL_TASK = "email_task"
    CALENDAR_TASK = "calendar_task"
    DESKTOP_TASK = "desktop_task"
    DESTRUCTIVE = "destructive"
    UNKNOWN = "unknown"


_PATTERNS: list[tuple[Intent, re.Pattern]] = [
    (Intent.DESTRUCTIVE, re.compile(r"\b(delete|remove|wipe|erase|format)\b.*\b(all|every|everything|folder|downloads)\b", re.I)),
    (Intent.EMAIL_TASK, re.compile(r"\b(email|inbox|gmail|mail|send.*message)\b", re.I)),
    (Intent.CALENDAR_TASK, re.compile(r"\b(calendar|event|meeting|schedule|free\s+slot|appointment)\b", re.I)),
    (Intent.WEB_TASK, re.compile(r"\b(search|google|website|url|browser|book|ticket|train|flight|hotel)\b", re.I)),
    (Intent.FILE_TASK, re.compile(r"\b(file|folder|directory|document|read|write|create|save|move)\b", re.I)),
    (Intent.APP_TASK, re.compile(r"\b(open|launch|start|close|quit)\b.*\b(app|application|notepad|calculator|word|excel|program)\b", re.I)),
    (Intent.DESKTOP_TASK, re.compile(r"\b(click|type|screenshot|scroll|hotkey|press)\b", re.I)),
]


def classify_intent(text: str) -> Intent:
    for intent, pattern in _PATTERNS:
        if pattern.search(text):
            return intent
    if len(text.split()) <= 6 and re.search(r"\b(hi|hello|hey|thanks|how are you)\b", text, re.I):
        return Intent.CHITCHAT
    return Intent.UNKNOWN
