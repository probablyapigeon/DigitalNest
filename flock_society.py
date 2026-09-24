"""Adapter to actual LonkWorld.xc language, development and society procedures.

Little Flock supplies habitat time and nonlethal nursery construction. The XC
procedures own learning, innovation, reciprocal bonds, colonies and inheritance.
"""
import copy
from pathlib import Path

from vendor.lonkworld.xc_app_runtime import XCApplication
from vendor.lonkworld.lonk_engine import Lonk, LonkWorld
from vendor.lonkworld import lonk_language as language, lonk_society as society

SOURCE = Path(__file__).parent / 'vendor' / 'lonkworld' / 'LonkWorld.xc'
MAX_FLOCK = 8


class FlockSociety:
    def __init__(self, specs, saved=None):
        self.app = XCApplication(SOURCE)
        self.lines = []
        self.app.procedures.globals['print'] = self.capture
        if saved:
            self.world = LonkWorld.from_dict(copy.deepcopy(saved['world']), controller=self.app)
            self.ids = copy.deepcopy(saved['ids'])
            if set(self.ids) != set(specs) or set(self.ids.values()) != {b.uid for b in self.world.lonks}:
                raise ValueError('Society bird identities do not match the flock save.')
        else:
            self.world = LonkWorld(starting_population=0, max_population=MAX_FLOCK, controller=self.app, seed=220926)
            self.world.toggles.update(violence=False, trauma=False, shinywars=False)
            self.ids = {}
            for key, spec in specs.items():
                bird = Lonk(self.world, name=spec['name'])
                self.world.lonks.append(bird)
                self.ids[key] = bird.uid
                self.world.event(bird, 'birth')
        self.drain()

    def capture(self, *args, **kwargs):
        self.lines.append(' '.join(str(a) for a in args)[:500])
        self.lines = self.lines[-60:]

    def drain(self):
        result, self.lines = self.lines, []
        return result

    def bird(self, key):
        return next(b for b in self.world.lonks if b.uid == self.ids[key])

    def key(self, uid):
        return next((key for key, value in self.ids.items() if value == uid), None)

    def export(self):
        return {'world': self.world.to_dict(), 'ids': copy.deepcopy(self.ids)}

    def learn(self, key, text):
        targets = list(self.ids) if key == 'everyone' else [key]
        for target in targets:
            bird = self.bird(target)
            bird.hear(text[:500], player=True)
            society.develop(bird)
        return targets

    def converse(self, a, b):
        if a == b:
            raise ValueError('Choose two different birds.')
        left, right = self.bird(a), self.bird(b)
        left.speak(target=right)
        right.speak(target=left)
        society.develop(left)
        society.develop(right)
        self.maintain_society()

    def maintain_society(self):
        culture = self.world.config['culture']
        chance = culture.get('conversation_chance', 0.9)
        culture['conversation_chance'] = 0
        try:
            society.society_tick(self.world)
        finally:
            culture['conversation_chance'] = chance

    def tick(self, tick, rooms=None):
        self.world.tick = tick
        for bird in self.world.lonks:
            bird.age += 1
            # Development comes from learning, not this age counter.
            if self.world.rng.random() < self.world.config['culture']['reflection_chance']:
                thought = language.reflect(bird)
                if thought:
                    bird.social['thoughts'].append({'tick': tick, 'text': thought})
                    bird.social['thoughts'] = bird.social['thoughts'][-self.world.config['culture']['thought_history']:]
        if rooms is None:
            society.society_tick(self.world)
            return
        # Keep native colony/development maintenance, but let the graphical
        # habitat choose physically present conversational partners.
        culture = self.world.config['culture']
        chance = culture.get('conversation_chance', 0.9)
        self.maintain_society()
        groups = {}
        for key, room in rooms.items():
            groups.setdefault(room, []).append(key)
        for members in groups.values():
            if len(members) < 2 or self.world.rng.random() >= chance:
                continue
            a, b = self.world.rng.sample(members, 2)
            left, right = self.bird(a), self.bird(b)
            left.speak(target=right)
            right.speak(target=left)
            society.develop(left)
            society.develop(right)

    def hatch(self, parent_key, child_key, name):
        if len(self.world.lonks) >= MAX_FLOCK:
            raise ValueError('All eight habitat berths are occupied.')
        parent = self.bird(parent_key)
        if parent.social['stage'] != 'graduate' or parent.social['colony_id'] is None:
            raise ValueError('The parent must graduate and belong to a colony first.')
        baby = Lonk(self.world, name=name)
        baby.generation = parent.generation + 1
        baby.faction, baby.territory = parent.faction, parent.territory
        mutation = self.world.config['world']['inheritance_mutation']
        baby.personality = {k: max(0, min(100, v + self.world.rng.randint(-mutation, mutation))) for k, v in parent.personality.items()}
        baby.memory['word_counts'] = dict(sorted(parent.vocabulary.items(), key=lambda item: -item[1])[:64])
        # These are the original XC inheritance procedures, independent deep copies.
        language.inherit(parent, baby)
        society.inherit(parent, baby)
        self.world.lonks.append(baby)
        self.ids[child_key] = baby.uid
        self.world.event(baby, 'birth')
        self.app.procedures.namespaces['society']._record(
            self.world, f'{parent.name} builds {baby.name}, a generation {baby.generation} hatchling carrying the family dialect.', 'hatchling', (parent, baby))
        society.validate_world(self.world)
        return baby

    def payload(self):
        birds = {}
        for key in self.ids:
            b = self.bird(key)
            ling, social = b.linguistics, b.social
            colony = self.world.colonies.get(social['colony_id'])
            birds[key] = {
                'stage': social['stage'], 'words': len(ling['tokens']), 'conversations': social['conversations'],
                'vocabulary': sorted(ling['tokens'], key=lambda w: (-ling['tokens'][w], w))[:60],
                'associations': {w: list(followers)[:6] for w, followers in list(ling['bigrams'].items())[:24]},
                'origins': {w: ('you' if origin == 'player' else next((x.name for x in self.world.lonks if x.uid == origin), origin)) for w, origin in ling['origins'].items()},
                'inventions': list(ling['innovations'])[-12:], 'thoughts': social['thoughts'][-5:],
                'heard': ling['total_heard'], 'spoken': ling['total_spoken'],
                'partners': [self.key(uid) for uid in social['partners']],
                'parents': [self.key(uid) for uid in social['parents']],
                'colony': colony['name'] if colony else None, 'generation': b.generation,
                'temperament': [label for trait, label in [('curiosity','exploratory'),('loyalty','loyal'),('anxiety','cautious'),('aggression','assertive')] if b.personality[trait] >= 60],
                'affection': {self.key(uid): score for uid, score in social['affection'].items() if self.key(uid)},
            }
        return {'birds': birds, 'colonies': [dict(c, members=[self.key(uid) for uid in c['members']]) for c in self.world.colonies.values() if c['archived_at'] is None],
                'chronicle': copy.deepcopy(self.world.chronicle[-50:]), 'population': len(self.ids), 'capacity': MAX_FLOCK}
