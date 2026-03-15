#!/usr/bin/env python3
"""
♠ Poker Hand Tracker ♥ — Multi-site poker hand tracker with dark GUI.
Supports CoinPoker and ACR/WPN hand history formats.
"""

import os
import sys
import re
import json
import glob
import time
import base64
import subprocess
import threading
import tempfile
import sqlite3
from datetime import datetime
from collections import defaultdict, OrderedDict
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk, ImageEnhance, ImageFilter
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

try:
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False

# ─── Theme System ─────────────────────────────────────────────────────────────
THEMES = {
    "Midnight Purple": {
        "bg_base":       "#13111c",   # deep purple-black
        "bg_panel":      "#1c1929",   # dark purple panel
        "bg_accent":     "#4a2d8a",   # vibrant purple accent
        "bg_input":      "#110f1a",   # darkest purple input
        "bg_card":       "#252238",   # raised purple surface
        "bg_hover":      "#6c3ec7",   # bright purple hover
        "border":        "#332e4a",   # muted purple border
        "border_hl":     "#7c4dff",   # neon purple highlight
        "text":          "#e8e6f0",   # lavender white
        "text_dim":      "#9590b0",   # dim lavender
        "text_header":   "#ffd740",   # amber gold headers
        "green":         "#69f0ae",   # mint green wins
        "red":           "#ff5252",   # bright red losses
        "yellow":        "#ffd740",   # amber warnings
        "gold":          "#ffd740",   # amber highlights
        "orange":        "#ff6e40",   # coral orange
        "select_bg":     "#3d2b70",   # purple selection
        "row_win":       "#e8e6f0",
        "row_loss":      "#d4a0b0",
        "row_even":      "#9590b0",
        "graph_bg":      "#13111c",
        "graph_face":    "#1c1929",
        "graph_grid":    "#332e4a",
        "graph_line":    "#69f0ae",
        "graph_bar1":    "#7c4dff",
        "graph_bar2":    "#ff5252",
        "pie_colors":    ["#7c4dff", "#69f0ae", "#ff5252", "#ffd740", "#e040fb", "#18ffff"],
    },
    "Slate Blue": {
        "bg_base":       "#0f1923",   # deep navy slate
        "bg_panel":      "#172a3a",   # dark steel blue
        "bg_accent":     "#1e6091",   # rich ocean blue
        "bg_input":      "#0c1520",   # near-black navy
        "bg_card":       "#1f3347",   # steel blue card
        "bg_hover":      "#2196f3",   # bright blue hover
        "border":        "#2a4560",   # steel border
        "border_hl":     "#42a5f5",   # bright blue highlight
        "text":          "#e3eaf0",   # cool white
        "text_dim":      "#7a9bb5",   # muted steel
        "text_header":   "#ffc107",   # amber headers
        "green":         "#4caf50",   # standard green
        "red":           "#ef5350",   # warm red
        "yellow":        "#ffc107",   # amber
        "gold":          "#ffca28",   # bright gold
        "orange":        "#ff7043",   # deep orange
        "select_bg":     "#1a4a6e",
        "row_win":       "#e3eaf0",
        "row_loss":      "#cf9090",
        "row_even":      "#7a9bb5",
        "graph_bg":      "#0f1923",
        "graph_face":    "#172a3a",
        "graph_grid":    "#2a4560",
        "graph_line":    "#4caf50",
        "graph_bar1":    "#2196f3",
        "graph_bar2":    "#ef5350",
        "pie_colors":    ["#2196f3", "#4caf50", "#ef5350", "#ffc107", "#ab47bc", "#26c6da"],
    },
    "High Contrast": {
        "bg_base":       "#000000",
        "bg_panel":      "#1a1a1a",
        "bg_accent":     "#005fa3",
        "bg_input":      "#0d0d0d",
        "bg_card":       "#262626",
        "bg_hover":      "#0078d4",
        "border":        "#555555",
        "border_hl":     "#00b7ff",
        "text":          "#ffffff",
        "text_dim":      "#bbbbbb",
        "text_header":   "#ffdd00",
        "green":         "#00ff7f",
        "red":           "#ff4444",
        "yellow":        "#ffdd00",
        "gold":          "#ffdd00",
        "orange":        "#ff8800",
        "select_bg":     "#005fa3",
        "row_win":       "#ffffff",
        "row_loss":      "#ff9999",
        "row_even":      "#bbbbbb",
        "graph_bg":      "#000000",
        "graph_face":    "#1a1a1a",
        "graph_grid":    "#555555",
        "graph_line":    "#00ff7f",
        "graph_bar1":    "#0078d4",
        "graph_bar2":    "#ff4444",
        "pie_colors":    ["#0078d4", "#00ff7f", "#ff4444", "#ffdd00", "#cc66ff", "#00cccc"],
    },
    "Felt Green": {
        "bg_base":       "#0e2a1e",   # deeper felt green
        "bg_panel":      "#173628",   # rich dark felt
        "bg_accent":     "#1a7a4a",   # emerald accent
        "bg_input":      "#0b2218",   # darkest green input
        "bg_card":       "#204a36",   # raised felt card
        "bg_hover":      "#2ecc71",   # bright emerald hover
        "border":        "#2d5a42",   # green-tinted border
        "border_hl":     "#2ecc71",   # emerald highlight
        "text":          "#f0efe4",   # warm cream text
        "text_dim":      "#7ca08e",   # sage dim
        "text_header":   "#f1c40f",   # gold headers
        "green":         "#2ecc71",   # wins
        "red":           "#e74c3c",   # losses
        "yellow":        "#f39c12",   # caution
        "gold":          "#f1c40f",   # highlights
        "orange":        "#e67e22",   # tilt
        "select_bg":     "#1a5c3a",
        "row_win":       "#f0efe4",
        "row_loss":      "#d4a0a0",
        "row_even":      "#7ca08e",
        "graph_bg":      "#0e2a1e",
        "graph_face":    "#173628",
        "graph_grid":    "#2d5a42",
        "graph_line":    "#2ecc71",
        "graph_bar1":    "#1a7a4a",
        "graph_bar2":    "#e74c3c",
        "pie_colors":    ["#1a7a4a", "#2ecc71", "#e74c3c", "#f39c12", "#8e44ad", "#16a085"],
    },
    "Crimson Night": {
        "bg_base":       "#1a0f14",   # deep dark red-black
        "bg_panel":      "#261820",   # dark crimson panel
        "bg_accent":     "#8b2252",   # rich crimson accent
        "bg_input":      "#150c11",   # darkest crimson
        "bg_card":       "#30202a",   # raised dark surface
        "bg_hover":      "#c62828",   # bright red hover
        "border":        "#4a2838",   # crimson border
        "border_hl":     "#e91e63",   # hot pink highlight
        "text":          "#f0e8ec",   # warm pink-white
        "text_dim":      "#a08090",   # muted mauve
        "text_header":   "#ff8a65",   # warm coral headers
        "green":         "#66bb6a",   # soft green
        "red":           "#ef5350",   # vivid red
        "yellow":        "#ffb74d",   # warm amber
        "gold":          "#ff8a65",   # coral gold
        "orange":        "#ff7043",   # deep coral
        "select_bg":     "#5a1a38",
        "row_win":       "#f0e8ec",
        "row_loss":      "#d09090",
        "row_even":      "#a08090",
        "graph_bg":      "#1a0f14",
        "graph_face":    "#261820",
        "graph_grid":    "#4a2838",
        "graph_line":    "#66bb6a",
        "graph_bar1":    "#e91e63",
        "graph_bar2":    "#ef5350",
        "pie_colors":    ["#e91e63", "#66bb6a", "#ef5350", "#ffb74d", "#ce93d8", "#4dd0e1"],
    },
    "Carbon": {
        "bg_base":       "#141414",   # true dark carbon
        "bg_panel":      "#1e1e1e",   # neutral dark gray
        "bg_accent":     "#333333",   # medium gray accent
        "bg_input":      "#111111",   # near-black input
        "bg_card":       "#282828",   # raised gray surface
        "bg_hover":      "#484848",   # light gray hover
        "border":        "#3a3a3a",   # neutral border
        "border_hl":     "#00e676",   # neon green highlight
        "text":          "#e0e0e0",   # clean gray-white
        "text_dim":      "#888888",   # mid gray
        "text_header":   "#00e676",   # neon green headers
        "green":         "#00e676",   # neon green
        "red":           "#ff1744",   # neon red
        "yellow":        "#ffea00",   # neon yellow
        "gold":          "#00e676",   # neon green highlights
        "orange":        "#ff9100",   # neon orange
        "select_bg":     "#2a2a3a",
        "row_win":       "#e0e0e0",
        "row_loss":      "#c09090",
        "row_even":      "#888888",
        "graph_bg":      "#141414",
        "graph_face":    "#1e1e1e",
        "graph_grid":    "#3a3a3a",
        "graph_line":    "#00e676",
        "graph_bar1":    "#448aff",
        "graph_bar2":    "#ff1744",
        "pie_colors":    ["#448aff", "#00e676", "#ff1744", "#ffea00", "#e040fb", "#18ffff"],
    },
    "Ocean Deep": {
        "bg_base":       "#0a1628",   # deep ocean blue-black
        "bg_panel":      "#0f2038",   # dark ocean panel
        "bg_accent":     "#0d4f8b",   # deep ocean accent
        "bg_input":      "#081220",   # abyss input
        "bg_card":       "#152a48",   # ocean card surface
        "bg_hover":      "#0288d1",   # bright ocean hover
        "border":        "#1a3a5c",   # deep blue border
        "border_hl":     "#00b0ff",   # electric blue highlight
        "text":          "#e0ecf4",   # ice white
        "text_dim":      "#6a90b0",   # ocean gray
        "text_header":   "#00e5ff",   # cyan headers
        "green":         "#00c853",   # sea green
        "red":           "#ff1744",   # signal red
        "yellow":        "#ffab00",   # amber
        "gold":          "#00e5ff",   # cyan highlights
        "orange":        "#ff6d00",   # deep orange
        "select_bg":     "#0a3260",
        "row_win":       "#e0ecf4",
        "row_loss":      "#c0a0a0",
        "row_even":      "#6a90b0",
        "graph_bg":      "#0a1628",
        "graph_face":    "#0f2038",
        "graph_grid":    "#1a3a5c",
        "graph_line":    "#00c853",
        "graph_bar1":    "#00b0ff",
        "graph_bar2":    "#ff1744",
        "pie_colors":    ["#00b0ff", "#00c853", "#ff1744", "#ffab00", "#aa00ff", "#00e5ff"],
    },
}

# Legacy globals — kept for backward compat during transition, driven by active theme
_active_theme = THEMES["Midnight Purple"]
BG_DARK   = _active_theme["bg_base"]
BG_PANEL  = _active_theme["bg_panel"]
BG_ACCENT = _active_theme["bg_accent"]
GREEN     = _active_theme["green"]
RED       = _active_theme["red"]
YELLOW    = _active_theme["yellow"]
TEXT      = _active_theme["text"]
TEXT_DIM  = _active_theme["text_dim"]
GOLD      = _active_theme["gold"]
ORANGE    = _active_theme["orange"]


def _lighten(hex_color, amount=0.15):
    """Lighten a hex color by a fraction."""
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    r = min(255, int(r + (255 - r) * amount))
    g = min(255, int(g + (255 - g) * amount))
    b = min(255, int(b + (255 - b) * amount))
    return f"#{r:02x}{g:02x}{b:02x}"

def _darken(hex_color, amount=0.15):
    """Darken a hex color by a fraction."""
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    r = max(0, int(r * (1 - amount)))
    g = max(0, int(g * (1 - amount)))
    b = max(0, int(b * (1 - amount)))
    return f"#{r:02x}{g:02x}{b:02x}"

if getattr(sys, 'frozen', False):
    # Running as compiled executable
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Running as script
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SETTINGS_PATH = os.path.join(BASE_DIR, "settings.json")
# Fallback: look in parent directory if not found in current (useful for dist/ structure)
if not os.path.exists(SETTINGS_PATH):
    PARENT_DIR = os.path.dirname(BASE_DIR)
    PARENT_SETTINGS = os.path.join(PARENT_DIR, "settings.json")
    if os.path.exists(PARENT_SETTINGS):
        BASE_DIR = PARENT_DIR
        SETTINGS_PATH = PARENT_SETTINGS

DEFAULT_SETTINGS = {
    "hero_names": {"CoinPoker": "jdwalka", "ACR": "JohnDaWalka"},
    "scan_dirs": [
        {"path": r"C:\Hand2Note4Hh\CoinPoker", "site": "CoinPoker"},
        {"path": r"C:\ACR Poker\handHistory\JohnDaWalka", "site": "ACR"},
        {"path": r"C:\ACR Poker\handHistory\JohnDaWalka - Copy", "site": "ACR"},
        {"path": r"C:\ACR Poker\TournamentSummary\JohnDaWalka", "site": "ACR"},
        {"path": r"C:\HM3Archive\Winning Poker Network", "site": "ACR"},
    ],
    "auto_refresh": True,
    "refresh_interval": 5,
    "dh2_db_path": os.path.join(os.environ.get("APPDATA", ""), "DriveHUD 2", "drivehud.db"),
    "dh2_auto_sync": True,
    "dh2_sync_interval": 5,
    "theme": "Midnight Purple",
    "advanced_mode": False,
}


# ─── Hand Data Model ──────────────────────────────────────────────────────────
class Hand:
    def __init__(self):
        self.hand_id = ""
        self.site = ""
        self.date = None
        self.game_type = ""
        self.is_tournament = False
        self.tournament_id = ""
        self.buy_in = ""
        self.table_name = ""
        self.max_seats = 0
        self.button_seat = 0
        self.players = {}
        self.hero_cards = ""
        self.board_cards = []
        self.streets = []
        self.pot = 0.0
        self.rake = 0.0
        self.winners = []
        self.hero_won = 0.0
        self.hero_position = ""
        self.raw_text = ""

    def hero_name(self, settings):
        return settings.get("hero_names", {}).get(self.site, "")


# ─── Hand Database (SQLite) ───────────────────────────────────────────────────
DB_PATH = os.path.join(BASE_DIR, "poker_hands.db")


class HandDatabase:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path, timeout=10)

    def _init_db(self):
        with self.lock:
            conn = self._connect()
            try:
                c = conn.cursor()
                c.executescript("""
                    CREATE TABLE IF NOT EXISTS hands (
                        hand_id TEXT PRIMARY KEY,
                        site TEXT NOT NULL,
                        hand_number TEXT,
                        date TEXT,
                        game_type TEXT,
                        is_tournament INTEGER DEFAULT 0,
                        tournament_id TEXT,
                        buy_in TEXT,
                        table_name TEXT,
                        max_seats INTEGER DEFAULT 0,
                        button_seat INTEGER DEFAULT 0,
                        hero_cards TEXT,
                        board_cards TEXT,
                        pot REAL DEFAULT 0,
                        rake REAL DEFAULT 0,
                        hero_won REAL DEFAULT 0,
                        hero_position TEXT,
                        raw_text TEXT,
                        source_file TEXT,
                        imported_at TEXT
                    );
                    CREATE TABLE IF NOT EXISTS players (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        hand_id TEXT NOT NULL,
                        seat INTEGER,
                        name TEXT,
                        stack REAL DEFAULT 0,
                        is_hero INTEGER DEFAULT 0,
                        FOREIGN KEY (hand_id) REFERENCES hands(hand_id)
                    );
                    CREATE TABLE IF NOT EXISTS actions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        hand_id TEXT NOT NULL,
                        street TEXT,
                        sequence INTEGER,
                        player TEXT,
                        action TEXT,
                        amount REAL DEFAULT 0,
                        FOREIGN KEY (hand_id) REFERENCES hands(hand_id)
                    );
                    CREATE TABLE IF NOT EXISTS winners (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        hand_id TEXT NOT NULL,
                        player_name TEXT,
                        amount REAL DEFAULT 0,
                        FOREIGN KEY (hand_id) REFERENCES hands(hand_id)
                    );
                    CREATE TABLE IF NOT EXISTS ocr_imports (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        image_path TEXT,
                        ocr_text TEXT,
                        parsed_cards TEXT,
                        parsed_pot REAL,
                        parsed_bets TEXT,
                        parsed_blinds TEXT,
                        notes TEXT,
                        hand_id TEXT,
                        created_at TEXT,
                        FOREIGN KEY (hand_id) REFERENCES hands(hand_id)
                    );
                    CREATE TABLE IF NOT EXISTS hand_tags (
                        hand_id TEXT NOT NULL,
                        tag TEXT NOT NULL,
                        created_at TEXT,
                        PRIMARY KEY (hand_id, tag),
                        FOREIGN KEY (hand_id) REFERENCES hands(hand_id)
                    );
                    CREATE TABLE IF NOT EXISTS player_types (
                        name TEXT PRIMARY KEY,
                        site TEXT DEFAULT '',
                        auto_type TEXT DEFAULT 'Unknown',
                        manual_type TEXT DEFAULT '',
                        hands INTEGER DEFAULT 0,
                        vpip REAL DEFAULT 0,
                        pfr REAL DEFAULT 0,
                        af REAL DEFAULT 0,
                        fold_cbet REAL DEFAULT 0,
                        wtsd REAL DEFAULT 0,
                        updated_at TEXT
                    );
                """)
                conn.commit()
            finally:
                conn.close()

    def hand_exists(self, hand_id):
        with self.lock:
            conn = self._connect()
            try:
                row = conn.execute(
                    "SELECT 1 FROM hands WHERE hand_id = ?", (hand_id,)
                ).fetchone()
                return row is not None
            finally:
                conn.close()

    def save_hand(self, hand, source_file=""):
        with self.lock:
            conn = self._connect()
            try:
                c = conn.cursor()
                date_str = hand.date.isoformat() if hand.date else None
                board_str = " ".join(hand.board_cards) if hand.board_cards else ""
                c.execute("""
                    INSERT OR REPLACE INTO hands
                    (hand_id, site, hand_number, date, game_type, is_tournament,
                     tournament_id, buy_in, table_name, max_seats, button_seat,
                     hero_cards, board_cards, pot, rake, hero_won, hero_position,
                     raw_text, source_file, imported_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    hand.hand_id, hand.site,
                    hand.hand_id.split("_", 1)[-1] if "_" in hand.hand_id else hand.hand_id,
                    date_str, hand.game_type,
                    1 if hand.is_tournament else 0,
                    hand.tournament_id, hand.buy_in, hand.table_name,
                    hand.max_seats, hand.button_seat, hand.hero_cards,
                    board_str, hand.pot, hand.rake, hand.hero_won,
                    hand.hero_position, hand.raw_text, source_file,
                    datetime.now().isoformat(),
                ))
                # players
                c.execute("DELETE FROM players WHERE hand_id = ?", (hand.hand_id,))
                for seat, info in hand.players.items():
                    c.execute(
                        "INSERT INTO players (hand_id, seat, name, stack, is_hero) VALUES (?,?,?,?,?)",
                        (hand.hand_id, seat, info["name"], info["stack"],
                         1 if info.get("is_hero") else 0),
                    )
                # actions
                c.execute("DELETE FROM actions WHERE hand_id = ?", (hand.hand_id,))
                seq = 0
                for street in hand.streets:
                    for act in street.get("actions", []):
                        c.execute(
                            "INSERT INTO actions (hand_id, street, sequence, player, action, amount) "
                            "VALUES (?,?,?,?,?,?)",
                            (hand.hand_id, street["name"], seq,
                             act["player"], act["action"], act["amount"]),
                        )
                        seq += 1
                # winners
                c.execute("DELETE FROM winners WHERE hand_id = ?", (hand.hand_id,))
                for w in hand.winners:
                    c.execute(
                        "INSERT INTO winners (hand_id, player_name, amount) VALUES (?,?,?)",
                        (hand.hand_id, w["name"], w["amount"]),
                    )
                conn.commit()
            finally:
                conn.close()

    def get_all_hands(self):
        with self.lock:
            conn = self._connect()
            try:
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                rows = c.execute("SELECT * FROM hands ORDER BY date DESC").fetchall()
                hands = []
                for row in rows:
                    h = Hand()
                    h.hand_id = row["hand_id"]
                    h.site = row["site"] or ""
                    if row["date"]:
                        try:
                            h.date = datetime.fromisoformat(row["date"])
                        except (ValueError, TypeError):
                            h.date = datetime.now()
                    else:
                        h.date = datetime.now()
                    h.game_type = row["game_type"] or ""
                    h.is_tournament = bool(row["is_tournament"])
                    h.tournament_id = row["tournament_id"] or ""
                    h.buy_in = row["buy_in"] or ""
                    h.table_name = row["table_name"] or ""
                    h.max_seats = row["max_seats"] or 0
                    h.button_seat = row["button_seat"] or 0
                    h.hero_cards = row["hero_cards"] or ""
                    h.board_cards = row["board_cards"].split() if row["board_cards"] else []
                    h.pot = row["pot"] or 0.0
                    h.rake = row["rake"] or 0.0
                    h.hero_won = row["hero_won"] or 0.0
                    h.hero_position = row["hero_position"] or ""
                    h.raw_text = row["raw_text"] or ""

                    # players
                    players_rows = c.execute(
                        "SELECT seat, name, stack, is_hero FROM players WHERE hand_id = ?",
                        (h.hand_id,),
                    ).fetchall()
                    for pr in players_rows:
                        h.players[pr["seat"]] = {
                            "name": pr["name"],
                            "stack": pr["stack"],
                            "is_hero": bool(pr["is_hero"]),
                        }

                    # streets / actions
                    action_rows = c.execute(
                        "SELECT street, player, action, amount FROM actions "
                        "WHERE hand_id = ? ORDER BY sequence",
                        (h.hand_id,),
                    ).fetchall()
                    streets_map = OrderedDict()
                    for ar in action_rows:
                        sname = ar["street"]
                        if sname not in streets_map:
                            streets_map[sname] = {"name": sname, "cards": [], "actions": []}
                        streets_map[sname]["actions"].append({
                            "player": ar["player"],
                            "action": ar["action"],
                            "amount": ar["amount"],
                        })
                    h.streets = list(streets_map.values())

                    # winners
                    winner_rows = c.execute(
                        "SELECT player_name, amount FROM winners WHERE hand_id = ?",
                        (h.hand_id,),
                    ).fetchall()
                    h.winners = [{"name": wr["player_name"], "amount": wr["amount"]}
                                 for wr in winner_rows]

                    hands.append(h)
                return hands
            finally:
                conn.close()

    def get_hand_count(self):
        with self.lock:
            conn = self._connect()
            try:
                rows = conn.execute(
                    "SELECT site, COUNT(*) as cnt FROM hands GROUP BY site"
                ).fetchall()
                return {r[0]: r[1] for r in rows}
            finally:
                conn.close()

    def save_ocr_import(self, image_path, ocr_text, elements, notes=""):
        with self.lock:
            conn = self._connect()
            try:
                cards_str = " ".join(elements.get("cards", []))
                pot_val = elements.get("pot") or 0.0
                bets_str = ",".join(str(b) for b in elements.get("bets", []))
                blinds_str = elements.get("blinds") or ""
                conn.execute(
                    "INSERT INTO ocr_imports (image_path, ocr_text, parsed_cards, "
                    "parsed_pot, parsed_bets, parsed_blinds, notes, created_at) "
                    "VALUES (?,?,?,?,?,?,?,?)",
                    (image_path, ocr_text, cards_str, pot_val, bets_str,
                     blinds_str, notes, datetime.now().isoformat()),
                )
                conn.commit()
            finally:
                conn.close()

    def save_ocr_as_hand(self, ocr_id, hand):
        self.save_hand(hand, source_file="OCR Import")
        with self.lock:
            conn = self._connect()
            try:
                conn.execute(
                    "UPDATE ocr_imports SET hand_id = ? WHERE id = ?",
                    (hand.hand_id, ocr_id),
                )
                conn.commit()
            finally:
                conn.close()

    def get_ocr_imports(self):
        with self.lock:
            conn = self._connect()
            try:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    "SELECT * FROM ocr_imports ORDER BY created_at DESC"
                ).fetchall()
                return [dict(r) for r in rows]
            finally:
                conn.close()

    def delete_hand(self, hand_id):
        with self.lock:
            conn = self._connect()
            try:
                for tbl in ("players", "actions", "winners"):
                    conn.execute(f"DELETE FROM {tbl} WHERE hand_id = ?", (hand_id,))
                conn.execute("DELETE FROM hands WHERE hand_id = ?", (hand_id,))
                conn.commit()
            finally:
                conn.close()

    def add_tag(self, hand_id, tag):
        with self.lock:
            conn = self._connect()
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO hand_tags (hand_id, tag, created_at) VALUES (?, ?, ?)",
                    (hand_id, tag.strip(), datetime.now().isoformat()))
                conn.commit()
            finally:
                conn.close()

    def remove_tag(self, hand_id, tag):
        with self.lock:
            conn = self._connect()
            try:
                conn.execute("DELETE FROM hand_tags WHERE hand_id = ? AND tag = ?", (hand_id, tag.strip()))
                conn.commit()
            finally:
                conn.close()

    def get_tags(self, hand_id):
        with self.lock:
            conn = self._connect()
            try:
                rows = conn.execute("SELECT tag FROM hand_tags WHERE hand_id = ? ORDER BY tag", (hand_id,)).fetchall()
                return [r[0] for r in rows]
            finally:
                conn.close()

    def get_all_tags(self):
        with self.lock:
            conn = self._connect()
            try:
                rows = conn.execute("SELECT DISTINCT tag FROM hand_tags ORDER BY tag").fetchall()
                return [r[0] for r in rows]
            finally:
                conn.close()

    def get_hand_ids_by_tag(self, tag):
        with self.lock:
            conn = self._connect()
            try:
                rows = conn.execute("SELECT hand_id FROM hand_tags WHERE tag = ?", (tag.strip(),)).fetchall()
                return {r[0] for r in rows}
            finally:
                conn.close()


    def save_player_type(self, name, auto_type, hands, vpip, pfr, af, fold_cbet, wtsd, site=""):
        with self.lock:
            conn = self._connect()
            try:
                existing = conn.execute(
                    "SELECT manual_type FROM player_types WHERE name = ?", (name,)).fetchone()
                manual = existing[0] if existing else ""
                conn.execute(
                    "INSERT OR REPLACE INTO player_types "
                    "(name, site, auto_type, manual_type, hands, vpip, pfr, af, fold_cbet, wtsd, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (name, site, auto_type, manual, hands, vpip, pfr, af, fold_cbet, wtsd,
                     datetime.now().isoformat()))
                conn.commit()
            finally:
                conn.close()

    def set_manual_player_type(self, name, manual_type):
        with self.lock:
            conn = self._connect()
            try:
                conn.execute(
                    "UPDATE player_types SET manual_type = ?, updated_at = ? WHERE name = ?",
                    (manual_type, datetime.now().isoformat(), name))
                if conn.total_changes == 0:
                    conn.execute(
                        "INSERT INTO player_types (name, manual_type, updated_at) VALUES (?, ?, ?)",
                        (name, manual_type, datetime.now().isoformat()))
                conn.commit()
            finally:
                conn.close()

    def get_player_type(self, name):
        with self.lock:
            conn = self._connect()
            try:
                row = conn.execute(
                    "SELECT auto_type, manual_type, hands, vpip, pfr, af, fold_cbet, wtsd "
                    "FROM player_types WHERE name = ?", (name,)).fetchone()
                if not row:
                    return None
                return {
                    "auto_type": row[0], "manual_type": row[1], "hands": row[2],
                    "vpip": row[3], "pfr": row[4], "af": row[5],
                    "fold_cbet": row[6], "wtsd": row[7],
                    "effective_type": row[1] if row[1] else row[0],
                }
            finally:
                conn.close()

    def get_all_player_types(self):
        with self.lock:
            conn = self._connect()
            try:
                rows = conn.execute(
                    "SELECT name, auto_type, manual_type, hands, vpip, pfr, af, fold_cbet, wtsd "
                    "FROM player_types ORDER BY hands DESC").fetchall()
                results = []
                for r in rows:
                    results.append({
                        "name": r[0], "auto_type": r[1], "manual_type": r[2],
                        "hands": r[3], "vpip": r[4], "pfr": r[5], "af": r[6],
                        "fold_cbet": r[7], "wtsd": r[8],
                        "effective_type": r[2] if r[2] else r[1],
                    })
                return results
            finally:
                conn.close()

    def get_players_by_type(self, player_type):
        with self.lock:
            conn = self._connect()
            try:
                rows = conn.execute(
                    "SELECT name FROM player_types "
                    "WHERE (manual_type = ? AND manual_type != '') OR (manual_type = '' AND auto_type = ?)",
                    (player_type, player_type)).fetchall()
                return {r[0] for r in rows}
            finally:
                conn.close()


# ─── Unified Parser ───────────────────────────────────────────────────────────
class HandParser:
    def __init__(self, settings):
        self.settings = settings

    def detect_site(self, text):
        for line in text.split("\n"):
            stripped = line.strip()
            if stripped.startswith("CoinPoker Hand #"):
                return "CoinPoker"
            if stripped.startswith("Game Hand #"):
                return "ACR"
        return None

    def split_hands(self, text, site):
        hands = []
        current = []
        for line in text.split("\n"):
            if site == "CoinPoker" and line.strip().startswith("CoinPoker Hand #"):
                if current:
                    hands.append("\n".join(current))
                current = [line]
            elif site == "ACR" and line.strip().startswith("Game Hand #"):
                if current:
                    hands.append("\n".join(current))
                current = [line]
            else:
                current.append(line)
        if current:
            hands.append("\n".join(current))
        return hands

    def parse_file(self, filepath, site):
        results = []
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception:
            return results
        if not content.strip():
            return results
        detected = self.detect_site(content)
        if detected is None:
            return results
        raw_hands = self.split_hands(content, detected)
        for raw in raw_hands:
            try:
                h = self._parse_single(raw.strip(), detected)
                if h and h.hand_id:
                    h.raw_text = raw.strip()
                    results.append(h)
            except Exception:
                continue
        return results

    def _parse_single(self, text, site):
        if site == "CoinPoker":
            return self._parse_coinpoker(text)
        elif site == "ACR":
            return self._parse_acr(text)
        
        # Fallback: Try to detect format from content
        if "CoinPoker Hand #" in text:
            return self._parse_coinpoker(text)
        if "Game Hand #" in text:
            return self._parse_acr(text)

        return None

    # ── CoinPoker parser ──────────────────────────────────────────────────
    def _parse_coinpoker(self, text):
        h = Hand()
        h.site = "CoinPoker"
        lines = text.split("\n")
        hero = self.settings.get("hero_names", {}).get("CoinPoker", "jdwalka")

        header = lines[0] if lines else ""
        m = re.search(r"CoinPoker Hand #(\d+)", header)
        if not m:
            return None
        h.hand_id = f"CP_{m.group(1)}"

        tm = re.search(r"Tournament #(\d+)", header)
        if tm:
            h.is_tournament = True
            h.tournament_id = tm.group(1)
        bi = re.search(r"[₮$€](\d+(?:\.\d+)?)\+[₮$€]?(\d+(?:\.\d+)?)", header)
        if bi:
            h.buy_in = f"{bi.group(1)}+{bi.group(2)}"
        h.game_type = "NLHE"
        dm = re.search(r"(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2})", header)
        if dm:
            try:
                h.date = datetime.strptime(dm.group(1), "%Y/%m/%d %H:%M:%S")
            except ValueError:
                h.date = datetime.now()
        else:
            h.date = datetime.now()

        table_line = lines[1] if len(lines) > 1 else ""
        tm2 = re.search(r"Table '([^']+)'", table_line)
        if tm2:
            h.table_name = tm2.group(1)
        sm = re.search(r"(\d+)-max", table_line)
        if sm:
            h.max_seats = int(sm.group(1))
        bm = re.search(r"Seat #(\d+) is the button", table_line)
        if bm:
            h.button_seat = int(bm.group(1))

        for line in lines:
            seat_m = re.match(r"Seat (\d+): (.+?) \((\d+(?:\.\d+)?) in chips\)", line.strip())
            if seat_m:
                seat_num = int(seat_m.group(1))
                name = seat_m.group(2)
                stack = float(seat_m.group(3))
                h.players[seat_num] = {"name": name, "stack": stack, "is_hero": name == hero}

        hc = re.search(r"Dealt to " + re.escape(hero) + r" \[(.+?)\]", text)
        if hc:
            h.hero_cards = hc.group(1)

        h.streets = self._parse_streets_coinpoker(lines, hero)
        h.board_cards = self._extract_board(text)

        pot_m = re.search(r"Total pot (\d+(?:\.\d+)?)", text)
        if pot_m:
            h.pot = float(pot_m.group(1))
        rake_m = re.search(r"Rake (\d+(?:\.\d+)?)", text)
        if rake_m:
            h.rake = float(rake_m.group(1))

        for line in lines:
            wm = re.match(r"(.+?) collected (\d+(?:\.\d+)?) from", line.strip())
            if wm:
                h.winners.append({"name": wm.group(1), "amount": float(wm.group(2))})

        h.hero_won = self._calc_hero_result(h, hero)
        h.hero_position = self._calc_position(h, hero)
        return h

    def _parse_streets_coinpoker(self, lines, hero):
        streets = []
        current_street = None
        in_actions = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("*** HOLE CARDS ***"):
                current_street = {"name": "Preflop", "cards": [], "actions": []}
                streets.append(current_street)
                in_actions = True
                continue
            if stripped.startswith("*** FLOP ***"):
                cards_m = re.search(r"\[(.+?)\]", stripped)
                cards = cards_m.group(1).split() if cards_m else []
                current_street = {"name": "Flop", "cards": cards, "actions": []}
                streets.append(current_street)
                in_actions = True
                continue
            if stripped.startswith("*** TURN ***"):
                cards_m = re.findall(r"\[(.+?)\]", stripped)
                cards = cards_m[-1].split() if cards_m else []
                current_street = {"name": "Turn", "cards": cards, "actions": []}
                streets.append(current_street)
                in_actions = True
                continue
            if stripped.startswith("*** RIVER ***"):
                cards_m = re.findall(r"\[(.+?)\]", stripped)
                cards = cards_m[-1].split() if cards_m else []
                current_street = {"name": "River", "cards": cards, "actions": []}
                streets.append(current_street)
                in_actions = True
                continue
            if stripped.startswith("*** SHOW DOWN ***") or stripped.startswith("*** SUMMARY ***"):
                in_actions = False
                continue
            if in_actions and current_street is not None and ": " in stripped:
                act_m = re.match(r"(.+?): (.+)", stripped)
                if act_m:
                    pname = act_m.group(1)
                    action_str = act_m.group(2)
                    action, amount = self._parse_action(action_str)
                    if action and not stripped.startswith("Dealt to"):
                        current_street["actions"].append(
                            {"player": pname, "action": action, "amount": amount}
                        )
        return streets

    # ── ACR parser ────────────────────────────────────────────────────────
    def _parse_acr(self, text):
        h = Hand()
        h.site = "ACR"
        lines = text.split("\n")
        hero = self.settings.get("hero_names", {}).get("ACR", "JohnDaWalka")

        header = lines[0] if lines else ""
        m = re.search(r"Game Hand #(\d+)", header)
        if not m:
            return None
        h.hand_id = f"ACR_{m.group(1)}"

        tm = re.search(r"Tournament #(\d+)", header)
        if tm:
            h.is_tournament = True
            h.tournament_id = tm.group(1)
        h.game_type = "NLHE"
        dm = re.search(r"(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2})", header)
        if dm:
            try:
                h.date = datetime.strptime(dm.group(1), "%Y/%m/%d %H:%M:%S")
            except ValueError:
                h.date = datetime.now()
        else:
            h.date = datetime.now()

        table_line = lines[1] if len(lines) > 1 else ""
        tm2 = re.search(r"Table '([^']+)'", table_line)
        if tm2:
            h.table_name = tm2.group(1)
        sm = re.search(r"(\d+)-max", table_line)
        if sm:
            h.max_seats = int(sm.group(1))
        bm = re.search(r"Seat #(\d+) is the button", table_line)
        if bm:
            h.button_seat = int(bm.group(1))

        for line in lines:
            seat_m = re.match(r"Seat (\d+): (.+?) \((\d+(?:\.\d+)?)\)", line.strip())
            if seat_m:
                seat_num = int(seat_m.group(1))
                name = seat_m.group(2)
                stack = float(seat_m.group(3))
                h.players[seat_num] = {"name": name, "stack": stack, "is_hero": name == hero}

        hc = re.search(r"Dealt to " + re.escape(hero) + r" \[(.+?)\]", text)
        if hc:
            h.hero_cards = hc.group(1)

        h.streets = self._parse_streets_acr(lines, hero)
        h.board_cards = self._extract_board(text)

        pot_m = re.search(r"Total pot (\d+(?:\.\d+)?)", text)
        if pot_m:
            h.pot = float(pot_m.group(1))

        for line in lines:
            wm = re.match(r"(.+?) collected (\d+(?:\.\d+)?) from", line.strip())
            if wm:
                h.winners.append({"name": wm.group(1), "amount": float(wm.group(2))})

        h.hero_won = self._calc_hero_result(h, hero)
        h.hero_position = self._calc_position(h, hero)
        return h

    def _parse_streets_acr(self, lines, hero):
        streets = []
        current_street = None
        in_actions = False
        player_names = set()
        for line in lines:
            sm = re.match(r"Seat \d+: (.+?) \(", line.strip())
            if sm:
                player_names.add(sm.group(1))

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("*** HOLE CARDS ***"):
                current_street = {"name": "Preflop", "cards": [], "actions": []}
                streets.append(current_street)
                in_actions = True
                continue
            if stripped.startswith("*** FLOP ***"):
                cards_m = re.search(r"\[(.+?)\]", stripped)
                cards = cards_m.group(1).split() if cards_m else []
                current_street = {"name": "Flop", "cards": cards, "actions": []}
                streets.append(current_street)
                in_actions = True
                continue
            if stripped.startswith("*** TURN ***"):
                cards_m = re.findall(r"\[(.+?)\]", stripped)
                cards = cards_m[-1].split() if cards_m else []
                current_street = {"name": "Turn", "cards": cards, "actions": []}
                streets.append(current_street)
                in_actions = True
                continue
            if stripped.startswith("*** RIVER ***"):
                cards_m = re.findall(r"\[(.+?)\]", stripped)
                cards = cards_m[-1].split() if cards_m else []
                current_street = {"name": "River", "cards": cards, "actions": []}
                streets.append(current_street)
                in_actions = True
                continue
            if stripped.startswith("*** SHOW DOWN ***") or stripped.startswith("*** SUMMARY ***"):
                in_actions = False
                continue
            if in_actions and current_street is not None:
                if stripped.startswith("Dealt to"):
                    continue
                for pname in player_names:
                    if stripped.startswith(pname + " "):
                        rest = stripped[len(pname) + 1:]
                        action, amount = self._parse_action(rest)
                        if action:
                            current_street["actions"].append(
                                {"player": pname, "action": action, "amount": amount}
                            )
                        break
                else:
                    parts = stripped.split(" ", 1)
                    if len(parts) == 2:
                        action, amount = self._parse_action(parts[1])
                        if action:
                            current_street["actions"].append(
                                {"player": parts[0], "action": action, "amount": amount}
                            )
        return streets

    # ── Shared helpers ────────────────────────────────────────────────────
    def _parse_action(self, action_str):
        action_str = action_str.strip().lower()
        if action_str.startswith("fold"):
            return "fold", 0.0
        if action_str.startswith("check"):
            return "check", 0.0
        if action_str.startswith("call"):
            am = re.search(r"(\d+(?:\.\d+)?)", action_str)
            return "call", float(am.group(1)) if am else 0.0
        if action_str.startswith("raise"):
            am = re.search(r"to (\d+(?:\.\d+)?)", action_str)
            if am:
                return "raise", float(am.group(1))
            am = re.search(r"(\d+(?:\.\d+)?)", action_str)
            return "raise", float(am.group(1)) if am else 0.0
        if action_str.startswith("bet"):
            am = re.search(r"(\d+(?:\.\d+)?)", action_str)
            return "bet", float(am.group(1)) if am else 0.0
        if "all-in" in action_str or "allin" in action_str:
            am = re.search(r"(\d+(?:\.\d+)?)", action_str)
            return "raise", float(am.group(1)) if am else 0.0
        if action_str.startswith("posts"):
            am = re.search(r"(\d+(?:\.\d+)?)", action_str)
            return "post", float(am.group(1)) if am else 0.0
        return None, 0.0

    def _extract_board(self, text):
        m = re.search(r"Board \[(.+?)\]", text)
        if m:
            return m.group(1).split()
        return []

    def _calc_hero_result(self, h, hero):
        won = 0.0
        for w in h.winners:
            if w["name"] == hero:
                won += w["amount"]
        invested = 0.0
        for street in h.streets:
            for act in street["actions"]:
                if act["player"] == hero and act["action"] in ("call", "raise", "bet", "post"):
                    invested += act["amount"]
        if won > 0:
            return won - invested
        return -invested if invested > 0 else 0.0

    def _calc_position(self, h, hero):
        hero_seat = None
        for seat, info in h.players.items():
            if info["name"] == hero:
                hero_seat = seat
                break
        if hero_seat is None:
            return "?"
        if hero_seat == h.button_seat:
            return "BTN"
        seats_sorted = sorted(h.players.keys())
        n = len(seats_sorted)
        if n <= 1:
            return "?"
        btn_idx = seats_sorted.index(h.button_seat) if h.button_seat in seats_sorted else 0
        sb_idx = (btn_idx + 1) % n
        bb_idx = (btn_idx + 2) % n
        if seats_sorted[sb_idx] == hero_seat:
            return "SB"
        if seats_sorted[bb_idx] == hero_seat:
            return "BB"
        hero_idx = seats_sorted.index(hero_seat)
        dist = (hero_idx - btn_idx) % n
        if n <= 4:
            return "CO"
        if dist == n - 1:
            return "CO"
        if dist <= n // 2:
            return "EP"
        return "MP"


# ─── Leak Detection Engine ────────────────────────────────────────────────────
class LeakEngine:
    def __init__(self, settings):
        self.settings = settings

    def analyze(self, hands):
        stats = {
            "total_hands": 0, "vpip_hands": 0, "pfr_hands": 0,
            "bets_raises": 0, "calls": 0, "saw_flop": 0,
            "went_to_sd": 0, "won_at_sd": 0,
            "cbet_opportunities": 0, "cbet_made": 0,
            "by_position": defaultdict(lambda: {"total": 0, "vpip": 0, "pfr": 0}),
            "by_site": defaultdict(lambda: {
                "total": 0, "vpip": 0, "pfr": 0, "won": 0.0, "lost": 0.0
            }),
            "biggest_wins": [], "biggest_losses": [],
        }
        for h in hands:
            hero = h.hero_name(self.settings)
            if not hero:
                continue
            stats["total_hands"] += 1
            stats["by_site"][h.site]["total"] += 1
            pos = h.hero_position
            stats["by_position"][pos]["total"] += 1

            if h.hero_won > 0:
                stats["by_site"][h.site]["won"] += h.hero_won
            else:
                stats["by_site"][h.site]["lost"] += abs(h.hero_won)

            preflop = h.streets[0] if h.streets else None
            hero_vpip = False
            hero_pfr = False
            hero_is_pfr = False
            if preflop:
                for act in preflop["actions"]:
                    if act["player"] == hero:
                        if act["action"] in ("call", "raise", "bet"):
                            hero_vpip = True
                        if act["action"] in ("raise", "bet"):
                            hero_pfr = True
                            hero_is_pfr = True

            if hero_vpip:
                stats["vpip_hands"] += 1
                stats["by_site"][h.site]["vpip"] += 1
                stats["by_position"][pos]["vpip"] += 1
            if hero_pfr:
                stats["pfr_hands"] += 1
                stats["by_site"][h.site]["pfr"] += 1
                stats["by_position"][pos]["pfr"] += 1

            saw_flop = False
            went_sd = False
            for street in h.streets:
                for act in street["actions"]:
                    if act["player"] == hero:
                        if act["action"] in ("bet", "raise"):
                            stats["bets_raises"] += 1
                        if act["action"] == "call":
                            stats["calls"] += 1
                    if street["name"] == "Flop":
                        saw_flop = True
                    if street["name"] == "River":
                        for a2 in street["actions"]:
                            if a2["player"] == hero and a2["action"] != "fold":
                                went_sd = True

            if saw_flop:
                stats["saw_flop"] += 1
            if went_sd:
                stats["went_to_sd"] += 1
                hero_won_hand = any(w["name"] == hero for w in h.winners)
                if hero_won_hand:
                    stats["won_at_sd"] += 1

            if hero_is_pfr and len(h.streets) > 1:
                flop_street = h.streets[1] if h.streets[1]["name"] == "Flop" else None
                if flop_street:
                    stats["cbet_opportunities"] += 1
                    for act in flop_street["actions"]:
                        if act["player"] == hero and act["action"] in ("bet", "raise"):
                            stats["cbet_made"] += 1
                            break

            stats["biggest_wins"].append((h.hero_won, h))
            stats["biggest_losses"].append((h.hero_won, h))

        stats["biggest_wins"].sort(key=lambda x: x[0], reverse=True)
        stats["biggest_wins"] = stats["biggest_wins"][:5]
        stats["biggest_losses"].sort(key=lambda x: x[0])
        stats["biggest_losses"] = stats["biggest_losses"][:5]

        return self._compute_final(stats)

    def _compute_final(self, s):
        t = s["total_hands"] or 1
        sf = s["saw_flop"] or 1
        sd = s["went_to_sd"] or 1
        result = {
            "total_hands": s["total_hands"],
            "vpip": round(100 * s["vpip_hands"] / t, 1),
            "pfr": round(100 * s["pfr_hands"] / t, 1),
            "af": round(s["bets_raises"] / max(s["calls"], 1), 2),
            "wtsd": round(100 * s["went_to_sd"] / sf, 1),
            "wsd": round(100 * s["won_at_sd"] / sd, 1),
            "cbet": round(100 * s["cbet_made"] / max(s["cbet_opportunities"], 1), 1),
            "by_position": {},
            "by_site": {},
            "biggest_wins": s["biggest_wins"],
            "biggest_losses": s["biggest_losses"],
            "alerts": [],
        }
        for pos, d in s["by_position"].items():
            pt = d["total"] or 1
            result["by_position"][pos] = {
                "total": d["total"],
                "vpip": round(100 * d["vpip"] / pt, 1),
                "pfr": round(100 * d["pfr"] / pt, 1),
            }
        for site, d in s["by_site"].items():
            st = d["total"] or 1
            result["by_site"][site] = {
                "total": d["total"],
                "vpip": round(100 * d["vpip"] / st, 1),
                "pfr": round(100 * d["pfr"] / st, 1),
                "won": round(d["won"], 2),
                "lost": round(d["lost"], 2),
                "net": round(d["won"] - d["lost"], 2),
            }
        result["alerts"] = self._generate_alerts(result)
        return result

    def _generate_alerts(self, r):
        alerts = []
        vpip = r["vpip"]
        pfr = r["pfr"]
        af = r["af"]
        wtsd = r["wtsd"]
        wsd = r["wsd"]
        cbet = r["cbet"]

        if vpip > 30:
            alerts.append(("red", f"VPIP too high ({vpip}%) — playing too many hands"))
        elif vpip < 15:
            alerts.append(("red", f"VPIP too low ({vpip}%) — playing too tight"))
        elif 15 <= vpip <= 22:
            alerts.append(("green", f"VPIP looks good ({vpip}%)"))
        else:
            alerts.append(("yellow", f"VPIP borderline ({vpip}%) — monitor closely"))

        if pfr > 25:
            alerts.append(("red", f"PFR too high ({pfr}%) — raising too much preflop"))
        elif pfr < 10:
            alerts.append(("red", f"PFR too low ({pfr}%) — not aggressive enough preflop"))
        elif 12 <= pfr <= 20:
            alerts.append(("green", f"PFR looks good ({pfr}%)"))
        else:
            alerts.append(("yellow", f"PFR borderline ({pfr}%)"))

        gap = vpip - pfr
        if gap > 12:
            alerts.append(("red", f"VPIP-PFR gap too wide ({gap:.1f}%) — calling too much preflop"))
        elif gap < 3:
            alerts.append(("yellow", f"VPIP-PFR gap narrow ({gap:.1f}%) — consider more calls"))
        else:
            alerts.append(("green", f"VPIP-PFR gap healthy ({gap:.1f}%)"))

        if af < 1.5:
            alerts.append(("red", f"AF too low ({af}) — too passive postflop"))
        elif af > 4.0:
            alerts.append(("yellow", f"AF very high ({af}) — may be over-aggressive"))
        else:
            alerts.append(("green", f"AF looks balanced ({af})"))

        if wtsd > 35:
            alerts.append(("yellow", f"WTSD high ({wtsd}%) — may be calling too much"))
        elif wtsd < 20:
            alerts.append(("yellow", f"WTSD low ({wtsd}%) — may be folding too much"))
        else:
            alerts.append(("green", f"WTSD balanced ({wtsd}%)"))

        if wsd < 45:
            alerts.append(("red", f"W$SD low ({wsd}%) — losing too often at showdown"))
        elif wsd > 55:
            alerts.append(("green", f"W$SD strong ({wsd}%)"))
        else:
            alerts.append(("green", f"W$SD acceptable ({wsd}%)"))

        if cbet > 80:
            alerts.append(("yellow", f"C-Bet too high ({cbet}%) — opponents can exploit"))
        elif cbet < 50:
            alerts.append(("yellow", f"C-Bet low ({cbet}%) — missing value"))
        else:
            alerts.append(("green", f"C-Bet % balanced ({cbet}%)"))

        return alerts


# ─── AI Summary Generator ────────────────────────────────────────────────────
class SummaryGenerator:
    def generate(self, stats, hands):
        lines = []
        lines.append("=" * 60)
        lines.append("POKER HAND TRACKER — AI ANALYSIS SUMMARY")
        lines.append("=" * 60)
        lines.append(f"Total Hands Analyzed: {stats['total_hands']}")
        lines.append("")

        lines.append("── Overall Stats ──")
        lines.append(f"  VPIP:    {stats['vpip']}%")
        lines.append(f"  PFR:     {stats['pfr']}%")
        lines.append(f"  AF:      {stats['af']}")
        lines.append(f"  WTSD:    {stats['wtsd']}%")
        lines.append(f"  W$SD:    {stats['wsd']}%")
        lines.append(f"  C-Bet:   {stats['cbet']}%")
        lines.append("")

        lines.append("── Per-Site Breakdown ──")
        for site, sd in stats.get("by_site", {}).items():
            lines.append(f"  {site}: {sd['total']} hands | "
                         f"VPIP {sd['vpip']}% | PFR {sd['pfr']}% | "
                         f"Net: {sd['net']:+.2f}")
        lines.append("")

        lines.append("── Positional Analysis ──")
        for pos in ["EP", "MP", "CO", "BTN", "SB", "BB"]:
            pd = stats.get("by_position", {}).get(pos)
            if pd:
                lines.append(f"  {pos:3s}: {pd['total']:4d} hands | "
                             f"VPIP {pd['vpip']:5.1f}% | PFR {pd['pfr']:5.1f}%")
        lines.append("")

        lines.append("── Leak Alerts ──")
        for color, msg in stats.get("alerts", []):
            icon = {"green": "\u2705", "yellow": "\u26a0\ufe0f", "red": "\u274c"}.get(color, "")
            lines.append(f"  {icon} {msg}")
        lines.append("")

        lines.append("── Top 5 Biggest Pots Won ──")
        for amt, h in stats.get("biggest_wins", []):
            if amt > 0:
                lines.append(f"  +{amt:.0f} | {h.site} | {h.hero_cards} | "
                             f"Board: {' '.join(h.board_cards)} | {h.hand_id}")
        lines.append("")

        lines.append("── Top 5 Biggest Pots Lost ──")
        for amt, h in stats.get("biggest_losses", []):
            if amt < 0:
                lines.append(f"  {amt:.0f} | {h.site} | {h.hero_cards} | "
                             f"Board: {' '.join(h.board_cards)} | {h.hand_id}")
        lines.append("")
        lines.append("=" * 60)
        lines.append("Generated by Poker Hand Tracker")
        lines.append("Paste this into ChatGPT or Grok for further analysis.")
        return "\n".join(lines)


# ─── File Watcher / Importer ──────────────────────────────────────────────────
class HandImporter:
    def __init__(self, settings, db=None):
        self.settings = settings
        self.parser = HandParser(settings)
        self.db = db
        self.hands = []
        self.files_scanned = set()
        self.file_mtimes = {}
        self.lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = None

    def update_settings(self, settings):
        with self.lock:
            self.settings = settings
            self.parser = HandParser(settings)

    def full_scan(self):
        new_hands = []
        files_count = 0
        for entry in self.settings.get("scan_dirs", []):
            path = entry["path"]
            site = entry["site"]
            if not os.path.isdir(path):
                continue
            for root, dirs, files in os.walk(path):
                for fname in files:
                    if not fname.lower().endswith(".txt"):
                        continue
                    fpath = os.path.join(root, fname)
                    mtime = os.path.getmtime(fpath)
                    if fpath in self.file_mtimes and self.file_mtimes[fpath] == mtime:
                        continue
                    self.file_mtimes[fpath] = mtime
                    parsed = self.parser.parse_file(fpath, site)
                    for h in parsed:
                        if self.db and self.db.hand_exists(h.hand_id):
                            continue
                        new_hands.append((h, fpath))
                    files_count += 1
                    self.files_scanned.add(fpath)
        saved = 0
        for h, fpath in new_hands:
            if self.db:
                self.db.save_hand(h, source_file=fpath)
                saved += 1
            else:
                with self.lock:
                    existing_ids = {hh.hand_id for hh in self.hands}
                    if h.hand_id not in existing_ids:
                        self.hands.append(h)
                        saved += 1
        return saved, files_count

    def import_files(self, file_paths):
        """Import hands from explicit file paths (manual import)."""
        new_hands = []
        files_count = 0
        for fpath in file_paths:
            if not os.path.isfile(fpath):
                continue
            try:
                with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
            except Exception:
                continue
            detected = self.parser.detect_site(content)
            if detected is None:
                continue
            parsed = self.parser.parse_file(fpath, detected)
            for h in parsed:
                if self.db and self.db.hand_exists(h.hand_id):
                    continue
                new_hands.append((h, fpath))
            files_count += 1
            self.file_mtimes[fpath] = os.path.getmtime(fpath)
            self.files_scanned.add(fpath)
        saved = 0
        for h, fpath in new_hands:
            if self.db:
                self.db.save_hand(h, source_file=fpath)
                saved += 1
            else:
                with self.lock:
                    existing_ids = {hh.hand_id for hh in self.hands}
                    if h.hand_id not in existing_ids:
                        self.hands.append(h)
                        saved += 1
        return saved, files_count

    def start_watcher(self, callback=None):
        self._stop.clear()
        self._thread = threading.Thread(target=self._watch_loop, args=(callback,), daemon=True)
        self._thread.start()

    def stop_watcher(self):
        self._stop.set()

    def _watch_loop(self, callback):
        while not self._stop.is_set():
            try:
                new_count, file_count = self.full_scan()
                if callback and new_count > 0:
                    callback(new_count, file_count)
            except Exception:
                pass
            interval = self.settings.get("refresh_interval", 5)
            self._stop.wait(interval)

    def get_hands(self):
        if self.db:
            return self.db.get_all_hands()
        with self.lock:
            return list(self.hands)

    def get_stats_text(self):
        if self.db:
            counts = self.db.get_hand_count()
            total = sum(counts.values())
            parts = [f"{site}: {count}" for site, count in counts.items() if count > 0]
            fcount = len(self.files_scanned)
            return f"{total} hands imported from {fcount} files ({', '.join(parts)})"
        with self.lock:
            total = len(self.hands)
            # Dynamic count for in-memory mode too
            counts = defaultdict(int)
            for h in self.hands:
                counts[h.site] += 1
            parts = [f"{site}: {count}" for site, count in counts.items()]
            fcount = len(self.files_scanned)
        return f"{total} hands imported from {fcount} files ({', '.join(parts)})"


# ─── DriveHUD 2 Database Sync ─────────────────────────────────────────────────
DH2_DB_DEFAULT = os.path.join(os.environ.get("APPDATA", ""), "DriveHUD 2", "drivehud.db")
DH2_STATE_FILE = os.path.join(os.path.dirname(DB_PATH), "dh2_sync_state.json")

# DH2 PokerSiteId → our site name
DH2_SITE_MAP = {44: "CoinPoker", 12: "ACR", 24: "ACR", 21: "BetOnline", 10: "Ignition"}
# DH2 GameType int → readable name
DH2_GAMETYPE_MAP = {1: "NLHE", 2: "LHE", 3: "PLO", 4: "NLO", 5: "PLO8", 29: "NLHE", 30: "NLHE"}


class DriveHUD2Sync:
    """Reads hands from DriveHUD 2's SQLite database and imports into our poker_hands.db."""

    def __init__(self, settings, db=None):
        self.settings = settings
        self.db = db
        self.parser = HandParser(settings)
        self.lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = None
        self.last_id = 0
        self.last_sync = None
        self.total_imported = 0
        self.dh2_db_path = settings.get("dh2_db_path", DH2_DB_DEFAULT)
        self._load_state()

    def _load_state(self):
        try:
            if os.path.exists(DH2_STATE_FILE):
                with open(DH2_STATE_FILE, "r") as f:
                    state = json.load(f)
                self.last_id = state.get("last_id", 0)
                self.total_imported = state.get("total_imported", 0)
        except Exception:
            pass

    def _save_state(self):
        try:
            with open(DH2_STATE_FILE, "w") as f:
                json.dump({"last_id": self.last_id, "total_imported": self.total_imported}, f)
        except Exception:
            pass

    def _connect_dh2(self):
        """Open DH2 database in read-only mode to avoid locking conflicts."""
        if not os.path.exists(self.dh2_db_path):
            return None
        uri = f"file:{self.dh2_db_path}?mode=ro"
        conn = sqlite3.connect(uri, uri=True, timeout=5)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        return conn

    def sync(self):
        """Pull new hands from DH2 and import them. Returns count of new hands."""
        conn = self._connect_dh2()
        if conn is None:
            return 0
        try:
            rows = conn.execute(
                "SELECT HandHistoryId, HandHistory, PokerSiteId, HandHistoryTimestamp, "
                "GameType, TournamentNumber FROM HandHistories "
                "WHERE HandHistoryId > ? ORDER BY HandHistoryId ASC",
                (self.last_id,)
            ).fetchall()
            if not rows:
                self.last_sync = datetime.now()
                return 0

            saved = 0
            for row in rows:
                hh_id = row["HandHistoryId"]
                raw = row["HandHistory"] or ""
                site_id = row["PokerSiteId"] or 0
                site_name = DH2_SITE_MAP.get(site_id, "Unknown")
                if site_name == "Unknown" and site_id > 0:
                    print(f"[DriveHUD2] Unknown site ID: {site_id}")

                game_type_id = row["GameType"] or 0
                tournament_num = row["TournamentNumber"] or ""

                try:
                    if raw.strip().startswith("<?xml") or raw.strip().startswith("<HandHistory"):
                        hand = self._parse_dh2_xml(raw, site_name, game_type_id, tournament_num)
                    else:
                        hand = self._parse_dh2_text(raw, site_name)

                    if hand and hand.hand_id:
                        if self.db and not self.db.hand_exists(hand.hand_id):
                            self.db.save_hand(hand, source_file=f"DriveHUD2:{hh_id}")
                            saved += 1
                except Exception:
                    pass

                self.last_id = max(self.last_id, hh_id)

            self.total_imported += saved
            self.last_sync = datetime.now()
            self._save_state()
            return saved
        finally:
            conn.close()

    def _parse_dh2_xml(self, xml_text, site_name, game_type_id, tournament_num):
        """Parse DH2's XML hand history format (used for CoinPoker cash games)."""
        h = Hand()
        h.site = site_name
        hero = self.settings.get("hero_names", {}).get(site_name, "")

        # Extract basic info using regex (lightweight, no xml lib needed)
        def xval(tag):
            m = re.search(rf"<{tag}[^>]*>([^<]*)</{tag}>", xml_text, re.I)
            return m.group(1).strip() if m else ""

        def xattr(element, attr):
            m = re.search(rf'{attr}="([^"]*)"', element, re.I)
            return m.group(1) if m else ""

        hand_num = xval("HandId") or xval("HandNumber") or xval("GameNumber")
        if not hand_num:
            return None
        prefix = "CP" if site_name == "CoinPoker" else "ACR"
        h.hand_id = f"{prefix}_{hand_num}"

        h.game_type = DH2_GAMETYPE_MAP.get(game_type_id, "NLHE")
        h.is_tournament = bool(tournament_num)
        h.tournament_id = str(tournament_num) if tournament_num else ""

        # Table info
        h.table_name = xval("TableName")
        try:
            h.max_seats = int(xval("TotalSeatNumber") or xval("NumPlayersSeated") or "0")
        except ValueError:
            h.max_seats = 0

        # Timestamp
        ts = xval("DateOfHandUtc") or xval("DateOfHand")
        if ts:
            for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%m/%d/%Y %I:%M:%S %p"):
                try:
                    h.date = datetime.strptime(ts.split(".")[0], fmt)
                    break
                except ValueError:
                    continue
        if not h.date:
            h.date = datetime.now()

        # Hero name from XML (fallback to settings)
        xml_hero = xval("HeroName") or hero

        # Players
        player_count = 0
        for pm in re.finditer(r"<Player\b([^/]*?)/>", xml_text, re.S):
            elem = pm.group(0)
            pname = xattr(elem, "PlayerName")
            try:
                seat = int(xattr(elem, "SeatNumber") or "0")
            except ValueError:
                seat = 0
            try:
                stack = float(xattr(elem, "StartingStack") or "0")
            except ValueError:
                stack = 0.0
            is_hero = (pname == xml_hero)
            h.players[seat] = {"name": pname, "stack": stack, "is_hero": is_hero}
            player_count += 1
            if is_hero:
                # DH2 uses "Cards" attr (e.g. "Th5d"), not "HoleCards"
                cards_str = xattr(elem, "HoleCards") or xattr(elem, "Cards") or ""
                if cards_str:
                    h.hero_cards = " ".join(
                        cards_str[i:i+2] for i in range(0, len(cards_str) - 1, 2)
                    )
        if h.max_seats == 0:
            h.max_seats = player_count

        # Button seat
        try:
            h.button_seat = int(xval("DealerButtonPosition") or "0")
        except ValueError:
            h.button_seat = 0

        # Actions → streets
        action_map = {
            "SMALL_BLIND": "posts small blind", "BIG_BLIND": "posts big blind",
            "ANTE": "posts ante", "RAISE": "raises", "CALL": "calls",
            "CHECK": "checks", "BET": "bets", "FOLD": "folds",
            "UNCALLED_BET": "uncalled bet", "WINS": "collected",
            "ALL_IN": "all-in", "POSTS": "posts",
        }
        streets_order = ["Preflop", "Flop", "Turn", "River"]
        streets_map = {}
        for am in re.finditer(r"<HandAction\b([^/]*?)/>", xml_text, re.S):
            elem = am.group(0)
            pname = xattr(elem, "PlayerName")
            act_type = xattr(elem, "HandActionType")
            street = xattr(elem, "Street") or "Preflop"
            try:
                amount = abs(float(xattr(elem, "Amount") or "0"))
            except ValueError:
                amount = 0.0
            action_str = action_map.get(act_type, act_type.lower())
            if street not in streets_map:
                streets_map[street] = {"name": street, "cards": [], "actions": []}
            streets_map[street]["actions"].append(
                {"player": pname, "action": action_str, "amount": amount}
            )

        h.streets = [streets_map[s] for s in streets_order if s in streets_map]

        # Community cards
        comm = xval("CommunityCards")
        if comm:
            h.board_cards = [comm[i:i+2] for i in range(0, len(comm) - 1, 2)]

        # Pot & rake
        try:
            h.pot = float(xval("TotalPot") or "0")
        except ValueError:
            h.pot = 0.0
        try:
            h.rake = float(xval("Rake") or "0")
        except ValueError:
            h.rake = 0.0

        # Winners — extract from Player Win attribute (most reliable)
        for pm in re.finditer(r"<Player\b([^/]*?)/>", xml_text, re.S):
            elem = pm.group(0)
            pname = xattr(elem, "PlayerName")
            try:
                win_amt = float(xattr(elem, "Win") or "0")
            except ValueError:
                win_amt = 0.0
            if win_amt > 0:
                h.winners.append({"name": pname, "amount": win_amt})

        # Fallback: check WINS actions (including Summary street)
        if not h.winners:
            for am in re.finditer(r'<HandAction\b[^>]*HandActionType="WINS"[^/]*/>', xml_text, re.S):
                elem = am.group(0)
                pname = xattr(elem, "PlayerName")
                try:
                    amt = abs(float(xattr(elem, "Amount") or "0"))
                except ValueError:
                    amt = 0.0
                if amt > 0:
                    h.winners.append({"name": pname, "amount": amt})

        # Hero result
        hero_invested = 0.0
        hero_won_amt = 0.0
        for s in h.streets:
            for act in s["actions"]:
                if act["player"] == xml_hero:
                    if act["action"] in ("posts small blind", "posts big blind", "posts ante",
                                         "raises", "calls", "bets"):
                        hero_invested += act["amount"]
                    elif act["action"] in ("collected", "uncalled bet"):
                        hero_won_amt += act["amount"]
        h.hero_won = hero_won_amt - hero_invested

        # Hero position
        h.hero_position = self._calc_hero_position(h, xml_hero)
        h.raw_text = xml_text
        return h

    def _parse_dh2_text(self, text, site_name):
        """Parse DH2's text-format hand history (WPN/ACR tournaments)."""
        try:
            hand = self.parser._parse_single(text.strip(), site_name)
            if hand:
                hand.raw_text = text.strip()
            return hand
        except Exception:
            return None

    def _calc_hero_position(self, hand, hero):
        """Determine hero's position from seat/button info."""
        hero_seat = None
        for seat, info in hand.players.items():
            if info.get("is_hero") or info["name"] == hero:
                hero_seat = seat
                break
        if hero_seat is None or hand.button_seat == 0:
            return ""
        n = len(hand.players)
        if n <= 1:
            return ""
        if hero_seat == hand.button_seat:
            return "BTN"
        seats = sorted(hand.players.keys())
        btn_idx = seats.index(hand.button_seat) if hand.button_seat in seats else 0
        hero_idx = seats.index(hero_seat) if hero_seat in seats else 0
        offset = (hero_idx - btn_idx) % n
        if offset == 1:
            return "SB"
        elif offset == 2:
            return "BB"
        elif offset == n - 1:
            return "CO"
        else:
            return "MP"

    # ── Two-way note sync ────────────────────────────────────────────────
    def push_hand_note(self, hand_number, note, site_id=44):
        """Push a hand note back to DriveHUD 2's database."""
        if not os.path.exists(self.dh2_db_path):
            return False
        try:
            conn = sqlite3.connect(self.dh2_db_path, timeout=5)
            conn.execute(
                "INSERT OR REPLACE INTO HandNotes (HandNumber, Note, PokerSiteId) "
                "VALUES (?, ?, ?)",
                (str(hand_number), note, site_id)
            )
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    def push_player_note(self, player_name, note, site_id=44):
        """Push a player note back to DriveHUD 2's database."""
        if not os.path.exists(self.dh2_db_path):
            return False
        try:
            conn = sqlite3.connect(self.dh2_db_path, timeout=5)
            conn.execute(
                "INSERT OR REPLACE INTO PlayerNotes (PlayerName, Note, PokerSiteId) "
                "VALUES (?, ?, ?)",
                (player_name, note, site_id)
            )
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    def get_hand_notes(self):
        """Read all hand notes from DH2."""
        conn = self._connect_dh2()
        if conn is None:
            return []
        try:
            rows = conn.execute("SELECT * FROM HandNotes").fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []
        finally:
            conn.close()

    def get_player_notes(self):
        """Read all player notes from DH2."""
        conn = self._connect_dh2()
        if conn is None:
            return []
        try:
            rows = conn.execute("SELECT * FROM PlayerNotes").fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []
        finally:
            conn.close()

    def get_tournaments(self):
        """Read tournament results from DH2."""
        conn = self._connect_dh2()
        if conn is None:
            return []
        try:
            rows = conn.execute(
                "SELECT TournamentNumber, TournamentName, BuyIn, Rake, Rebuy, "
                "Placing, WinAmount, PokerSiteId, StartDate "
                "FROM Tournaments ORDER BY StartDate DESC LIMIT 200"
            ).fetchall()
            results = []
            for r in rows:
                results.append({
                    "number": r["TournamentNumber"],
                    "name": r["TournamentName"],
                    "buy_in": (r["BuyIn"] or 0) / 100.0,
                    "rake": (r["Rake"] or 0) / 100.0,
                    "rebuy": (r["Rebuy"] or 0) / 100.0,
                    "placing": r["Placing"],
                    "winnings": (r["WinAmount"] or 0) / 100.0,
                    "site": DH2_SITE_MAP.get(r["PokerSiteId"], "Unknown"),
                    "date": r["StartDate"],
                })
            return results
        except Exception:
            return []
        finally:
            conn.close()

    def get_status(self):
        return {
            "connected": os.path.exists(self.dh2_db_path),
            "last_id": self.last_id,
            "total_imported": self.total_imported,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "db_path": self.dh2_db_path,
        }

    def reset(self):
        self.last_id = 0
        self.total_imported = 0
        self._save_state()

    def start_polling(self, callback=None, interval=None):
        """Start background polling for new DH2 hands."""
        self._stop.clear()
        poll_interval = interval or self.settings.get("dh2_sync_interval", 5)
        self._thread = threading.Thread(
            target=self._poll_loop, args=(callback, poll_interval), daemon=True
        )
        self._thread.start()

    def stop_polling(self):
        self._stop.set()

    def _poll_loop(self, callback, interval):
        while not self._stop.is_set():
            try:
                new_count = self.sync()
                if callback and new_count > 0:
                    callback(new_count)
            except Exception:
                pass
            self._stop.wait(interval)


# ─── Settings I/O ─────────────────────────────────────────────────────────────
def load_settings():
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return dict(DEFAULT_SETTINGS)


def save_settings(settings):
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
    except Exception:
        pass


# ─── OCR Engine (Windows built-in OCR) ────────────────────────────────────────
class PokerOCR:
    """Uses Windows 10 built-in OCR (Windows.Media.Ocr) — no external binaries."""

    PS_SCRIPT = r'''
Add-Type -AssemblyName System.Runtime.WindowsRuntime
[Windows.Media.Ocr.OcrEngine,Windows.Foundation,ContentType=WindowsRuntime] | Out-Null
[Windows.Graphics.Imaging.BitmapDecoder,Windows.Foundation,ContentType=WindowsRuntime] | Out-Null
[Windows.Storage.StorageFile,Windows.Foundation,ContentType=WindowsRuntime] | Out-Null
[Windows.Storage.Streams.RandomAccessStream,Windows.Foundation,ContentType=WindowsRuntime] | Out-Null

$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() |
    Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and
    $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]

Function Await($WinRtTask, $ResultType) {
    $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
    $netTask = $asTask.Invoke($null, @($WinRtTask))
    $netTask.Wait(-1) | Out-Null
    $netTask.Result
}

$imagePath = $args[0]
$file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($imagePath)) ([Windows.Storage.StorageFile])
$stream = Await ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
$decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
$bitmap = Await ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])

$ocrEngine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
if (-not $ocrEngine) { Write-Error "No OCR engine"; exit 1 }
$ocrResult = Await ($ocrEngine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])

foreach ($line in $ocrResult.Lines) {
    Write-Output $line.Text
}
$stream.Dispose()
'''

    def __init__(self):
        self._script_path = os.path.join(tempfile.gettempdir(), "poker_ocr_bridge.ps1")
        with open(self._script_path, "w", encoding="utf-8") as f:
            f.write(self.PS_SCRIPT)

    def preprocess_image(self, image_path):
        """Enhance image for better OCR: grayscale, contrast, sharpen, upscale."""
        img = Image.open(image_path)
        if img.mode == "RGBA":
            bg = Image.new("RGB", img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[3])
            img = bg
        elif img.mode != "RGB":
            img = img.convert("RGB")
        w, h = img.size
        if max(w, h) < 1500:
            scale = 1500 / max(w, h)
            img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        img = ImageEnhance.Contrast(img).enhance(1.8)
        img = ImageEnhance.Sharpness(img).enhance(2.0)
        img = img.convert("L")
        img = img.point(lambda x: 0 if x < 140 else 255)
        tmp = os.path.join(tempfile.gettempdir(), "poker_ocr_preprocessed.png")
        img.save(tmp, "PNG")
        return tmp

    def ocr_image(self, image_path):
        """Run OCR: try Tesseract first, fall back to Windows built-in OCR."""
        preprocessed = self.preprocess_image(image_path)
        if HAS_TESSERACT:
            try:
                from PIL import Image as PILImage
                img = PILImage.open(preprocessed)
                text = pytesseract.image_to_string(img, config='--psm 6')
                if text.strip():
                    return text.strip()
            except Exception:
                pass
        return self._windows_ocr(preprocessed)

    def _windows_ocr(self, preprocessed):
        """Fallback: Windows 10 built-in OCR via PowerShell."""
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                 "-File", self._script_path, preprocessed],
                capture_output=True, text=True, timeout=30, encoding="utf-8"
            )
            if result.returncode != 0:
                return f"[OCR Error] {result.stderr.strip()}"
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            return "[OCR Error] Timed out after 30 seconds"
        except Exception as e:
            return f"[OCR Error] {e}"

    def parse_poker_elements(self, text):
        """Extract poker-specific elements from OCR text."""
        elements = {
            "cards": [], "bets": [], "pot": None,
            "players": [], "board": [], "blinds": None,
            "hand_number": None, "raw_text": text,
            "actions": [], "players_detected": [],
        }
        lines = text.split("\n")
        current_street = "preflop"
        players_seen = set()
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Track current street
            street_m = re.search(r'\*\*\*\s*(FLOP|TURN|RIVER|PREFLOP|HOLE\s*CARDS)', line, re.IGNORECASE)
            if street_m:
                sname = street_m.group(1).lower().replace("hole cards", "preflop").strip()
                current_street = sname
            elif re.search(r'\b(FLOP)\b', line, re.IGNORECASE) and "fold" not in line.lower():
                current_street = "flop"
            elif re.search(r'\b(TURN)\b', line, re.IGNORECASE):
                current_street = "turn"
            elif re.search(r'\b(RIVER)\b', line, re.IGNORECASE):
                current_street = "river"

            # Extract player names from "Seat N: PlayerName (stack)" patterns
            seat_m = re.match(r'Seat\s+\d+:\s+(\S+(?:\s+\S+)?)\s*\(', line)
            if seat_m:
                pname = seat_m.group(1).strip()
                if pname not in players_seen:
                    players_seen.add(pname)
                    elements["players_detected"].append(pname)

            # Parse betting actions: "PlayerName: action [amount]"
            action_m = re.match(
                r'(.+?):\s+(folds?|checks?|calls?|bets?|raises?|all-in|all\s*in)'
                r'(?:\s+(?:to\s+)?([\d,]+(?:\.\d+)?))?',
                line, re.IGNORECASE,
            )
            if action_m:
                pname = action_m.group(1).strip()
                raw_act = action_m.group(2).lower().rstrip("s")
                amt_str = action_m.group(3)
                amt = 0.0
                if amt_str:
                    try:
                        amt = float(amt_str.replace(",", ""))
                    except ValueError:
                        pass
                # For raise lines like "raises 500 to 1000", prefer the "to" amount
                raise_to = re.search(r'to\s+([\d,]+(?:\.\d+)?)', line, re.IGNORECASE)
                if raw_act == "raise" and raise_to:
                    try:
                        amt = float(raise_to.group(1).replace(",", ""))
                    except ValueError:
                        pass
                act_name = raw_act.replace(" ", "-")
                if act_name == "fold":
                    act_name = "fold"
                elif act_name == "check":
                    act_name = "check"
                elif act_name == "call":
                    act_name = "call"
                elif act_name == "bet":
                    act_name = "bet"
                elif act_name == "raise":
                    act_name = "raise"
                elif "all" in act_name:
                    act_name = "all-in"
                elements["actions"].append({
                    "player": pname, "action": act_name,
                    "amount": amt, "street": current_street,
                })
                if pname not in players_seen:
                    players_seen.add(pname)
                    elements["players_detected"].append(pname)

            # Also detect "PlayerName is all-in 5000" style
            allin_m = re.match(r'(.+?)\s+is\s+all[- ]?in\s+([\d,]+(?:\.\d+)?)', line, re.IGNORECASE)
            if allin_m and not action_m:
                pname = allin_m.group(1).strip()
                try:
                    amt = float(allin_m.group(2).replace(",", ""))
                except ValueError:
                    amt = 0.0
                elements["actions"].append({
                    "player": pname, "action": "all-in",
                    "amount": amt, "street": current_street,
                })
                if pname not in players_seen:
                    players_seen.add(pname)
                    elements["players_detected"].append(pname)

            cards = re.findall(
                r'\b([2-9TJQKA][shdcSHDC])\b'
                r'|([2-9TJQKA]\s*(?:of\s+)?(?:spades?|hearts?|diamonds?|clubs?))',
                line, re.IGNORECASE
            )
            for match in cards:
                card = match[0] if match[0] else match[1]
                card = card.strip()
                if len(card) == 2:
                    elements["cards"].append(card[0].upper() + card[1].lower())

            unicode_cards = re.findall(r'[♠♥♦♣]\s*[2-9TJQKA]|[2-9TJQKA]\s*[♠♥♦♣]', line)
            suit_map = {"♠": "s", "♥": "h", "♦": "d", "♣": "c"}
            for uc in unicode_cards:
                uc = uc.replace(" ", "")
                if uc[0] in suit_map:
                    elements["cards"].append(uc[1].upper() + suit_map[uc[0]])
                elif uc[-1] in suit_map:
                    elements["cards"].append(uc[0].upper() + suit_map[uc[-1]])

            bets = re.findall(r'(?:bet|raise|call|all.?in|pot)\D{0,3}([\d,]+(?:\.\d+)?)', line, re.IGNORECASE)
            for b in bets:
                try:
                    elements["bets"].append(float(b.replace(",", "")))
                except ValueError:
                    pass

            pot_m = re.search(r'\bpot\b\D{0,5}([\d,]+(?:\.\d+)?)', line, re.IGNORECASE)
            if pot_m and not elements["pot"]:
                try:
                    elements["pot"] = float(pot_m.group(1).replace(",", ""))
                except ValueError:
                    pass

            blind_m = re.search(r'(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)', line)
            if blind_m and not elements["blinds"]:
                elements["blinds"] = f"{blind_m.group(1)}/{blind_m.group(2)}"

            hand_m = re.search(r'(?:Hand|Game)\s*#?\s*(\d{6,})', line, re.IGNORECASE)
            if hand_m:
                elements["hand_number"] = hand_m.group(1)

            board_m = re.search(r'(?:board|flop|community)\D{0,5}((?:[2-9TJQKA][shdcSHDC]\s*){3,5})', line, re.IGNORECASE)
            if board_m:
                elements["board"] = re.findall(r'[2-9TJQKA][shdcSHDC]', board_m.group(1), re.IGNORECASE)

        elements["cards"] = list(dict.fromkeys(elements["cards"]))
        return elements

    def format_analysis(self, elements):
        """Format parsed poker elements into readable analysis."""
        lines = []
        lines.append("=" * 50)
        lines.append("  POKER TABLE OCR ANALYSIS")
        lines.append("=" * 50)

        if elements.get("hand_number"):
            lines.append(f"\n  Hand #: {elements['hand_number']}")
        if elements.get("blinds"):
            lines.append(f"  Blinds: {elements['blinds']}")
        if elements.get("pot"):
            lines.append(f"  Pot: {elements['pot']:,.0f}")

        if elements.get("cards"):
            lines.append(f"\n  Cards detected: {' '.join(elements['cards'])}")
            if len(elements["cards"]) >= 2:
                lines.append(f"  Likely hole cards: {elements['cards'][0]} {elements['cards'][1]}")
            if len(elements["cards"]) >= 5:
                lines.append(f"  Likely board: {' '.join(elements['cards'][2:7])}")

        if elements.get("board"):
            lines.append(f"  Board: {' '.join(elements['board'])}")

        if elements.get("bets"):
            lines.append(f"\n  Bet amounts detected: {', '.join(f'{b:,.0f}' for b in elements['bets'])}")

        if elements.get("actions"):
            lines.append(f"\n  BETTING ACTIONS ({len(elements['actions'])} detected):")
            lines.append("  " + "-" * 46)
            current_street = ""
            for act in elements["actions"]:
                if act.get("street") and act["street"] != current_street:
                    current_street = act["street"]
                    lines.append(f"\n  [{current_street.upper()}]")
                amt = f" {act['amount']:,.0f}" if act["amount"] else ""
                lines.append(f"    {act['player']}: {act['action']}{amt}")

        if elements.get("players_detected"):
            lines.append(f"\n  Players: {', '.join(elements['players_detected'])}")

        lines.append("\n" + "=" * 50)
        lines.append("  RAW OCR TEXT:")
        lines.append("-" * 50)
        lines.append(elements.get("raw_text", "(no text)"))
        lines.append("=" * 50)
        return "\n".join(lines)


# ─── Station Detector (Player Classification) ────────────────────────────────
class StationDetector:
    """Analyze all opponents across all hands and classify player types."""

    def __init__(self, settings):
        self.settings = settings

    def analyze_players(self, hands):
        player_data = defaultdict(lambda: {
            "total_hands": 0, "vpip_hands": 0, "pfr_hands": 0,
            "bets_raises": 0, "calls": 0, "folds_to_cbet": 0,
            "cbet_faced": 0, "saw_flop": 0, "went_to_sd": 0,
        })

        for h in hands:
            hero = h.hero_name(self.settings)
            player_names = {info["name"] for info in h.players.values()}
            preflop = h.streets[0] if h.streets else None

            # Determine preflop raiser (last raiser)
            pfr_player = None
            if preflop:
                for act in preflop["actions"]:
                    if act["action"] in ("raise", "bet"):
                        pfr_player = act["player"]

            for pname in player_names:
                if pname == hero:
                    continue
                player_data[pname]["total_hands"] += 1

                if preflop:
                    p_vpip = False
                    p_pfr = False
                    for act in preflop["actions"]:
                        if act["player"] == pname:
                            if act["action"] in ("call", "raise", "bet"):
                                p_vpip = True
                            if act["action"] in ("raise", "bet"):
                                p_pfr = True
                    if p_vpip:
                        player_data[pname]["vpip_hands"] += 1
                    if p_pfr:
                        player_data[pname]["pfr_hands"] += 1

                saw_flop = False
                went_sd = False
                for street in h.streets:
                    for act in street["actions"]:
                        if act["player"] == pname:
                            if act["action"] in ("bet", "raise"):
                                player_data[pname]["bets_raises"] += 1
                            if act["action"] == "call":
                                player_data[pname]["calls"] += 1
                    if street["name"] == "Flop":
                        saw_flop = True
                    if street["name"] == "River":
                        for a2 in street["actions"]:
                            if a2["player"] == pname and a2["action"] != "fold":
                                went_sd = True
                if saw_flop:
                    player_data[pname]["saw_flop"] += 1
                if went_sd:
                    player_data[pname]["went_to_sd"] += 1

                # Fold to C-Bet
                if len(h.streets) > 1 and pfr_player and pfr_player != pname:
                    flop_st = h.streets[1] if h.streets[1]["name"] == "Flop" else None
                    if flop_st:
                        pfr_cbet = False
                        for act in flop_st["actions"]:
                            if act["player"] == pfr_player and act["action"] in ("bet", "raise"):
                                pfr_cbet = True
                            if pfr_cbet and act["player"] == pname:
                                player_data[pname]["cbet_faced"] += 1
                                if act["action"] == "fold":
                                    player_data[pname]["folds_to_cbet"] += 1
                                break

        results = []
        for pname, d in player_data.items():
            t = d["total_hands"] or 1
            sf = d["saw_flop"] or 1
            vpip = round(100 * d["vpip_hands"] / t, 1)
            pfr = round(100 * d["pfr_hands"] / t, 1)
            af = round(d["bets_raises"] / max(d["calls"], 1), 2)
            fold_cbet = round(100 * d["folds_to_cbet"] / max(d["cbet_faced"], 1), 1)
            wtsd = round(100 * d["went_to_sd"] / sf, 1)
            classification = self._classify(vpip, pfr, af, d["total_hands"])
            results.append({
                "name": pname, "hands": d["total_hands"],
                "vpip": vpip, "pfr": pfr, "af": af,
                "fold_cbet": fold_cbet, "wtsd": wtsd,
                "auto_type": classification,
                "manual_type": "",
                "classification": classification,
            })
        results.sort(key=lambda x: x["hands"], reverse=True)
        return results

    def apply_manual_overrides(self, results, db):
        """Apply manual type overrides from database."""
        for p in results:
            try:
                db_info = db.get_player_type(p["name"])
                if db_info and db_info["manual_type"]:
                    p["manual_type"] = db_info["manual_type"]
                    p["classification"] = db_info["manual_type"]
            except Exception:
                pass
        return results

    def _classify(self, vpip, pfr, af, hands):
        if hands < 10:
            return "Unknown"
        if vpip > 50 and pfr > 30:
            return "Maniac"
        if vpip > 40 and pfr < 10 and af < 1.5:
            return "Calling Station"
        if vpip > 35 and (vpip - pfr) > 15:
            return "Fish"
        if vpip > 28 and pfr > 20 and af > 2.5:
            return "LAG"
        if 15 <= vpip <= 25 and 12 <= pfr <= 22 and af > 2:
            return "TAG"
        if vpip < 15 and pfr < 10:
            return "Nit"
        return "Regular"


# ─── EV Calculator ────────────────────────────────────────────────────────────
class EVCalculator:
    """Simplified Expected Value analysis per hand."""

    HAND_STRENGTH = {
        "AA": 100, "KK": 95, "QQ": 90, "JJ": 85, "TT": 78,
        "99": 72, "88": 68, "77": 62, "66": 58, "55": 54,
        "44": 50, "33": 46, "22": 42,
        "AKs": 88, "AKo": 82, "AQs": 80, "AQo": 75,
        "AJs": 76, "AJo": 71, "ATs": 70, "ATo": 65,
        "A9s": 60, "A8s": 58, "A7s": 56, "A6s": 54,
        "A5s": 56, "A4s": 54, "A3s": 52, "A2s": 50,
        "KQs": 74, "KQo": 69, "KJs": 68, "KJo": 63,
        "KTs": 64, "K9s": 58, "K8s": 52, "K7s": 50,
        "K6s": 48, "K5s": 46, "K4s": 44, "K3s": 42, "K2s": 40,
        "QJs": 66, "QTs": 62, "Q9s": 54, "Q8s": 48,
        "JTs": 64, "J9s": 52, "J8s": 46,
        "T9s": 56, "T8s": 50, "T7s": 44,
        "98s": 54, "97s": 48, "96s": 42,
        "87s": 52, "86s": 46, "85s": 40,
        "76s": 50, "75s": 44, "74s": 38,
        "65s": 48, "64s": 42, "63s": 36,
        "54s": 46, "53s": 40, "52s": 34,
        "43s": 38, "42s": 32,
    }

    POSITION_MULT = {
        "BTN": 1.15, "CO": 1.10, "MP": 1.0, "EP": 0.90,
        "SB": 0.85, "BB": 0.90, "?": 1.0,
    }

    def get_hand_strength(self, hero_cards):
        if not hero_cards or len(hero_cards.split()) < 2:
            return 0
        parts = hero_cards.split()
        c1, c2 = parts[0], parts[1]
        if len(c1) < 2 or len(c2) < 2:
            return 0
        r1, s1 = c1[0].upper(), c1[1].lower()
        r2, s2 = c2[0].upper(), c2[1].lower()
        suited = s1 == s2
        rank_order = "23456789TJQKA"
        r1_idx = rank_order.index(r1) if r1 in rank_order else -1
        r2_idx = rank_order.index(r2) if r2 in rank_order else -1
        if r1_idx < 0 or r2_idx < 0:
            return 0
        if r2_idx > r1_idx:
            r1, r2 = r2, r1
            r1_idx, r2_idx = r2_idx, r1_idx
        if r1 == r2:
            key = r1 + r2
        else:
            key = r1 + r2 + ("s" if suited else "o")
        if key in self.HAND_STRENGTH:
            return self.HAND_STRENGTH[key]
        # Fallback for hands not in table
        if r1 == r2:
            return min(100, 35 + r1_idx * 5)
        if suited:
            return min(90, 20 + r1_idx * 3 + r2_idx * 2)
        return min(80, 15 + r1_idx * 3 + r2_idx)

    def calc_ev_diff(self, hand, settings):
        strength = self.get_hand_strength(hand.hero_cards)
        if strength == 0 or hand.pot <= 0:
            return 0.0
        pos = hand.hero_position or "MP"
        pos_mult = self.POSITION_MULT.get(pos, 1.0)
        adj_strength = min(100, strength * pos_mult)
        winrate = adj_strength / 100.0
        expected_result = hand.pot * (2 * winrate - 1)
        ev_diff = hand.hero_won - expected_result
        return round(ev_diff, 1)


# ─── Session Tilt Meter ──────────────────────────────────────────────────────
class TiltMeter:
    """Analyzes hero's recent play patterns to detect tilt."""

    def __init__(self, settings, window_size=20):
        self.settings = settings
        self.window_size = window_size

    def analyze(self, hands):
        if not hands or len(hands) < 5:
            return {"score": 0, "label": "Cool", "emoji": "COOL",
                    "color": GREEN, "indicators": [],
                    "advice": "Not enough data to analyze tilt."}

        sorted_hands = sorted(hands, key=lambda h: h.date or datetime.min, reverse=True)
        recent = sorted_hands[:self.window_size]
        baseline = sorted_hands

        base_vpip = self._calc_vpip(baseline)
        base_pfr = self._calc_pfr(baseline)
        base_af = self._calc_af(baseline)
        base_avg_pot = self._avg_pot(baseline)

        rec_vpip = self._calc_vpip(recent)
        rec_pfr = self._calc_pfr(recent)
        rec_af = self._calc_af(recent)
        rec_avg_pot = self._avg_pot(recent)
        rec_net = sum(h.hero_won for h in recent)

        rec_ep = sum(1 for h in recent if h.hero_position in ("EP", "MP")) / max(len(recent), 1)
        base_ep = sum(1 for h in baseline if h.hero_position in ("EP", "MP")) / max(len(baseline), 1)

        score = 0
        indicators = []

        vpip_diff = rec_vpip - base_vpip
        if vpip_diff > 10:
            score += 25
            indicators.append(f"VPIP spiked +{vpip_diff:.0f}% vs baseline")
        elif vpip_diff > 5:
            score += 12
            indicators.append(f"VPIP up +{vpip_diff:.0f}% vs baseline")

        pfr_diff = base_pfr - rec_pfr
        if pfr_diff > 8:
            score += 20
            indicators.append(f"PFR dropped {pfr_diff:.0f}% (passive)")
        elif pfr_diff > 4:
            score += 10
            indicators.append(f"PFR down {pfr_diff:.0f}%")

        af_diff = base_af - rec_af
        if af_diff > 1.0:
            score += 15
            indicators.append(f"AF dropped {af_diff:.1f} (calling more)")
        elif af_diff > 0.5:
            score += 8
            indicators.append(f"AF down {af_diff:.1f}")

        if rec_net < 0:
            loss_severity = min(abs(rec_net) / max(base_avg_pot * 10, 1) * 15, 20)
            score += int(loss_severity)
            indicators.append(f"Recent net: {rec_net:+.0f} (losing)")

        if base_avg_pot > 0:
            pot_ratio = rec_avg_pot / base_avg_pot
            if pot_ratio > 1.5:
                score += 15
                indicators.append(f"Avg pot {pot_ratio:.1f}x bigger (chasing)")
            elif pot_ratio > 1.2:
                score += 8
                indicators.append(f"Avg pot {pot_ratio:.1f}x larger")

        ep_diff = rec_ep - base_ep
        if ep_diff > 0.15:
            score += 10
            indicators.append("Playing more hands from early position")

        score = min(100, max(0, score))

        if score <= 25:
            label, emoji, color = "Cool", "COOL", GREEN
            advice = "You are playing your A-game. Stay focused!"
        elif score <= 50:
            label, emoji, color = "Warm", "WARM", YELLOW
            advice = "Some tilt indicators detected. Take a short break if needed."
        elif score <= 75:
            label, emoji, color = "Heated", "HOT!", ORANGE
            advice = "Significant tilt detected! Consider stopping or taking a 15-min break."
        else:
            label, emoji, color = "Tilting", "TILT", RED
            advice = "STOP PLAYING! You are on heavy tilt. Walk away and come back later."

        return {"score": score, "label": label, "emoji": emoji, "color": color,
                "indicators": indicators, "advice": advice}

    def _calc_vpip(self, hands):
        t, v = 0, 0
        for h in hands:
            hero = h.hero_name(self.settings)
            if not hero:
                continue
            t += 1
            pf = h.streets[0] if h.streets else None
            if pf:
                for act in pf["actions"]:
                    if act["player"] == hero and act["action"] in ("call", "raise", "bet"):
                        v += 1
                        break
        return 100 * v / max(t, 1)

    def _calc_pfr(self, hands):
        t, p = 0, 0
        for h in hands:
            hero = h.hero_name(self.settings)
            if not hero:
                continue
            t += 1
            pf = h.streets[0] if h.streets else None
            if pf:
                for act in pf["actions"]:
                    if act["player"] == hero and act["action"] in ("raise", "bet"):
                        p += 1
                        break
        return 100 * p / max(t, 1)

    def _calc_af(self, hands):
        br, ca = 0, 0
        for h in hands:
            hero = h.hero_name(self.settings)
            if not hero:
                continue
            for street in h.streets:
                for act in street["actions"]:
                    if act["player"] == hero:
                        if act["action"] in ("bet", "raise"):
                            br += 1
                        if act["action"] == "call":
                            ca += 1
        return br / max(ca, 1)

    def _avg_pot(self, hands):
        if not hands:
            return 0
        return sum(h.pot for h in hands) / len(hands)


# ─── GUI Application ──────────────────────────────────────────────────────────
class PokerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Poker Tracker")
        self.geometry("1280x800")
        self.settings = load_settings()
        self.theme_name = self.settings.get("theme", "Midnight Purple")
        self.theme = THEMES.get(self.theme_name, THEMES["Midnight Purple"])
        self.advanced_mode = self.settings.get("advanced_mode", False)

        self.configure(fg_color=self.theme["bg_base"])

        self.db = HandDatabase()
        self.importer = HandImporter(self.settings, db=self.db)
        self.dh2_sync = DriveHUD2Sync(self.settings, db=self.db)
        self.leak_engine = LeakEngine(self.settings)
        self.summary_gen = SummaryGenerator()
        self.ocr_engine = PokerOCR()
        self.current_stats = {}
        self.station_detector = StationDetector(self.settings)
        self.ev_calculator = EVCalculator()
        self.tilt_meter = TiltMeter(self.settings)
        self.player_stats = []
        self.tilt_data = {}

        self._build_ui()
        self._initial_scan()

    # ── UI Construction ───────────────────────────────────────────────────
    def _build_ui(self):
        self.tabview = ctk.CTkTabview(self, fg_color=self.theme["bg_panel"],
                                       segmented_button_fg_color=self.theme["bg_accent"],
                                       segmented_button_selected_color=self.theme["bg_accent"],
                                       segmented_button_unselected_color=self.theme["bg_base"],
                                       text_color=self.theme["text"])
        self.tabview.pack(fill="both", expand=True, padx=8, pady=(8, 0))

        self.tab_dash = self.tabview.add("Dashboard")
        self.tab_hands = self.tabview.add("Hands")
        self.tab_leak = self.tabview.add("Leaks")
        self.tab_ocr = self.tabview.add("OCR")
        self.tab_ai = self.tabview.add("AI / GTO")
        self.tab_settings = self.tabview.add("Settings")

        self._build_dashboard()
        self._build_hands_tab()
        self._build_leak_tab()
        self._build_ocr_tab()
        self._build_ai_tab()
        self._build_settings_tab()
        self._build_status_bar()

    def _panel(self, parent, *, fill="x", expand=False, padx=6, pady=4, fg_color=None):
        panel = ctk.CTkFrame(
            parent,
            fg_color=fg_color or self.theme["bg_panel"],
            border_width=1,
            border_color=self.theme["border"],
            corner_radius=10,
        )
        panel.pack(fill=fill, expand=expand, padx=padx, pady=pady)
        return panel

    def _section_label(self, parent, text, *, size=14, color=None):
        return ctk.CTkLabel(
            parent,
            text=text,
            text_color=color or self.theme["gold"],
            font=("Consolas", size, "bold"),
        )

    def _action_button(self, parent, text, command, *, tone="neutral", width=100, height=30, bold=False):
        palettes = {
            "neutral": (self.theme["bg_accent"], self.theme["green"], self.theme["text"]),
            "accent": (self.theme["gold"], self.theme["bg_accent"], self.theme["bg_base"]),
            "success": (self.theme["green"], self.theme["bg_accent"], self.theme["bg_base"]),
            "danger": (self.theme["red"], self.theme["bg_accent"], self.theme["text"]),
        }
        fg_color, hover_color, text_color = palettes.get(tone, palettes["neutral"])
        weight = "bold" if bold else "normal"
        return ctk.CTkButton(
            parent,
            text=text,
            command=command,
            fg_color=fg_color,
            hover_color=hover_color,
            text_color=text_color,
            width=width,
            height=height,
            font=("Consolas", 11, weight),
        )

    def _build_dashboard(self):
        tab = self.tab_dash
        top = self._panel(tab, pady=6)

        self.dash_cards = {}
        card_defs = [
            ("Hands", "0", self.theme["text"]),
            ("VPIP", "0%", self.theme["gold"]),
            ("PFR", "0%", self.theme["gold"]),
            ("AF", "0.0", self.theme["gold"]),
            ("Won", "0", self.theme["green"]),
            ("Lost", "0", self.theme["red"]),
            ("EV Diff", "0", self.theme["gold"]),
        ]
        for i, (label, default, color) in enumerate(card_defs):
            frame = ctk.CTkFrame(
                top,
                fg_color=self.theme["bg_card"],
                corner_radius=10,
                width=150,
                height=80,
                border_width=1,
                border_color=self.theme["border"],
            )
            frame.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")
            frame.grid_propagate(False)
            top.grid_columnconfigure(i, weight=1)
            ctk.CTkLabel(
                frame,
                text=label,
                text_color=self.theme["text_dim"],
                font=("Consolas", 12),
            ).pack(pady=(8, 0))
            val = ctk.CTkLabel(frame, text=default, text_color=color, font=("Consolas", 20, "bold"))
            val.pack(pady=(0, 8))
            self.dash_cards[label] = val

        overview_row = ctk.CTkFrame(tab, fg_color="transparent")
        overview_row.pack(fill="x", padx=6, pady=4)
        overview_row.grid_columnconfigure(0, weight=3)
        overview_row.grid_columnconfigure(1, weight=2)

        site_frame = ctk.CTkFrame(
            overview_row,
            fg_color=self.theme["bg_panel"],
            border_width=1,
            border_color=self.theme["border"],
            corner_radius=10,
        )
        site_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 3))
        self._section_label(site_frame, "By Site").pack(anchor="w", padx=8, pady=4)
        self.dash_site_text = ctk.CTkTextbox(
            site_frame,
            height=86,
            fg_color=self.theme["bg_input"],
            text_color=self.theme["text"],
            font=("Consolas", 12),
        )
        self.dash_site_text.pack(fill="x", padx=8, pady=(0, 8))
        self.dash_site_text.configure(state="disabled")

        tilt_frame = ctk.CTkFrame(
            overview_row,
            fg_color=self.theme["bg_panel"],
            border_width=1,
            border_color=self.theme["border"],
            corner_radius=10,
        )
        tilt_frame.grid(row=0, column=1, sticky="nsew", padx=(3, 0))
        tilt_top = ctk.CTkFrame(tilt_frame, fg_color="transparent")
        tilt_top.pack(fill="x", padx=8, pady=(6, 0))
        self._section_label(tilt_top, "Tilt", size=13).pack(side="left")
        self.tilt_score_label = ctk.CTkLabel(
            tilt_top,
            text="Cool 0/100",
            text_color=self.theme["green"],
            font=("Consolas", 12, "bold"),
        )
        self.tilt_score_label.pack(side="right")
        self.tilt_bar = ctk.CTkProgressBar(
            tilt_frame,
            fg_color=self.theme["bg_input"],
            progress_color=self.theme["green"],
            height=18,
        )
        self.tilt_bar.pack(fill="x", padx=8, pady=4)
        self.tilt_bar.set(0)
        self.tilt_advice_label = ctk.CTkLabel(
            tilt_frame,
            text="Waiting for data",
            text_color=self.theme["text_dim"],
            font=("Consolas", 11),
        )
        self.tilt_advice_label.pack(anchor="w", padx=12, pady=(0, 2))
        self.tilt_indicators_text = ctk.CTkTextbox(
            tilt_frame,
            height=52,
            fg_color=self.theme["bg_input"],
            text_color=self.theme["text"],
            font=("Consolas", 10),
        )
        self.tilt_indicators_text.pack(fill="x", padx=8, pady=(0, 4))
        self.tilt_indicators_text.configure(state="disabled")

        action_bar = ctk.CTkFrame(tilt_frame, fg_color="transparent")
        action_bar.pack(fill="x", padx=8, pady=(0, 8))
        self._action_button(
            action_bar,
            "Player HUD",
            self._open_hud_window,
            tone="accent",
            width=120,
            bold=True,
        ).pack(side="left")

        self.graph_frame = self._panel(tab)
        self._section_label(self.graph_frame, "Trend & Mix").pack(anchor="w", padx=8, pady=4)
        self.dash_fig = Figure(figsize=(10, 3), dpi=80)
        self.dash_fig.patch.set_facecolor(self.theme["graph_bg"])
        self.dash_canvas = FigureCanvasTkAgg(self.dash_fig, master=self.graph_frame)
        self.dash_canvas.get_tk_widget().pack(fill="x", padx=8, pady=(0, 8))

        recent_frame = self._panel(tab, fill="both", expand=True)
        self._section_label(recent_frame, "Recent Hands").pack(anchor="w", padx=8, pady=4)
        self.dash_recent = ctk.CTkTextbox(
            recent_frame,
            fg_color=self.theme["bg_input"],
            text_color=self.theme["text"],
            font=("Consolas", 11),
        )
        self.dash_recent.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.dash_recent.configure(state="disabled")

    def _build_hands_tab(self):
        tab = self.tab_hands

        filter_frame = ctk.CTkFrame(tab, fg_color=self.theme["bg_panel"],
                                    border_width=1, border_color=self.theme["border"])
        filter_frame.pack(fill="x", padx=6, pady=(6, 2))

        ctk.CTkLabel(filter_frame, text="Site", text_color=self.theme["text"]).pack(side="left", padx=4)
        self.hand_site_var = ctk.StringVar(value="All")
        self.hand_site_menu = ctk.CTkOptionMenu(
            filter_frame,
            variable=self.hand_site_var,
            values=["All", "CoinPoker", "ACR", "OCR"],
            fg_color=self.theme["bg_accent"],
            button_color=self.theme["bg_hover"],
            text_color=self.theme["text"],
            width=100,
            dropdown_fg_color=self.theme["bg_card"],
            dropdown_hover_color=self.theme["bg_accent"],
            command=lambda _: self._refresh_hands_list(),
        )
        self.hand_site_menu.pack(side="left", padx=4)

        ctk.CTkLabel(filter_frame, text="Net", text_color=self.theme["text"]).pack(side="left", padx=4)
        self.hand_result_var = ctk.StringVar(value="All")
        ctk.CTkOptionMenu(
            filter_frame,
            variable=self.hand_result_var,
            values=["All", "Won", "Lost"],
            fg_color=self.theme["bg_accent"],
            button_color=self.theme["bg_hover"],
            text_color=self.theme["text"],
            width=80,
            dropdown_fg_color=self.theme["bg_card"],
            dropdown_hover_color=self.theme["bg_accent"],
            command=lambda _: self._refresh_hands_list(),
        ).pack(side="left", padx=4)

        ctk.CTkLabel(filter_frame, text="Sort", text_color=self.theme["text"]).pack(side="left", padx=(12, 4))
        self.hand_sort_var = ctk.StringVar(value="Date ↓")
        ctk.CTkOptionMenu(
            filter_frame,
            variable=self.hand_sort_var,
            values=["Date ↓", "Date ↑", "Result ↓ (Big wins)", "Result ↑ (Big losses)", "Pot ↓", "Pot ↑"],
            fg_color=self.theme["bg_accent"],
            button_color=self.theme["bg_hover"],
            text_color=self.theme["text"],
            width=170,
            dropdown_fg_color=self.theme["bg_card"],
            dropdown_hover_color=self.theme["bg_accent"],
            command=lambda _: self._refresh_hands_list(),
        ).pack(side="left", padx=4)

        self._action_button(filter_frame, "Reload", self._manual_refresh, width=74).pack(side="right", padx=4)

        adv_filter_frame = ctk.CTkFrame(tab, fg_color=self.theme["bg_panel"],
                                        border_width=1, border_color=self.theme["border"])
        adv_filter_frame.pack(fill="x", padx=6, pady=(0, 2))

        ctk.CTkLabel(adv_filter_frame, text="From", text_color=self.theme["text"], font=("Consolas", 11)).pack(side="left", padx=(6, 2))
        self.filter_date_from_var = ctk.StringVar(value="")
        ctk.CTkEntry(
            adv_filter_frame,
            textvariable=self.filter_date_from_var,
            fg_color=self.theme["bg_input"],
            text_color=self.theme["text"],
            width=90,
            placeholder_text="MM/DD/YYYY",
            font=("Consolas", 10),
        ).pack(side="left", padx=2)

        ctk.CTkLabel(adv_filter_frame, text="To", text_color=self.theme["text"], font=("Consolas", 11)).pack(side="left", padx=(6, 2))
        self.filter_date_to_var = ctk.StringVar(value="")
        ctk.CTkEntry(
            adv_filter_frame,
            textvariable=self.filter_date_to_var,
            fg_color=self.theme["bg_input"],
            text_color=self.theme["text"],
            width=90,
            placeholder_text="MM/DD/YYYY",
            font=("Consolas", 10),
        ).pack(side="left", padx=2)

        ctk.CTkLabel(adv_filter_frame, text="Pot", text_color=self.theme["text"], font=("Consolas", 11)).pack(side="left", padx=(10, 2))
        self.filter_pot_min_var = ctk.StringVar(value="")
        ctk.CTkEntry(
            adv_filter_frame,
            textvariable=self.filter_pot_min_var,
            fg_color=self.theme["bg_input"],
            text_color=self.theme["text"],
            width=60,
            placeholder_text="Min",
            font=("Consolas", 10),
        ).pack(side="left", padx=2)

        self.filter_pot_max_var = ctk.StringVar(value="")
        ctk.CTkEntry(
            adv_filter_frame,
            textvariable=self.filter_pot_max_var,
            fg_color=self.theme["bg_input"],
            text_color=self.theme["text"],
            width=60,
            placeholder_text="Max",
            font=("Consolas", 10),
        ).pack(side="left", padx=2)

        ctk.CTkLabel(adv_filter_frame, text="Game", text_color=self.theme["text"], font=("Consolas", 11)).pack(side="left", padx=(10, 2))
        self.filter_type_var = ctk.StringVar(value="All")
        ctk.CTkOptionMenu(
            adv_filter_frame,
            variable=self.filter_type_var,
            values=["All", "Cash", "Tournament"],
            fg_color=self.theme["bg_accent"],
            button_color=self.theme["bg_hover"],
            text_color=self.theme["text"],
            width=100,
            dropdown_fg_color=self.theme["bg_card"],
            dropdown_hover_color=self.theme["bg_accent"],
            font=("Consolas", 10),
            command=lambda _: self._refresh_hands_list(),
        ).pack(side="left", padx=2)

        ctk.CTkLabel(adv_filter_frame, text="Tag", text_color=self.theme["text"], font=("Consolas", 11)).pack(side="left", padx=(10, 2))
        self.filter_tag_var = ctk.StringVar(value="All")
        self.filter_tag_menu = ctk.CTkOptionMenu(
            adv_filter_frame,
            variable=self.filter_tag_var,
            values=["All"],
            fg_color=self.theme["bg_accent"],
            button_color=self.theme["bg_hover"],
            text_color=self.theme["text"],
            width=110,
            dropdown_fg_color=self.theme["bg_card"],
            dropdown_hover_color=self.theme["bg_accent"],
            font=("Consolas", 10),
            command=lambda _: self._refresh_hands_list(),
        )
        self.filter_tag_menu.pack(side="left", padx=2)

        self._action_button(adv_filter_frame, "Apply", self._refresh_hands_list, width=64, height=24, bold=True).pack(side="left", padx=(8, 2))
        ctk.CTkLabel(adv_filter_frame, text="Villain", text_color=self.theme["text"], font=("Consolas", 11)).pack(side="left", padx=(10, 2))
        self.filter_opp_type_var = ctk.StringVar(value="All")
        self.filter_opp_type_menu = ctk.CTkOptionMenu(
            adv_filter_frame,
            variable=self.filter_opp_type_var,
            values=["All", "Fish", "Calling Station", "LAG", "TAG", "Nit", "Maniac", "Regular", "Unknown"],
            fg_color=self.theme["bg_accent"],
            button_color=self.theme["bg_hover"],
            text_color=self.theme["text"],
            width=120,
            dropdown_fg_color=self.theme["bg_card"],
            dropdown_hover_color=self.theme["bg_accent"],
            font=("Consolas", 10),
            command=lambda _: self._refresh_hands_list(),
        )
        self.filter_opp_type_menu.pack(side="left", padx=2)

        self._action_button(adv_filter_frame, "Clear", self._clear_filters, width=60, height=24).pack(side="left", padx=2)

        sel_frame = ctk.CTkFrame(tab, fg_color=self.theme["bg_panel"],
                                 border_width=1, border_color=self.theme["border"])
        sel_frame.pack(fill="x", padx=6, pady=(0, 4))

        self.select_all_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            sel_frame,
            text="All",
            variable=self.select_all_var,
            fg_color=self.theme["bg_accent"],
            hover_color=self.theme["green"],
            text_color=self.theme["text"],
            font=("Consolas", 11),
            checkbox_width=18,
            checkbox_height=18,
            command=self._toggle_select_all,
        ).pack(side="left", padx=8)

        self.hand_sel_count_label = ctk.CTkLabel(
            sel_frame,
            text="0 selected",
            text_color=self.theme["text_dim"],
            font=("Consolas", 11),
        )
        self.hand_sel_count_label.pack(side="left", padx=8)

        self._action_button(sel_frame, "Compare", self._compare_selected, tone="accent", width=100, bold=True).pack(side="left", padx=4)
        self._action_button(sel_frame, "Copy", self._copy_selected_hands, width=84).pack(side="left", padx=4)
        self._action_button(sel_frame, "Tag", self._tag_selected_hands, width=70).pack(side="left", padx=4)
        self._action_button(sel_frame, "Analyze", self._analyze_filtered, tone="accent", width=96, bold=True).pack(side="left", padx=4)
        self._action_button(sel_frame, "Export", self._export_filtered, width=82).pack(side="right", padx=4)

        hand_list_container = ctk.CTkFrame(tab, fg_color=self.theme["bg_input"])
        hand_list_container.pack(fill="both", expand=True, padx=6, pady=2)

        header_text = f"  {'Date':14s} {'Site':10s} {'Game':5s} {'Cards':8s} {'Pos':4s} {'Net':>8s} {'Pot':>7s} {'EV':>7s}  Tags"
        header_label = ctk.CTkLabel(
            hand_list_container,
            text=header_text,
            text_color=self.theme["gold"],
            font=("Consolas", 11, "bold"),
            anchor="w",
        )
        header_label.pack(fill="x", padx=2, pady=(2, 0))

        self.hands_text = tk.Text(
            hand_list_container,
            bg=self.theme["bg_input"],
            fg=self.theme["text"],
            font=("Consolas", 11),
            relief="flat",
            cursor="arrow",
            selectbackground=self.theme["select_bg"],
            wrap="none",
            state="disabled",
        )
        self.hands_text.pack(fill="both", expand=True, side="left")
        hands_scrollbar = tk.Scrollbar(hand_list_container, command=self.hands_text.yview)
        hands_scrollbar.pack(fill="y", side="right")
        self.hands_text.configure(yscrollcommand=hands_scrollbar.set)

        self.hand_count_label = ctk.CTkLabel(tab, text="0 hands", text_color=self.theme["text_dim"], font=("Consolas", 10))
        self.hand_count_label.pack(anchor="w", padx=10, pady=(0, 2))

        detail_frame = ctk.CTkFrame(tab, fg_color=self.theme["bg_panel"],
                                    border_width=1, border_color=self.theme["border"])
        detail_frame.pack(fill="both", expand=True, padx=6, pady=4)

        detail_top = ctk.CTkFrame(detail_frame, fg_color=self.theme["bg_panel"])
        detail_top.pack(fill="x")
        self.detail_title_label = ctk.CTkLabel(
            detail_top,
            text="Details",
            text_color=self.theme["gold"],
            font=("Consolas", 13, "bold"),
        )
        self.detail_title_label.pack(side="left", anchor="w", padx=8, pady=4)

        self.hand_detail_text = ctk.CTkTextbox(
            detail_frame,
            fg_color=self.theme["bg_input"],
            text_color=self.theme["text"],
            font=("Consolas", 10),
        )
        self.hand_detail_text.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self._hand_objects = {}
        self._selected_hand_ids = set()

    def _build_leak_tab(self):
        tab = self.tab_leak
        top = self._panel(tab, pady=6)
        ctk.CTkLabel(top, text="Leak Analysis", text_color=self.theme["gold"], font=("Consolas", 16, "bold")).pack(pady=8)

        self.leak_stats_frame = self._panel(tab)

        self.leak_alerts_frame = self._panel(tab)
        self._section_label(self.leak_alerts_frame, "Alerts").pack(anchor="w", padx=8, pady=4)
        self.leak_alerts_text = ctk.CTkTextbox(
            self.leak_alerts_frame,
            height=120,
            fg_color=self.theme["bg_input"],
            text_color=self.theme["text"],
            font=("Consolas", 12),
        )
        self.leak_alerts_text.pack(fill="x", padx=8, pady=(0, 8))

        pos_frame = self._panel(tab, fill="both", expand=True)
        self._section_label(pos_frame, "By Position").pack(anchor="w", padx=8, pady=4)
        self.leak_pos_text = ctk.CTkTextbox(
            pos_frame,
            fg_color=self.theme["bg_input"],
            text_color=self.theme["text"],
            font=("Consolas", 12),
        )
        self.leak_pos_text.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self.leak_graph_frame = self._panel(tab)
        self._section_label(self.leak_graph_frame, "Position VPIP / PFR").pack(anchor="w", padx=8, pady=4)
        self.leak_fig = Figure(figsize=(10, 3), dpi=80)
        self.leak_fig.patch.set_facecolor(self.theme["graph_bg"])
        self.leak_canvas = FigureCanvasTkAgg(self.leak_fig, master=self.leak_graph_frame)
        self.leak_canvas.get_tk_widget().pack(fill="x", padx=8, pady=(0, 8))

        site_frame = self._panel(tab)
        self._section_label(site_frame, "By Site").pack(anchor="w", padx=8, pady=4)
        self.leak_site_text = ctk.CTkTextbox(
            site_frame,
            height=80,
            fg_color=self.theme["bg_input"],
            text_color=self.theme["text"],
            font=("Consolas", 12),
        )
        self.leak_site_text.pack(fill="x", padx=8, pady=(0, 8))

    def _build_ocr_tab(self):
        tab = self.tab_ocr

        top_frame = self._panel(tab, pady=6)
        self._section_label(top_frame, "Table Screenshot").pack(anchor="w", padx=8, pady=4)

        btn_row = ctk.CTkFrame(top_frame, fg_color=self.theme["bg_panel"])
        btn_row.pack(fill="x", padx=8, pady=4)
        self._action_button(btn_row, "Browse", self._ocr_browse, tone="success", width=92, bold=True).pack(side="left", padx=4)
        self._action_button(btn_row, "Paste", self._ocr_paste, width=88).pack(side="left", padx=4)
        self._action_button(btn_row, "Analyze", self._ocr_analyze, tone="accent", width=92, bold=True).pack(side="left", padx=4)
        self._action_button(btn_row, "Copy", self._ocr_copy_analysis, width=84).pack(side="left", padx=4)
        self._action_button(btn_row, "Save OCR", self._ocr_save_to_db, width=96).pack(side="right", padx=4)

        self.ocr_file_var = ctk.StringVar(value="No image")
        ctk.CTkLabel(top_frame, textvariable=self.ocr_file_var, text_color=self.theme["text_dim"], font=("Consolas", 10)).pack(anchor="w", padx=12, pady=(0, 4))

        content = self._panel(tab, fill="both", expand=True, pady=(0, 2))
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=1)
        content.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(content, fg_color=self.theme["bg_input"], corner_radius=8)
        left.grid(row=0, column=0, sticky="nsew", padx=(4, 2), pady=4)
        ctk.CTkLabel(left, text="Preview", text_color=self.theme["text_dim"], font=("Consolas", 11)).pack(anchor="w", padx=6, pady=2)

        self.ocr_preview_label = ctk.CTkLabel(
            left,
            text="No image\n\nPaste or browse to start",
            text_color=self.theme["text_dim"],
            font=("Consolas", 12),
            fg_color=self.theme["bg_input"],
        )
        self.ocr_preview_label.pack(fill="both", expand=True, padx=4, pady=4)
        self._ocr_photo = None

        right = ctk.CTkFrame(content, fg_color=self.theme["bg_input"], corner_radius=8)
        right.grid(row=0, column=1, sticky="nsew", padx=(2, 4), pady=4)
        ctk.CTkLabel(right, text="Result", text_color=self.theme["text_dim"], font=("Consolas", 11)).pack(anchor="w", padx=6, pady=2)

        self.ocr_result_text = ctk.CTkTextbox(right, fg_color=self.theme["bg_input"], text_color=self.theme["text"], font=("Consolas", 11))
        self.ocr_result_text.pack(fill="both", expand=True, padx=4, pady=4)
        ocr_method = "Tesseract + Windows OCR fallback" if HAS_TESSERACT else "Windows built-in OCR"
        self.ocr_result_text.insert(
            "1.0",
            "Quick start\n\n"
            "1. Capture the table.\n"
            "2. Paste or browse the image.\n"
            "3. Analyze the hand.\n"
            "4. Copy the result or save it.\n\n"
            f"Engine: {ocr_method}\n"
            "Formats: PNG, JPG, BMP",
        )

        self._ocr_current_path = None
        self._ocr_current_elements = None
        self._ocr_current_raw_text = ""

        convert_frame = self._panel(tab, pady=(2, 2))
        ctk.CTkLabel(convert_frame, text="Save Hand", text_color=self.theme["gold"], font=("Consolas", 12, "bold")).grid(row=0, column=0, columnspan=6, sticky="w", padx=8, pady=4)

        ctk.CTkLabel(convert_frame, text="Hero", text_color=self.theme["text"], font=("Consolas", 11)).grid(row=1, column=0, padx=4, pady=2, sticky="w")
        self.ocr_hero_cards_var = ctk.StringVar()
        ctk.CTkEntry(convert_frame, textvariable=self.ocr_hero_cards_var, fg_color=self.theme["bg_input"], text_color=self.theme["text"], width=100).grid(row=1, column=1, padx=4, pady=2, sticky="w")

        ctk.CTkLabel(convert_frame, text="Board", text_color=self.theme["text"], font=("Consolas", 11)).grid(row=1, column=2, padx=4, pady=2, sticky="w")
        self.ocr_board_var = ctk.StringVar()
        ctk.CTkEntry(convert_frame, textvariable=self.ocr_board_var, fg_color=self.theme["bg_input"], text_color=self.theme["text"], width=140).grid(row=1, column=3, padx=4, pady=2, sticky="w")

        ctk.CTkLabel(convert_frame, text="Pot", text_color=self.theme["text"], font=("Consolas", 11)).grid(row=1, column=4, padx=4, pady=2, sticky="w")
        self.ocr_pot_var = ctk.StringVar(value="0")
        ctk.CTkEntry(convert_frame, textvariable=self.ocr_pot_var, fg_color=self.theme["bg_input"], text_color=self.theme["text"], width=80).grid(row=1, column=5, padx=4, pady=2, sticky="w")

        ctk.CTkLabel(convert_frame, text="Pos", text_color=self.theme["text"], font=("Consolas", 11)).grid(row=2, column=0, padx=4, pady=2, sticky="w")
        self.ocr_position_var = ctk.StringVar(value="BTN")
        ctk.CTkOptionMenu(
            convert_frame,
            variable=self.ocr_position_var,
            values=["BTN", "CO", "MP", "EP", "SB", "BB"],
            fg_color=self.theme["bg_accent"],
            button_color=self.theme["bg_hover"],
            text_color=self.theme["text"],
            width=80,
            dropdown_fg_color=self.theme["bg_card"],
            dropdown_hover_color=self.theme["bg_accent"],
        ).grid(row=2, column=1, padx=4, pady=2, sticky="w")

        ctk.CTkLabel(convert_frame, text="Net", text_color=self.theme["text"], font=("Consolas", 11)).grid(row=2, column=2, padx=4, pady=2, sticky="w")
        self.ocr_result_var = ctk.StringVar(value="0")
        ctk.CTkEntry(convert_frame, textvariable=self.ocr_result_var, fg_color=self.theme["bg_input"], text_color=self.theme["text"], width=80).grid(row=2, column=3, padx=4, pady=2, sticky="w")

        ctk.CTkLabel(convert_frame, text="Site", text_color=self.theme["text"], font=("Consolas", 11)).grid(row=2, column=4, padx=4, pady=2, sticky="w")
        self.ocr_site_var = ctk.StringVar(value="Manual")
        ctk.CTkOptionMenu(
            convert_frame,
            variable=self.ocr_site_var,
            values=["CoinPoker", "ACR", "Manual"],
            fg_color=self.theme["bg_accent"],
            button_color=self.theme["bg_hover"],
            text_color=self.theme["text"],
            width=100,
            dropdown_fg_color=self.theme["bg_card"],
            dropdown_hover_color=self.theme["bg_accent"],
        ).grid(row=2, column=5, padx=4, pady=2, sticky="w")

        ctk.CTkLabel(convert_frame, text="Notes", text_color=self.theme["text"], font=("Consolas", 11)).grid(row=3, column=0, padx=4, pady=2, sticky="w")
        self.ocr_notes_var = ctk.StringVar()
        ctk.CTkEntry(convert_frame, textvariable=self.ocr_notes_var, fg_color=self.theme["bg_input"], text_color=self.theme["text"], width=350).grid(row=3, column=1, columnspan=4, padx=4, pady=2, sticky="w")
        self._action_button(convert_frame, "Save Hand", self._ocr_save_as_hand, tone="success", width=98, bold=True).grid(row=3, column=5, padx=4, pady=2)

        history_frame = self._panel(tab, pady=(2, 4))
        ctk.CTkLabel(history_frame, text="Recent OCR", text_color=self.theme["gold"], font=("Consolas", 11, "bold")).pack(anchor="w", padx=8, pady=2)
        self.ocr_history_text = ctk.CTkTextbox(history_frame, height=70, fg_color=self.theme["bg_input"], text_color=self.theme["text"], font=("Consolas", 10))
        self.ocr_history_text.pack(fill="x", padx=8, pady=(0, 4))
        self.ocr_history_text.configure(state="disabled")
        self._refresh_ocr_history()

    def _ocr_browse(self):
        filetypes = [("Image files", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff"),
                     ("All files", "*.*")]
        path = filedialog.askopenfilename(title="Select poker table screenshot",
                                          filetypes=filetypes)
        if path:
            self._ocr_load_image(path)

    def _ocr_paste(self):
        """Grab image from clipboard and save to temp file."""
        try:
            from PIL import ImageGrab
            img = ImageGrab.grabclipboard()
            if img is None:
                self._set_status("No image found on clipboard")
                return
            tmp = os.path.join(tempfile.gettempdir(), "poker_ocr_clipboard.png")
            img.save(tmp, "PNG")
            self._ocr_load_image(tmp)
            self._set_status("Image pasted from clipboard")
        except Exception as e:
            self._set_status(f"Clipboard error: {e}")

    def _ocr_load_image(self, path):
        self._ocr_current_path = path
        self.ocr_file_var.set(os.path.basename(path))
        try:
            img = Image.open(path)
            if img.mode == "RGBA":
                bg = Image.new("RGB", img.size, (255, 255, 255))
                bg.paste(img, mask=img.split()[3])
                img = bg
            pw = self.ocr_preview_label.winfo_width() or 450
            ph = self.ocr_preview_label.winfo_height() or 350
            pw, ph = max(pw - 10, 200), max(ph - 10, 150)
            img.thumbnail((pw, ph), Image.LANCZOS)
            self._ocr_photo = ImageTk.PhotoImage(img)
            self.ocr_preview_label.configure(image=self._ocr_photo, text="")
            self._set_status(f"Image loaded: {os.path.basename(path)}")
        except Exception as e:
            self.ocr_preview_label.configure(image=None, text=f"Error loading image:\n{e}")
            self._set_status(f"Image load error: {e}")

    def _ocr_analyze(self):
        if not self._ocr_current_path:
            self._set_status("No image loaded — browse or paste first")
            return
        self._set_status("Running OCR analysis...")
        self.ocr_result_text.delete("1.0", "end")
        self.ocr_result_text.insert("1.0", "  Analyzing image...\n  Please wait...")
        threading.Thread(target=self._ocr_do_analyze, daemon=True).start()

    def _ocr_do_analyze(self):
        raw_text = self.ocr_engine.ocr_image(self._ocr_current_path)
        elements = self.ocr_engine.parse_poker_elements(raw_text)
        analysis = self.ocr_engine.format_analysis(elements)
        self.after(0, lambda: self._ocr_show_result(analysis, elements, raw_text))

    def _ocr_show_result(self, analysis, elements=None, raw_text=""):
        self.ocr_result_text.delete("1.0", "end")
        self.ocr_result_text.insert("1.0", analysis)
        self._set_status("OCR analysis complete!")
        if elements:
            self._ocr_current_elements = elements
            self._ocr_current_raw_text = raw_text
            # Pre-fill convert fields
            cards = elements.get("cards", [])
            if len(cards) >= 2:
                self.ocr_hero_cards_var.set(f"{cards[0]} {cards[1]}")
            if len(cards) >= 5:
                self.ocr_board_var.set(" ".join(cards[2:7]))
            elif elements.get("board"):
                self.ocr_board_var.set(" ".join(elements["board"]))
            if elements.get("pot"):
                self.ocr_pot_var.set(str(elements["pot"]))

    def _ocr_copy_analysis(self):
        text = self.ocr_result_text.get("1.0", "end").strip()
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            self._set_status("Analysis copied to clipboard!")

    def _ocr_save_to_db(self):
        if not self._ocr_current_elements:
            self._set_status("Run OCR analysis first")
            return
        notes = self.ocr_notes_var.get().strip()
        self.db.save_ocr_import(
            self._ocr_current_path or "",
            self._ocr_current_raw_text,
            self._ocr_current_elements,
            notes=notes,
        )
        self._set_status("OCR import saved to database!")
        self._refresh_ocr_history()
        # Also show action count in status if we have parsed actions
        if self._ocr_current_elements and self._ocr_current_elements.get("actions"):
            actions = self._ocr_current_elements["actions"]
            self._set_status(f"OCR import saved! ({len(actions)} actions detected)")

    def _ocr_save_as_hand(self):
        hero_cards = self.ocr_hero_cards_var.get().strip()
        board_str = self.ocr_board_var.get().strip()
        try:
            pot = float(self.ocr_pot_var.get().strip())
        except (ValueError, TypeError):
            pot = 0.0
        position = self.ocr_position_var.get()
        try:
            result_val = float(self.ocr_result_var.get().strip())
        except (ValueError, TypeError):
            result_val = 0.0
        site = self.ocr_site_var.get()

        h = Hand()
        h.hand_id = f"OCR_{int(time.time() * 1000)}"
        h.site = site if site != "Manual" else "OCR"
        h.date = datetime.now()
        h.game_type = "NLHE"
        h.hero_cards = hero_cards
        h.board_cards = board_str.split() if board_str else []
        h.pot = pot
        h.hero_won = result_val
        h.hero_position = position
        notes = self.ocr_notes_var.get().strip()
        h.raw_text = notes if notes else f"OCR import from {self._ocr_current_path or 'clipboard'}"

        # Build streets from OCR-parsed actions
        if self._ocr_current_elements and self._ocr_current_elements.get("actions"):
            streets_map = OrderedDict()
            for act in self._ocr_current_elements["actions"]:
                sname = act.get("street", "preflop")
                if sname not in streets_map:
                    streets_map[sname] = {"name": sname, "cards": [], "actions": []}
                streets_map[sname]["actions"].append({
                    "player": act["player"],
                    "action": act["action"],
                    "amount": act.get("amount", 0),
                })
            h.streets = list(streets_map.values())

        # Build players from OCR
        if self._ocr_current_elements and self._ocr_current_elements.get("players_detected"):
            for i, pname in enumerate(self._ocr_current_elements["players_detected"]):
                h.players[i + 1] = {"name": pname, "stack": 0, "is_hero": False}

        # Save via db
        self.db.save_hand(h, source_file="OCR Import")

        # If there's a pending OCR import, link it
        ocr_imports = self.db.get_ocr_imports()
        if ocr_imports:
            latest = ocr_imports[0]
            if not latest.get("hand_id"):
                self.db.save_ocr_as_hand(latest["id"], h)

        self._set_status(f"Hand {h.hand_id} saved to database!")
        self._refresh_ocr_history()
        self._post_scan()

    def _refresh_ocr_history(self):
        try:
            imports = self.db.get_ocr_imports()[:10]
            self.ocr_history_text.configure(state="normal")
            self.ocr_history_text.delete("1.0", "end")
            if not imports:
                self.ocr_history_text.insert("1.0", "  No OCR imports yet")
            else:
                for imp in imports:
                    dt = imp.get("created_at", "?")
                    if len(dt) > 16:
                        dt = dt[:16]
                    cards = imp.get("parsed_cards", "")
                    pot = imp.get("parsed_pot", 0)
                    linked = " -> " + imp["hand_id"] if imp.get("hand_id") else ""
                    fname = os.path.basename(imp.get("image_path", "") or "clipboard")
                    self.ocr_history_text.insert("end",
                        f"  {dt}  {fname:20s}  cards: {cards:16s}  pot: {pot:>8.0f}{linked}\n")
            self.ocr_history_text.configure(state="disabled")
        except Exception:
            pass

    def _build_ai_tab(self):
        tab = self.tab_ai

        # ── Source selector ──
        src_frame = ctk.CTkFrame(tab, fg_color=self.theme["bg_panel"],
                                  border_width=1, border_color=self.theme["border"])
        src_frame.pack(fill="x", padx=6, pady=(6, 2))

        ctk.CTkLabel(src_frame, text="Analyze:", text_color=self.theme["text"],
                     font=("Consolas", 12)).pack(side="left", padx=(8, 4), pady=6)
        self.ai_source_var = ctk.StringVar(value="Filtered Hands")
        ctk.CTkOptionMenu(src_frame, variable=self.ai_source_var,
                          values=["All Hands", "Filtered Hands", "Selected Hands"],
                          fg_color=self.theme["bg_accent"], button_color=self.theme["bg_hover"],
                          text_color=self.theme["text"], width=160,
                          dropdown_fg_color=self.theme["bg_card"],
                          dropdown_hover_color=self.theme["bg_accent"],
                          font=("Consolas", 11)).pack(side="left", padx=4, pady=6)

        self.ai_filter_label = ctk.CTkLabel(src_frame, text="Filters: All Hands (no filters)",
                                             text_color=self.theme["text_dim"],
                                             font=("Consolas", 10))
        self.ai_filter_label.pack(side="left", padx=12, pady=6)

        # ── Action buttons ──
        btn_frame = ctk.CTkFrame(tab, fg_color=self.theme["bg_panel"],
                                  border_width=1, border_color=self.theme["border"])
        btn_frame.pack(fill="x", padx=6, pady=2)

        ctk.CTkButton(btn_frame, text="📊 Generate Analysis", fg_color=self.theme["green"],
                      hover_color=self.theme["bg_accent"],
                      text_color=self.theme["bg_base"], font=("Consolas", 13, "bold"),
                      command=self._generate_summary).pack(side="left", padx=8, pady=6)
        ctk.CTkButton(btn_frame, text="Copy to Clipboard", fg_color=self.theme["bg_accent"],
                      hover_color=self.theme["green"],
                      text_color=self.theme["text"], command=self._copy_summary).pack(side="left", padx=4, pady=6)
        ctk.CTkButton(btn_frame, text="💾 Save As...", fg_color=self.theme["bg_accent"],
                      hover_color=self.theme["green"],
                      text_color=self.theme["text"],
                      command=self._save_summary_as).pack(side="left", padx=4, pady=6)
        ctk.CTkButton(btn_frame, text="Export to GTO Wizard", fg_color=self.theme["gold"],
                      hover_color=self.theme["bg_accent"], text_color=self.theme["bg_base"],
                      font=("Consolas", 12, "bold"),
                      command=self._export_gto_wizard).pack(side="left", padx=4, pady=6)

        self.ai_text = ctk.CTkTextbox(tab, fg_color=self.theme["bg_input"],
                                       text_color=self.theme["text"], font=("Consolas", 11))
        self.ai_text.pack(fill="both", expand=True, padx=6, pady=(4, 6))

    def _build_settings_tab(self):
        tab = self.tab_settings
        hero_frame = ctk.CTkFrame(tab, fg_color=self.theme["bg_panel"],
                                   border_width=1, border_color=self.theme["border"])
        hero_frame.pack(fill="x", padx=6, pady=6)
        ctk.CTkLabel(hero_frame, text="Hero Names", text_color=self.theme["gold"],
                     font=("Consolas", 14, "bold")).pack(anchor="w", padx=8, pady=4)

        row1 = ctk.CTkFrame(hero_frame, fg_color=self.theme["bg_panel"])
        row1.pack(fill="x", padx=8, pady=2)
        ctk.CTkLabel(row1, text="CoinPoker:", text_color=self.theme["text"], width=100).pack(side="left")
        self.hero_cp_var = ctk.StringVar(value=self.settings["hero_names"].get("CoinPoker", ""))
        ctk.CTkEntry(row1, textvariable=self.hero_cp_var, fg_color=self.theme["bg_input"],
                     text_color=self.theme["text"], width=200).pack(side="left", padx=4)

        row2 = ctk.CTkFrame(hero_frame, fg_color=self.theme["bg_panel"])
        row2.pack(fill="x", padx=8, pady=2)
        ctk.CTkLabel(row2, text="ACR:", text_color=self.theme["text"], width=100).pack(side="left")
        self.hero_acr_var = ctk.StringVar(value=self.settings["hero_names"].get("ACR", ""))
        ctk.CTkEntry(row2, textvariable=self.hero_acr_var, fg_color=self.theme["bg_input"],
                     text_color=self.theme["text"], width=200).pack(side="left", padx=4)

        dir_frame = ctk.CTkFrame(tab, fg_color=self.theme["bg_panel"],
                                  border_width=1, border_color=self.theme["border"])
        dir_frame.pack(fill="both", expand=True, padx=6, pady=4)
        ctk.CTkLabel(dir_frame, text="Scan Directories", text_color=self.theme["gold"],
                     font=("Consolas", 14, "bold")).pack(anchor="w", padx=8, pady=4)

        self.dir_listbox = ctk.CTkTextbox(dir_frame, height=120, fg_color=self.theme["bg_input"],
                                           text_color=self.theme["text"], font=("Consolas", 11))
        self.dir_listbox.pack(fill="both", expand=True, padx=8, pady=4)
        self._refresh_dir_list()

        dir_btn_row = ctk.CTkFrame(dir_frame, fg_color=self.theme["bg_panel"])
        dir_btn_row.pack(fill="x", padx=8, pady=4)
        ctk.CTkLabel(dir_btn_row, text="Path:", text_color=self.theme["text"]).pack(side="left")
        self.new_dir_var = ctk.StringVar()
        ctk.CTkEntry(dir_btn_row, textvariable=self.new_dir_var, fg_color=self.theme["bg_input"],
                     text_color=self.theme["text"], width=300).pack(side="left", padx=4)
        ctk.CTkLabel(dir_btn_row, text="Site:", text_color=self.theme["text"]).pack(side="left")
        self.new_dir_site_var = ctk.StringVar(value="CoinPoker")
        ctk.CTkOptionMenu(dir_btn_row, variable=self.new_dir_site_var,
                          values=["CoinPoker", "ACR"], fg_color=self.theme["bg_accent"],
                          button_color=self.theme["bg_hover"], text_color=self.theme["text"],
                          dropdown_fg_color=self.theme["bg_card"],
                          dropdown_hover_color=self.theme["bg_accent"]).pack(side="left", padx=4)
        ctk.CTkButton(dir_btn_row, text="Add", fg_color=self.theme["green"],
                      hover_color=self.theme["bg_accent"],
                      text_color=self.theme["bg_base"], width=60, command=self._add_dir).pack(side="left", padx=4)
        ctk.CTkButton(dir_btn_row, text="Remove Last", fg_color=self.theme["red"],
                      hover_color=self.theme["bg_accent"],
                      text_color=self.theme["text"], width=100, command=self._remove_dir).pack(side="left", padx=4)

        opts_frame = ctk.CTkFrame(tab, fg_color=self.theme["bg_panel"],
                                   border_width=1, border_color=self.theme["border"])
        opts_frame.pack(fill="x", padx=6, pady=4)
        self.auto_refresh_var = ctk.BooleanVar(value=self.settings.get("auto_refresh", True))
        ctk.CTkCheckBox(opts_frame, text="Auto-refresh", variable=self.auto_refresh_var,
                        text_color=self.theme["text"], fg_color=self.theme["bg_accent"],
                        hover_color=self.theme["green"]).pack(side="left", padx=8, pady=6)

        ctk.CTkLabel(opts_frame, text="Interval (s):", text_color=self.theme["text"]).pack(side="left", padx=4)
        self.interval_var = ctk.StringVar(value=str(self.settings.get("refresh_interval", 5)))
        ctk.CTkEntry(opts_frame, textvariable=self.interval_var, fg_color=self.theme["bg_input"],
                     text_color=self.theme["text"], width=60).pack(side="left", padx=4)

        ctk.CTkButton(opts_frame, text="Save Settings", fg_color=self.theme["green"],
                      hover_color=self.theme["bg_accent"],
                      text_color=self.theme["bg_base"], font=("Consolas", 13, "bold"),
                      command=self._save_settings).pack(side="right", padx=8, pady=6)

        # ── Appearance / Theme Section ────────────────────────────────────
        theme_frame = ctk.CTkFrame(tab, fg_color=self.theme["bg_panel"],
                                    border_width=1, border_color=self.theme["border"])
        theme_frame.pack(fill="x", padx=6, pady=4)

        ctk.CTkLabel(theme_frame, text="Appearance", text_color=self.theme["gold"],
                     font=("Consolas", 14, "bold")).pack(anchor="w", padx=8, pady=4)

        theme_row = ctk.CTkFrame(theme_frame, fg_color=self.theme["bg_panel"])
        theme_row.pack(fill="x", padx=8, pady=4)

        ctk.CTkLabel(theme_row, text="Theme:", text_color=self.theme["text"],
                     width=100).pack(side="left")
        self.settings_theme_var = ctk.StringVar(value=self.theme_name)
        ctk.CTkOptionMenu(theme_row, variable=self.settings_theme_var,
                          values=list(THEMES.keys()),
                          fg_color=self.theme["bg_accent"], button_color=self.theme["bg_hover"],
                          text_color=self.theme["text"], width=160,
                          dropdown_fg_color=self.theme["bg_card"],
                          dropdown_hover_color=self.theme["bg_accent"],
                          command=self._change_theme).pack(side="left", padx=4)

        adv_row = ctk.CTkFrame(theme_frame, fg_color=self.theme["bg_panel"])
        adv_row.pack(fill="x", padx=8, pady=(0, 6))

        self.settings_adv_var = ctk.BooleanVar(value=self.advanced_mode)
        ctk.CTkCheckBox(adv_row, text="Advanced Mode (show extra stats & EV columns)",
                        variable=self.settings_adv_var,
                        text_color=self.theme["text"], fg_color=self.theme["bg_accent"],
                        hover_color=self.theme["green"],
                        command=lambda: self._toggle_advanced_from_settings()).pack(side="left", padx=4)

        # ── DriveHUD 2 Integration Section ───────────────────────────────
        dh2_frame = ctk.CTkFrame(tab, fg_color=self.theme["bg_panel"],
                                  border_width=1, border_color=self.theme["border"])
        dh2_frame.pack(fill="x", padx=6, pady=6)
        ctk.CTkLabel(dh2_frame, text="♦ DriveHUD 2 Integration", text_color=self.theme["gold"],
                     font=("Consolas", 14, "bold")).pack(anchor="w", padx=8, pady=4)

        dh2_path_row = ctk.CTkFrame(dh2_frame, fg_color=self.theme["bg_panel"])
        dh2_path_row.pack(fill="x", padx=8, pady=2)
        ctk.CTkLabel(dh2_path_row, text="DH2 DB Path:", text_color=self.theme["text"], width=100).pack(side="left")
        self.dh2_path_var = ctk.StringVar(value=self.settings.get("dh2_db_path", DH2_DB_DEFAULT))
        ctk.CTkEntry(dh2_path_row, textvariable=self.dh2_path_var, fg_color=self.theme["bg_input"],
                     text_color=self.theme["text"], width=400).pack(side="left", padx=4)
        ctk.CTkButton(dh2_path_row, text="Browse", fg_color=self.theme["bg_accent"],
                      hover_color=self.theme["green"],
                      text_color=self.theme["text"], width=70, command=self._browse_dh2_path).pack(side="left", padx=4)

        dh2_opts_row = ctk.CTkFrame(dh2_frame, fg_color=self.theme["bg_panel"])
        dh2_opts_row.pack(fill="x", padx=8, pady=2)
        self.dh2_auto_var = ctk.BooleanVar(value=self.settings.get("dh2_auto_sync", True))
        ctk.CTkCheckBox(dh2_opts_row, text="Auto-sync from DH2", variable=self.dh2_auto_var,
                        text_color=self.theme["text"], fg_color=self.theme["bg_accent"],
                        hover_color=self.theme["green"]).pack(side="left", padx=4)
        ctk.CTkLabel(dh2_opts_row, text="Interval (s):", text_color=self.theme["text"]).pack(side="left", padx=(12, 4))
        self.dh2_interval_var = ctk.StringVar(value=str(self.settings.get("dh2_sync_interval", 5)))
        ctk.CTkEntry(dh2_opts_row, textvariable=self.dh2_interval_var, fg_color=self.theme["bg_input"],
                     text_color=self.theme["text"], width=50).pack(side="left", padx=4)

        dh2_btn_row = ctk.CTkFrame(dh2_frame, fg_color=self.theme["bg_panel"])
        dh2_btn_row.pack(fill="x", padx=8, pady=4)
        ctk.CTkButton(dh2_btn_row, text="Sync Now", fg_color=self.theme["green"],
                      hover_color=self.theme["bg_accent"],
                      text_color=self.theme["bg_base"], width=100, command=self._dh2_sync_now).pack(side="left", padx=4)
        ctk.CTkButton(dh2_btn_row, text="Reset Sync", fg_color=self.theme["red"],
                      hover_color=self.theme["bg_accent"],
                      text_color=self.theme["text"], width=100, command=self._dh2_reset).pack(side="left", padx=4)

        self.dh2_status_label = ctk.CTkLabel(dh2_btn_row, text="", text_color=self.theme["text_dim"],
                                              font=("Consolas", 11))
        self.dh2_status_label.pack(side="left", padx=12)
        self._update_dh2_status()

    def _build_status_bar(self):
        self.taskbar = ctk.CTkFrame(self, fg_color=self.theme["bg_card"], height=38, corner_radius=0)
        self.taskbar.pack(fill="x", side="bottom", padx=0, pady=0)
        self.taskbar.pack_propagate(False)

        self._action_button(self.taskbar, "Import", self._manual_import, width=96, bold=True).pack(side="left", padx=(8, 4), pady=5)
        self._action_button(self.taskbar, "Reload", self._manual_refresh, width=88).pack(side="left", padx=4, pady=5)
        self._action_button(self.taskbar, "Sync DH2", self._dh2_sync_now, width=96).pack(side="left", padx=4, pady=5)

        self.adv_mode_var = ctk.BooleanVar(value=self.advanced_mode)
        ctk.CTkSwitch(
            self.taskbar,
            text="Advanced",
            variable=self.adv_mode_var,
            fg_color=self.theme["border"],
            progress_color=self.theme["gold"],
            text_color=self.theme["text_dim"],
            font=("Consolas", 11),
            command=self._toggle_advanced_mode,
        ).pack(side="left", padx=8, pady=5)

        self.status_bar = ctk.CTkLabel(self.taskbar, text="Starting...", text_color=self.theme["text_dim"], font=("Consolas", 11), anchor="e")
        self.status_bar.pack(side="right", fill="x", expand=True, padx=10)

        self.theme_var = ctk.StringVar(value=self.theme_name)
        ctk.CTkOptionMenu(
            self.taskbar,
            variable=self.theme_var,
            values=list(THEMES.keys()),
            fg_color=self.theme["bg_accent"],
            button_color=self.theme["bg_hover"],
            text_color=self.theme["text"],
            width=120,
            height=28,
            font=("Consolas", 11),
            dropdown_fg_color=self.theme["bg_card"],
            dropdown_hover_color=self.theme["bg_accent"],
            command=self._change_theme,
        ).pack(side="right", padx=(4, 8), pady=5)
        ctk.CTkLabel(self.taskbar, text="Theme:", text_color=self.theme["text_dim"], font=("Consolas", 11)).pack(side="right", padx=(8, 0), pady=5)

    def _toggle_advanced_mode(self):
        self.advanced_mode = self.adv_mode_var.get()
        self.settings["advanced_mode"] = self.advanced_mode
        self._save_settings_quiet()
        self._refresh_hands_list()
        self._update_leak_tab()

    def _toggle_advanced_from_settings(self):
        self.advanced_mode = self.settings_adv_var.get()
        self.adv_mode_var.set(self.advanced_mode)
        self.settings["advanced_mode"] = self.advanced_mode
        self._save_settings_quiet()
        self._refresh_hands_list()
        self._update_leak_tab()

    def _change_theme(self, new_theme):
        self.theme_name = new_theme
        self.theme = THEMES.get(new_theme, THEMES["Midnight Purple"])
        self.settings["theme"] = new_theme
        self._save_settings_quiet()
        self._set_status(f"Theme changed to {new_theme} — restart app to fully apply")

    def _save_settings_quiet(self):
        """Save settings without UI feedback."""
        try:
            with open(SETTINGS_PATH, "w") as f:
                json.dump(self.settings, f, indent=2)
        except Exception:
            pass

    # ── Actions / Callbacks ───────────────────────────────────────────────
    def _initial_scan(self):
        self._set_status("Scanning hand history directories...")
        threading.Thread(target=self._do_initial_scan, daemon=True).start()

    def _do_initial_scan(self):
        new_count, file_count = self.importer.full_scan()
        total_hands = len(self.importer.get_hands())
        self.after(0, lambda: self._set_status(
            f"Scan: {new_count} new from {file_count} files | {total_hands} total hands"))
        # Also sync from DriveHUD 2
        try:
            dh2_count = self.dh2_sync.sync()
            if dh2_count > 0:
                self.after(0, lambda: self._set_status(
                    f"DH2: +{dh2_count} hands | {total_hands + dh2_count} total"))
        except Exception as e:
            self.after(0, lambda: self._set_status(f"DH2 sync issue: {e}"))
        self.after(0, self._post_scan)
        if self.settings.get("auto_refresh", True):
            self.importer.start_watcher(callback=self._watcher_callback)
        if self.settings.get("dh2_auto_sync", True):
            self.dh2_sync.start_polling(
                callback=self._dh2_callback,
                interval=self.settings.get("dh2_sync_interval", 5),
            )

    def _watcher_callback(self, new_count, file_count):
        self.after(0, self._post_scan)

    def _dh2_callback(self, new_count):
        self.after(0, self._post_scan)
        self.after(0, lambda: self._update_dh2_status())

    def _post_scan(self):
        self._set_status(self.importer.get_stats_text())
        hands = self.importer.get_hands()
        if hands:
            self.current_stats = self.leak_engine.analyze(hands)
        else:
            self.current_stats = {}
        self._update_dashboard()
        self._refresh_hands_list()
        self._update_leak_tab()
        # Defer heavy HUD computation to background thread
        threading.Thread(target=self._compute_players_bg, daemon=True).start()

    def _manual_refresh(self):
        self._set_status("Refreshing...")
        threading.Thread(target=self._do_manual_refresh, daemon=True).start()

    def _do_manual_refresh(self):
        self.importer.full_scan()
        try:
            self.dh2_sync.sync()
        except Exception:
            pass
        self.after(0, self._post_scan)

    def _manual_import(self):
        """Open file dialog to manually import hand history files."""
        file_paths = filedialog.askopenfilenames(
            title="Select Hand History Files",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not file_paths:
            return
        self._set_status(f"Importing {len(file_paths)} file(s)...")

        def _do_import():
            saved, files = self.importer.import_files(file_paths)
            self.after(0, lambda: self._set_status(
                f"Manual import: {saved} new hand(s) from {files} file(s)"))
            self.after(0, self._post_scan)

        threading.Thread(target=_do_import, daemon=True).start()

    def _set_status(self, text):
        self.status_bar.configure(text=text)

    def _update_dashboard(self):
        s = self.current_stats
        if not s:
            return
        self.dash_cards["Hands"].configure(text=str(s.get("total_hands", 0)))
        self.dash_cards["VPIP"].configure(text=f"{s.get('vpip', 0)}%")
        self.dash_cards["PFR"].configure(text=f"{s.get('pfr', 0)}%")
        self.dash_cards["AF"].configure(text=str(s.get("af", 0)))

        total_won = sum(d["won"] for d in s.get("by_site", {}).values())
        total_lost = sum(d["lost"] for d in s.get("by_site", {}).values())
        self.dash_cards["Won"].configure(text=f"+{total_won:.0f}")
        self.dash_cards["Lost"].configure(text=f"-{total_lost:.0f}")

        self.dash_site_text.configure(state="normal")
        self.dash_site_text.delete("1.0", "end")
        for site, sd in s.get("by_site", {}).items():
            self.dash_site_text.insert(
                "end",
                f"  {site:10s} {sd['total']:4d}h  VPIP {sd['vpip']:>2}%  PFR {sd['pfr']:>2}%  Net {sd['net']:+.2f}\n",
            )
        self.dash_site_text.configure(state="disabled")

        self.dash_recent.configure(state="normal")
        self.dash_recent.delete("1.0", "end")
        hands = self.importer.get_hands()
        recent = sorted(hands, key=lambda h: h.date or datetime.min, reverse=True)[:10]
        for h in recent:
            dt = h.date.strftime("%m/%d %H:%M") if h.date else "?"
            result_str = f"+{h.hero_won:.0f}" if h.hero_won >= 0 else f"{h.hero_won:.0f}"
            self.dash_recent.insert(
                "end",
                f"  {dt}  {h.site:10s}  {h.hero_cards:8s}  {h.hero_position:3s}  {result_str}\n",
            )
        if not recent:
            self.dash_recent.insert("end", "  No hands yet")
        self.dash_recent.configure(state="disabled")

        td = self.tilt_meter.analyze(hands)
        self.tilt_data = td
        tilt_text = f"{td['label']} {td['score']}/100"
        self.tilt_score_label.configure(text=tilt_text, text_color=td["color"])
        self.tilt_bar.set(td["score"] / 100)
        self.tilt_bar.configure(progress_color=td["color"])
        self.tilt_advice_label.configure(text=td["advice"], text_color=td["color"])
        self.tilt_indicators_text.configure(state="normal")
        self.tilt_indicators_text.delete("1.0", "end")
        for ind in td.get("indicators", []):
            self.tilt_indicators_text.insert("end", f"  - {ind}\n")
        if not td.get("indicators"):
            self.tilt_indicators_text.insert("end", "  No tilt flags")
        self.tilt_indicators_text.configure(state="disabled")

        total_ev_diff = sum(self.ev_calculator.calc_ev_diff(h, self.settings) for h in hands)
        ev_str = f"+{total_ev_diff:.0f}" if total_ev_diff >= 0 else f"{total_ev_diff:.0f}"
        ev_color = self.theme["green"] if total_ev_diff >= 0 else self.theme["red"]
        self.dash_cards["EV Diff"].configure(text=ev_str, text_color=ev_color)

        self._update_dashboard_graphs()

    def _update_dashboard_graphs(self):
        """Render profit line graph and game-type pie chart on dashboard."""
        if not hasattr(self, 'dash_fig'):
            return
        t = self.theme
        hands = self.importer.get_hands()
        self.dash_fig.clear()
        self.dash_fig.patch.set_facecolor(t["graph_bg"])

        # Left: Profit/Loss over time
        ax1 = self.dash_fig.add_subplot(121)
        ax1.set_facecolor(t["graph_face"])
        ax1.tick_params(colors=t["text_dim"], labelsize=8)
        ax1.set_title("Session Profit / Loss", color=t["gold"], fontsize=10, fontweight="bold")
        for spine in ax1.spines.values():
            spine.set_color(t["graph_grid"])

        if hands:
            sorted_hands = sorted([h for h in hands if h.date], key=lambda h: h.date)
            cumulative = []
            running = 0.0
            dates = []
            for h in sorted_hands:
                running += h.hero_won
                cumulative.append(running)
                dates.append(h.date)
            ax1.plot(range(len(cumulative)), cumulative, color=t["graph_line"], linewidth=1.5)
            ax1.axhline(y=0, color=t["red"], linewidth=0.5, linestyle="--", alpha=0.5)
            ax1.fill_between(range(len(cumulative)), cumulative, 0,
                             where=[c >= 0 for c in cumulative], alpha=0.15, color=t["green"])
            ax1.fill_between(range(len(cumulative)), cumulative, 0,
                             where=[c < 0 for c in cumulative], alpha=0.15, color=t["red"])
            ax1.set_xlabel("Hands", color=t["text_dim"], fontsize=8)
            ax1.set_ylabel("Profit", color=t["text_dim"], fontsize=8)
        else:
            ax1.text(0.5, 0.5, "No data", ha="center", va="center", color=t["text_dim"], fontsize=12)
        ax1.grid(True, color=t["graph_grid"], alpha=0.3, linewidth=0.5)

        # Right: Game type pie chart
        ax2 = self.dash_fig.add_subplot(122)
        ax2.set_facecolor(t["graph_face"])
        ax2.set_title("Game Types", color=t["gold"], fontsize=10, fontweight="bold")
        if hands:
            from collections import Counter
            game_counts = Counter(h.game_type or "Unknown" for h in hands)
            if game_counts:
                labels = list(game_counts.keys())
                sizes = list(game_counts.values())
                colors = t["pie_colors"][:len(labels)]
                ax2.pie(sizes, labels=labels, colors=colors, autopct="%1.0f%%",
                        textprops={"color": t["text"], "fontsize": 8}, startangle=90)
            else:
                ax2.text(0.5, 0.5, "No data", ha="center", va="center", color=t["text_dim"])
        else:
            ax2.text(0.5, 0.5, "No data", ha="center", va="center", color=t["text_dim"], fontsize=12)

        self.dash_fig.tight_layout(pad=1.5)
        self.dash_canvas.draw()

    # ── Hands tab ─────────────────────────────────────────────────────────
    def _refresh_hands_list(self):
        self.hands_text.configure(state="normal")
        self.hands_text.delete("1.0", "end")
        self._hand_objects.clear()
        self._selected_hand_ids = set()

        hands = self.importer.get_hands()
        filtered = self._apply_filters(hands)

        sort_choice = self.hand_sort_var.get()
        if "Date \u2193" in sort_choice:
            filtered.sort(key=lambda h: h.date or datetime.min, reverse=True)
        elif "Date \u2191" in sort_choice:
            filtered.sort(key=lambda h: h.date or datetime.min)
        elif "Big wins" in sort_choice:
            filtered.sort(key=lambda h: h.hero_won, reverse=True)
        elif "Big losses" in sort_choice:
            filtered.sort(key=lambda h: h.hero_won)
        elif "Pot \u2193" in sort_choice:
            filtered.sort(key=lambda h: h.pot, reverse=True)
        elif "Pot \u2191" in sort_choice:
            filtered.sort(key=lambda h: h.pot)

        for i, h in enumerate(filtered[:500]):
            self._hand_objects[h.hand_id] = h
            dt = h.date.strftime("%m/%d %H:%M") if h.date else "?"
            game = "Trn" if h.is_tournament else "Cash"
            result = f"+{h.hero_won:.0f}" if h.hero_won >= 0 else f"{h.hero_won:.0f}"
            pot_str = f"{h.pot:.0f}" if h.pot else ""
            ev_diff = self.ev_calculator.calc_ev_diff(h, self.settings)
            ev_str = f"+{ev_diff:.0f}" if ev_diff >= 0 else f"{ev_diff:.0f}"

            tags = self.db.get_tags(h.hand_id)
            tag_str = f" [{','.join(tags)}]" if tags else ""
            line = f"  {dt:14s} {h.site:10s} {game:5s} {h.hero_cards:8s} {h.hero_position:4s} {result:>8s} {pot_str:>7s} {ev_str:>7s}{tag_str}\n"
            tag_name = f"hand_{i}"
            self.hands_text.insert("end", line, (tag_name,))

            self.hands_text.tag_bind(tag_name, "<Button-1>", lambda e, hand=h: self._show_hand_detail(hand))
            if h.hero_won > 0:
                self.hands_text.tag_configure(tag_name, foreground=self.theme["row_win"])
            elif h.hero_won < 0:
                self.hands_text.tag_configure(tag_name, foreground=self.theme["row_loss"])
            else:
                self.hands_text.tag_configure(tag_name, foreground=self.theme["row_even"])

        if not filtered:
            self.hands_text.insert("end", "  No hands match filters")

        self.hands_text.configure(state="disabled")
        self.hand_count_label.configure(text=f"{len(filtered)} hands ({min(len(filtered), 500)} shown)")
        self._update_selection_count()

    def _apply_filters(self, hands):
        """Apply all active filters to hands list."""
        site_filter = self.hand_site_var.get()
        result_filter = self.hand_result_var.get()

        # Advanced filters
        date_from_str = self.filter_date_from_var.get().strip() if hasattr(self, 'filter_date_from_var') else ""
        date_to_str = self.filter_date_to_var.get().strip() if hasattr(self, 'filter_date_to_var') else ""
        pot_min_str = self.filter_pot_min_var.get().strip() if hasattr(self, 'filter_pot_min_var') else ""
        pot_max_str = self.filter_pot_max_var.get().strip() if hasattr(self, 'filter_pot_max_var') else ""
        type_filter = self.filter_type_var.get() if hasattr(self, 'filter_type_var') else "All"
        tag_filter = self.filter_tag_var.get() if hasattr(self, 'filter_tag_var') else "All"
        opp_type_filter = self.filter_opp_type_var.get() if hasattr(self, 'filter_opp_type_var') else "All"

        # Parse dates
        date_from = None
        date_to = None
        for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y"):
            if date_from_str and not date_from:
                try:
                    date_from = datetime.strptime(date_from_str, fmt)
                except ValueError:
                    pass
            if date_to_str and not date_to:
                try:
                    date_to = datetime.strptime(date_to_str, fmt)
                    date_to = date_to.replace(hour=23, minute=59, second=59)
                except ValueError:
                    pass

        # Parse pot range
        pot_min = None
        pot_max = None
        try:
            if pot_min_str:
                pot_min = float(pot_min_str)
        except ValueError:
            pass
        try:
            if pot_max_str:
                pot_max = float(pot_max_str)
        except ValueError:
            pass

        # Get tagged hand IDs if filtering by tag
        tag_hand_ids = None
        if tag_filter and tag_filter != "All":
            tag_hand_ids = self.db.get_hand_ids_by_tag(tag_filter)

        # Get player names matching opponent type filter
        opp_type_names = None
        if opp_type_filter and opp_type_filter != "All":
            opp_type_names = self.db.get_players_by_type(opp_type_filter)

        filtered = []
        for h in hands:
            if site_filter != "All" and h.site != site_filter:
                continue
            if result_filter == "Won" and h.hero_won <= 0:
                continue
            if result_filter == "Lost" and h.hero_won >= 0:
                continue
            if date_from and h.date and h.date < date_from:
                continue
            if date_to and h.date and h.date > date_to:
                continue
            if pot_min is not None and h.pot < pot_min:
                continue
            if pot_max is not None and h.pot > pot_max:
                continue
            if type_filter == "Cash" and h.is_tournament:
                continue
            if type_filter == "Tournament" and not h.is_tournament:
                continue
            if tag_hand_ids is not None and h.hand_id not in tag_hand_ids:
                continue
            if opp_type_names is not None:
                hand_players = {info["name"] for info in (h.players or {}).values()}
                if not hand_players or not hand_players.intersection(opp_type_names):
                    continue
            filtered.append(h)
        return filtered

    def _get_filtered_hands(self):
        """Return currently filtered hands list (for AI analysis and export)."""
        hands = self.importer.get_hands()
        return self._apply_filters(hands)

    def _get_filter_description(self):
        """Return a human-readable description of active filters."""
        parts = []
        site = self.hand_site_var.get()
        if site != "All":
            parts.append(f"Site: {site}")
        result = self.hand_result_var.get()
        if result != "All":
            parts.append(f"Result: {result}")
        if hasattr(self, 'filter_date_from_var'):
            df = self.filter_date_from_var.get().strip()
            dt = self.filter_date_to_var.get().strip()
            if df:
                parts.append(f"From: {df}")
            if dt:
                parts.append(f"To: {dt}")
        if hasattr(self, 'filter_pot_min_var'):
            pm = self.filter_pot_min_var.get().strip()
            px = self.filter_pot_max_var.get().strip()
            if pm:
                parts.append(f"Pot ≥ {pm}")
            if px:
                parts.append(f"Pot ≤ {px}")
        if hasattr(self, 'filter_type_var'):
            t = self.filter_type_var.get()
            if t != "All":
                parts.append(f"Type: {t}")
        if hasattr(self, 'filter_tag_var'):
            tag = self.filter_tag_var.get()
            if tag != "All":
                parts.append(f"Tag: {tag}")
        if hasattr(self, 'filter_opp_type_var'):
            opp = self.filter_opp_type_var.get()
            if opp != "All":
                parts.append(f"Vs: {opp}")
        return " | ".join(parts) if parts else "All Hands (no filters)"

    def _clear_filters(self):
        """Reset all filters to defaults."""
        self.hand_site_var.set("All")
        self.hand_result_var.set("All")
        if hasattr(self, 'filter_date_from_var'):
            self.filter_date_from_var.set("")
            self.filter_date_to_var.set("")
        if hasattr(self, 'filter_pot_min_var'):
            self.filter_pot_min_var.set("")
            self.filter_pot_max_var.set("")
        if hasattr(self, 'filter_type_var'):
            self.filter_type_var.set("All")
        if hasattr(self, 'filter_tag_var'):
            self.filter_tag_var.set("All")
        if hasattr(self, 'filter_opp_type_var'):
            self.filter_opp_type_var.set("All")
        self._refresh_hands_list()

    def _refresh_tag_filter(self):
        """Refresh the tag filter dropdown with current tags from DB."""
        if hasattr(self, 'filter_tag_menu'):
            tags = self.db.get_all_tags()
            values = ["All"] + tags
            self.filter_tag_menu.configure(values=values)

    def _tag_selected_hands(self):
        """Open dialog to tag selected hands."""
        selected = self._get_selected_hands()
        if not selected:
            self._set_status("Select hands first, then tag them")
            return
        self._open_tag_dialog(selected)

    def _open_tag_dialog(self, hands):
        """Popup to add/remove tags on given hands."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Tag Hands")
        dialog.geometry("380x320")
        dialog.configure(fg_color=self.theme["bg_base"])
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text=f"Tag {len(hands)} hand(s)",
                     text_color=self.theme["gold"], font=("Consolas", 14, "bold")
                     ).pack(pady=(12, 4))

        # Existing tags on these hands
        all_tags_on = set()
        for h in hands:
            for t in self.db.get_tags(h.hand_id):
                all_tags_on.add(t)

        if all_tags_on:
            ctk.CTkLabel(dialog, text="Current tags: " + ", ".join(sorted(all_tags_on)),
                         text_color=self.theme["text_dim"], font=("Consolas", 10)
                         ).pack(padx=12, pady=2)

        # Preset tag buttons
        preset_frame = ctk.CTkFrame(dialog, fg_color=self.theme["bg_panel"])
        preset_frame.pack(fill="x", padx=12, pady=6)
        ctk.CTkLabel(preset_frame, text="Quick Tags:", text_color=self.theme["text_dim"],
                     font=("Consolas", 10)).pack(anchor="w", padx=4, pady=2)

        presets_row = ctk.CTkFrame(preset_frame, fg_color=self.theme["bg_panel"])
        presets_row.pack(fill="x", padx=4, pady=2)
        preset_tags = ["Review", "Bluff", "Bad Beat", "Key Hand", "Cooler",
                       "Misplay", "Hero Call", "Big Pot", "Tournament"]
        for ptag in preset_tags:
            ctk.CTkButton(presets_row, text=ptag, width=80, height=24,
                          fg_color=self.theme["bg_card"], hover_color=self.theme["bg_accent"],
                          text_color=self.theme["text"], font=("Consolas", 9),
                          command=lambda t=ptag: _apply_tag(t)
                          ).pack(side="left", padx=2, pady=2)

        # Custom tag entry
        entry_frame = ctk.CTkFrame(dialog, fg_color=self.theme["bg_panel"])
        entry_frame.pack(fill="x", padx=12, pady=4)
        ctk.CTkLabel(entry_frame, text="Custom Tag:", text_color=self.theme["text"],
                     font=("Consolas", 11)).pack(side="left", padx=4)
        tag_entry_var = ctk.StringVar()
        tag_entry = ctk.CTkEntry(entry_frame, textvariable=tag_entry_var,
                                  fg_color=self.theme["bg_input"], text_color=self.theme["text"],
                                  width=160, font=("Consolas", 11))
        tag_entry.pack(side="left", padx=4)
        ctk.CTkButton(entry_frame, text="Add", fg_color=self.theme["green"],
                      hover_color=self.theme["bg_accent"], text_color=self.theme["bg_base"],
                      width=50, height=26, font=("Consolas", 11, "bold"),
                      command=lambda: _apply_tag(tag_entry_var.get())
                      ).pack(side="left", padx=4)

        # Remove tag
        remove_frame = ctk.CTkFrame(dialog, fg_color=self.theme["bg_panel"])
        remove_frame.pack(fill="x", padx=12, pady=4)
        ctk.CTkLabel(remove_frame, text="Remove Tag:", text_color=self.theme["text"],
                     font=("Consolas", 11)).pack(side="left", padx=4)
        existing_tags = sorted(all_tags_on) if all_tags_on else ["(none)"]
        remove_var = ctk.StringVar(value=existing_tags[0])
        ctk.CTkOptionMenu(remove_frame, variable=remove_var, values=existing_tags,
                          fg_color=self.theme["bg_accent"], button_color=self.theme["bg_hover"],
                          text_color=self.theme["text"], width=120,
                          dropdown_fg_color=self.theme["bg_card"],
                          dropdown_hover_color=self.theme["bg_accent"]
                          ).pack(side="left", padx=4)
        ctk.CTkButton(remove_frame, text="Remove", fg_color=self.theme["red"],
                      hover_color=self.theme["bg_accent"], text_color=self.theme["text"],
                      width=70, height=26, font=("Consolas", 11),
                      command=lambda: _remove_tag(remove_var.get())
                      ).pack(side="left", padx=4)

        # Status label
        status_lbl = ctk.CTkLabel(dialog, text="", text_color=self.theme["green"],
                                   font=("Consolas", 11))
        status_lbl.pack(pady=4)

        def _apply_tag(tag):
            tag = tag.strip()
            if not tag:
                return
            for h in hands:
                self.db.add_tag(h.hand_id, tag)
            status_lbl.configure(text=f"✓ Tagged {len(hands)} hands with '{tag}'")
            self._refresh_tag_filter()

        def _remove_tag(tag):
            tag = tag.strip()
            if not tag or tag == "(none)":
                return
            for h in hands:
                self.db.remove_tag(h.hand_id, tag)
            status_lbl.configure(text=f"✗ Removed '{tag}' from {len(hands)} hands")
            self._refresh_tag_filter()

        ctk.CTkButton(dialog, text="Done", fg_color=self.theme["bg_accent"],
                      hover_color=self.theme["green"], text_color=self.theme["text"],
                      width=100, command=lambda: [dialog.destroy(), self._refresh_hands_list()]
                      ).pack(pady=(8, 12))

    def _update_selection_count(self):
        count = len(self._selected_hand_ids)
        self.hand_sel_count_label.configure(text=f"{count} selected")

    def _toggle_select_all(self):
        val = self.select_all_var.get()
        if val:
            self._selected_hand_ids = set(self._hand_objects.keys())
        else:
            self._selected_hand_ids.clear()
        self._update_selection_count()

    def _get_selected_hands(self):
        selected = []
        for hid in self._selected_hand_ids:
            if hid in self._hand_objects:
                selected.append(self._hand_objects[hid])
        return selected

    def _compare_selected(self):
        selected = self._get_selected_hands()
        if len(selected) < 2:
            self._set_status("Select at least 2 hands to compare")
            return
        self.detail_title_label.configure(text=f"Compare {len(selected)} Hands")
        self.hand_detail_text.configure(state="normal")
        self.hand_detail_text.delete("1.0", "end")

        sep = "=" * 60
        self.hand_detail_text.insert("end", f"{sep}\n")
        self.hand_detail_text.insert("end", f"  HAND COMPARISON  ({len(selected)} hands)\n")
        self.hand_detail_text.insert("end", f"{sep}\n\n")

        # Summary table
        self.hand_detail_text.insert("end",
            f"  {'#':3s} {'Site':10s} {'Cards':10s} {'Pos':4s} {'Result':>9s} {'Pot':>8s} {'Date'}\n")
        self.hand_detail_text.insert("end", "  " + "-" * 70 + "\n")
        total_result = 0.0
        for i, h in enumerate(selected, 1):
            dt = h.date.strftime("%m/%d %H:%M") if h.date else "?"
            res = f"+{h.hero_won:.0f}" if h.hero_won >= 0 else f"{h.hero_won:.0f}"
            total_result += h.hero_won
            self.hand_detail_text.insert("end",
                f"  {i:<3d} {h.site:10s} {h.hero_cards:10s} {h.hero_position:4s} "
                f"{res:>9s} {h.pot:>8.0f} {dt}\n")
        self.hand_detail_text.insert("end", "  " + "-" * 70 + "\n")
        net_str = f"+{total_result:.0f}" if total_result >= 0 else f"{total_result:.0f}"
        self.hand_detail_text.insert("end", f"  NET RESULT: {net_str}\n\n")

        # Stats for selected hands only
        positions = defaultdict(int)
        vpip_count = 0
        for h in selected:
            positions[h.hero_position] += 1
            if h.streets:
                pf = h.streets[0]
                hero = h.hero_name(self.settings) if hasattr(h, 'hero_name') else ""
                for act in pf.get("actions", []):
                    if act["player"] == hero and act["action"] in ("call", "raise", "bet"):
                        vpip_count += 1
                        break

        self.hand_detail_text.insert("end", "  Positions: ")
        for pos in ["EP", "MP", "CO", "BTN", "SB", "BB"]:
            if positions.get(pos, 0) > 0:
                self.hand_detail_text.insert("end", f"{pos}={positions[pos]}  ")
        self.hand_detail_text.insert("end", "\n")
        if len(selected) > 0:
            self.hand_detail_text.insert("end",
                f"  VPIP in selection: {100*vpip_count/len(selected):.0f}%\n")
        self.hand_detail_text.insert("end", f"\n{sep}\n")
        self.hand_detail_text.insert("end", "  FULL HAND DETAILS:\n")
        self.hand_detail_text.insert("end", f"{sep}\n\n")

        for i, h in enumerate(selected, 1):
            self.hand_detail_text.insert("end", f"--- Hand {i}/{len(selected)} ---\n")
            self.hand_detail_text.insert("end", h.raw_text if h.raw_text else "(no raw text)")
            self.hand_detail_text.insert("end", "\n\n")

        self.hand_detail_text.configure(state="disabled")
        self._set_status(f"Comparing {len(selected)} hands — net result: {net_str}")

    def _copy_selected_hands(self):
        selected = self._get_selected_hands()
        if not selected:
            self._set_status("No hands selected")
            return
        text_parts = []
        for h in selected:
            if h.raw_text:
                text_parts.append(h.raw_text)
        full = "\n\n".join(text_parts)
        self.clipboard_clear()
        self.clipboard_append(full)
        self._set_status(f"Copied {len(selected)} hands to clipboard!")

    def _show_hand_detail(self, hand):
        """Open a lightweight native Toplevel window showing hand details."""
        # Also update the embedded detail panel
        self.detail_title_label.configure(text="Details")
        self.hand_detail_text.configure(state="normal")
        self.hand_detail_text.delete("1.0", "end")
        ev_diff = self.ev_calculator.calc_ev_diff(hand, self.settings)
        strength = self.ev_calculator.get_hand_strength(hand.hero_cards)
        ev_str = f"+{ev_diff:.1f}" if ev_diff >= 0 else f"{ev_diff:.1f}"
        self.hand_detail_text.insert("end", "\u2500\u2500 EV Analysis \u2500\u2500\n")
        self.hand_detail_text.insert("end",
            f"  Hand Strength: {strength}/100 | EV Diff: {ev_str}\n")
        self.hand_detail_text.insert("end",
            f"  Position: {hand.hero_position} | Pot: {hand.pot:.0f} | "
            f"Result: {hand.hero_won:+.0f}\n\n")
        self.hand_detail_text.insert("end", hand.raw_text if hand.raw_text else "(no raw text)")

        # Show opponent types
        hero = hand.hero_name(self.settings)
        opponents = [info["name"] for info in hand.players.values() if info["name"] != hero]
        if opponents:
            self.hand_detail_text.insert("end", "\n── Opponent Types ──\n")
            for opp in opponents:
                pinfo = self.db.get_player_type(opp)
                if pinfo:
                    etype = pinfo["effective_type"]
                    override_mark = " (manual)" if pinfo["manual_type"] else ""
                    self.hand_detail_text.insert("end",
                        f"  {opp:20s}  {etype}{override_mark}  "
                        f"({pinfo['hands']} hands, VPIP:{pinfo['vpip']:.0f}% PFR:{pinfo['pfr']:.0f}%)\n")
                else:
                    self.hand_detail_text.insert("end", f"  {opp:20s}  Unknown (no data)\n")

        self.hand_detail_text.configure(state="disabled")

        # Open a separate popup window
        self._open_hand_popup(hand, ev_diff, strength)

    def _open_hand_popup(self, hand, ev_diff, strength):
        """Lightweight native tkinter Toplevel for hand detail."""
        popup = tk.Toplevel(self)
        popup.title(f"Hand {hand.hand_id}")
        popup.geometry("620x500")
        popup.configure(bg=self.theme["bg_input"])
        popup.attributes("-topmost", True)
        popup.focus_force()

        # Header bar
        header = tk.Frame(popup, bg=self.theme["bg_accent"], height=36)
        header.pack(fill="x")
        header.pack_propagate(False)

        dt = hand.date.strftime("%m/%d/%Y %H:%M") if hand.date else "?"
        res = f"+{hand.hero_won:.0f}" if hand.hero_won >= 0 else f"{hand.hero_won:.0f}"
        res_color = self.theme["green"] if hand.hero_won >= 0 else self.theme["red"]
        ev_str = f"+{ev_diff:.1f}" if ev_diff >= 0 else f"{ev_diff:.1f}"

        tk.Label(header, text=f"{hand.hero_cards}  |  {hand.hero_position}  |  {dt}",
                 bg=self.theme["bg_accent"], fg=self.theme["text"], font=("Consolas", 12, "bold")).pack(side="left", padx=8)
        tk.Label(header, text=f"Result: {res}", bg=self.theme["bg_accent"], fg=res_color,
                 font=("Consolas", 12, "bold")).pack(side="right", padx=8)

        # EV bar
        ev_bar = tk.Frame(popup, bg=self.theme["bg_panel"], height=28)
        ev_bar.pack(fill="x")
        ev_bar.pack_propagate(False)
        tk.Label(ev_bar, text=f"Strength: {strength}/100  |  EV Diff: {ev_str}  |  Pot: {hand.pot:.0f}  |  {hand.site}",
                 bg=self.theme["bg_panel"], fg=self.theme["gold"], font=("Consolas", 10)).pack(side="left", padx=8)

        # Raw hand text
        txt = tk.Text(popup, bg=self.theme["bg_input"], fg=self.theme["text"], font=("Consolas", 10),
                      insertbackground=self.theme["text"], relief="flat", padx=8, pady=6,
                      selectbackground=self.theme["select_bg"])
        txt.pack(fill="both", expand=True, padx=4, pady=4)
        txt.insert("1.0", hand.raw_text if hand.raw_text else "(no raw text)")
        txt.configure(state="disabled")

        # Bottom buttons
        btn_bar = tk.Frame(popup, bg=self.theme["bg_input"], height=32)
        btn_bar.pack(fill="x", pady=(0, 4))

        def _copy():
            popup.clipboard_clear()
            popup.clipboard_append(hand.raw_text or "")
            close_btn.configure(text="Copied!")
            popup.after(1500, lambda: close_btn.configure(text="Close"))

        tk.Button(btn_bar, text="Copy Hand", bg=self.theme["bg_accent"], fg=self.theme["text"],
                  font=("Consolas", 10), relief="flat", padx=12, command=_copy
                  ).pack(side="left", padx=8)
        close_btn = tk.Button(btn_bar, text="Close", bg=self.theme["bg_accent"], fg=self.theme["text"],
                              font=("Consolas", 10), relief="flat", padx=12,
                              command=popup.destroy)
        close_btn.pack(side="right", padx=8)

    # ── HUD Popup Window ──────────────────────────────────────────────────
    def _open_hud_window(self):
        """Open a separate native Toplevel window for Player HUD / Station Detector."""

        hud = tk.Toplevel(self)
        hud.title("\u2660 Player HUD / Station Detector")
        hud.geometry("750x550")
        hud.configure(bg=self.theme["bg_input"])
        hud.attributes("-topmost", True)
        hud.focus_force()

        # Ensure player stats are computed
        if not self.player_stats:
            hands = self.importer.get_hands()
            if hands:
                self.player_stats = self.station_detector.analyze_players(hands)

        # Top bar
        top_bar = tk.Frame(hud, bg=self.theme["bg_accent"])
        top_bar.pack(fill="x")
        tk.Label(top_bar, text="\u2660 Player HUD / Station Detector \u2665",
                 bg=self.theme["bg_accent"], fg=self.theme["gold"], font=("Consolas", 14, "bold")).pack(side="left", padx=8, pady=6)

        def _copy_hud():
            if not self.player_stats:
                return
            lines = [f"{'Player':20s} {'Type':16s} {'VPIP':>6s} {'PFR':>6s} {'AF':>5s} {'F2CB':>6s} {'Hands':>6s}"]
            lines.append("-" * 68)
            for p in self.player_stats:
                lines.append(f"{p['name']:20s} {p['classification']:16s} {p['vpip']:5.1f}% {p['pfr']:5.1f}% "
                           f"{p['af']:5.2f} {p['fold_cbet']:5.1f}% {p['hands']:6d}")
            hud.clipboard_clear()
            hud.clipboard_append("\n".join(lines))

        tk.Button(top_bar, text="Copy Stats", bg=self.theme["bg_accent"], fg=self.theme["text"],
                  font=("Consolas", 10), relief="flat", padx=10,
                  command=_copy_hud).pack(side="right", padx=8, pady=4)

        # Search
        search_frame = tk.Frame(hud, bg=self.theme["bg_panel"])
        search_frame.pack(fill="x", padx=4, pady=2)
        tk.Label(search_frame, text="Search:", bg=self.theme["bg_panel"], fg=self.theme["text"],
                 font=("Consolas", 10)).pack(side="left", padx=6)
        search_var = tk.StringVar()
        tk.Entry(search_frame, textvariable=search_var, bg=self.theme["bg_input"], fg=self.theme["text"],
                 font=("Consolas", 10), insertbackground=self.theme["text"],
                 relief="flat", width=25).pack(side="left", padx=4)

        # Type filter
        tk.Label(search_frame, text="  Type:", bg=self.theme["bg_panel"],
                 fg=self.theme["text"], font=("Consolas", 10)).pack(side="left", padx=(8, 2))
        hud_type_var = tk.StringVar(value="All")
        type_values = ["All", "Fish", "Calling Station", "LAG", "TAG", "Nit", "Maniac", "Regular", "Unknown"]
        hud_type_menu = tk.OptionMenu(search_frame, hud_type_var, *type_values,
                                      command=lambda _: _populate(search_var.get(), hud_type_var.get()))
        hud_type_menu.configure(bg=self.theme["bg_accent"], fg=self.theme["text"],
                                font=("Consolas", 9), relief="flat", highlightthickness=0)
        hud_type_menu["menu"].configure(bg=self.theme["bg_card"], fg=self.theme["text"],
                                         font=("Consolas", 9))
        hud_type_menu.pack(side="left", padx=2)

        # Legend
        legend = tk.Frame(hud, bg=self.theme["bg_panel"])
        legend.pack(fill="x", padx=4, pady=1)
        type_badges = [("Calling Station", self.theme["red"]), ("Nit", self.theme["text_dim"]),
                       ("TAG", self.theme["green"]),
                       ("LAG", self.theme["yellow"]), ("Maniac", self.theme["red"]),
                       ("Fish", self.theme["red"])]
        for tname, tcolor in type_badges:
            tk.Label(legend, text=tname, bg=self.theme["bg_panel"], fg=tcolor,
                     font=("Consolas", 9, "bold")).pack(side="left", padx=4)

        # Header
        header = tk.Frame(hud, bg=self.theme["bg_accent"])
        header.pack(fill="x", padx=4, pady=(2, 0))
        cols = ["Player", "Type", "VPIP", "PFR", "AF", "F2CB", "WTSD", "Hands"]
        col_widths = [18, 14, 7, 7, 6, 7, 7, 6]
        header_text = "  ".join(f"{c:<{w}}" for c, w in zip(cols, col_widths))
        tk.Label(header, text=header_text, bg=self.theme["bg_accent"], fg=self.theme["gold"],
                 font=("Consolas", 10, "bold"), anchor="w").pack(fill="x", padx=6, pady=2)

        # Scrollable player list using Canvas + Text widget (lightweight)
        list_text = tk.Text(hud, bg=self.theme["bg_input"], fg=self.theme["text"], font=("Consolas", 10),
                            relief="flat", padx=6, pady=4, state="disabled",
                            selectbackground=self.theme["select_bg"], cursor="arrow")
        scrollbar = tk.Scrollbar(hud, command=list_text.yview)
        list_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y", padx=(0, 4), pady=4)
        list_text.pack(fill="both", expand=True, padx=(4, 0), pady=4)

        # Define color tags
        type_color_map = {
            "Calling Station": self.theme["red"], "Nit": self.theme["text_dim"],
            "TAG": self.theme["green"],
            "LAG": self.theme["yellow"], "Maniac": self.theme["red"],
            "Fish": self.theme["red"],
            "Unknown": self.theme["text_dim"], "Regular": self.theme["text"],
        }
        for tname, tcolor in type_color_map.items():
            list_text.tag_configure(f"type_{tname}", foreground=tcolor)
        list_text.tag_configure("stat_good", foreground=self.theme["green"])
        list_text.tag_configure("stat_warn", foreground=self.theme["yellow"])
        list_text.tag_configure("stat_bad", foreground=self.theme["red"])
        list_text.tag_configure("dim", foreground=self.theme["text_dim"])

        def _populate(filter_text="", type_filter="All"):
            list_text.configure(state="normal")
            list_text.delete("1.0", "end")
            ft = filter_text.lower()
            count = 0
            for p in self.player_stats:
                if ft and ft not in p["name"].lower():
                    continue
                if type_filter != "All" and p["classification"] != type_filter:
                    continue
                if count >= 200:
                    break
                count += 1
                override = p.get("manual_type", "")
                type_display = p["classification"]
                if override:
                    type_display = f"{override}*"
                name_str = f"  {p['name']:<18s}"
                type_str = f"{type_display:<14s}"
                vpip_str = f"{p['vpip']:5.1f}%  "
                pfr_str = f"{p['pfr']:5.1f}%  "
                af_str = f"{p['af']:5.2f} "
                ftcb_str = f"{p['fold_cbet']:5.1f}%  "
                wtsd_str = f"{p['wtsd']:5.1f}%  "
                hands_str = f"{p['hands']:5d}\n"

                list_text.insert("end", name_str)
                list_text.insert("end", type_str, f"type_{p['classification']}")
                # Color VPIP
                vtag = "stat_bad" if p["vpip"] > 35 else "stat_good" if p["vpip"] > 25 else "dim"
                list_text.insert("end", vpip_str, vtag)
                # Color PFR
                ptag = "stat_good" if 12 <= p["pfr"] <= 22 else "stat_warn" if p["pfr"] < 12 else "stat_bad"
                list_text.insert("end", pfr_str, ptag)
                # Color AF
                atag = "stat_good" if 1.5 <= p["af"] <= 3.5 else "stat_warn" if p["af"] < 1.5 else "stat_bad"
                list_text.insert("end", af_str, atag)
                list_text.insert("end", ftcb_str, "stat_good" if p["fold_cbet"] > 60 else "stat_warn")
                list_text.insert("end", wtsd_str, "stat_good" if 25 <= p["wtsd"] <= 35 else "stat_warn")
                list_text.insert("end", hands_str, "dim")
            if count == 0:
                list_text.insert("end", "  No players found. Import hands first.")
            list_text.configure(state="disabled")

        _populate()

        def _on_search(*_):
            _populate(search_var.get(), hud_type_var.get())
        search_var.trace_add("write", _on_search)

        # Manual type override section
        override_frame = tk.Frame(hud, bg=self.theme["bg_panel"])
        override_frame.pack(fill="x", padx=4, pady=(0, 4))

        tk.Label(override_frame, text="Override Player Type:", bg=self.theme["bg_panel"],
                 fg=self.theme["gold"], font=("Consolas", 10, "bold")).pack(side="left", padx=6)

        override_name_var = tk.StringVar()
        tk.Label(override_frame, text="Player:", bg=self.theme["bg_panel"],
                 fg=self.theme["text"], font=("Consolas", 10)).pack(side="left", padx=(4, 2))
        override_entry = tk.Entry(override_frame, textvariable=override_name_var,
                                   bg=self.theme["bg_input"], fg=self.theme["text"],
                                   font=("Consolas", 10), insertbackground=self.theme["text"],
                                   relief="flat", width=18)
        override_entry.pack(side="left", padx=2)

        override_type_var = tk.StringVar(value="Fish")
        override_types = ["Fish", "Calling Station", "LAG", "TAG", "Nit", "Maniac", "Regular", "Whale", "Rec"]
        override_menu = tk.OptionMenu(override_frame, override_type_var, *override_types)
        override_menu.configure(bg=self.theme["bg_accent"], fg=self.theme["text"],
                                font=("Consolas", 9), relief="flat", highlightthickness=0)
        override_menu["menu"].configure(bg=self.theme["bg_card"], fg=self.theme["text"],
                                         font=("Consolas", 9))
        override_menu.pack(side="left", padx=4)

        def _set_override():
            pname = override_name_var.get().strip()
            ptype = override_type_var.get()
            if not pname:
                return
            self.db.set_manual_player_type(pname, ptype)
            # Update in-memory stats
            for p in self.player_stats:
                if p["name"] == pname:
                    p["manual_type"] = ptype
                    p["classification"] = ptype
                    break
            _populate(search_var.get(), hud_type_var.get())
            # Also push to DH2 if connected
            try:
                self.dh2_sync.push_player_note(pname, f"Type: {ptype}")
            except Exception:
                pass

        def _clear_override():
            pname = override_name_var.get().strip()
            if not pname:
                return
            self.db.set_manual_player_type(pname, "")
            for p in self.player_stats:
                if p["name"] == pname:
                    p["manual_type"] = ""
                    p["classification"] = p.get("auto_type", "Unknown")
                    break
            _populate(search_var.get(), hud_type_var.get())

        tk.Button(override_frame, text="Set Type", bg=self.theme["green"],
                  fg=self.theme["bg_base"], font=("Consolas", 9, "bold"),
                  relief="flat", padx=8, command=_set_override).pack(side="left", padx=4)
        tk.Button(override_frame, text="Clear", bg=self.theme["red"],
                  fg=self.theme["text"], font=("Consolas", 9),
                  relief="flat", padx=6, command=_clear_override).pack(side="left", padx=2)

        # Click player name to auto-fill override
        def _on_player_click(event):
            idx = list_text.index(f"@{event.x},{event.y}")
            line = list_text.get(f"{idx} linestart", f"{idx} lineend").strip()
            if line:
                pname = line.split()[0] if line.split() else ""
                override_name_var.set(pname)
        list_text.bind("<Double-Button-1>", _on_player_click)

    # ── Leak Analysis tab ─────────────────────────────────────────────────
    def _update_leak_tab(self):
        s = self.current_stats
        if not s:
            return
        for widget in self.leak_stats_frame.winfo_children():
            widget.destroy()

        stat_defs = [
            ("VPIP", f"{s['vpip']}%", self._stat_color(s["vpip"], 15, 22, 30)),
            ("PFR", f"{s['pfr']}%", self._stat_color(s["pfr"], 10, 20, 25)),
            ("AF", str(s["af"]), self._stat_color(s["af"], 1.5, 3.5, 4.5)),
            ("WTSD", f"{s['wtsd']}%", self._stat_color(s["wtsd"], 20, 32, 40)),
            ("W$SD", f"{s['wsd']}%", self.theme["green"] if s["wsd"] >= 50 else self.theme["yellow"] if s["wsd"] >= 45 else self.theme["red"]),
            ("C-Bet", f"{s['cbet']}%", self._stat_color(s["cbet"], 50, 70, 80)),
        ]
        for i, (name, val, color) in enumerate(stat_defs):
            frame = ctk.CTkFrame(self.leak_stats_frame, fg_color=self.theme["bg_card"],
                                  corner_radius=8, width=140, height=70,
                                  border_width=1, border_color=self.theme["border"])
            frame.grid(row=0, column=i, padx=4, pady=4, sticky="nsew")
            frame.grid_propagate(False)
            self.leak_stats_frame.grid_columnconfigure(i, weight=1)
            ctk.CTkLabel(frame, text=name, text_color=self.theme["text_dim"], font=("Consolas", 11)).pack(pady=(6, 0))
            ctk.CTkLabel(frame, text=val, text_color=color, font=("Consolas", 18, "bold")).pack()

        self.leak_alerts_text.configure(state="normal")
        self.leak_alerts_text.delete("1.0", "end")
        for color, msg in s.get("alerts", []):
            icon = {"green": "\u2705", "yellow": "\u26a0\ufe0f", "red": "\u274c"}.get(color, "")
            self.leak_alerts_text.insert("end", f"  {icon}  {msg}\n")
        self.leak_alerts_text.configure(state="disabled")

        self.leak_pos_text.configure(state="normal")
        self.leak_pos_text.delete("1.0", "end")
        self.leak_pos_text.insert("end", f"  {'Pos':4s} {'Hands':>6s} {'VPIP':>7s} {'PFR':>7s}\n")
        self.leak_pos_text.insert("end", "  " + "-" * 30 + "\n")
        for pos in ["EP", "MP", "CO", "BTN", "SB", "BB"]:
            pd = s.get("by_position", {}).get(pos)
            if pd:
                self.leak_pos_text.insert("end",
                                           f"  {pos:4s} {pd['total']:6d} {pd['vpip']:6.1f}% {pd['pfr']:6.1f}%\n")
        self.leak_pos_text.configure(state="disabled")

        self.leak_site_text.configure(state="normal")
        self.leak_site_text.delete("1.0", "end")
        for site, sd in s.get("by_site", {}).items():
            self.leak_site_text.insert("end",
                                        f"  {site}: {sd['total']} hands | VPIP {sd['vpip']}% | "
                                        f"PFR {sd['pfr']}% | Net: {sd['net']:+.2f}\n")
        self.leak_site_text.configure(state="disabled")

        self._update_leak_graphs()

    def _update_leak_graphs(self):
        """Render positional VPIP/PFR bar chart on leak tab."""
        if not hasattr(self, 'leak_fig'):
            return
        t = self.theme
        s = self.current_stats
        self.leak_fig.clear()
        self.leak_fig.patch.set_facecolor(t["graph_bg"])

        ax = self.leak_fig.add_subplot(111)
        ax.set_facecolor(t["graph_face"])
        ax.tick_params(colors=t["text_dim"], labelsize=8)
        ax.set_title("VPIP / PFR by Position", color=t["gold"], fontsize=10, fontweight="bold")
        for spine in ax.spines.values():
            spine.set_color(t["graph_grid"])

        pos_stats = s.get("by_position", {}) if s else {}
        if pos_stats:
            positions = list(pos_stats.keys())
            vpip_vals = [pos_stats[p].get("vpip", 0) for p in positions]
            pfr_vals = [pos_stats[p].get("pfr", 0) for p in positions]
            import numpy as np
            x = np.arange(len(positions))
            w = 0.35
            ax.bar(x - w/2, vpip_vals, w, label="VPIP", color=t["graph_bar1"], alpha=0.85)
            ax.bar(x + w/2, pfr_vals, w, label="PFR", color=t["graph_bar2"], alpha=0.85)
            ax.set_xticks(x)
            ax.set_xticklabels(positions, color=t["text_dim"], fontsize=9)
            ax.set_ylabel("%", color=t["text_dim"], fontsize=9)
            ax.legend(facecolor=t["graph_face"], edgecolor=t["graph_grid"],
                      labelcolor=t["text_dim"], fontsize=8)
        else:
            ax.text(0.5, 0.5, "No positional data", ha="center", va="center",
                    color=t["text_dim"], fontsize=12)
        ax.grid(True, axis="y", color=t["graph_grid"], alpha=0.3, linewidth=0.5)

        self.leak_fig.tight_layout(pad=1.5)
        self.leak_canvas.draw()

    def _stat_color(self, val, low, high_good, high_bad):
        if val < low:
            return self.theme["red"]
        if val > high_bad:
            return self.theme["red"]
        if low <= val <= high_good:
            return self.theme["green"]
        return self.theme["yellow"]

    # ── AI Summary ────────────────────────────────────────────────────────
    def _generate_summary(self):
        source = self.ai_source_var.get() if hasattr(self, 'ai_source_var') else "All Hands"
        if source == "Selected Hands":
            hands = self._get_selected_hands()
            desc = f"Selected Hands ({len(hands)})"
        elif source == "Filtered Hands":
            hands = self._get_filtered_hands()
            desc = self._get_filter_description()
        else:
            hands = self.importer.get_hands()
            desc = "All Hands"

        if hasattr(self, 'ai_filter_label'):
            self.ai_filter_label.configure(text=f"Source: {desc}")

        if not hands:
            self.ai_text.configure(state="normal")
            self.ai_text.delete("1.0", "end")
            self.ai_text.insert("end", "No hands match current selection/filters.")
            return
        stats = self.leak_engine.analyze(hands)
        summary = self.summary_gen.generate(stats, hands)

        # Prepend filter info header
        header = f"{'='*60}\nANALYSIS SOURCE: {desc}\nHands Analyzed: {len(hands)}\n{'='*60}\n\n"
        self.ai_text.configure(state="normal")
        self.ai_text.delete("1.0", "end")
        self.ai_text.insert("end", header + summary)

    def _analyze_filtered(self):
        """Analyze currently filtered hands in the AI tab."""
        if hasattr(self, 'ai_source_var'):
            self.ai_source_var.set("Filtered Hands")
        self.tabview.set("AI / GTO")
        self._generate_summary()

    def _export_filtered(self):
        """Export filtered hands to file (txt/csv/json)."""
        hands = self._get_filtered_hands()
        if not hands:
            self._set_status("No hands match filters")
            return

        path = filedialog.asksaveasfilename(
            title="Export Filtered Hands",
            defaultextension=".txt",
            filetypes=[("Text file", "*.txt"), ("CSV file", "*.csv"),
                       ("JSON file", "*.json"), ("All files", "*.*")]
        )
        if not path:
            return

        try:
            ext = os.path.splitext(path)[1].lower()
            filter_desc = self._get_filter_description()
            stats = self.leak_engine.analyze(hands)

            if ext == ".csv":
                lines = ["hand_id,date,site,type,cards,position,result,pot,ev_diff,tags"]
                for h in hands:
                    dt = h.date.strftime("%Y-%m-%d %H:%M") if h.date else ""
                    game = "Tournament" if h.is_tournament else "Cash"
                    ev = self.ev_calculator.calc_ev_diff(h, self.settings)
                    tags = ";".join(self.db.get_tags(h.hand_id) or [])
                    lines.append(f"{h.hand_id},{dt},{h.site},{game},{h.hero_cards},"
                                 f"{h.hero_position},{h.hero_won:.2f},{h.pot:.2f},{ev:.2f},{tags}")
                with open(path, "w", encoding="utf-8") as f:
                    f.write("\n".join(lines))

            elif ext == ".json":
                data = {
                    "export_date": datetime.now().isoformat(),
                    "filters": filter_desc,
                    "total_hands": len(hands),
                    "stats": stats,
                    "hands": []
                }
                for h in hands:
                    data["hands"].append({
                        "hand_id": h.hand_id,
                        "date": h.date.isoformat() if h.date else None,
                        "site": h.site,
                        "is_tournament": h.is_tournament,
                        "tournament_id": h.tournament_id,
                        "hero_cards": h.hero_cards,
                        "position": h.hero_position,
                        "result": h.hero_won,
                        "pot": h.pot,
                        "board": " ".join(h.board_cards) if h.board_cards else "",
                        "tags": self.db.get_tags(h.hand_id),
                        "raw_text": h.raw_text or "",
                    })
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, default=str)

            else:  # .txt or any other
                summary = self.summary_gen.generate(stats, hands)
                header = (f"{'='*60}\n"
                          f"POKER HAND TRACKER — FILTERED EXPORT\n"
                          f"{'='*60}\n"
                          f"Filters: {filter_desc}\n"
                          f"Hands: {len(hands)}\n"
                          f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                          f"{'='*60}\n\n")
                raw_section = "\n\n" + "="*60 + "\nRAW HAND HISTORIES\n" + "="*60 + "\n\n"
                raw_texts = []
                for h in hands:
                    if h.raw_text:
                        tags = self.db.get_tags(h.hand_id) or []
                        tag_line = f"[Tags: {', '.join(tags)}]\n" if tags else ""
                        raw_texts.append(tag_line + h.raw_text)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(header + summary + raw_section + "\n\n".join(raw_texts))

            self._set_status(f"Exported {len(hands)} hands to {os.path.basename(path)}")
        except Exception as e:
            self._set_status(f"Export failed: {e}")

    def _save_summary_as(self):
        """Save AI analysis with file type picker."""
        text = self.ai_text.get("1.0", "end").strip()
        if not text:
            self._set_status("Nothing to save — generate an analysis first")
            return
        path = filedialog.asksaveasfilename(
            title="Save Analysis",
            defaultextension=".txt",
            filetypes=[("Text file", "*.txt"), ("Markdown", "*.md"), ("All files", "*.*")]
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            self._set_status(f"Analysis saved to {os.path.basename(path)}")
        except Exception as e:
            self._set_status(f"Save failed: {e}")

    def _copy_summary(self):
        try:
            text = self.ai_text.get("1.0", "end").strip()
            if text:
                self.clipboard_clear()
                self.clipboard_append(text)
                self._set_status("Summary copied to clipboard!")
        except Exception:
            self._set_status("Failed to copy to clipboard")

    def _save_summary(self):
        text = self.ai_text.get("1.0", "end").strip()
        if not text:
            self._set_status("Nothing to save — generate a summary first")
            return
        outpath = r"C:\poker-build\ai_summary.txt"
        try:
            with open(outpath, "w", encoding="utf-8") as f:
                f.write(text)
            self._set_status(f"Summary saved to {outpath}")
        except Exception as e:
            self._set_status(f"Save failed: {e}")

    # ── GTO Wizard Export ─────────────────────────────────────────────────
    def _export_gto_wizard(self):
        source = self.ai_source_var.get() if hasattr(self, 'ai_source_var') else "All Hands"
        if source == "Selected Hands":
            hands = self._get_selected_hands()
        elif source == "Filtered Hands":
            hands = self._get_filtered_hands()
        else:
            hands = self.importer.get_hands()
        if not hands:
            self._set_status("No hands to export")
            return
        output_parts = []
        for h in hands:
            if not h.raw_text:
                continue
            if h.site == "ACR":
                output_parts.append(h.raw_text)
            elif h.site == "CoinPoker":
                output_parts.append(self._convert_coinpoker_to_pokerstars(h))
            else:
                output_parts.append(h.raw_text)
        export_path = r"C:\poker-build\gto_wizard_export.txt"
        try:
            with open(export_path, "w", encoding="utf-8") as f:
                f.write("\n\n\n".join(output_parts))
            self._set_status(
                f"Exported {len(output_parts)} hands to {export_path}")
        except Exception as e:
            self._set_status(f"Export failed: {e}")

    def _convert_coinpoker_to_pokerstars(self, hand):
        """Convert CoinPoker hand history to PokerStars-compatible format."""
        text = hand.raw_text
        lines = text.split("\n")
        out = []
        for i, line in enumerate(lines):
            if i == 0:
                converted = line.replace("CoinPoker Hand #", "PokerStars Hand #")
                converted = converted.replace("\u20ae", "$")
                if " ET" not in converted and " UTC" not in converted:
                    converted = converted.rstrip() + " ET"
                out.append(converted)
            else:
                out.append(line.replace("\u20ae", "$"))
        return "\n".join(out)

    # ── Players / HUD tab ─────────────────────────────────────────────────
    def _compute_players_bg(self):
        """Run heavy player analysis off the GUI thread and persist to DB."""
        hands = self.importer.get_hands()
        stats = self.station_detector.analyze_players(hands)
        stats = self.station_detector.apply_manual_overrides(stats, self.db)
        self.player_stats = stats
        # Persist player types to database
        for p in stats:
            try:
                self.db.save_player_type(
                    name=p["name"], auto_type=p.get("auto_type", p["classification"]),
                    hands=p["hands"], vpip=p["vpip"], pfr=p["pfr"],
                    af=p["af"], fold_cbet=p["fold_cbet"], wtsd=p["wtsd"])
            except Exception:
                pass

    # ── Settings ──────────────────────────────────────────────────────────
    def _refresh_dir_list(self):
        self.dir_listbox.configure(state="normal")
        self.dir_listbox.delete("1.0", "end")
        for entry in self.settings.get("scan_dirs", []):
            self.dir_listbox.insert("end", f"  [{entry['site']}]  {entry['path']}\n")

    def _add_dir(self):
        path = self.new_dir_var.get().strip()
        site = self.new_dir_site_var.get()
        if path:
            self.settings.setdefault("scan_dirs", []).append({"path": path, "site": site})
            self._refresh_dir_list()
            self.new_dir_var.set("")

    def _remove_dir(self):
        dirs = self.settings.get("scan_dirs", [])
        if dirs:
            dirs.pop()
            self._refresh_dir_list()

    def _save_settings(self):
        self.settings["hero_names"]["CoinPoker"] = self.hero_cp_var.get().strip()
        self.settings["hero_names"]["ACR"] = self.hero_acr_var.get().strip()
        self.settings["auto_refresh"] = self.auto_refresh_var.get()
        try:
            self.settings["refresh_interval"] = int(self.interval_var.get())
        except ValueError:
            self.settings["refresh_interval"] = 5
        # DH2 settings
        self.settings["dh2_db_path"] = self.dh2_path_var.get().strip()
        self.settings["dh2_auto_sync"] = self.dh2_auto_var.get()
        try:
            self.settings["dh2_sync_interval"] = int(self.dh2_interval_var.get())
        except ValueError:
            self.settings["dh2_sync_interval"] = 5

        save_settings(self.settings)
        self.importer.update_settings(self.settings)
        self.dh2_sync.settings = self.settings
        self.dh2_sync.dh2_db_path = self.settings["dh2_db_path"]
        self._set_status("Settings saved!")

        if self.settings["auto_refresh"]:
            self.importer.stop_watcher()
            self.importer.start_watcher(callback=self._watcher_callback)
        else:
            self.importer.stop_watcher()

        # Restart DH2 polling with updated settings
        self.dh2_sync.stop_polling()
        if self.settings["dh2_auto_sync"]:
            self.dh2_sync.start_polling(
                callback=self._dh2_callback,
                interval=self.settings["dh2_sync_interval"],
            )
        self._update_dh2_status()

    # ── DriveHUD 2 Actions ────────────────────────────────────────────────
    def _browse_dh2_path(self):
        path = filedialog.askopenfilename(
            title="Select DriveHUD 2 Database",
            filetypes=[("SQLite Database", "*.db"), ("All Files", "*.*")],
            initialdir=os.path.join(os.environ.get("APPDATA", ""), "DriveHUD 2"),
        )
        if path:
            self.dh2_path_var.set(path)

    def _dh2_sync_now(self):
        self._set_status("Syncing from DriveHUD 2...")
        def do_sync():
            try:
                count = self.dh2_sync.sync()
                total = self.dh2_sync.total_imported
                msg = f"DH2 sync: {count} new | {total} total imported"
                if count == 0:
                    msg += " (all caught up)"
                self.after(0, lambda: self._set_status(msg))
                if count > 0:
                    self.after(0, self._post_scan)
                self.after(0, self._update_dh2_status)
            except Exception as e:
                self.after(0, lambda: self._set_status(f"DH2 sync error: {e}"))
        threading.Thread(target=do_sync, daemon=True).start()

    def _dh2_reset(self):
        self.dh2_sync.reset()
        self._update_dh2_status()
        self._set_status("DH2 sync state reset — next sync will re-import all hands")

    def _update_dh2_status(self):
        try:
            status = self.dh2_sync.get_status()
            if status["connected"]:
                txt = f"✓ Connected | {status['total_imported']} imported | Last ID: {status['last_id']}"
                if status["last_sync"]:
                    txt += f" | Last: {status['last_sync'][:19]}"
                self.dh2_status_label.configure(text=txt, text_color=self.theme["green"])
            else:
                self.dh2_status_label.configure(text="✗ DH2 database not found", text_color=self.theme["red"])
        except Exception:
            self.dh2_status_label.configure(text="✗ Status unavailable", text_color=self.theme["red"])


# ─── Main Entry Point ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    app = PokerApp()
    app.mainloop()
