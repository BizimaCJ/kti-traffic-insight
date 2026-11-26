from django.test import SimpleTestCase, override_settings

from apps.incidents.models import IncidentStatus as S
from apps.incidents.status import can_transition
from apps.traffic.levels import classify_delay, worst_level
from apps.traffic.models import TrafficLevel as L


class TrafficLevelTests(SimpleTestCase):
    def test_srs_boundaries(self):
        cases = [(0, L.FREE_FLOW), (2, L.FREE_FLOW), (3, L.MODERATE), (7, L.MODERATE),
                 (8, L.HEAVY), (15, L.HEAVY), (16, L.BLOCKED), (60, L.BLOCKED)]
        for delay, expected in cases:
            with self.subTest(delay=delay):
                self.assertEqual(classify_delay(delay), expected)

    def test_negative_delay_rejected(self):
        with self.assertRaises(ValueError):
            classify_delay(-1)

    @override_settings(FREE_FLOW_MAX_DELAY=0, MODERATE_MAX_DELAY=2, HEAVY_MAX_DELAY=5)
    def test_thresholds_are_configurable(self):
        self.assertEqual(classify_delay(1), L.MODERATE)
        self.assertEqual(classify_delay(6), L.BLOCKED)

    def test_worst_level(self):
        self.assertEqual(worst_level([L.FREE_FLOW, L.HEAVY, L.MODERATE]), L.HEAVY)
        self.assertEqual(worst_level([L.BLOCKED, L.HEAVY]), L.BLOCKED)
        self.assertIsNone(worst_level([]))


class StatusRuleTests(SimpleTestCase):
    def test_allowed_transitions(self):
        for a, b in [(S.SUBMITTED, S.UNDER_REVIEW), (S.UNDER_REVIEW, S.VERIFIED), (S.VERIFIED, S.RESOLVED),
                     (S.SUBMITTED, S.REJECTED), (S.UNDER_REVIEW, S.REJECTED)]:
            with self.subTest(a=a, b=b):
                self.assertTrue(can_transition(a, b))

    def test_blocked_transitions(self):
        for a, b in [(S.SUBMITTED, S.VERIFIED), (S.SUBMITTED, S.RESOLVED), (S.VERIFIED, S.REJECTED),
                     (S.RESOLVED, S.VERIFIED), (S.REJECTED, S.UNDER_REVIEW), (S.UNDER_REVIEW, S.SUBMITTED)]:
            with self.subTest(a=a, b=b):
                self.assertFalse(can_transition(a, b))

    def test_final_states_have_no_exit(self):
        for final in (S.RESOLVED, S.REJECTED):
            self.assertFalse(any(can_transition(final, other) for other in S))
