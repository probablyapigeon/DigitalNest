"""One shared local-model exchange at a time, grounded in two nearby birds."""
import json
import urllib.request

from conversation import MODEL, chat_messages
from speech_memory import is_fresh


def exchange(snapshot, first, second, room_name):
    # Reuse the same retrieved personal context as direct player chat.
    identities = [chat_messages(snapshot, key, 'What is on your mind here?')[0]['content'] for key in (first, second)]
    prompt = (
        'Write a brief natural conversation between two robot birds sharing ' + room_name + '. '
        'The first bird starts a topic based on a real possession, feeling, plan or remembered report; '
        'the second responds to that specific topic. They are talking to each other, not the player. '
        'No catchphrases, repeated lines, stage directions, or claims to have performed new actions. '
        'Return JSON only: {"first":"one short sentence","second":"one short sentence"}. '
        'Here are the two character descriptions and factual contexts:\n' + '\n'.join(identities))
    payload = dict(model=MODEL, stream=False, think=False, format='json', keep_alive='3m',
                   messages=[{'role': 'system', 'content': prompt}],
                   options=dict(num_ctx=4096, num_predict=180, temperature=.85, repeat_penalty=1.12))
    request = urllib.request.Request('http://127.0.0.1:11434/api/chat', json.dumps(payload).encode(),
                                     {'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=25) as response:
        outer = json.load(response)
    result = json.loads(outer['message']['content'])
    if not isinstance(result, dict):
        raise ValueError('Expected a two-bird exchange.')
    lines = []
    seen = dict(snapshot.data)
    seen['chats'] = list(snapshot.data['chats'])
    for field, key in (('first', first), ('second', second)):
        text = result.get(field)
        if not isinstance(text, str) or not 1 <= len(text.strip()) <= 400 or not is_fresh(seen, text):
            raise ValueError('The conversation was empty, too long or repeated.')
        lines.append(text.strip())
        seen['chats'].append(dict(role='assistant', bird=key, text=text))
    return lines
