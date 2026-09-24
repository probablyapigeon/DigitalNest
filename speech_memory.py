"""Persistent, flock-wide protection against recycling spoken lines.

Normalizes case and punctuation, not meaning. Stores hashes rather than a second
copy of dialogue. Deliberate user replay and factual action logs are unaffected.
"""
import hashlib
import re


def normalize(text):
    return ' '.join(re.findall(r"[\w]+", str(text).casefold()))


def fingerprints(text):
    parts = [str(text)] + re.split(r'[.!?\n]+', str(text))
    return {hashlib.sha256(normalize(part).encode('utf-8')).hexdigest()
            for part in parts if normalize(part)}


def historical_keys(data):
    keys = set(data.get('spoken_phrases', {}))
    for entry in data.get('chats', []):
        if entry['role'] == 'assistant':
            keys.update(fingerprints(entry['text']))
    for entry in data.get('voices', []):
        if entry['kind'] in ('speech', 'reply', 'thought'):
            keys.update(fingerprints(entry['text']))
    return keys


def is_fresh(data, text):
    sentences = [normalize(s) for s in re.split(r'[.!?\n]+', str(text)) if normalize(s)]
    if len(sentences) != len(set(sentences)):
        return False
    keys = fingerprints(text)
    return bool(keys) and not keys.intersection(historical_keys(data))


def remember_speech(data, text):
    if not is_fresh(data, text):
        return False
    if 'spoken_phrases' not in data:
        data['spoken_phrases'] = dict.fromkeys(historical_keys(data), True)
    data['spoken_phrases'].update(dict.fromkeys(fingerprints(text), True))
    return True
