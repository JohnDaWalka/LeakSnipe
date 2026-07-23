import json
import unittest

from parsers import HandParser


def _cp_pipe_line(cmd, bean, room="", ts="2026-07-23 08:46:50"):
    """Build one CoinPoker main.log line in the pipe-JSON format parsers.py expects."""
    outer = {
        "EventName": "extension_event",
        "Data": {
            "cmd_bean": {
                "Cmd": cmd,
                "RoomName": room,
                "BeanData": json.dumps(bean),
            }
        },
    }
    return f"{ts} INFO SendMessageToPipe - {json.dumps(outer)}"


def _seat_list(names_and_stacks):
    return [
        {"seatId": seat, "userName": name, "userChips": stack}
        for seat, (name, stack) in enumerate(names_and_stacks, start=1)
    ]


class CoinPokerRoomParsingTests(unittest.TestCase):
    """Unit tests for HandParser._coinpoker_parse_room (P0 fix)."""

    def setUp(self):
        self.parser = HandParser({"hero_names": {"CoinPoker": "jdwalka"}})

    def test_cash_stakes_table_name_is_not_treated_as_tournament(self):
        tid, buy_in, table_name, is_cash = self.parser._coinpoker_parse_room(
            "31st NL 0.05-0.10 EV-INRIT-(A) 948685"
        )
        self.assertEqual(tid, "")
        self.assertEqual(buy_in, "0.05-0.10")
        self.assertTrue(is_cash)
        self.assertEqual(table_name, "31st NL 0.05-0.10 EV-INRIT-(A) 948685")

    def test_tournament_room_name_extracts_id_and_buyin(self):
        tid, buy_in, table_name, is_cash = self.parser._coinpoker_parse_room(
            "$2.20 Asia 6-Max Classic 1115916"
        )
        self.assertEqual(tid, "1115916")
        self.assertEqual(buy_in, "2.20+0")
        self.assertFalse(is_cash)

    def test_ambiguous_trailing_digits_are_not_guessed_as_tournament(self):
        tid, buy_in, table_name, is_cash = self.parser._coinpoker_parse_room(
            "Some Random Table 948685"
        )
        self.assertEqual(tid, "")
        self.assertEqual(buy_in, "")
        self.assertFalse(is_cash)

    def test_empty_room_name(self):
        self.assertEqual(
            self.parser._coinpoker_parse_room(""), ("", "", "", False)
        )


class CoinPokerJsonLogClassificationTests(unittest.TestCase):
    """Integration tests through the main.log JSON ingestion path."""

    def setUp(self):
        self.parser = HandParser({"hero_names": {"CoinPoker": "jdwalka"}})

    def _build_hand(self, room, extra_bean=None):
        seats = _seat_list([
            ("jdwalka", 100.0), ("villain1", 90.0), ("villain2", 80.0),
            ("villain3", 70.0), ("villain4", 60.0), ("villain5", 50.0),
        ])
        alldata_bean = {
            "gameInitResponseData": {
                "dealerSeatId": 2,
                "tableId": 948685,
                "gameHandId": "111591600168",
            },
            "seatInfoRsponseData": {"seatResponseDataList": seats},
        }
        if extra_bean:
            alldata_bean.update(extra_bean)
        content = "\n".join([
            _cp_pipe_line("game.game_alldata", alldata_bean, room=room),
            _cp_pipe_line(
                "game.pre_hand_start_info",
                {"gameHandId": "111591600168", "dealerSeatId": 2},
                room=room,
            ),
            _cp_pipe_line("game.winnerInfo", {"gameHandId": "111591600168"}, room=room),
        ])
        hands = self.parser.parse_coinpoker_json_log(content)
        self.assertEqual(len(hands), 1)
        return hands[0]

    def test_cash_table_without_gametype_signal_stays_cash(self):
        # No roomProperties.gameType anywhere in the log -- before the P0 fix
        # this fell back to the tournament default and also picked up the
        # table's trailing digits as tournament_id.
        hand = self._build_hand("31st NL 0.05-0.10 EV-INRIT-(A) 948685")
        self.assertFalse(hand.is_tournament)
        self.assertEqual(hand.tournament_id, "")
        self.assertEqual(hand.buy_in, "0.05-0.10")
        self.assertEqual(hand.max_seats, 6)
        self.assertEqual(hand.button_seat, 2)

    def test_tournament_table_extracts_tournament_id(self):
        hand = self._build_hand("$2.20 Asia 6-Max Classic 1115916")
        self.assertTrue(hand.is_tournament)
        self.assertEqual(hand.tournament_id, "1115916")

    def test_gametype_ring_signal_prevents_tableid_leaking_into_tournament_id(self):
        hand = self._build_hand(
            "Some Random Table 948685",
            extra_bean={"roomProperties": {"gameType": "RING"}},
        )
        self.assertFalse(hand.is_tournament)
        self.assertEqual(hand.tournament_id, "")


class CoinPokerSyntheticReparseTests(unittest.TestCase):
    """_parse_coinpoker must be able to re-parse our own synthetic raw_text
    (see _format_coinpoker_hand_text) so reparse_hands_missing_hero can
    backfill JSON-log-derived CoinPoker hands instead of silently no-op'ing."""

    def setUp(self):
        self.parser = HandParser({"hero_names": {"CoinPoker": "jdwalka"}})

    def test_synthetic_header_cash_table_reparse(self):
        text = (
            "Hand #CP_111591600168 - Holdem (No Limit) - 2026/07/23 08:46:50 UTC\n"
            "Table '31st NL 0.05-0.10 EV-INRIT-(A) 948685' 6-max Seat #2 is the button\n"
            "Seat 1: markiin14 (56306)\n"
            "Seat 2: jdwalka (63656.15)\n"
            "*** HOLE CARDS ***\n"
            "Dealt to jdwalka [As Kd]\n"
            "*** SUMMARY ***\n"
            "Total pot 10 | Rake 0.5\n"
        )
        hand = self.parser._parse_coinpoker(text)
        self.assertIsNotNone(hand)
        self.assertEqual(hand.hand_id, "CP_111591600168")
        self.assertEqual(hand.raw_text, text)
        self.assertFalse(hand.is_tournament)
        self.assertEqual(hand.tournament_id, "")
        self.assertEqual(hand.buy_in, "0.05-0.10")
        self.assertEqual(hand.max_seats, 6)
        self.assertEqual(hand.button_seat, 2)

    def test_synthetic_header_tournament_table_reparse(self):
        text = (
            "Hand #CP_111591600168 - Holdem (No Limit) - 2026/07/23 08:46:50 UTC\n"
            "Table '$2.20 Asia 6-Max Classic 1115916' 6-max Seat #2 is the button\n"
            "Seat 1: markiin14 (56306)\n"
            "Seat 2: jdwalka (63656.15)\n"
            "*** HOLE CARDS ***\n"
            "Dealt to jdwalka [As Kd]\n"
            "*** SUMMARY ***\n"
            "Total pot 10 | Rake 0.5\n"
        )
        hand = self.parser._parse_coinpoker(text)
        self.assertIsNotNone(hand)
        self.assertTrue(hand.is_tournament)
        self.assertEqual(hand.tournament_id, "1115916")

    def test_real_export_header_with_explicit_tournament_marker_still_works(self):
        text = (
            "CoinPoker Hand #987654 - Tournament #555 - Holdem (No Limit) - "
            "2026/07/23 08:46:50 UTC\n"
            "Table 'Some Table' 6-max Seat #1 is the button\n"
            "Seat 1: jdwalka (1000)\n"
            "*** HOLE CARDS ***\n"
            "*** SUMMARY ***\n"
            "Total pot 0 | Rake 0\n"
        )
        hand = self.parser._parse_coinpoker(text)
        self.assertIsNotNone(hand)
        self.assertEqual(hand.hand_id, "CP_987654")
        self.assertTrue(hand.is_tournament)
        self.assertEqual(hand.tournament_id, "555")


if __name__ == "__main__":
    unittest.main()
