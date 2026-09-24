"""Disk-backed personal language, with a replayable save outbox.

JSON saves carry pending events until SQLite commits them. Replaying a pending
event is idempotent, so interruption between the two files never loses a lesson.
The archive has no vocabulary-count ceiling; XC keeps its bounded working set.
"""
import hashlib
import re
import sqlite3
from contextlib import closing


def words(text):
    return [w[:40] for w in re.findall(r"[\w']+", str(text).casefold())]


class LanguageArchive:
    def __init__(self, world):
        self.world = world
        identity = hashlib.sha256(world.data['instance_id'].encode()).hexdigest()[:16]
        self.path = world.path.with_name(f'{world.path.stem}.{identity}.language.sqlite3')
        if world.data.get('language_seeded') and not self.path.exists():
            raise ValueError(f'Language archive is missing. Restore {self.path.name} alongside {world.path.name}; the save has not been changed.')
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self.connect()) as db, db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY, bird TEXT, source TEXT, text TEXT, tick INTEGER);
                CREATE TABLE IF NOT EXISTS words (
                    bird TEXT, word TEXT, uses INTEGER, source TEXT, node TEXT, tick INTEGER,
                    PRIMARY KEY(bird,word));
                CREATE TABLE IF NOT EXISTS links (
                    bird TEXT, a TEXT, b TEXT, uses INTEGER, PRIMARY KEY(bird,a,b));
                CREATE TABLE IF NOT EXISTS terms (
                    bird TEXT, word TEXT, event INTEGER, PRIMARY KEY(bird,word,event));
                CREATE INDEX IF NOT EXISTS events_bird ON events(bird,id DESC);
                CREATE INDEX IF NOT EXISTS word_frequency ON words(bird,uses DESC);
                CREATE INDEX IF NOT EXISTS word_recency ON words(bird,tick DESC,uses DESC);
            ''')
            last = db.execute('SELECT coalesce(max(id),0) FROM events').fetchone()[0]
            if last > world.data.get('language_sequence', 0):
                raise ValueError('The language archive is newer than this save. Restore a matching save/archive backup pair.')
        self.flush()

    def connect(self):
        return sqlite3.connect(self.path, timeout=10)

    def queue(self, bird, text, source, *, parent=None):
        d = self.world.data
        d['language_sequence'] = d.get('language_sequence', 0) + 1
        nodes = self.world.brains[bird].morph_state['Structural']['nodes'] if bird in self.world.brains else []
        d.setdefault('_language_pending', []).append(dict(
            id=d['language_sequence'], bird=bird, text=str(text)[:2000], source=source,
            tick=d['tick'], nodes=[str(n['id']) for n in nodes] or ['0'], parent=parent))

    def flush(self):
        pending = self.world.data.get('_language_pending', [])
        if not pending:
            return
        with closing(self.connect()) as db, db:
            for event in pending:
                inserted = db.execute('INSERT OR IGNORE INTO events VALUES(?,?,?,?,?)',
                    (event['id'], event['bird'], event['source'], event['text'], event['tick'])).rowcount
                if not inserted:
                    continue
                key, source, tick = event['bird'], event['source'], event['tick']
                if event.get('parent'):
                    db.execute('INSERT OR IGNORE INTO words SELECT ?,word,uses,?,?,tick FROM words WHERE bird=?',
                               (key, 'inherited:' + event['parent'], event['nodes'][0], event['parent']))
                    db.execute('INSERT OR IGNORE INTO links SELECT ?,a,b,uses FROM links WHERE bird=?', (key, event['parent']))
                tokens = words(event['text'])
                groups = {'garden': {'moss','garden','flower','leaf','plant'},
                          'friendship': {'friend','hug','love','gift','together'},
                          'building': {'build','parts','world','shelter','home'},
                          'music': {'song','sing','music','tune','sound'}}
                concept = max(groups, key=lambda k: len(groups[k].intersection(tokens))) if any(set(tokens).intersection(v) for v in groups.values()) else event['source']
                node = event['nodes'][int(hashlib.sha256(concept.encode()).hexdigest()[:8], 16) % len(event['nodes'])]
                for word in tokens:
                    db.execute('''INSERT INTO words VALUES(?,?,?,?,?,?) ON CONFLICT(bird,word)
                                  DO UPDATE SET uses=uses+1,tick=excluded.tick''', (key, word, 1, source, node, tick))
                    db.execute('INSERT OR IGNORE INTO terms VALUES(?,?,?)', (key, word, event['id']))
                for a, b in zip(tokens, tokens[1:]):
                    db.execute('INSERT INTO links VALUES(?,?,?,1) ON CONFLICT(bird,a,b) DO UPDATE SET uses=uses+1', (key, a, b))
        self.world.data.pop('_language_pending', None)

    def seed_existing(self):
        if self.world.data.get('language_seeded'):
            return
        for key in self.world.specs:
            b = self.world.society.bird(key)
            tokens = list(b.linguistics['tokens'])
            for offset in range(0, len(tokens), 30):
                self.queue(key, ' '.join(tokens[offset:offset+30]), 'existing-vocabulary')
            for entry in b.memory['player_interactions']:
                self.queue(key, entry['text'], 'player-history')
        self.world.data['language_seeded'] = True

    def stats(self, bird):
        with closing(self.connect()) as db:
            return {'words': db.execute('SELECT count(*) FROM words WHERE bird=?', (bird,)).fetchone()[0],
                    'experiences': db.execute('SELECT count(*) FROM events WHERE bird=?', (bird,)).fetchone()[0]}

    def retrieve(self, bird, prompt='', limit=16):
        query = list(dict.fromkeys(words(prompt)))[:20]
        brain = self.world.brains[bird]
        strengths = {str(n['id']): sum(abs(float(x)) for x in n['vector']) / max(1, len(n['vector']))
                     for n in brain.morph_state['Structural']['nodes']}
        with closing(self.connect()) as db:
            candidates = {}
            if query:
                marks = ','.join('?' for _ in query)
                rows = db.execute(f'SELECT word,uses,source,node FROM words WHERE bird=? AND word IN ({marks})', [bird]+query)
                candidates.update((row[0], row) for row in rows)
                links = db.execute(f'''SELECT w.word,w.uses,w.source,w.node FROM links l JOIN words w
                    ON w.bird=l.bird AND w.word=l.b WHERE l.bird=? AND l.a IN ({marks}) ORDER BY l.uses DESC LIMIT 32''', [bird]+query)
                candidates.update((row[0], row) for row in links)
            for row in db.execute('SELECT word,uses,source,node FROM words WHERE bird=? ORDER BY tick DESC,uses DESC LIMIT 32', (bird,)):
                candidates.setdefault(row[0], row)
            heart = self.world.data['birds'][bird].get('heart', {})
            openness = heart.get('light', .5)
            ranked = sorted(candidates.values(), key=lambda r: (r[0] in query,
                strengths.get(r[3], 0) + (openness*.2 if r[2].startswith('player') else 0), r[1]), reverse=True)[:limit]
            memories = []
            if query:
                for row in db.execute(f'''SELECT DISTINCT e.text,e.source FROM terms t JOIN events e ON e.id=t.event
                    WHERE t.bird=? AND t.word IN ({marks}) AND e.source!='existing-vocabulary' ORDER BY e.id DESC LIMIT 3''', [bird]+query):
                    memories.append({'text': row[0][:240], 'source': row[1]})
        return {'words': [r[0] for r in ranked], 'concepts': [{'word': r[0], 'node': r[3], 'origin': r[2]} for r in ranked], 'memories': memories}

    def activate(self, bird, prompt):
        retrieved = self.retrieve(bird, prompt)
        state = self.world.society.bird(bird).linguistics
        for word in retrieved['words']:
            if word not in state['tokens']:
                if len(state['tokens']) >= 256:
                    state['tokens'].pop(min(state['tokens'], key=state['tokens'].get))
                state['tokens'][word] = 1
                state['origins'][word] = 'archive'
                state['dialect'][word] = 1
        namespace = self.world.society.app.procedures.namespaces['language']
        namespace._prune(state, namespace._settings(self.world.society.bird(bird)))
        return retrieved
