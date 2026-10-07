import unittest
from rosters import assemble, TEAMS

def profiles():
    return [dict(sourcePage=f'Person {i}', ID=f'Nick {i}', Team=team, Role='Top') for i, team in enumerate(TEAMS)]

class RosterTests(unittest.TestCase):
    def test_latest_role_and_inactive_status(self):
        rows = profiles() + [dict(sourcePage='Coach page', ID='Coach', Team='T1', Role='Coach')]
        old = dict(sourcePage='Coach page', Team='T1', IsCurrent='1', Roles='Head Coach', roleDate='2025-01-01', Status='')
        new = dict(old, roleDate='2026-01-01', Roles='Interim Head Coach', Status='inactive')
        data = assemble(rows, [new, old], 'now')
        coach = next(m for m in data['teams'][0]['members'] if m['id'] == 'Coach page')
        self.assertEqual(coach['roles'], ['Interim Head Coach'])
        self.assertEqual(coach['status'], 'inactive')
        self.assertTrue(coach['roleVerified'])
    def test_ambiguous_role_does_not_invent_head_coach(self):
        rows = profiles() + [dict(sourcePage='Coach', Team='T1', Role='Coach')]
        one = dict(sourcePage='Coach', Team='T1', IsCurrent='1', Roles='Head Coach', roleDate='2026-01-01')
        data = assemble(rows, [one, dict(one, Roles='Coach')], 'now')
        coach = next(m for m in data['teams'][0]['members'] if m['id'] == 'Coach')
        self.assertEqual(coach['roles'], ['Coach'])
        self.assertFalse(coach['roleVerified'])
    def test_streamer_excluded_and_canonical_identity_preserved(self):
        rows = profiles() + [dict(sourcePage='Stream', Team='T1', Role='Streamer'), dict(sourcePage='Nick (Other person)', ID='Nick 0', Team='T1', Role='Support')]
        result = assemble(rows, [], 'now')['teams'][0]['members']
        self.assertEqual(len(result), 2)
        self.assertEqual(len(set(m['id'] for m in result)), 2)
    def test_missing_team_or_duplicate_aborts_snapshot(self):
        with self.assertRaises(ValueError): assemble(profiles()[:-1], [], 'now')
        with self.assertRaises(ValueError): assemble(profiles() + [profiles()[0]], [], 'now')

if __name__ == '__main__': unittest.main()
