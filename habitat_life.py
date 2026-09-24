"""Interactive room objects, resource sinks and a bounded, saved dialogue stream."""
from vendor.lonkworld import lonk_language as language
from speech_memory import remember_speech

OBJECTS = {
    'workshop': [dict(id='workbench', name='Workbench', label='Build a wind-up toy', cost=2, x=-250, y=100),
                 dict(id='drawers', name='Parts drawers', label='Find a spare part', cost=0, x=-270, y=-70)],
    'garden': [dict(id='planter', name='Planter', label='Fit a watering bracket', cost=1, x=0, y=-65),
               dict(id='pond', name='Pond', label='Rest by the water', cost=0, x=0, y=70)],
    'roost': [dict(id='charger', name='Charging nest', label='Recharge', cost=0, x=-270, y=-40),
              dict(id='perch', name='Perch', label='Build / maintain a perch', cost=3, x=90, y=105)],
    'commons': [dict(id='table', name='Conversation table', label='Talk with a resident', cost=0, x=0, y=35),
                dict(id='radio', name='Radio', label='Make a washer melody', cost=1, x=275, y=-70)],
    'archive': [dict(id='book', name='Memory book', label='Reflect on learned words', cost=0, x=0, y=-65),
               dict(id='press', name='Story press', label='Print a little phrase', cost=1, x=135, y=95)],
    'nursery': [dict(id='mobile', name='Nursery toys', label='Build a learning toy', cost=2, x=0, y=110),
               dict(id='incubator', name='Incubator', label='Build a hatchling', cost=0, x=-225, y=-60)],
}


class HabitatLife:
    def emit(self, bird, text, kind='speech', target=None):
        d = self.data
        if kind in ('speech', 'reply', 'thought') and not remember_speech(d, text):
            return False
        if kind in ('speech', 'reply') and hasattr(self, 'archive'):
            self.archive.seed_existing()
            self.archive.queue(bird, text, 'self-expression')
        serial = d.get('voice_serial', 0) + 1
        d['voice_serial'] = serial
        event = dict(id=serial, tick=d['tick'], bird=bird, text=str(text)[:600], kind=kind,
                     target=target, room=self.room_of(d['birds'][bird]))
        d.setdefault('voices', []).append(event)
        d['voices'] = d['voices'][-80:]
        return True

    def object_reason(self, bird, room, item):
        b = self.data['birds'][bird]
        if not self.data['habitat_open']:
            return 'Meet the flock first.'
        if self.room_of(b) != room:
            return 'Invite this bird here first.'
        if b['scrap'] < item['cost']:
            return f"Needs {item['cost']} spare parts."
        if self.data['tick'] - b.get('object_ticks', {}).get(room + ':' + item['id'], -10) < 2:
            return 'Ready again in two station minutes.'
        if item['id'] in ('drawers', 'built-salvager') and b['scrap'] >= 8:
            return 'Parts tray full. Build or share something.'
        if item['id'] in ('charger', 'pond') and b['energy'] >= 100:
            return 'Already fully charged.'
        if item['id'] == 'incubator':
            return self.nursery_reason(bird)
        if item['id'] == 'table' and not any(k != bird and self.room_of(v) == room for k, v in self.data['birds'].items()):
            return 'Invite another bird to the table.'
        if item['id'] in ('book', 'press', 'built-library') and not self.society.bird(bird).linguistics['tokens']:
            return 'Teach this bird a few words first.'
        return None

    def tinker(self, bird):
        b = self.data['birds'][bird]
        self.require(b['scrap'] >= 2, 'A wind-up toy needs two spare parts.')
        b['scrap'] -= 2
        b['toys'] = min(9999, b.get('toys', 0) + 1)
        b['energy'] = min(100, b['energy'] + 5)
        self.stimulate(bird, 'NovelInput')
        self.emit(bird, 'Two spare parts. One extremely important wind-up friend.', 'action')
        return 'Built a wind-up toy: 2 parts used, 5 charge restored.'

    def interact_object(self, bird, room, object_id):
        self.require(isinstance(room, str) and room in self.spaces(), 'Unknown room.')
        item = next((v for v in self.room_items(room) if v['id'] == object_id), None)
        self.require(item is not None, 'Unknown room object.')
        reason = self.object_reason(bird, room, item)
        self.require(reason is None, reason)
        b = self.data['birds'][bird]
        # All eligibility checks precede mutations.
        if object_id == 'incubator':
            child = self.hatch(bird)
            reply = f"Welcome, {self.specs[child]['name']}. A new little voice."
        elif object_id == 'workbench':
            reply = self.tinker(bird)
        else:
            b['scrap'] -= item['cost']
            if object_id in ('drawers', 'built-salvager'):
                recovered = min(8 - b['scrap'], item.get('level', 1))
                b['scrap'] += recovered
                reply = f'Found {recovered} useful spare parts.'
            elif object_id in ('charger', 'pond', 'built-solar', 'built-shelter', 'built-planter'):
                gained = min(100 - b['energy'], (25 if object_id in ('charger', 'built-solar', 'built-shelter') else 10) * item.get('level', 1))
                b['energy'] += gained
                reply = f"Used the {item['name'].lower()}. {gained} charge restored."
            elif object_id == 'perch':
                b['nest'] = min(5, b['nest'] + 1)
                b['energy'] = min(100, b['energy'] + 15)
                reply = 'Three parts fitted. A sturdier perch and freshly cleaned charging contacts.'
            elif object_id == 'planter':
                reply = 'A watering bracket fitted. The garden has a little more support.'
            elif object_id in ('book', 'press', 'built-library'):
                lonk = self.society.bird(bird)
                thought = language.reflect(lonk) or ' '.join(list(lonk.linguistics['tokens'])[:6])
                lonk.social['thoughts'].append(dict(tick=self.data['tick'], text=thought))
                lonk.social['thoughts'] = lonk.social['thoughts'][-self.society.world.config['culture']['thought_history']:]
                self.emit(bird, thought, 'thought')
                if object_id == 'press':
                    self.data.setdefault('printed_stories', []).append(dict(bird=bird, text=thought, tick=self.data['tick']))
                    self.data['printed_stories'] = self.data['printed_stories'][-20:]
                reply = 'A little phrase printed for the archive.' if object_id == 'press' else 'A remembered word turns into another thought.'
            elif object_id == 'table':
                friend = next(k for k, v in self.data['birds'].items() if k != bird and self.room_of(v) == room)
                self.society.converse(bird, friend)
                self.bond(bird, friend, 2)
                self.social_notes()
                reply = f"Trading words with {self.specs[friend]['name']}."
            elif object_id in ('radio', 'built-chimes'):
                for key, other in self.data['birds'].items():
                    if self.room_of(other) == room:
                        self.stimulate(key, 'MusicPulse')
                        if self.data['taught']:
                            other['knows_song'] = True
                reply = 'A washer becomes a tiny bell. The room joins in.'
            else:  # Nursery mobile: parts become a developmental toy, not a free birth.
                for key, other in self.data['birds'].items():
                    if self.room_of(other) == room:
                        self.stimulate(key, 'HarmonicRise')
                        other['energy'] = min(100, other['energy'] + 8)
                reply = 'A new learning toy for the nursery. Little lights follow its movement.'
            self.stimulate(bird, 'HarmonicRise')
            self.emit(bird, reply, 'action')
        b.setdefault('object_ticks', {})[room + ':' + object_id] = self.data['tick']
        objects = self.data.setdefault('room_objects', {}).setdefault(room, {})
        objects[object_id] = min(9999, objects.get(object_id, 0) + 1)
        b['activity'] = item['label'].lower()
        self.note(self.specs[bird]['name'], reply)
        return reply

    def autonomous_objects(self):
        keys = list(self.specs)
        key = keys[self.data['tick'] % len(keys)]
        b = self.data['birds'][key]
        if b.get('world_project'):
            return
        if self.wants_nursery(key) and b['nest'] >= 2:
            return  # Reserve parts for the parent's nursery goal.
        if b['scrap'] >= 2 and b['nest'] >= 5 and self.nursery_reason(key) is not None:
            from world_building import BLUEPRINTS
            available = [bp for bp in BLUEPRINTS if self.build_reason(self.room_of(b), bp, key) is None]
            if available:
                self.build(self.room_of(b), available[0], key)
                return
            if b['scrap'] >= 6:
                self.note(self.specs[key]['name'], self.tinker(key))
                return
        if b.get('destination') and b['destination'] != self.room_of(b):
            return
        room = self.room_of(b)
        choices = [o for o in self.room_items(room) if o['id'] != 'incubator' and self.object_reason(key, room, o) is None]
        if choices:
            item = choices[(self.data['tick'] // len(keys)) % len(choices)]
            self.interact_object(key, room, item['id'])
