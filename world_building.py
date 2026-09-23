"""Saved world topology, player supplies and part-funded habitat construction."""
import copy
from spaces import SPACES
from habitat_life import OBJECTS

MAX_WORLDS = 18
WORLD_COST = 8
STARTING_SUPPLIES = 24
PLOTS = [(-310, 140), (-190, 180), (-65, 200), (65, 200), (190, 180), (310, 140)]
BLUEPRINTS = {
    'solar': dict(name='Solar canopy', cost=4, label='Charge under the canopy', effect='Restores charge; passively powers resident birds.'),
    'planter': dict(name='Flower terrace', cost=2, label='Tend the flowers', effect='Restores a little charge and stimulates LUMINA growth.'),
    'shelter': dict(name='Cozy shelter', cost=3, label='Rest in the shelter', effect='A sheltered resting place that restores charge.'),
    'salvager': dict(name='Parts recycler', cost=4, label='Recover a spare part', effect='Produces a usable part on each cooldown.'),
    'library': dict(name='Story perch', cost=3, label='Reflect on remembered words', effect='Turns learned words into saved thoughts.'),
    'chimes': dict(name='Wind chimes', cost=2, label='Play the chimes', effect='Stimulates music responses in the room.'),
}


class WorldBuilding:
    def validate_building_state(self):
        catalog = self.spaces()
        if not isinstance(catalog, dict) or not set(SPACES) <= set(catalog) or len(catalog) > MAX_WORLDS:
            raise ValueError('Invalid saved world catalog')
        for key, room in catalog.items():
            if not isinstance(key, str) or not isinstance(room, dict) or room.get('kind') not in SPACES:
                raise ValueError('Invalid saved world theme')
            if not isinstance(room.get('name'), str) or not 1 <= len(room['name']) <= 40:
                raise ValueError('Invalid saved world name')
            links = room.get('links')
            if not isinstance(links, list) or any(not isinstance(n, str) or n not in catalog or n == key for n in links) or len(set(links)) != len(links):
                raise ValueError('Invalid saved portal links')
        seen, pending = set(), ['workshop']
        while pending:
            key = pending.pop()
            if key in seen:
                continue
            seen.add(key)
            for other in catalog[key]['links']:
                if key not in catalog[other]['links']:
                    raise ValueError('Saved portals must be reciprocal')
                pending.append(other)
        if seen != set(catalog):
            raise ValueError('Saved worlds must remain connected')
        if type(self.supplies()) is not int or not 0 <= self.supplies() <= 999:
            raise ValueError('Invalid saved construction supplies')
        for bird in self.data['birds'].values():
            if self.room_of(bird) not in catalog or ('destination' in bird and bird['destination'] not in catalog):
                raise ValueError('A saved bird references an unknown world')
        for room, structures in self.data.get('structures', {}).items():
            if room not in catalog or not isinstance(structures, list) or len(structures) > len(BLUEPRINTS):
                raise ValueError('Invalid saved structures')
            types = set()
            for structure in structures:
                kind = structure.get('type')
                if kind not in BLUEPRINTS or kind in types or type(structure.get('level')) is not int or not 1 <= structure['level'] <= 3:
                    raise ValueError('Invalid saved structure level or type')
                types.add(kind)

    def spaces(self):
        return self.data.get('world_catalog', SPACES)

    def supplies(self):
        return self.data.get('building_supplies', STARTING_SUPPLIES)

    def structures(self, room):
        return self.data.get('structures', {}).get(room, [])

    def room_items(self, room):
        result = copy.deepcopy(OBJECTS[self.spaces()[room]['kind']])
        for i, structure in enumerate(self.structures(room)):
            spec = BLUEPRINTS[structure['type']]
            result.append(dict(id='built-' + structure['type'], name=spec['name'], label=spec['label'], cost=0,
                               x=PLOTS[i][0], y=PLOTS[i][1], level=structure['level'], built=True))
        return result

    def build_reason(self, room, blueprint, bird=None):
        if not self.data['habitat_open']:
            return 'Meet the flock first.'
        if room not in self.spaces() or blueprint not in BLUEPRINTS:
            return 'Choose a world and a blueprint.'
        existing = next((s for s in self.structures(room) if s['type'] == blueprint), None)
        if existing and existing['level'] >= 3:
            return 'Fully upgraded to level 3.'
        if bird and self.room_of(self.data['birds'][bird]) != room:
            return 'Invite the builder into this world first.'
        parts = self.data['birds'][bird]['scrap'] if bird else self.supplies()
        if parts < BLUEPRINTS[blueprint]['cost']:
            return f"Needs {BLUEPRINTS[blueprint]['cost']} parts from {'this bird' if bird else 'station supplies'}."
        return None

    def build(self, room, blueprint, bird=None):
        self.require(isinstance(room, str) and isinstance(blueprint, str), 'Choose a world and blueprint.')
        reason = self.build_reason(room, blueprint, bird)
        self.require(reason is None, reason)
        cost = BLUEPRINTS[blueprint]['cost']
        if bird:
            self.data['birds'][bird]['scrap'] -= cost
        else:
            self.data['building_supplies'] = self.supplies() - cost
        structures = self.data.setdefault('structures', {}).setdefault(room, [])
        structure = next((s for s in structures if s['type'] == blueprint), None)
        if structure:
            structure['level'] += 1
            structure['upgraded_by'] = bird or 'user'
        else:
            structure = dict(type=blueprint, level=1, builder=bird or 'user', tick=self.data['tick'])
            structures.append(structure)
        name = BLUEPRINTS[blueprint]['name']
        reply = f"{name}, level {structure['level']}, built in {self.spaces()[room]['name']}. {cost} parts used."
        self.note(self.specs[bird]['name'] if bird else 'You', reply)
        if bird:
            self.stimulate(bird, 'HarmonicRise')
            self.emit(bird, reply, 'action')
            self.data['birds'][bird]['activity'] = f'building a {name.lower()}'
        return reply

    def create_world(self, name, kind, link):
        self.require(self.data['habitat_open'], 'Meet the flock first.')
        self.require(isinstance(name, str) and 1 <= len(name.strip()) <= 40 and all(ord(c) >= 32 for c in name), 'Name your world using 1-40 printable characters.')
        self.require(isinstance(kind, str) and kind in SPACES and isinstance(link, str) and link in self.spaces(), 'Choose a theme and an existing portal connection.')
        self.require(len(self.spaces()) < MAX_WORLDS, f'This station has room for {MAX_WORLDS} worlds.')
        self.require(name.strip().casefold() not in {r['name'].casefold() for r in self.spaces().values()}, 'That world name is already in use.')
        self.require(self.supplies() >= WORLD_COST, f'A new world needs {WORLD_COST} station parts.')
        serial = self.data.get('next_world', 1)
        key = f'world-{serial}'
        catalog = copy.deepcopy(self.spaces())
        catalog[key] = dict(name=name.strip(), kind=kind, subtitle='Built together. A new place to belong.',
                            color=SPACES[kind]['color'], icon=SPACES[kind]['icon'], links=[link], map=[0, 0])
        catalog[link]['links'].append(key)
        self.data['world_catalog'] = catalog
        self.data['next_world'] = serial + 1
        self.data['building_supplies'] = self.supplies() - WORLD_COST
        self.data['last_created_world'] = key
        self.note('You', f"Built {name.strip()}, connected to {catalog[link]['name']}.")
        return f"{name.strip()} is ready. A new portal connects it to {catalog[link]['name']}."

    def player_object_reason(self, room, item):
        if not self.data['habitat_open']:
            return 'Meet the flock first.'
        if item['id'] == 'incubator':
            return 'Select an eligible parent and use the bird action to build a hatchling.'
        if self.supplies() < item['cost']:
            return f"Needs {item['cost']} station parts. Salvage supplies or ask a bird to donate."
        last = self.data.get('player_object_ticks', {}).get(room + ':' + item['id'], -10)
        if self.data['tick'] - last < 2:
            return 'Cooling down. Resume station time to use it again.' if self.data['paused'] else 'Ready again in two station minutes.'
        return None

    def player_interact(self, room, object_id):
        self.require(isinstance(room, str) and room in self.spaces(), 'Unknown room.')
        item = next((o for o in self.room_items(room) if o['id'] == object_id), None)
        self.require(item is not None, 'Unknown object.')
        reason = self.player_object_reason(room, item)
        self.require(reason is None, reason)
        self.data['building_supplies'] = self.supplies() - item['cost']
        residents = [k for k, b in self.data['birds'].items() if self.room_of(b) == room]
        if object_id in ('drawers', 'built-salvager'):
            self.data['building_supplies'] = min(999, self.supplies() + 2 * item.get('level', 1))
            reply = f"Recovered {2 * item.get('level', 1)} parts for station building supplies."
        elif object_id in ('book', 'press', 'built-library'):
            stories = self.data.get('printed_stories', [])
            reply = stories[-1]['text'] if stories else 'A blank page, waiting for the flock to teach it something.'
            for key in residents:
                self.society.bird(key).speak()
            self.social_notes()
        elif object_id == 'table':
            if len(residents) > 1:
                self.society.converse(*residents[:2])
                self.social_notes()
            reply = 'You set the table for a little conversation.'
        elif object_id in ('charger', 'pond', 'perch', 'built-solar', 'built-shelter', 'built-planter'):
            self.data.setdefault('room_charge', {})[room] = min(100, self.data.get('room_charge', {}).get(room, 0) + 25 * item.get('level', 1))
            reply = f"Added {25 * item.get('level', 1)} charge to this world. Resident and arriving birds can use it."
        else:
            for key in residents:
                self.stimulate(key, 'MusicPulse' if object_id in ('radio', 'built-chimes') else 'HarmonicRise')
            reply = f"You used the {item['name'].lower()}. Its improvements stay with this world."
        uses = self.data.setdefault('room_objects', {}).setdefault(room, {})
        uses[object_id] = min(9999, uses.get(object_id, 0) + 1)
        self.data.setdefault('player_object_ticks', {})[room + ':' + object_id] = self.data['tick']
        self.note('You', reply)
        return reply

    def apply_building_effects(self):
        for bird in self.data['birds'].values():
            room = self.room_of(bird)
            power = sum(s['level'] for s in self.structures(room) if s['type'] == 'solar')
            reserve = self.data.get('room_charge', {}).get(room, 0)
            transfer = min(5, reserve, 100 - bird['energy'])
            bird['energy'] = min(100, bird['energy'] + transfer + power)
            if transfer:
                self.data['room_charge'][room] -= transfer

    def building_payload(self):
        return dict(supplies=self.supplies(), world_cost=WORLD_COST, max_worlds=MAX_WORLDS,
                    blueprints=copy.deepcopy(BLUEPRINTS), structures=copy.deepcopy(self.data.get('structures', {})),
                    reasons={room: {bp: dict(user=self.build_reason(room, bp), birds={k: self.build_reason(room, bp, k) for k in self.specs})
                                    for bp in BLUEPRINTS} for room in self.spaces()})
