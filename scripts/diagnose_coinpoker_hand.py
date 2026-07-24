"""Diagnose why a specific CoinPoker JSON main.log hand ends up with
max_seats=0 / button_seat=0 / empty players after import.

Run from the repo root on the machine where CoinPoker actually writes its
logs (so it sees the real main.log chain):

    python scripts/diagnose_coinpoker_hand.py <hand_number> [logs_dir]

<hand_number> is the numeric id from the hand_id, e.g. for CP_112395700107
pass 112395700107. logs_dir defaults to
%APPDATA%\\CoinPoker\\logs on Windows.

Prints, for the matching hand: which event cmd types were grouped under it,
counts per cmd, whether game.pre_hand_start_info / game.game_alldata /
game.seat / game.seatInfo were present, and the resulting
max_seats/button_seat/player count/hero_position the parser computed --
without printing hole cards, table names, or other hand content.
"""

import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers import HandParser  # noqa: E402
from importing import HandImporter  # noqa: E402


def default_logs_dir() -> str:
    appdata = os.environ.get("APPDATA", "")
    return os.path.join(appdata, "CoinPoker", "logs")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python scripts/diagnose_coinpoker_hand.py <hand_number> [logs_dir]")
        sys.exit(1)
    target = str(sys.argv[1]).strip()
    logs_dir = sys.argv[2] if len(sys.argv) > 2 else default_logs_dir()

    if not os.path.isdir(logs_dir):
        print(f"Logs dir not found: {logs_dir}")
        sys.exit(1)

    settings = {"hero_names": {}}
    parser = HandParser(settings)
    # Reuse the real importer's chain discovery so ordering exactly matches
    # what production import sees (main.N.log.gz oldest->newest, then live
    # main.log last).
    importer = HandImporter(settings, db=None)
    chain = importer._coinpoker_chain(logs_dir)
    print(f"Chain ({len(chain)} segment(s)): {[os.path.basename(p) for p in chain]}")

    all_events = []
    for path in chain:
        try:
            content = parser._read_file_text(path)
        except Exception as exc:
            print(f"  skip {os.path.basename(path)}: {exc}")
            continue
        events = parser._extract_coinpoker_events(content)
        print(f"  {os.path.basename(path)}: {len(events)} game.* events")
        all_events.extend(events)

    print(f"\nTotal events across chain: {len(all_events)}")

    matching = []
    last_key = ""
    for event in all_events:
        bean = event.get("bean") or {}
        hand_key = parser._coinpoker_event_hand_key(bean)
        if not hand_key:
            hand_key = last_key
        if not hand_key:
            continue
        last_key = hand_key
        if str(hand_key) == target:
            matching.append(event)

    if not matching:
        print(f"\nNo events grouped under hand {target}. It may have scrolled "
              f"out of the current chain, or the hand number is wrong.")
        sys.exit(0)

    cmd_counts = Counter(ev["cmd"] for ev in matching)
    print(f"\nHand {target}: {len(matching)} events grouped under it")
    print("Event cmd counts:")
    for cmd, count in sorted(cmd_counts.items()):
        print(f"  {cmd}: {count}")

    has_pre_hand_start = "game.pre_hand_start_info" in cmd_counts
    has_game_alldata = "game.game_alldata" in cmd_counts
    has_seat = "game.seat" in cmd_counts
    has_seat_info = "game.seatInfo" in cmd_counts
    print(f"\ngame.pre_hand_start_info present: {has_pre_hand_start}")
    print(f"game.game_alldata present:        {has_game_alldata}")
    print(f"game.seat present:                {has_seat}")
    print(f"game.seatInfo present:            {has_seat_info}")

    hero_candidates = parser._hero_candidates("CoinPoker")
    try:
        hand = parser._build_coinpoker_hand_from_events(
            matching, hero_candidates[0] if hero_candidates else "",
        )
    except Exception as exc:
        print(f"\n_build_coinpoker_hand_from_events raised: {exc!r}")
        sys.exit(1)

    if hand is None:
        print("\n_build_coinpoker_hand_from_events returned None")
        sys.exit(0)

    print(f"\nResult: max_seats={hand.max_seats} button_seat={hand.button_seat} "
          f"players={len(hand.players)} hero_position={hand.hero_position!r}")


if __name__ == "__main__":
    main()
