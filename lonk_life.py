"""Original Lonk impulses translated into persistent, room-local bird life."""
import copy
import re
from heart import initial_heart, update_heart, heart_event


class LonkLife:
    def gossip_line(self, key, target):
        """Talk about observed facts; never quote our own generated memory log."""
        b, other = self.society.bird(key), self.society.bird(target)
        life = self.data['birds'][key].setdefault('inner_life', {})
        room = self.spaces()[self.room_of(self.data['birds'][key])]['name']
        candidates = [
            f'{other.name}, what should we make in {room}?',
            f'{room} could use a very small, very unnecessary invention.',
            f'{other.name}, serious question. Is moss a suitable hat?',
            f'I like having company here, {other.name}. Please do not make it a whole thing.',
            'Would a tiny door make this place more mysterious, or just drafty?',
            f'{other.name}, choose one: sensible architecture or a magnificent pile of shiny things?',
            'I propose a club for objects that look slightly confused.',
            'If we build another perch, can we give it a ridiculous name?',
        ]
        if b.inventory:
            item = b.inventory[-1]
            candidates += [f'Does my {item} look suspicious to you?',
                           f'I have a {item}. This raises several logistical questions.',
                           f'{other.name}, help me find a good spot for my {item}.']
        if other.inventory:
            candidates.append(f'{other.name}, how is your {other.inventory[-1]} collection going?')
        recent = life.get('recent_topics', [])
        # Real player speech is eligible occasionally, without nested recall wrappers.
        count = life.get('gossip_count', 0)
        if count % 4 == 0:
            for memory in b.memory['player_interactions'][-4:]:
                words = re.sub(r'^(?:\s*I remember\s*[:.,]?\s*)+', '', memory['text'], flags=re.I).strip()
                if words and len(words) <= 140:
                    candidates.insert(0, f'Our human said "{words}". What do you think?')
        fresh = [line for line in candidates if line not in recent[-6:]]
        line = fresh[0] if fresh and fresh[0].startswith('Our human said') else self.society.world.rng.choice(fresh or candidates)
        life['recent_topics'] = (recent + [line])[-12:]
        life['gossip_count'] = count + 1
        return line

    def wants_nursery(self, key):
        b, social = self.data['birds'][key], self.society.bird(key).social
        return (len(self.specs) < 8 and social['stage'] == 'graduate'
                and social['colony_id'] is not None
                and self.data['tick'] - b.get('last_hatch', -20) >= 20)

    def lonk_say(self, key, text, target=None, thought=False):
        b = self.society.bird(key)
        if not self.emit(key, text, 'thought' if thought else 'speech', target):
            return False
        b.remember(text)
        if not thought:
            listeners = [target] if target and target != 'user' else [
                k for k in self.specs if k != key and self.room_of(self.data['birds'][k]) == self.room_of(self.data['birds'][key])]
            for other in listeners:
                self.society.bird(other).hear(text, b)
        return True

    def lonk_profile(self, key):
        b = self.society.bird(key)
        life = self.data['birds'][key].get('inner_life', {})
        return dict(emotions=copy.deepcopy(b.emotion), faction=b.faction,
                    territory=b.territory, inventory=list(b.inventory), catchphrase=b.catchphrase,
                    rival=self.society.key(b.rival), memories=copy.deepcopy(b.memory['events'][-5:]),
                    relationships={self.society.key(uid): score for uid, score in b.relationships.items() if self.society.key(uid)},
                    **copy.deepcopy(life))

    def lonk_event(self, key, event, target=None):
        b, world = self.society.bird(key), self.society.world
        bird = self.data['birds'][key]
        self.require(event in ('forage', 'dream', 'contest', 'gossip', 'hug', 'keepsake_gift'), 'Unknown Lonk activity.')
        self.require(self.data['habitat_open'], 'Meet the flock first.')
        self.require(not bird.get('destination') or bird['destination'] == self.room_of(bird), 'Wait until your bird arrives.')
        if event in ('contest', 'gossip', 'keepsake_gift'):
            self.require(target in self.specs and target != key, 'Choose another bird.')
            self.require(self.room_of(bird) == self.room_of(self.data['birds'][target]), 'Your friend must be in the same world.')
        if event == 'keepsake_gift':
            self.require(bool(b.inventory), 'Find a keepsake first.')
            self.require(len(self.society.bird(target).inventory) < 12, 'Your friend needs room in their keepsake collection.')
        life = bird.get('inner_life', {})
        self.require(self.data['tick'] >= life.get('ready_at', 0), 'Let this little adventure settle for two ticks.')
        life = bird.setdefault('inner_life', {})
        life['ready_at'] = self.data['tick'] + 2
        heart = bird.setdefault('heart', initial_heart())
        heart_event(heart, .9 if event in ('hug', 'keepsake_gift') else .7, pressure=event == 'contest')
        world.tick = self.data['tick']
        if event == 'forage':
            item = world.rng.choice(list(world.config['items']))
            if len(b.inventory) >= 12:
                released = b.inventory.pop(0)
                b.remember(f'Left {released} for another collector.')
            b.inventory.append(item)
            world.event(b, 'find_item')
            b.apply_effects(world.config['items'][item].get('effect', {}))
            life['treasure'] = item
            text = f'I found a {item}. {world.config["items"][item]["vibe"]}. I am emotionally attached.'
            life['goal'] = f'Keep {item} safe'
        elif event == 'keepsake_gift':
            other = self.society.bird(target)
            item = b.inventory.pop()
            other.inventory.append(item)
            life['treasure'] = b.inventory[-1] if b.inventory else None
            self.data['birds'][target].setdefault('inner_life', {})['treasure'] = item
            b.update_relationship(other, 5)
            other.update_relationship(b, 5)
            self.bond(key, target, 3)
            world.event(other, 'social')
            text = f'{other.name}, I brought you my {item}. Please tell it I still care.'
            other.remember(f'{b.name} gave me {item}.')
        elif event == 'dream':
            b.dream()
            subject = life.get('treasure', 'the moon')
            text = f'I dreamed {subject} owed the moss rent. I shall investigate after my nap.'
            life['dream'] = text
            bird['energy'] = min(100, bird['energy'] + 8)
            self.stimulate(key, 'Quiet')
        elif event == 'hug':
            world.event(b, 'dream')
            text = 'Softness acquired. I was saving this very specific happy noise for you.'
            self.stimulate(key, 'HarmonicRise')
        elif event == 'contest':
            other = self.society.bird(target)
            winner = world.rng.choice([key, target])
            b.rival, other.rival = other.uid, b.uid
            b.update_relationship(other, -2)
            other.update_relationship(b, -2)
            # A toy contest has social consequences, but no injury or lost possessions.
            world.event(self.society.bird(winner), 'win_duel')
            text = f'I challenge {other.name} to a dramatic leaf duel! {self.specs[winner]["name"]} wins. The air clearly cheated.'
            other.remember(text)
            life['goal'] = f'Rematch with {other.name}'
        else:
            text = self.gossip_line(key, target)
            b.update_relationship(self.society.bird(target), 2)
        if not b.catchphrase:
            b.catchphrase = world.line('catchphrase')
        b.normalize()
        self.lonk_say(key, text, target, thought=event == 'dream')
        self.note(b.name, text)
        return text

    def lonk_tick(self):
        world = self.society.world
        world.tick = self.data['tick']
        for index, key in enumerate(self.specs):
            b, bird = self.society.bird(key), self.data['birds'][key]
            life = bird.setdefault('inner_life', {})
            heart = bird.setdefault('heart', initial_heart())
            update_heart(heart, .65 if bird['energy'] >= 35 else .2,
                         pressure=bird['energy'] < 35, seconds=5)
            # LUMINA remains a behavioral input: its policy supplies the current
            # stimulus, then the Lonk's own emotional controller chooses an impulse.
            stimulus = {'FLOW': 'social', 'BRANCH': 'explore',
                        'CONTRACT': 'idle', 'RESONATE': 'dream'}.get(self.brains[key].action, 'idle')
            world.event(b, stimulus)
            impulse = self.society.app.step(b)
            b.normalize()
            life['impulse'] = impulse
            b.habits[impulse] = min(1000, b.habits[impulse] + 1)
            for uid in b.relationships:
                b.relationships[uid] *= world.config['world']['relationship_decay']
            room = self.room_of(bird)
            if life.get('last_room') != room:
                life['last_room'] = room
                # Original territory identities give each graphical room a local flavor.
                kind = self.spaces()[room]['kind']
                territory = dict(garden='The Moss Blanket', workshop='The Shiny Pit',
                                 commons='The Loud Bush', roost='The Big Rock',
                                 nursery='The Screaming Meadow', archive='The Unreasonable Clearing')[kind]
                if territory in world.config['territories']:
                    b.territory = territory
                    world.event(b, 'territory')
                    place = world.config['territories'][territory]
                    b.apply_effects(place.get('bonus', {}))
                    if place.get('faction_bonus') == b.faction:
                        b.personality['loyalty'] += 3
                    b.normalize()
            if bird.get('destination') and bird['destination'] != room:
                continue
            if self.data['tick'] < life.get('ready_at', 0) or (self.data['tick'] + index) % 6:
                continue
            neighbors = [k for k in self.specs if k != key and self.room_of(self.data['birds'][k]) == room]
            if bird['energy'] < 45 or impulse == 'idle':
                self.lonk_event(key, 'dream')
            elif impulse == 'explore':
                self.lonk_event(key, 'forage')
            elif neighbors:
                target = world.rng.choice(neighbors)
                self.lonk_event(key, 'contest' if impulse == 'attack' else 'gossip', target)
            else:
                text = world.line('general')
                self.lonk_say(key, text, 'user')
                life['goal'] = 'Find a friend to tell about this'
                if not b.catchphrase:
                    b.catchphrase = world.line('catchphrase')

    def lonk_routine(self, key):
        b = self.data['birds'][key]
        if b.get('heart', {}).get('perturb', 0) > .35:
            return ('finding a quiet place to settle', 'nest', 'Quiet')
        impulse = b.get('inner_life', {}).get('impulse', 'idle')
        if impulse == 'explore':
            b['scrap'] = min(8, b['scrap'] + 1)
        return {
            'explore': ('hunting for an emotionally important shiny', 'scrap', 'NovelInput'),
            'think': ('contemplating a deeply suspicious memory', 'garden', 'HarmonicRise'),
            'attack': ('looking for a leaf-duel challenger', 'choir', 'MusicPulse'),
            'ouch': ('recovering from an embarrassing idea', 'nest', 'Quiet'),
            'idle': ('dreaming about impossible moss', 'nest', 'Quiet'),
        }[impulse]
