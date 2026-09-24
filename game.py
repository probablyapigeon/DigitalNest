"""Little Flock: deterministic habitat + independent, genuine LUMINA XC brains."""
import copy
import json
import os
import shutil
import re
import uuid
from pathlib import Path

from vendor import xc
from lonk_life import LonkLife
from flock_society import FlockSociety, MAX_FLOCK
from spaces import SPACES, LOCATION_SPACE, next_portal
from habitat_life import HabitatLife, OBJECTS
from world_building import WorldBuilding, BLUEPRINTS
from language_archive import LanguageArchive
from heart import initial_heart, heart_event

ROOT = Path(__file__).resolve().parent
SOURCE = (ROOT / 'vendor' / 'lumina_core.xc').read_text(encoding='utf-8')
BIRDS = {
    'pip': dict(name='Pip', role='Chief intelligence officer. Allegedly.', color='#e9b65f', seed=260914,
                personality='Composed, practical, dryly funny. Secretly affectionate. Collects washers. Calls the player technician.'),
    'moss': dict(name='Moss', role='Nest architect & quiet caretaker', color='#8fc6ae', seed=260925,
                 personality='Gentle, observant, few words. Repairs friends nests and denies being sentimental. Loves plants.'),
    'zip': dict(name='Zip', role='Salvage enthusiast / minor liability', color='#e89079', seed=260936,
                personality='Quick, curious, enthusiastic. Collects improbable inventions. Kind, never mean. Bad at whispering.'),
    'alto': dict(name='Alto', role='Ventilation choir, founding member', color='#a8a5d9', seed=260947,
                 personality='Dreamy, musical, thoughtful. Hums to the ventilation. Finds beauty in ordinary machinery.'),
}
PLACES = {'bench': [0.28, 0.67], 'nest': [0.73, 0.42], 'scrap': [0.28, 0.41],
          'heater': [0.72, 0.70], 'choir': [0.52, 0.48], 'garden': [0.48, 0.75]}
IR = {key: xc.compile_text(SOURCE.replace('seed = 260914', f"seed = {spec['seed']}"), 'lumina_core.xc')
      for key, spec in BIRDS.items()}


class World(HabitatLife, WorldBuilding, LonkLife):
    def __init__(self, save_path):
        self.path = Path(save_path)
        self.specs = copy.deepcopy(BIRDS)
        self._needs_legacy_backup = False
        if self.path.exists():
            try:
                saved = json.loads(self.path.read_text(encoding='utf-8'))
                if saved['schema'] not in (1, 2):
                    raise ValueError('Unsupported save version')
                self.specs = saved['catalog'] if saved['schema'] == 2 else self.specs
                self.data = saved['world']
                if not 4 <= len(self.specs) <= MAX_FLOCK or set(self.specs) != set(self.data['birds']) or not set(BIRDS) <= set(self.specs):
                    raise ValueError('Invalid flock catalog')
                self.brains = {key: xc.Runtime(self.brain_ir(key), checkpoint_data=saved['brains'][key]) for key in self.specs}
                for key in ('birds', 'tick', 'awake', 'wing_fixed', 'habitat_open', 'journal', 'chats'):
                    if key not in self.data:
                        raise ValueError('Incomplete save')
                self.society = FlockSociety(self.specs, saved.get('society'))
                if saved['schema'] == 2 and 'society' not in saved:
                    raise ValueError('Missing society checkpoint')
                if saved['schema'] == 1:
                    self._needs_legacy_backup = True
                    self.society.world.tick = self.data['tick']
                    # Import only real stored player messages, never invented conversations.
                    for chat in self.data['chats']:
                        if chat['role'] == 'user' and chat['bird'] in self.specs:
                            self.society.learn(chat['bird'], chat['text'])
                    for key, bird in self.data['birds'].items():
                        self.society.bird(key).social['affection'] = {
                            self.society.ids[other]: max(0, min(100, score - 20)) for other, score in bird['bonds'].items()}
                    self.society.drain()
                self.validate_building_state()
            except Exception as exc:
                raise ValueError(f'Cannot load {self.path}. Original save preserved: {exc}') from exc
        else:
            self.brains = {key: xc.Runtime(IR[key]) for key in self.specs}
            self.data = dict(tick=0, awake=False, inspected=False, servo=0, salvaged=False, wing_fixed=False,
                             habitat_open=False, cassette=False, reassured=False, listened=False,
                             decoded=False, taught=False, tape_reaction=None, paused=False,
                             heater=False, journal=[], chats=[], facts={}, birds={})
            for i, key in enumerate(BIRDS):
                self.data['birds'][key] = dict(energy=75 + i * 5, nest=1, scrap=0, knows_song=False,
                    activity='sleeping' if key == 'pip' else 'pottering', location='bench' if key == 'pip' else ['nest', 'scrap', 'choir'][i - 1],
                    bonds={other: 20 for other in BIRDS if other != key})
            self.note('Station log', 'A quiet station. Four small lives. One spare pair of hands.')
            self.society = FlockSociety(self.specs)

        self.data.setdefault('instance_id', uuid.uuid5(uuid.NAMESPACE_URL, str(self.path.resolve()) + str(self.data['tick'])).hex if self.path.exists() else uuid.uuid4().hex)
        self.data.setdefault('player_identity', uuid.uuid5(uuid.NAMESPACE_URL, str(self.path.parent.resolve())).hex)
        self.archive = LanguageArchive(self)
        language = self.society.app.procedures.namespaces['language']
        native_learn = language.learn
        def archived_learn(lonk, message, speaker_id='player', internal=False):
            if not internal:
                key = self.society.key(lonk.uid)
                if key:
                    self.archive.seed_existing()
                    self.archive.queue(key, message, str(speaker_id))
            return native_learn(lonk, message, speaker_id, internal)
        language._scope['learn'] = archived_learn
        native_innovate = language._innovate
        def archived_innovation(lonk, word):
            self.archive.seed_existing()
            result = native_innovate(lonk, word)
            key = self.society.key(lonk.uid)
            if key and result != word:
                self.archive.queue(key, result, 'invention')
            return result
        language._scope['_innovate'] = archived_innovation

    def brain_ir(self, key):
        if key in IR:
            return IR[key]
        return xc.compile_text(SOURCE.replace('seed = 260914', f"seed = {int(self.specs[key]['seed'])}"), 'lumina_core.xc')

    def export(self):
        return copy.deepcopy({'schema': 2, 'world': self.data, 'catalog': self.specs, 'society': self.society.export(),
                              'brains': {k: b.export_checkpoint() for k, b in self.brains.items()}})

    def save(self):
        self.archive.seed_existing()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self._needs_legacy_backup and self.path.exists():
            backup = self.path.with_name(self.path.stem + '.before-society.json')
            if not backup.exists():
                shutil.copy2(self.path, backup)
            self._needs_legacy_backup = False
        temp = self.path.with_suffix('.tmp')
        with temp.open('w', encoding='utf-8') as handle:
            json.dump(self.export(), handle, ensure_ascii=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, self.path)
        self.archive.flush()

    def note(self, who, text):
        self.data['journal'].append({'tick': self.data['tick'], 'who': who, 'text': text})
        self.data['journal'] = self.data['journal'][-60:]

    def stimulate(self, key, event):
        brain = self.brains[key]
        heart = self.data['birds'][key].setdefault('heart', initial_heart())
        heart_event(heart, {'Quiet': .55, 'NovelInput': .7, 'HarmonicRise': .85, 'MusicPulse': .8}.get(event, .5))
        before = brain.morphology_summary()['Structural']['nodes']
        brain.dispatch(event)
        after = brain.morphology_summary()['Structural']['nodes']
        if after > before:
            self.note(self.specs[key]['name'], 'A new connection glows in their LUMINA lattice.')

    def require(self, condition, message):
        if not condition:
            raise ValueError(message)

    def act(self, action, bird='pip', value=None):
        self.require(bird in self.specs, 'Unknown bird.')
        d = self.data
        if action == 'natural_conversations':
            d['natural_conversations'] = not d.get('natural_conversations', True)
            reply = 'Natural conversations enabled.' if d['natural_conversations'] else 'The birds will use their learned language without the local model.'
        elif action == 'plan_world':
            reply = self.plan_world(bird)
        elif action == 'lonk_life':
            self.require(isinstance(value, dict), 'Choose a Lonk activity.')
            reply = self.lonk_event(bird, value.get('event'), value.get('target'))
        elif action == 'wake':
            self.require(not d['awake'], 'Pip is already awake.')
            d['awake'] = True
            d['birds']['pip']['activity'] = 'waiting by the repair bench'
            self.stimulate('pip', 'NovelInput')
            reply = 'Diagnostics complete. You appear to be my technician. ...Oh. Neither of us is qualified.'
        elif action == 'inspect':
            self.require(d['awake'] and not d['inspected'], 'Wake Pip first; the wing only needs one inspection.')
            d['inspected'] = True
            self.stimulate('pip', 'Quiet')
            reply = 'Left wing servo: seized. Dignity: mostly intact. There should be a spare in that scrap drawer.'
        elif action == 'salvage':
            self.require(d['inspected'] and not d['salvaged'], 'Inspect the wing first. The spare can only be collected once.')
            d['servo'] = 1
            d['salvaged'] = True
            reply = 'One replacement servo. And a brass washer. I shall supervise the washer.'
        elif action == 'repair':
            self.require(d['inspected'] and d['servo'] == 1 and not d['wing_fixed'], 'Find a spare servo after inspecting the wing.')
            d['servo'] = 0
            d['wing_fixed'] = True
            self.stimulate('pip', 'HarmonicRise')
            reply = 'That joint has not moved properly in years. ...Thank you. Shall we meet the others?'
        elif action == 'hatch':
            self.require(d['wing_fixed'] and not d['habitat_open'], 'Repair Pip before opening the habitat.')
            d['habitat_open'] = True
            for key in self.specs:
                self.stimulate(key, 'NovelInput')
            reply = 'This is our human. Their wiring knowledge is limited, but they are trying. Be pleasant.'
            self.note('Zip', 'You brought someone! Can they fix the heater?')
        elif action == 'cassette':
            self.require(d['habitat_open'] and not d['cassette'], 'Open the habitat first. The cassette is already on the bench if collected.')
            d['cassette'] = True
            reply = 'A blue cassette. The label says HOME. I recognise the handwriting, but not the tune.'
        elif action == 'reassure':
            self.require(d['cassette'] and not d['decoded'] and not d['reassured'], 'Reassurance is available once during the cassette experiment.')
            d['reassured'] = True
            self.stimulate('pip', 'Quiet')
            reply = 'You will stay by the volume switch? Good. Strictly a maintenance precaution.'
        elif action == 'listen':
            self.require(d['cassette'] and not d['listened'], 'Find the cassette first. Its signal has already been sampled if heard.')
            d['listened'] = True
            d['tape_reaction'] = 'safe' if d['reassured'] else 'startled'
            self.stimulate('pip', 'HarmonicRise' if d['reassured'] else 'NovelInput')
            self.stimulate('pip', 'MusicPulse')
            reply = ('You waited until I was ready. I remember that. Three notes: two, four, three.' if d['reassured'] else
                     'A LITTLE WARNING. Please. ...There is a tune under the static: two, four, three.')
        elif action == 'tune':
            self.require(d['listened'] and not d['decoded'], 'Listen to the cassette before tuning.')
            self.require(value == [2, 4, 3], 'Still static. Match the three signal peaks: 2 - 4 - 3.')
            d['decoded'] = True
            d['birds']['pip']['knows_song'] = True
            self.stimulate('pip', 'HarmonicRise')
            reply = 'That is it. The sound the station made when somebody came home. I thought we had lost it.'
        elif action == 'teach':
            self.require(d['decoded'] and not d['taught'], 'Decode the home tune first. The flock is already learning if shared.')
            d['taught'] = True
            d['birds']['alto']['knows_song'] = True
            self.stimulate('alto', 'MusicPulse')
            self.bond('pip', 'alto', 12)
            reply = 'Alto, this is a historically important recording. You may harmonise. Sensibly.'
            self.note('Alto', 'A home tune. I will teach the others when we gather.')
        elif action == 'heater':
            self.require(d['habitat_open'] and not d['heater'], 'The heater is only available after opening the habitat, and only needs one repair.')
            d['heater'] = True
            for key in self.specs:
                self.stimulate(key, 'HarmonicRise')
            reply = 'Warm vents. A luxury previously available only to the dust. Moss has already moved a cushion.'
        elif action == 'gift':
            self.require(d['habitat_open'], 'Open the habitat first.')
            b = d['birds'][bird]
            self.require(b['scrap'] < 8, 'Their parts tray is full. Let them build something first.')
            b['scrap'] += 1
            self.stimulate(bird, 'NovelInput')
            reply = {'pip': 'An essential component. Place it in my quarters. Carefully.', 'moss': 'A little bracket. Just what that second perch needed.',
                     'zip': 'Oh! This could be a wheel. Or a hat. Critical research ahead.', 'alto': 'It rings when you tap it. May I keep the sound?'}.get(bird, 'A part for my very own nest. Thank you!')
        elif action == 'create_world':
            self.require(isinstance(value, dict), 'Name and connect your new world.')
            reply = self.create_world(value.get('name'), value.get('kind'), value.get('link'))
        elif action == 'build_structure':
            self.require(isinstance(value, dict) and value.get('payer') in ('user', 'bird'), 'Choose who is building.')
            reply = self.build(value.get('room'), value.get('blueprint'), bird if value['payer'] == 'bird' else None)
        elif action == 'donate_parts':
            self.require(d['habitat_open'] and d['birds'][bird]['scrap'] >= 1, 'This bird needs a part to donate.')
            self.require(self.supplies() < 999, 'Station supplies are full.')
            d['birds'][bird]['scrap'] -= 1
            d['building_supplies'] = self.supplies() + 1
            reply = 'One part added to shared world-building supplies.'
        elif action == 'salvage_supplies':
            self.require(d['habitat_open'], 'Meet the flock first.')
            self.require(d['tick'] - d.get('last_player_salvage', -10) >= 2, 'Resume station time; another salvage batch is ready in two minutes.')
            self.require(self.supplies() <= 995, 'Station supplies are full.')
            d['building_supplies'] = self.supplies() + 4
            d['last_player_salvage'] = d['tick']
            reply = 'Recovered four construction parts from station storage.'
        elif action == 'player_interact':
            self.require(isinstance(value, dict), 'Choose an object.')
            reply = self.player_interact(value.get('room'), value.get('object'))
        elif action == 'tinker':
            self.require(d['habitat_open'], 'Meet the flock first.')
            reply = self.tinker(bird)
        elif action == 'share_part':
            self.require(d['habitat_open'] and isinstance(value, str) and value in self.specs and value != bird, 'Choose a flock friend.')
            self.require(d['birds'][bird]['scrap'] >= 1, 'No spare parts to share.')
            self.require(d['birds'][value]['scrap'] < 8, 'Your friend already has a full tray.')
            d['birds'][bird]['scrap'] -= 1
            d['birds'][value]['scrap'] += 1
            self.bond(bird, value, 3)
            reply = f"One part delivered to {self.specs[value]['name']}. Something useful, from a friend."
            self.emit(bird, reply, 'action', value)
        elif action == 'interact':
            self.require(isinstance(value, dict), 'Choose an object in the room.')
            reply = self.interact_object(bird, value.get('room'), value.get('object'))
        elif action == 'whistle':
            self.require(d['habitat_open'], 'Open the habitat first.')
            self.stimulate(bird, 'MusicPulse')
            reply = 'A familiar little melody answers you.' if d['birds'][bird]['knows_song'] else 'A questioning chirp. They are listening.'
        elif action == 'teach_words':
            self.require(d['habitat_open'], 'Meet the flock first.')
            self.require(isinstance(value, dict) and isinstance(value.get('text'), str) and 1 <= len(value['text'].strip()) <= 500, 'Write 1–500 characters to teach.')
            target = 'everyone' if value.get('everyone') is True else bird
            self.learn_text(target, value['text'].strip())
            reply = 'We are listening. Those words are part of our little language now.'
        elif action == 'travel':
            self.require(d['habitat_open'], 'Meet the flock first.')
            self.require(isinstance(value, str) and value in self.spaces(), 'Choose a world on the map.')
            b = d['birds'][bird]
            b['destination'] = value
            b['stay_until'] = d['tick'] + 6
            reply = f"{self.specs[bird]['name']} is heading to {self.spaces()[value]['name']}. Follow their portal trail on the world map."
        elif action == 'visit':
            self.require(d['habitat_open'] and isinstance(value, str) and value in self.specs and value != bird, 'Choose a different flock friend to visit.')
            self.society.converse(bird, value)
            self.stimulate(bird, 'MusicPulse')
            self.stimulate(value, 'MusicPulse')
            d['birds'][bird]['room'] = self.room_of(d['birds'][bird])
            d['birds'][bird]['location'] = d['birds'][value]['location']
            d['birds'][bird]['destination'] = self.room_of(d['birds'][value])
            d['birds'][bird]['stay_until'] = d['tick'] + 6
            self.bond(bird, value, 2)
            self.social_notes()
            reply = f"{self.specs[bird]['name']} and {self.specs[value]['name']} trade a few words. Shared phrases can become a shared dialect."
        elif action == 'nursery':
            self.require(d['habitat_open'], 'Meet the flock first.')
            child = self.hatch(bird)
            reply = f"Welcome, {self.specs[child]['name']}. A little new voice, with a little family history."
        elif action == 'pause':
            d['paused'] = not d['paused']
            reply = 'Take your time. We will be right here.' if d['paused'] else 'Station routines resumed. The washer audit continues.'
        else:
            raise ValueError('Unknown action.')
        self.note(self.specs[bird]['name'] if action in ('gift', 'whistle', 'teach_words', 'visit', 'nursery', 'interact', 'tinker', 'share_part', 'plan_world') else 'Pip', reply)
        self.save()
        return reply

    def social_notes(self):
        for line in self.society.drain():
            self.note('Flock life', line)
            # Speech is emitted by the original XC speak procedure; no invented dialogue.
            match = re.match(r'^([^:]+): (.+)$', line)
            if match:
                speakers = match[1].split(' -> ', 1)
                key = next((k for k, spec in self.specs.items() if spec['name'] == speakers[0]), None)
                target = next((k for k, spec in self.specs.items() if len(speakers) > 1 and spec['name'] == speakers[1]), None)
                if key:
                    self.emit(key, match[2], 'speech', target)
                    if (target and self.data['taught'] and self.data['birds'][key]['knows_song']
                            and not self.data['birds'][target]['knows_song']
                            and self.room_of(self.data['birds'][key]) == self.room_of(self.data['birds'][target])):
                        self.data['birds'][target]['knows_song'] = True
                        self.stimulate(target, 'MusicPulse')
                        self.note(self.specs[target]['name'], 'Picked up the home tune while talking with a flock friend.')

    def learn_text(self, target, text):
        for key in (list(self.specs) if target == 'everyone' else [target]):
            self.archive.activate(key, text)
            heart_event(self.data['birds'][key].setdefault('heart', initial_heart()), .7,
                        pressure=bool(re.search(r'\b(hate|hurt|bad|stop)\b', text, re.I)))
        for key in self.society.learn(target, text):
            self.stimulate(key, 'NovelInput')
        self.social_notes()

    def nursery_reason(self, key):
        bird, social = self.data['birds'][key], self.society.bird(key).social
        if len(self.specs) >= MAX_FLOCK:
            return 'All eight habitat berths are occupied.'
        if social['stage'] != 'graduate':
            return 'Graduate first: learn 12 words across 6 conversations.'
        if social['colony_id'] is None:
            return 'Join or found a colony with a developed friend first.'
        if bird['nest'] < 2 or bird['scrap'] < 3:
            return 'A nursery needs a second perch and 3 spare parts.'
        if self.data['tick'] - bird.get('last_hatch', -20) < 20:
            return 'This parent is resting between nursery projects.'
        return None

    def hatch(self, parent):
        reason = self.nursery_reason(parent)
        self.require(reason is None, reason)
        number = self.society.world.next_uid
        key = f'chick-{number}'
        name = ['Wren', 'Pixel', 'Chirp', 'Sprocket'][len(self.specs) - 4]
        baby = self.society.hatch(parent, key, name)
        self.specs[key] = dict(name=name, role=f"Generation {baby.generation} · {self.specs[parent]['name']}'s hatchling",
                              color=self.specs[parent]['color'], seed=261000 + number,
                              personality=f"A curious young robot bird descended from {self.specs[parent]['name']}. Learning a voice of their own. Be gentle, playful, and concrete.")
        for friend in self.data['birds'].values():
            friend['bonds'][key] = 20
        self.data['birds'][key] = dict(energy=85, nest=1, scrap=0, knows_song=self.data['birds'][parent]['knows_song'],
            activity='discovering the nursery', location='nest', room='nursery', bonds={other: 20 for other in self.specs if other != key})
        self.data['birds'][parent]['scrap'] -= 3
        self.data['birds'][parent]['last_hatch'] = self.data['tick']
        self.brains[key] = xc.Runtime(self.brain_ir(key))
        self.archive.queue(key, '', 'inherited:' + parent, parent=parent)
        self.stimulate(key, 'HarmonicRise')
        self.social_notes()
        return key

    def bond(self, a, b, amount):
        for left, right in ((a, b), (b, a)):
            bonds = self.data['birds'][left]['bonds']
            bonds[right] = min(100, bonds[right] + amount)

    def room_of(self, bird):
        return bird.get('room', LOCATION_SPACE.get(bird['location'], 'workshop'))

    def advance_room(self, key, target):
        bird = self.data['birds'][key]
        old = self.room_of(bird)
        new = next_portal(old, target, self.spaces())
        bird['room'] = new
        if old != new:
            bird['crossing'] = dict(source=old, target=new, tick=self.data['tick'])
            bird['activity'] = f"arriving in {self.spaces()[new]['name']}"
            self.note(self.specs[key]['name'], f"Travelled from {self.spaces()[old]['name']} to {self.spaces()[new]['name']}.")

    def tick(self):
        d = self.data
        if d['paused'] or not d['habitat_open']:
            return
        d['tick'] += 1
        self.lonk_tick()
        for index, (key, bird) in enumerate(d['birds'].items()):
            brain = self.brains[key]
            if bird.get('destination') and (self.room_of(bird) != bird['destination'] or d['tick'] <= bird.get('stay_until', 0)):
                target = bird['destination']
                was_there = self.room_of(bird) == target
                self.advance_room(key, target)
                if not was_there and self.room_of(bird) == target:
                    bird['stay_until'] = d['tick'] + 4
                kind = self.spaces()[target]['kind']
                if self.room_of(bird) == target:
                    bird['activity'] = {'archive': 'remixing remembered words', 'nursery': 'watching over the little incubators',
                        'garden': 'tending the glass garden', 'roost': 'resting in a charging nest',
                        'commons': 'listening for a friend', 'workshop': 'sorting useful little things'}[kind]
                    if kind == 'roost':
                        bird['energy'] = min(100, bird['energy'] + 12)
                    self.stimulate(key, 'HarmonicRise' if kind in ('garden', 'nursery') else 'Quiet')
                continue
            bird.pop('destination', None)
            # Needs constrain actions; XC policy decides the remaining routine.
            # The shared choir period creates contact opportunities, not forced friendships.
            if bird['energy'] < 35:
                activity, place, event = 'recharging', 'nest', 'Quiet'
                bird['energy'] = min(100, bird['energy'] + 22)
            elif bird.get('world_project'):
                activity, place, event = 'saving parts for a world of their own', 'scrap', 'NovelInput'
                bird['scrap'] = min(8, bird['scrap'] + 1)
            elif self.wants_nursery(key) and bird['nest'] >= 2:
                bird['inner_life']['goal'] = 'Save three parts for a little descendant'
                if bird['scrap'] < 3:
                    activity, place, event = 'collecting parts for a nursery', 'scrap', 'NovelInput'
                    bird['scrap'] += 1
                else:
                    activity, place, event = 'preparing a nursery', 'nest', 'HarmonicRise'
            elif bird['scrap'] >= 3 and bird['nest'] < 5:
                activity, place, event = 'building a perch', 'nest', 'HarmonicRise'
                bird['scrap'] -= 3
                bird['nest'] += 1
                self.note(self.specs[key]['name'], 'Built another perch from collected parts. There is room for a friend.')
            elif d['taught'] and d['tick'] % 6 == 0:
                activity, place, event = 'gathering for the home tune', 'choir', 'MusicPulse'
            elif (d['tick'] + index) % 7 == 0:
                activity, place, event = {
                    'pip': ('conducting a washer audit', 'bench', 'Quiet'),
                    'moss': ('checking the flock nests', 'nest', 'HarmonicRise'),
                    'zip': ('sorting gifts for friends', 'scrap', 'NovelInput'),
                    'alto': ('composing a ventilation duet', 'choir', 'MusicPulse'),
                }.get(key, ('practising a family tune', 'choir', 'MusicPulse'))
                if key == 'moss' and bird['scrap'] > 0:
                    friend = min((k for k in self.specs if k != key), key=lambda k: d['birds'][k]['energy'])
                    bird['scrap'] -= 1
                    d['birds'][friend]['energy'] = min(100, d['birds'][friend]['energy'] + 8)
                    self.bond(key, friend, 3)
                    self.note('Moss', f"Adjusted {self.specs[friend]['name']}'s charging contacts. Purely routine. Definitely not affection.")
                elif key == 'zip' and bird['scrap'] > 0:
                    friend = min((k for k in self.specs if k != key), key=lambda k: d['birds'][k]['scrap'])
                    if d['birds'][friend]['scrap'] < 8:
                        bird['scrap'] -= 1
                        d['birds'][friend]['scrap'] += 1
                        self.bond(key, friend, 3)
                        self.note('Zip', f"Left a useful little part beside {self.specs[friend]['name']}'s nest.")
            elif (d['tick'] + index) % 5 == 0:
                activity, place, event = 'collecting spare parts', 'scrap', 'NovelInput'
                bird['scrap'] = min(8, bird['scrap'] + 1)
            else:
                activity, place, event = self.lonk_routine(key)
            old_room = self.room_of(bird)
            bird['activity'], bird['location'] = activity, place
            bird['room'] = old_room
            target = LOCATION_SPACE[place]
            if (d['tick'] + index) % 11 == 0:
                destinations = ['archive', 'nursery'] + [r for r in self.spaces() if r not in SPACES]
                target = destinations[(d['tick'] // 11 + index) % len(destinations)]
                bird['destination'], bird['stay_until'] = target, d['tick'] + 5
            self.advance_room(key, target)
            if activity != 'recharging':
                bird['energy'] = max(0, bird['energy'] - (3 if d['heater'] else 4))
            self.stimulate(key, event)
        keys = list(self.specs)
        for i, a in enumerate(keys):
            for b in keys[i + 1:]:
                left, right = d['birds'][a], d['birds'][b]
                if left['location'] == right['location']:
                    self.bond(a, b, 1)
                    if d['taught'] and left['knows_song'] != right['knows_song'] and left['location'] == 'choir':
                        learner = b if left['knows_song'] else a
                        d['birds'][learner]['knows_song'] = True
                        self.stimulate(learner, 'MusicPulse')
                        self.note(self.specs[learner]['name'], 'Learned the home tune from a flock friend. A tiny tradition takes root.')
        heard_before = {key: self.society.bird(key).linguistics['total_heard'] for key in self.specs}
        self.society.tick(d['tick'], {key: self.room_of(bird) for key, bird in d['birds'].items()})
        for key in self.specs:
            if self.society.bird(key).linguistics['total_heard'] > heard_before[key]:
                self.stimulate(key, 'MusicPulse')
        self.social_notes()
        for key in self.specs:
            for thought in self.society.bird(key).social['thoughts']:
                if thought['tick'] == d['tick']:
                    self.emit(key, thought['text'], 'thought')
        self.autonomous_objects()
        self.advance_world_projects()
        self.apply_building_effects()
        # Nursery construction is paced and nonlethal. Parents remain in the flock.
        if d['tick'] % 12 == 0:
            for key in list(self.specs):
                graduated = self.society.bird(key).social['graduated_at']
                if graduated is not None and d['tick'] - graduated >= 20 and self.nursery_reason(key) is None:
                    self.hatch(key)
                    break
        self.save()

    def payload(self):
        d = copy.deepcopy(self.data)
        d.pop('spoken_phrases', None)
        d.pop('_language_pending', None)
        d['spaces'] = copy.deepcopy(self.spaces())
        d['building'] = self.building_payload()
        for room_id, room in d['spaces'].items():
            room.setdefault('design', self.world_design(room_id))
            room['residents'] = [key for key, b in d['birds'].items() if self.room_of(b) == room_id]
            room['visits'] = sum(1 for entry in d['journal'] if f"to {room['name']}." in entry['text'])
        d['objects'] = {room: self.room_items(room) for room in self.spaces()}
        for room, items in d['objects'].items():
            for item in items:
                item['uses'] = d.get('room_objects', {}).get(room, {}).get(item['id'], 0)
                item['player_reason'] = self.player_object_reason(room, item)
                item['reasons'] = {k: self.object_reason(k, room, item) for k in self.specs}
        d['voices'] = d.get('voices', [])
        d['society'] = self.society.payload()
        for key, bird in d['birds'].items():
            brain = self.brains[key]
            structure = brain.morph_state['Structural']
            bird.update({k: v for k, v in self.specs[key].items() if k not in ('seed', 'personality')})
            bird['room'] = self.room_of(bird)
            bird['culture'] = d['society']['birds'][key]
            bird['archive'] = self.archive.stats(key)
            bird['inner_life'] = self.lonk_profile(key)
            bird['nursery_reason'] = self.nursery_reason(key)
            bird.update(state=brain.state_dict(), policy=brain.action, events=brain.event_counter,
                        morphology=brain.morphology_summary()['Structural'],
                        lattice={'nodes': [{'id': n['id'], 'vector': n['vector']} for n in structure['nodes']],
                                 'edges': structure['connections']})
        return d
