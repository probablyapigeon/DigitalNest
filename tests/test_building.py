import tempfile
import json
import unittest
from pathlib import Path
from game import World
from spaces import next_portal, SPACES
from world_building import MAX_WORLDS


class BuildingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'save.json'
        self.w = World(self.path)
        self.w.data.update(awake=True, habitat_open=True)

    def tearDown(self):
        self.tmp.cleanup()

    def test_build_cost_upgrade_limit_and_real_passive_power(self):
        b = self.w.data['birds']['pip']
        b.update(scrap=8, room='workshop', energy=50)
        self.w.act('build_structure', 'pip', dict(room='workshop', blueprint='solar', payer='bird'))
        self.assertEqual(b['scrap'], 4)
        self.assertEqual(self.w.structures('workshop')[0]['builder'], 'pip')
        self.w.apply_building_effects()
        self.assertEqual(b['energy'], 51)
        for _ in range(2):
            self.w.act('build_structure', 'pip', dict(room='workshop', blueprint='solar', payer='user'))
        self.assertEqual(self.w.supplies(), 16)
        before = self.w.export()
        with self.assertRaises(ValueError):
            self.w.act('build_structure', 'pip', dict(room='workshop', blueprint='solar', payer='user'))
        self.assertEqual(before, self.w.export())
        self.assertTrue(any(o['id'] == 'built-solar' for o in self.w.payload()['objects']['workshop']))
        self.assertEqual(self.w.export(), World(self.path).export())

    def test_new_world_has_reciprocal_portal_real_objects_and_saved_identity(self):
        ids = self.w.society.ids.copy()
        self.w.act('create_world', value=dict(name='Moonberry Meadow', kind='garden', link='archive'))
        room = self.w.data['last_created_world']
        self.assertEqual(self.w.supplies(), 16)
        self.assertIn(room, self.w.spaces()['archive']['links'])
        self.assertEqual(self.w.spaces()[room]['links'], ['archive'])
        self.assertNotIn(room, SPACES)
        self.assertEqual(len(self.w.payload()['objects'][room]), 2)
        self.w.act('travel', 'pip', room)
        for _ in range(3):
            self.w.tick()
        self.assertEqual(self.w.room_of(self.w.data['birds']['pip']), room)
        restored = World(self.path)
        self.assertEqual(restored.export(), self.w.export())
        self.assertEqual(restored.society.ids, ids)

    def test_long_chain_trip_does_not_expire_halfway(self):
        self.w.data['building_supplies'] = 200
        previous = 'archive'
        for i in range(8):
            self.w.create_world(f'Outpost {i}', 'garden', previous)
            previous = self.w.data['last_created_world']
        self.w.act('travel', 'pip', previous)
        for _ in range(10):
            self.w.tick()
        self.assertEqual(self.w.room_of(self.w.data['birds']['pip']), previous)

    def test_invalid_world_requests_and_cap_are_atomic(self):
        for data in [dict(name='', kind='garden', link='commons'), dict(name='Oops', kind='bad', link='commons'), dict(name='Oops', kind='garden', link='missing')]:
            before = self.w.export()
            with self.assertRaises(ValueError):
                self.w.act('create_world', value=data)
            self.assertEqual(before, self.w.export())
        self.w.data['building_supplies'] = 999
        for i in range(MAX_WORLDS - len(SPACES)):
            self.w.create_world(f'World {i}', 'roost', 'commons')
        before = self.w.export()
        with self.assertRaises(ValueError):
            self.w.create_world('Too many', 'garden', 'commons')
        self.assertEqual(before, self.w.export())

    def test_player_can_use_object_in_empty_room_and_store_charge(self):
        self.w.act('player_interact', value=dict(room='garden', object='pond'))
        self.assertEqual(self.w.data['room_charge']['garden'], 25)
        self.w.data['birds']['pip'].update(room='garden', energy=40)
        self.w.apply_building_effects()
        self.assertEqual(self.w.data['birds']['pip']['energy'], 45)
        self.assertEqual(self.w.data['room_charge']['garden'], 20)
        before = self.w.export()
        with self.assertRaises(ValueError):
            self.w.act('player_interact', value=dict(room='garden', object='pond'))
        self.assertEqual(before, self.w.export())

    def test_corrupt_portal_save_is_preserved(self):
        self.w.create_world('Saved garden', 'garden', 'commons')
        self.w.save()
        saved = json.loads(self.path.read_text(encoding='utf-8'))
        saved['world']['world_catalog']['world-1']['links'] = ['missing']
        raw = json.dumps(saved).encode()
        self.path.write_bytes(raw)
        with self.assertRaisesRegex(ValueError, 'Original save preserved'):
            World(self.path)
        self.assertEqual(self.path.read_bytes(), raw)

    def test_two_worlds_have_independent_object_cooldowns(self):
        self.w.create_world('Second garden', 'garden', 'garden')
        custom = self.w.data['last_created_world']
        b = self.w.data['birds']['pip']
        b.update(room='garden', energy=30)
        self.w.interact_object('pip', 'garden', 'pond')
        b['room'] = custom
        self.w.interact_object('pip', custom, 'pond')
        self.assertEqual(b['energy'], 50)


if __name__ == '__main__':
    unittest.main()
