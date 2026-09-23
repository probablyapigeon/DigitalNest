import copy
import json
import tempfile
import unittest
from pathlib import Path

from game import World
from flock_society import MAX_FLOCK
from vendor.lonkworld import lonk_language as language, lonk_society as society

PHRASE = 'beep boop moonberry moss garden warm nest friend song shiny feather home'


class FlockSocietyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'save.json'
        self.world = World(self.path)
        for action in ('wake', 'inspect', 'salvage', 'repair', 'hatch'):
            self.world.act(action)

    def tearDown(self):
        self.temp.cleanup()

    def develop_colony(self):
        for _ in range(6):
            self.world.act('teach_words', value={'text': PHRASE, 'everyone': True})
        for _ in range(8):
            self.world.act('visit', bird='pip', value='moss')

    def test_player_words_associations_and_real_teaching(self):
        self.world.act('teach_words', bird='pip', value={'text': PHRASE})
        a, b = self.world.society.bird('pip'), self.world.society.bird('moss')
        self.assertIn('moonberry', a.linguistics['tokens'])
        self.assertIn('boop', a.linguistics['bigrams']['beep'])
        self.assertNotIn('moonberry', b.linguistics['tokens'])
        a.speak(language.compose(a, prompt='moonberry'), target=b)
        self.assertIn('moonberry', b.linguistics['tokens'])
        self.assertEqual(b.linguistics['origins']['moonberry'], a.uid)

    def test_stages_depend_on_learning_and_innovation_is_internal(self):
        a = self.world.society.bird('pip')
        a.age = 999
        society.develop(a)
        self.assertEqual(a.social['stage'], 'hatchling')
        for i in range(6):
            self.world.act('teach_words', value={'text': PHRASE})
            if i == 0:
                self.assertEqual(a.social['stage'], 'apprentice')
            if i == 2:
                self.assertEqual(a.social['stage'], 'storyteller')
        self.assertEqual(a.social['stage'], 'graduate')
        heard = a.linguistics['total_heard']
        self.world.society.world.config['culture']['innovation_chance'] = 1
        for _ in range(16):
            language.reflect(a)
        self.assertTrue(a.linguistics['innovations'])
        self.assertEqual(a.linguistics['total_heard'], heard)

    def test_reciprocal_partnerships_colonies_and_hatchling_inheritance(self):
        self.world.society.world.config['society']['bond_chance'] = 1
        self.develop_colony()
        for _ in range(8):
            self.world.act('visit', bird='pip', value='alto')
        parent = self.world.society.bird('pip')
        self.assertGreaterEqual(len(parent.social['partners']), 2)
        self.assertIsNotNone(parent.social['colony_id'])
        for uid in parent.social['partners']:
            partner = self.world.society.bird(self.world.society.key(uid))
            self.assertIn(parent.uid, partner.social['partners'])
        self.world.data['birds']['pip'].update(nest=2, scrap=3)
        before = copy.deepcopy(parent.linguistics)
        self.world.act('nursery', bird='pip')
        child_key = next(k for k in self.world.specs if k.startswith('chick-'))
        baby = self.world.society.bird(child_key)
        self.assertTrue(parent.alive)
        self.assertEqual(baby.generation, 2)
        self.assertEqual(baby.social['parents'], [parent.uid])
        self.assertEqual(baby.social['stage'], 'hatchling')
        self.assertEqual(baby.linguistics['total_heard'], 0)
        mutation = self.world.society.world.config['world']['inheritance_mutation']
        self.assertTrue(all(abs(baby.personality[k] - parent.personality[k]) <= mutation for k in parent.personality))
        self.assertIn('moonberry', baby.linguistics['tokens'])
        self.assertIn(child_key, self.world.brains)
        baby.linguistics['tokens']['moonberry'] += 3
        self.assertEqual(parent.linguistics, before)
        self.world.save()
        restored = World(self.path)
        self.assertEqual(self.world.export(), restored.export())
        self.world.tick()
        restored.tick()
        self.assertEqual(self.world.export(), restored.export())

    def test_schema_one_migration_keeps_old_brains_and_makes_backup(self):
        modern = self.world.export()
        old = {'schema': 1, 'world': modern['world'], 'brains': modern['brains']}
        raw = json.dumps(old).encode()
        self.path.write_bytes(raw)
        migrated = World(self.path)
        self.assertEqual(migrated.data, old['world'])
        self.assertEqual({k:b.export_checkpoint() for k,b in migrated.brains.items()}, old['brains'])
        self.assertEqual(self.path.read_bytes(), raw)
        migrated.save()
        self.assertEqual(self.path.with_name('save.before-society.json').read_bytes(), raw)
        self.assertEqual(json.loads(self.path.read_text())['schema'], 2)

    def test_population_cap_and_invalid_teaching_leave_state_unchanged(self):
        before = self.world.export()
        for action, value in [('nursery', None), ('teach_words', {'text': ''}), ('visit', 'pip')]:
            with self.assertRaises(ValueError):
                self.world.act(action, value=value)
        self.assertEqual(before, self.world.export())
        self.develop_colony()
        for _ in range(MAX_FLOCK - 4):
            self.world.data['birds']['pip'].update(nest=2, scrap=3, last_hatch=-20)
            self.world.act('nursery', bird='pip')
        self.assertEqual(len(self.world.specs), MAX_FLOCK)
        before = self.world.export()
        with self.assertRaises(ValueError):
            self.world.act('nursery', bird='pip')
        self.assertEqual(before, self.world.export())

    def test_autonomous_nursery_keeps_parents_and_transmits_language(self):
        self.develop_colony()
        for _ in range(60):
            self.world.tick()
        children = [k for k in self.world.specs if k.startswith('chick-')]
        self.assertTrue(children)
        self.assertLessEqual(len(self.world.specs), MAX_FLOCK)
        self.assertTrue(all(self.world.society.bird(k).alive for k in ('pip', 'moss', 'zip', 'alto')))
        self.assertTrue(all(self.world.society.bird(k).social['parents'] for k in children))
        self.assertTrue(any('moonberry' in self.world.society.bird(k).linguistics['tokens'] for k in children))

if __name__ == '__main__':
    unittest.main()
