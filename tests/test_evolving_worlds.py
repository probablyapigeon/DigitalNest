import copy
import math
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from game import World
from heart import initial_heart, update_heart, heart_event
from server import copy_world
from conversation import chat_messages
from world_identity import visual_genome


class EvolvingWorldsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'save.json'
        self.w = World(self.path)
        self.w.data.update(awake=True, habitat_open=True)

    def teach_archive(self):
        for offset in range(0, 600, 25):
            self.w.learn_text('pip', ' '.join(f'orchid{i:04d}' for i in range(offset, offset+25)))
        self.w.save()

    def test_archive_grows_past_working_limit_and_recalls_old_word(self):
        self.teach_archive()
        self.assertGreaterEqual(self.w.archive.stats('pip')['words'], 600)
        self.assertLessEqual(len(self.w.society.bird('pip').linguistics['tokens']), 256)
        restored = World(self.path)
        recalled = restored.archive.activate('pip', 'orchid0000')
        self.assertIn('orchid0000', recalled['words'])
        self.assertIn('orchid0000', restored.society.bird('pip').linguistics['tokens'])
        self.assertNotIn('orchid0000', restored.archive.retrieve('moss', 'orchid0000')['words'])
        self.assertTrue(recalled['memories'])
        self.assertIn('orchid0000', chat_messages(copy_world(restored, 'pip', 'orchid0000'), 'pip', 'orchid0000')[0]['content'])

    def test_archive_outbox_recovers_after_interrupted_commit_without_double_count(self):
        self.w.learn_text('pip', 'iridescent fern')
        with patch.object(self.w.archive, 'flush', side_effect=OSError('simulated disk interruption')):
            with self.assertRaises(OSError):
                self.w.save()
        restored = World(self.path)
        before = restored.archive.stats('pip')
        self.assertIn('iridescent', restored.archive.retrieve('pip', 'iridescent')['words'])
        again = World(self.path)
        self.assertEqual(before, again.archive.stats('pip'))
        self.assertNotIn('_language_pending', again.data)

    def test_missing_archive_never_silently_discards_long_term_memory(self):
        self.w.learn_text('pip', 'moon fern')
        self.w.save()
        original = self.path.read_bytes()
        self.w.archive.path.rename(self.w.archive.path.with_suffix('.backup'))
        with self.assertRaisesRegex(ValueError, 'archive is missing'):
            World(self.path)
        self.assertEqual(original, self.path.read_bytes())

    def test_heart_is_time_scaled_and_events_do_not_advance_time(self):
        one, many = initial_heart(), initial_heart()
        heart_event(one, .9, pressure=True)
        heart_event(many, .9, pressure=True)
        self.assertEqual(one['elapsed'], 0)
        update_heart(one, .75, seconds=90)
        for _ in range(9):
            update_heart(many, .75, seconds=10)
        self.assertEqual(one, many)
        self.assertLess(one['perturb'], .02)
        self.assertTrue(all(math.isfinite(v) for v in one.values()))
        self.assertEqual(one['elapsed'], 90)

    def test_bird_builds_connected_world_using_own_parts_and_saved_visuals(self):
        bird = self.w.data['birds']['pip']
        bird.update(scrap=8, nest=3)
        supplies = self.w.supplies()
        self.w.act('plan_world', 'pip')
        link = bird['world_project']['link']
        self.w.advance_world_projects()
        key = self.w.data['last_created_world']
        room = self.w.spaces()[key]
        self.assertEqual(room['builder'], 'pip')
        self.assertEqual(room['design']['creator'], 'pip')
        self.assertEqual(bird['scrap'], 0)
        self.assertEqual(self.w.supplies(), supplies)
        self.assertIn(key, self.w.spaces()[link]['links'])
        self.assertIn(link, room['links'])
        self.assertEqual(bird['destination'], key)
        self.w.save()
        self.assertEqual(World(self.path).spaces()[key], room)

    def test_projects_collect_parts_without_toy_spending(self):
        bird = self.w.data['birds']['pip']
        bird.update(scrap=6, nest=5, energy=100)
        self.w.act('plan_world', 'pip')
        self.w.data['tick'] = 0
        self.w.autonomous_objects()
        self.assertEqual(bird['scrap'], 6)
        for _ in range(5):
            self.w.tick()
        self.assertGreaterEqual(bird.get('worlds_built', 0), 1)

    def test_visual_identity_changes_per_builder_player_instance_and_room(self):
        original = visual_genome('game-a', 'player-a', 'world-1', 'pip')
        self.assertEqual(original, visual_genome('game-a', 'player-a', 'world-1', 'pip'))
        for args in [('game-b','player-a','world-1','pip'), ('game-a','player-b','world-1','pip'),
                     ('game-a','player-a','world-2','pip'), ('game-a','player-a','world-1','moss')]:
            self.assertNotEqual(original, visual_genome(*args))

    def test_new_game_at_same_path_does_not_share_previous_archive(self):
        self.w.learn_text('pip', 'privateorchid')
        self.w.save()
        # A new game starts with a new instance identity, even at the same location.
        self.path.rename(self.path.with_suffix('.old'))
        new = World(self.path)
        self.assertNotEqual(new.archive.path, self.w.archive.path)
        self.assertEqual(new.archive.stats('pip')['words'], 0)

    def test_pause_preserves_heart_and_archive_and_project(self):
        self.w.act('plan_world', 'pip')
        self.w.data['paused'] = True
        before = self.w.export()
        self.w.tick()
        self.assertEqual(before, self.w.export())

    def test_descendant_inherits_archived_language_beyond_active_cache(self):
        self.teach_archive()
        for _ in range(6):
            self.w.act('teach_words', value={'text': 'beep boop moonberry moss garden warm nest friend song shiny feather home', 'everyone': True})
        for _ in range(8):
            self.w.act('visit', 'pip', 'moss')
        self.w.data['birds']['pip'].update(scrap=3, nest=2)
        child = self.w.hatch('pip')
        self.w.save()
        self.assertGreaterEqual(self.w.archive.stats(child)['words'], 600)
        self.assertIn('orchid0000', self.w.archive.retrieve(child, 'orchid0000')['words'])
        self.assertEqual(World(self.path).archive.stats(child), self.w.archive.stats(child))

    def test_established_bird_initiates_own_world_project(self):
        self.w.data['tick'] = 48
        self.w.data['birds']['pip']['nest'] = 3
        self.w.society.bird('pip').social['stage'] = 'graduate'
        self.w.advance_world_projects()
        self.assertIn('world_project', self.w.data['birds']['pip'])
