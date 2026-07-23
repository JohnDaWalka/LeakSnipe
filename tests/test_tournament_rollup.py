import tempfile
import unittest
from datetime import datetime, timedelta

from models import Hand, HandDatabase


def _tourney_hand(hand_id, tournament_id, date, table_name, players, hero_won=0.0,
                   site="CoinPoker", buy_in=""):
    h = Hand()
    h.hand_id = hand_id
    h.site = site
    h.game_type = "NLHE"
    h.is_tournament = True
    h.tournament_id = tournament_id
    h.buy_in = buy_in
    h.table_name = table_name
    h.date = date
    h.hero_won = hero_won
    h.players = players
    return h


class TournamentHandRollupTests(unittest.TestCase):
    """get_tournament_hand_rollup: the computed (not .ots-sourced) summary
    that fills the CoinPoker tournament_summaries gap."""

    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.db = HandDatabase(self.db_path)
        self.base = datetime(2026, 7, 23, 8, 0, 0)

    def test_hero_busted_out_when_final_stack_is_zero(self):
        self.db.save_hand(_tourney_hand(
            "CP_1", "1115916", self.base, "Table A",
            {1: {"name": "jdwalka", "stack": 500.0, "is_hero": True},
             2: {"name": "villain", "stack": 500.0, "is_hero": False}},
            hero_won=-50.0, buy_in="2.20+0",
        ), "t.log")
        self.db.save_hand(_tourney_hand(
            "CP_2", "1115916", self.base + timedelta(minutes=5), "Table A",
            {1: {"name": "jdwalka", "stack": 0.0, "is_hero": True},
             2: {"name": "villain", "stack": 1000.0, "is_hero": False}},
            hero_won=-450.0,
        ), "t.log")

        rollup = self.db.get_tournament_hand_rollup(site="CoinPoker", tournament_id="1115916")
        self.assertEqual(len(rollup), 1)
        row = rollup[0]
        self.assertEqual(row["hand_count"], 2)
        self.assertEqual(row["buy_in"], "2.20+0")
        self.assertTrue(row["hero_busted_out"])
        self.assertEqual(row["hero_final_stack"], 0.0)
        self.assertEqual(row["hero_chip_result"], -500.0)
        self.assertIsNone(row["finish_position"])
        self.assertIsNone(row["prize"])
        self.assertEqual(row["source"], "computed_from_hands")

    def test_likely_final_table_requires_multiple_tables_and_short_handed(self):
        self.db.save_hand(_tourney_hand(
            "CP_10", "555", self.base, "Table A (6-max)",
            {i: {"name": f"p{i}", "stack": 1000.0, "is_hero": i == 1} for i in range(1, 7)},
        ), "t.log")
        self.db.save_hand(_tourney_hand(
            "CP_11", "555", self.base + timedelta(minutes=30), "Table B (Final)",
            {1: {"name": "jdwalka", "stack": 3000.0, "is_hero": True},
             2: {"name": "p2", "stack": 3000.0, "is_hero": False}},
        ), "t.log")

        rollup = self.db.get_tournament_hand_rollup(site="CoinPoker", tournament_id="555")
        row = rollup[0]
        self.assertEqual(row["tables_played"], 2)
        self.assertEqual(row["last_table_name"], "Table B (Final)")
        self.assertEqual(row["min_seated_on_last_table"], 2)
        self.assertTrue(row["likely_final_table"])
        # hero still had chips -- not a confirmed bust, and we never guess a
        # finish position/prize even when the heuristic says "likely final table".
        self.assertFalse(row["hero_busted_out"])
        self.assertIsNone(row["finish_position"])

    def test_single_table_is_not_flagged_as_final_table(self):
        self.db.save_hand(_tourney_hand(
            "CP_20", "777", self.base, "Only Table",
            {1: {"name": "jdwalka", "stack": 1000.0, "is_hero": True},
             2: {"name": "p2", "stack": 1000.0, "is_hero": False}},
        ), "t.log")

        row = self.db.get_tournament_hand_rollup(site="CoinPoker", tournament_id="777")[0]
        self.assertEqual(row["tables_played"], 1)
        self.assertFalse(row["likely_final_table"])

    def test_filters_by_site_and_ignores_non_tournament_hands(self):
        self.db.save_hand(_tourney_hand(
            "CP_30", "999", self.base, "Table X",
            {1: {"name": "jdwalka", "stack": 1000.0, "is_hero": True}},
        ), "t.log")
        cash_hand = Hand()
        cash_hand.hand_id = "CP_31"
        cash_hand.site = "CoinPoker"
        cash_hand.is_tournament = False
        cash_hand.tournament_id = ""
        cash_hand.date = self.base
        cash_hand.players = {1: {"name": "jdwalka", "stack": 100.0, "is_hero": True}}
        self.db.save_hand(cash_hand, "t.log")

        self.assertEqual(len(self.db.get_tournament_hand_rollup(site="CoinPoker")), 1)
        self.assertEqual(self.db.get_tournament_hand_rollup(site="BetACR"), [])


if __name__ == "__main__":
    unittest.main()
