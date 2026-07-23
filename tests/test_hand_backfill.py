import tempfile
import unittest
from datetime import datetime

from models import Hand, HandDatabase


class HeroAndSeatBackfillGatingTests(unittest.TestCase):
    """hand_needs_hero_backfill/hand_has_hero_fields also gate on
    max_seats/button_seat so reparse_hands_missing_hero can fix rows that
    were saved with hero fields present but seat/button info missing (0)."""

    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.db = HandDatabase(self.db_path)

        self.hand = Hand()
        self.hand.hand_id = "CP_1"
        self.hand.site = "CoinPoker"
        self.hand.game_type = "NLHE"
        self.hand.date = datetime.now()
        self.hand.hero_cards = "As Kd"
        self.hand.hero_position = "BTN"
        self.hand.max_seats = 0
        self.hand.button_seat = 0
        self.db.save_hand(self.hand, "test.log")

    def test_needs_backfill_true_when_seats_missing_even_with_hero_fields(self):
        self.assertTrue(self.db.hand_needs_hero_backfill("CP_1"))

    def test_needs_backfill_false_once_seats_present(self):
        self.hand.max_seats = 6
        self.hand.button_seat = 2
        self.db.save_hand(self.hand, "test.log")
        self.assertFalse(self.db.hand_needs_hero_backfill("CP_1"))

    def test_has_hero_fields_true_for_seats_only(self):
        parsed = Hand()
        parsed.hero_cards = ""
        parsed.hero_position = ""
        parsed.max_seats = 6
        parsed.button_seat = 2
        self.assertTrue(HandDatabase.hand_has_hero_fields(parsed))

    def test_has_hero_fields_false_when_nothing_usable(self):
        parsed = Hand()
        self.assertFalse(HandDatabase.hand_has_hero_fields(parsed))


if __name__ == "__main__":
    unittest.main()
