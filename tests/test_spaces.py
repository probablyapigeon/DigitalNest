import tempfile
import unittest
from pathlib import Path
from game import World
from spaces import SPACES, next_portal


class SpacesTest(unittest.TestCase):
    def test_all_worlds_reachable_through_reciprocal_portals(self):
        for start in SPACES:
            for neighbor in SPACES[start]['links']:
                self.assertIn(start, SPACES[neighbor]['links'])
            for end in SPACES:
                current = start
                for _ in range(len(SPACES)):
                    if current == end:
                        break
                    following = next_portal(current, end)
                    self.assertIn(following, SPACES[current]['links'])
                    current = following
                self.assertEqual(current, end)

    def test_trip_save_resume_and_single_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'save.json'
            world = World(path)
            world.data.update(awake=True, habitat_open=True)
            world.act('teach_words', 'pip', {'text': 'moonberry friends remember the garden', 'everyone': False})
            ids = world.society.ids.copy()
            world.act('travel', 'pip', 'garden')
            world.tick()
            self.assertEqual(world.data['birds']['pip']['room'], 'commons')
            world = World(path)
            world.tick()
            self.assertEqual(world.data['birds']['pip']['room'], 'garden')
            self.assertEqual(world.society.ids, ids)
            self.assertIn('moonberry', world.society.bird('pip').linguistics['tokens'])
            payload = world.payload()
            residents = [k for r in payload['spaces'].values() for k in r['residents']]
            self.assertEqual(sorted(residents), sorted(world.specs))
            before = world.export()
            with self.assertRaises(ValueError):
                world.act('travel', 'pip', 'missing')
            self.assertEqual(world.export(), before)
            world.data['paused'] = True
            before = world.export()
            world.tick()
            self.assertEqual(world.export(), before)

    def test_locked_before_opening(self):
        with tempfile.TemporaryDirectory() as directory:
            world = World(Path(directory) / 'save.json')
            with self.assertRaises(ValueError):
                world.act('travel', 'pip', 'garden')


if __name__ == '__main__':
    unittest.main()
