import json
import shutil
import tempfile
import unittest
from pathlib import Path

from game import World


class WorldTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'save.json'
        self.world = World(self.path)

    def tearDown(self):
        self.temp.cleanup()

    def open_habitat(self):
        for action in ['wake', 'inspect', 'salvage', 'repair', 'hatch']:
            self.world.act(action)

    def test_repair_requires_parts_and_inspection(self):
        with self.assertRaises(ValueError):
            self.world.act('repair')
        self.assertFalse(self.world.data['wing_fixed'])
        self.open_habitat()
        self.assertTrue(self.world.data['wing_fixed'])
        self.assertTrue(self.world.data['habitat_open'])
        self.assertEqual(self.world.data['servo'], 0)

    def test_checkpoint_resume_exact(self):
        self.open_habitat()
        for _ in range(12):
            self.world.tick()
        restored = World(self.path)
        self.assertEqual(self.world.export(), restored.export())
        self.world.tick()
        restored.tick()
        self.assertEqual(self.world.export(), restored.export())

    def test_cassette_and_culture(self):
        self.open_habitat()
        self.world.act('cassette')
        self.world.act('reassure')
        self.world.act('listen')
        with self.assertRaises(ValueError):
            self.world.act('tune', value=[1, 2, 3])
        self.world.act('tune', value=[2, 4, 3])
        self.world.act('teach')
        for _ in range(45):
            self.world.tick()
        self.assertTrue(all(b['knows_song'] for b in self.world.data['birds'].values()))

    def test_order_changes_real_xc_state(self):
        self.open_habitat()
        self.world.act('cassette')
        baseline = self.world.export()
        # A checkpoint branch includes both durable save components.
        other_path = Path(self.temp.name) / 'other.json'
        other_path.write_text(json.dumps(baseline), encoding='utf-8')
        archive = self.world.archive.path
        shutil.copy2(archive, archive.with_name('other' + archive.name[len(self.path.stem):]))
        self.world.act('reassure')
        self.world.act('listen')
        first = self.world.brains['pip'].export_checkpoint()
        other = World(other_path)
        other.act('listen')
        other.act('reassure')
        self.assertNotEqual(first['state'], other.brains['pip'].export_checkpoint()['state'])
        self.assertNotEqual(self.world.data['tape_reaction'], other.data['tape_reaction'])

    def test_growth_and_self_maintenance_are_bounded(self):
        self.open_habitat()
        for _ in range(100):
            self.world.tick()
        for brain in self.world.brains.values():
            m = brain.morphology_summary()['Structural']
            self.assertGreater(m['nodes'], 1)
            self.assertLessEqual(m['nodes'], 48)
            self.assertLessEqual(m['operators'], 12)
        for bird in self.world.data['birds'].values():
            self.assertGreaterEqual(bird['energy'], 0)
            self.assertLessEqual(bird['energy'], 100)
        self.assertTrue(any(b['nest'] > 1 for b in self.world.data['birds'].values()))

    def test_bad_save_not_overwritten(self):
        self.path.write_text('{broken', encoding='utf-8')
        with self.assertRaises(ValueError):
            World(self.path)
        self.assertEqual(self.path.read_text(), '{broken')

    def test_repeated_rewards_and_unknown_actions_rejected(self):
        self.open_habitat()
        before = self.world.export()
        for action in ['salvage', 'repair', 'not-an-action']:
            with self.assertRaises(ValueError):
                self.world.act(action)
        self.assertEqual(before, self.world.export())

if __name__ == '__main__':
    unittest.main()
