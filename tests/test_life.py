import tempfile
import unittest
from pathlib import Path
from game import World
from habitat_life import OBJECTS


class LifeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'save.json'
        self.w = World(self.path)
        self.w.data.update(awake=True, habitat_open=True)

    def tearDown(self):
        self.tmp.cleanup()

    def test_full_trays_have_repeatable_sink_and_sharing_is_atomic(self):
        b = self.w.data['birds']['pip']
        b.update(scrap=8, nest=5)
        self.w.act('tinker', 'pip')
        self.assertEqual((b['scrap'], b['toys']), (6, 1))
        self.w.act('share_part', 'pip', 'moss')
        self.assertEqual(b['scrap'], 5)
        self.assertEqual(self.w.data['birds']['moss']['scrap'], 1)
        self.w.data['birds']['moss']['scrap'] = 8
        before = self.w.export()
        with self.assertRaises(ValueError):
            self.w.act('share_part', 'pip', 'moss')
        self.assertEqual(before, self.w.export())

    def test_autonomous_full_tray_gets_used(self):
        b = self.w.data['birds']['pip']
        b.update(scrap=8, nest=5)
        self.w.data['tick'] = 4  # Pip owns this bounded autonomous turn.
        self.w.autonomous_objects()
        self.assertEqual(b['scrap'], 4)
        self.assertEqual(self.w.structures('workshop')[0]['type'], 'solar')

    def test_every_room_has_usable_distinct_objects_and_persists(self):
        self.w.learn_text('pip', 'little moon garden friends remember warm birds')
        for room, items in OBJECTS.items():
            for item in items:
                if item['id'] == 'incubator':
                    continue  # Existing nursery tests cover eligible births.
                self.w.data['tick'] += 3
                self.w.data['birds']['pip'].update(room=room, scrap=5, energy=50)
                self.w.data['birds']['moss']['room'] = room
                self.w.act('interact', 'pip', dict(room=room, object=item['id']))
                self.assertEqual(self.w.data['room_objects'][room][item['id']], 1)
        self.assertTrue(self.w.data['printed_stories'])
        self.assertEqual(self.w.export(), World(self.path).export())

    def test_wrong_room_and_cooldown_do_not_mutate(self):
        before = self.w.export()
        with self.assertRaises(ValueError):
            self.w.act('interact', 'pip', dict(room='garden', object='pond'))
        self.assertEqual(before, self.w.export())
        self.w.data['birds']['pip'].update(room='garden', energy=50)
        self.w.act('interact', 'pip', dict(room='garden', object='pond'))
        self.assertEqual(self.w.data['birds']['pip']['energy'], 60)
        before = self.w.export()
        with self.assertRaises(ValueError):
            self.w.act('interact', 'pip', dict(room='garden', object='pond'))
        self.assertEqual(before, self.w.export())

    def test_real_xc_speech_and_thoughts_are_saved_and_bounded(self):
        self.w.learn_text('everyone', 'moonberry friend garden little warm song')
        self.w.act('visit', 'pip', 'moss')
        events = self.w.payload()['voices']
        self.assertTrue(any(e['kind'] == 'speech' and e['bird'] == 'pip' and e['target'] == 'moss' for e in events))
        self.w.data['birds']['pip']['room'] = 'archive'
        self.w.act('interact', 'pip', dict(room='archive', object='book'))
        thought = self.w.society.bird('pip').social['thoughts'][-1]['text']
        self.assertTrue(any(e['text'] == thought and e['kind'] == 'thought' for e in self.w.data['voices']))
        for i in range(100):
            self.w.emit('pip', str(i))
        self.assertEqual(len(self.w.data['voices']), 80)
        self.assertEqual(len({e['id'] for e in self.w.data['voices']}), 80)
        self.w.save()
        self.assertEqual(self.w.export(), World(self.path).export())


if __name__ == '__main__':
    unittest.main()
