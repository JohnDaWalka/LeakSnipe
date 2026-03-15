"""
CoinPoker Hand Tracker v2.0 — GUI Edition
Dark poker-table themed interface using customtkinter.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import json
import os
import csv
from datetime import datetime

# ── Theme & Colours ──────────────────────────────────────────────
FELT_GREEN   = "#1a5c2a"
DARK_BG      = "#0d1117"
CARD_BG      = "#161b22"
ACCENT_GOLD  = "#d4a017"
ACCENT_GREEN = "#2ea043"
TEXT_PRIMARY  = "#e6edf3"
TEXT_DIM      = "#8b949e"
BORDER_CLR   = "#30363d"
WIN_CLR      = "#3fb950"
LOSS_CLR     = "#f85149"
FOLD_CLR     = "#8b949e"
SPLIT_CLR    = "#d29922"
CHIP_RED     = "#da3633"

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "coinpoker_hands.json")

# ── Data layer ───────────────────────────────────────────────────

def load_hands():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

def save_hands(hands):
    with open(DATA_FILE, "w") as f:
        json.dump(hands, f, indent=2)

# ── Suit / card rendering helpers ────────────────────────────────

SUIT_SYMBOLS = {"h": "♥", "d": "♦", "c": "♣", "s": "♠"}
SUIT_COLORS  = {"h": "#f85149", "d": "#539bf5", "c": "#3fb950", "s": "#e6edf3"}

def format_card_text(raw):
    """Turn 'AhKs' into 'A♥ K♠' style text."""
    if not raw:
        return ""
    out = []
    i = 0
    while i < len(raw):
        if i + 1 < len(raw) and raw[i + 1].lower() in SUIT_SYMBOLS:
            rank = raw[i].upper()
            suit = SUIT_SYMBOLS[raw[i + 1].lower()]
            out.append(f"{rank}{suit}")
            i += 2
        else:
            out.append(raw[i])
            i += 1
    return " ".join(out)


# ── Reusable widgets ─────────────────────────────────────────────

class CardLabel(ctk.CTkFrame):
    """Small card-chip widget showing rank+suit with colour."""
    def __init__(self, master, card_str, **kw):
        super().__init__(master, fg_color=CARD_BG, corner_radius=6,
                         border_width=1, border_color=BORDER_CLR, **kw)
        if len(card_str) >= 2:
            rank = card_str[0]
            suit_key = card_str[1].lower()
            suit = SUIT_SYMBOLS.get(suit_key, card_str[1])
            clr = SUIT_COLORS.get(suit_key, TEXT_PRIMARY)
            lbl = ctk.CTkLabel(self, text=f" {rank}{suit} ",
                               font=ctk.CTkFont(size=14, weight="bold"),
                               text_color=clr)
            lbl.pack(padx=4, pady=2)


class StatCard(ctk.CTkFrame):
    """A small stat box: title on top, big number below."""
    def __init__(self, master, title, value, color=TEXT_PRIMARY, **kw):
        super().__init__(master, fg_color=CARD_BG, corner_radius=10,
                         border_width=1, border_color=BORDER_CLR, **kw)
        ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=11),
                     text_color=TEXT_DIM).pack(pady=(10, 0), padx=16)
        ctk.CTkLabel(self, text=str(value),
                     font=ctk.CTkFont(size=22, weight="bold"),
                     text_color=color).pack(pady=(0, 10), padx=16)


# ── Main application ─────────────────────────────────────────────

class PokerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("♠ CoinPoker Hand Tracker")
        self.geometry("1100x720")
        self.minsize(900, 600)
        self.configure(fg_color=DARK_BG)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        self.hands = load_hands()

        self._build_ui()
        self._refresh_table()
        self._refresh_stats()

    # ── UI construction ──────────────────────────────────────────

    def _build_ui(self):
        # Top banner
        banner = ctk.CTkFrame(self, fg_color=FELT_GREEN, corner_radius=0, height=56)
        banner.pack(fill="x")
        banner.pack_propagate(False)

        ctk.CTkLabel(banner, text="♠ ♥ ♦ ♣",
                     font=ctk.CTkFont(size=20),
                     text_color="#aab4be").pack(side="left", padx=16)
        ctk.CTkLabel(banner, text="CoinPoker Hand Tracker",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color="white").pack(side="left", padx=4)
        ctk.CTkLabel(banner, text="v2.0",
                     font=ctk.CTkFont(size=12),
                     text_color="#c8cdd2").pack(side="left", padx=4, pady=(4, 0))

        # Toolbar
        toolbar = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=0, height=48)
        toolbar.pack(fill="x")
        toolbar.pack_propagate(False)

        btn_kw = dict(height=34, corner_radius=8,
                      font=ctk.CTkFont(size=13, weight="bold"))

        ctk.CTkButton(toolbar, text="＋ Add Hand", fg_color=ACCENT_GREEN,
                      hover_color="#238636", command=self._open_add_dialog,
                      **btn_kw).pack(side="left", padx=(12, 4), pady=7)
        ctk.CTkButton(toolbar, text="🗑  Delete", fg_color=CHIP_RED,
                      hover_color="#b62324", command=self._delete_selected,
                      **btn_kw).pack(side="left", padx=4, pady=7)
        ctk.CTkButton(toolbar, text="📄 Export CSV", fg_color="#30363d",
                      hover_color="#484f58", command=self._export_csv,
                      **btn_kw).pack(side="left", padx=4, pady=7)

        # Search
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._refresh_table())
        search_entry = ctk.CTkEntry(toolbar, textvariable=self.search_var,
                                    placeholder_text="🔍  Search hands…",
                                    width=220, height=34, corner_radius=8,
                                    fg_color=DARK_BG, border_color=BORDER_CLR)
        search_entry.pack(side="right", padx=12, pady=7)

        # Body: left=table, right=stats
        body = ctk.CTkFrame(self, fg_color=DARK_BG)
        body.pack(fill="both", expand=True, padx=12, pady=(8, 12))
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        # Table panel
        table_frame = ctk.CTkFrame(body, fg_color=CARD_BG, corner_radius=12,
                                   border_width=1, border_color=BORDER_CLR)
        table_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        # Table header
        cols = ("ID", "Date", "Table", "Cards", "Board", "Hand", "Pl",
                "Pot", "Coin In", "Coin Out", "Result")
        col_widths = (36, 110, 90, 70, 110, 90, 30, 70, 70, 70, 55)

        header_frame = ctk.CTkFrame(table_frame, fg_color="#21262d",
                                    corner_radius=0, height=32)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        for i, (col, w) in enumerate(zip(cols, col_widths)):
            ctk.CTkLabel(header_frame, text=col, width=w,
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=TEXT_DIM, anchor="w").pack(
                side="left", padx=(8 if i == 0 else 2, 2))

        # Scrollable list
        self.list_frame = ctk.CTkScrollableFrame(
            table_frame, fg_color=CARD_BG, corner_radius=0,
            scrollbar_button_color=BORDER_CLR,
            scrollbar_button_hover_color=TEXT_DIM)
        self.list_frame.pack(fill="both", expand=True)

        self.col_widths = col_widths

        # Stats panel (right)
        self.stats_frame = ctk.CTkScrollableFrame(
            body, fg_color=CARD_BG, corner_radius=12,
            border_width=1, border_color=BORDER_CLR, width=260,
            scrollbar_button_color=BORDER_CLR)
        self.stats_frame.grid(row=0, column=1, sticky="nsew")

    # ── Table rendering ──────────────────────────────────────────

    def _refresh_table(self):
        for w in self.list_frame.winfo_children():
            w.destroy()

        query = self.search_var.get().lower().strip()
        filtered = [h for h in self.hands if self._matches(h, query)]

        if not filtered:
            ctk.CTkLabel(self.list_frame, text="No hands recorded yet.\nClick '＋ Add Hand' to get started!",
                         font=ctk.CTkFont(size=14), text_color=TEXT_DIM,
                         justify="center").pack(pady=60)
            return

        for idx, h in enumerate(filtered):
            self._render_row(h, idx)

    def _matches(self, h, query):
        if not query:
            return True
        searchable = " ".join([
            str(h.get("id", "")),
            h.get("date", ""), h.get("table", ""),
            h.get("cards", ""), h.get("board", ""),
            h.get("hand_type", ""), h.get("result", "")
        ]).lower()
        return query in searchable

    def _render_row(self, h, idx):
        bg = "#161b22" if idx % 2 == 0 else "#1c2128"
        row = ctk.CTkFrame(self.list_frame, fg_color=bg, corner_radius=0,
                           height=36)
        row.pack(fill="x", pady=0)
        row.pack_propagate(False)
        row.bind("<Button-1>", lambda e, hid=h["id"]: self._select_row(hid))

        result = h.get("result", "")
        res_clr = {
            "WIN": WIN_CLR, "LOSS": LOSS_CLR,
            "FOLD": FOLD_CLR, "SPLIT": SPLIT_CLR
        }.get(result.upper(), TEXT_PRIMARY)

        net = h.get("coin_out", 0) - h.get("coin_in", 0)

        values = [
            str(h.get("id", "")),
            h.get("date", ""),
            h.get("table", ""),
            format_card_text(h.get("cards", "")),
            format_card_text(h.get("board", "")),
            h.get("hand_type", ""),
            str(h.get("players", "")),
            f"{h.get('pot', 0):.0f}",
            f"{h.get('coin_in', 0):.0f}",
            f"{h.get('coin_out', 0):.0f}",
            result.upper(),
        ]

        for i, (val, w) in enumerate(zip(values, self.col_widths)):
            clr = res_clr if i == len(values) - 1 else TEXT_PRIMARY
            lbl = ctk.CTkLabel(row, text=val, width=w,
                               font=ctk.CTkFont(size=12),
                               text_color=clr, anchor="w")
            lbl.pack(side="left", padx=(8 if i == 0 else 2, 2))
            lbl.bind("<Button-1>", lambda e, hid=h["id"]: self._select_row(hid))

    def _select_row(self, hand_id):
        self.selected_id = hand_id
        # highlight
        for w in self.list_frame.winfo_children():
            w.configure(fg_color="#161b22")
        for w in self.list_frame.winfo_children():
            if isinstance(w, ctk.CTkFrame):
                for child in w.winfo_children():
                    if isinstance(child, ctk.CTkLabel):
                        try:
                            if child.cget("text") == str(hand_id):
                                w.configure(fg_color="#1f3a28")
                                break
                        except Exception:
                            pass

    # ── Stats panel ──────────────────────────────────────────────

    def _refresh_stats(self):
        for w in self.stats_frame.winfo_children():
            w.destroy()

        ctk.CTkLabel(self.stats_frame, text="📊  Session Stats",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=ACCENT_GOLD).pack(pady=(12, 8))

        n = len(self.hands)
        wins = sum(1 for h in self.hands if h.get("result", "").upper() == "WIN")
        losses = sum(1 for h in self.hands if h.get("result", "").upper() == "LOSS")
        folds = sum(1 for h in self.hands if h.get("result", "").upper() == "FOLD")
        splits = sum(1 for h in self.hands if h.get("result", "").upper() == "SPLIT")
        total_in = sum(h.get("coin_in", 0) for h in self.hands)
        total_out = sum(h.get("coin_out", 0) for h in self.hands)
        net = total_out - total_in
        biggest = max((h.get("pot", 0) for h in self.hands), default=0)
        win_pct = (100.0 * wins / n) if n else 0

        StatCard(self.stats_frame, "Hands Played", n,
                 ACCENT_GOLD).pack(fill="x", padx=8, pady=4)
        StatCard(self.stats_frame, "Win Rate",
                 f"{win_pct:.1f}%", WIN_CLR).pack(fill="x", padx=8, pady=4)

        # Win/Loss/Fold/Split bar
        bar_frame = ctk.CTkFrame(self.stats_frame, fg_color=CARD_BG, height=50)
        bar_frame.pack(fill="x", padx=8, pady=4)
        for label, count, clr in [("W", wins, WIN_CLR), ("L", losses, LOSS_CLR),
                                   ("F", folds, FOLD_CLR), ("S", splits, SPLIT_CLR)]:
            f = ctk.CTkFrame(bar_frame, fg_color=CARD_BG)
            f.pack(side="left", expand=True, fill="both")
            ctk.CTkLabel(f, text=label, font=ctk.CTkFont(size=10),
                         text_color=TEXT_DIM).pack()
            ctk.CTkLabel(f, text=str(count), font=ctk.CTkFont(size=16, weight="bold"),
                         text_color=clr).pack()

        sep = ctk.CTkFrame(self.stats_frame, fg_color=BORDER_CLR, height=1)
        sep.pack(fill="x", padx=16, pady=8)

        net_clr = WIN_CLR if net >= 0 else LOSS_CLR
        StatCard(self.stats_frame, "Net Profit",
                 f"{net:+,.0f}", net_clr).pack(fill="x", padx=8, pady=4)
        StatCard(self.stats_frame, "Total Coin In",
                 f"{total_in:,.0f}", TEXT_DIM).pack(fill="x", padx=8, pady=4)
        StatCard(self.stats_frame, "Total Coin Out",
                 f"{total_out:,.0f}", TEXT_DIM).pack(fill="x", padx=8, pady=4)
        StatCard(self.stats_frame, "Biggest Pot",
                 f"{biggest:,.0f}", ACCENT_GOLD).pack(fill="x", padx=8, pady=4)

    # ── Add hand dialog ──────────────────────────────────────────

    def _open_add_dialog(self):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Add New Hand")
        dlg.geometry("480x620")
        dlg.configure(fg_color=DARK_BG)
        dlg.transient(self)
        dlg.grab_set()
        dlg.resizable(False, False)

        # Center on parent
        dlg.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 480) // 2
        y = self.winfo_y() + (self.winfo_height() - 620) // 2
        dlg.geometry(f"+{x}+{y}")

        header = ctk.CTkFrame(dlg, fg_color=FELT_GREEN, corner_radius=0, height=44)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="♠  New Hand",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color="white").pack(side="left", padx=16)

        form = ctk.CTkScrollableFrame(dlg, fg_color=DARK_BG)
        form.pack(fill="both", expand=True, padx=20, pady=12)

        fields = {}

        def add_field(label, default="", width=420):
            ctk.CTkLabel(form, text=label, font=ctk.CTkFont(size=12),
                         text_color=TEXT_DIM, anchor="w").pack(fill="x", pady=(8, 2))
            entry = ctk.CTkEntry(form, width=width, height=36, corner_radius=8,
                                 fg_color=CARD_BG, border_color=BORDER_CLR,
                                 text_color=TEXT_PRIMARY)
            if default:
                entry.insert(0, default)
            entry.pack(fill="x")
            return entry

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        fields["date"]      = add_field("Date", now_str)
        fields["table"]     = add_field("Table Name")
        fields["cards"]     = add_field("Hole Cards  (e.g. AhKs)")
        fields["board"]     = add_field("Board  (e.g. Qh9d3cTh2s)")
        fields["hand_type"] = add_field("Hand Type  (e.g. Flush, Two Pair)")
        fields["players"]   = add_field("Number of Players", "6")
        fields["pot"]       = add_field("Pot Size")
        fields["coin_in"]   = add_field("Coins Wagered (In)")
        fields["coin_out"]  = add_field("Coins Received (Out)")

        # Result selector
        ctk.CTkLabel(form, text="Result", font=ctk.CTkFont(size=12),
                     text_color=TEXT_DIM, anchor="w").pack(fill="x", pady=(8, 2))
        result_var = ctk.StringVar(value="Win")
        result_frame = ctk.CTkFrame(form, fg_color="transparent")
        result_frame.pack(fill="x")
        for val, clr in [("Win", WIN_CLR), ("Loss", LOSS_CLR),
                         ("Fold", FOLD_CLR), ("Split", SPLIT_CLR)]:
            ctk.CTkRadioButton(result_frame, text=val, variable=result_var,
                               value=val, text_color=clr,
                               font=ctk.CTkFont(size=13),
                               fg_color=clr, hover_color=clr,
                               border_color=BORDER_CLR).pack(
                side="left", padx=(0, 16), pady=4)

        def on_save():
            try:
                hand = {
                    "id": len(self.hands) + 1,
                    "date": fields["date"].get().strip(),
                    "table": fields["table"].get().strip(),
                    "cards": fields["cards"].get().strip(),
                    "board": fields["board"].get().strip(),
                    "hand_type": fields["hand_type"].get().strip(),
                    "players": int(fields["players"].get() or 0),
                    "pot": float(fields["pot"].get() or 0),
                    "coin_in": float(fields["coin_in"].get() or 0),
                    "coin_out": float(fields["coin_out"].get() or 0),
                    "result": result_var.get().upper(),
                }
            except ValueError as e:
                messagebox.showerror("Input Error", str(e), parent=dlg)
                return

            self.hands.append(hand)
            save_hands(self.hands)
            self._refresh_table()
            self._refresh_stats()
            dlg.destroy()

        btn_bar = ctk.CTkFrame(dlg, fg_color=DARK_BG, height=56)
        btn_bar.pack(fill="x", padx=20, pady=(0, 12))
        ctk.CTkButton(btn_bar, text="Cancel", fg_color="#30363d",
                      hover_color="#484f58", width=100, height=38,
                      corner_radius=8, command=dlg.destroy).pack(
            side="right", padx=(4, 0))
        ctk.CTkButton(btn_bar, text="💾  Save Hand", fg_color=ACCENT_GREEN,
                      hover_color="#238636", width=160, height=38,
                      corner_radius=8, font=ctk.CTkFont(size=13, weight="bold"),
                      command=on_save).pack(side="right", padx=(0, 4))

    # ── Delete ───────────────────────────────────────────────────

    def _delete_selected(self):
        sel = getattr(self, "selected_id", None)
        if sel is None:
            messagebox.showinfo("Delete", "Click a row first to select it.")
            return
        if not messagebox.askyesno("Confirm",
                                   f"Delete hand #{sel}?"):
            return
        self.hands = [h for h in self.hands if h["id"] != sel]
        # re-number
        for i, h in enumerate(self.hands):
            h["id"] = i + 1
        self.selected_id = None
        save_hands(self.hands)
        self._refresh_table()
        self._refresh_stats()

    # ── CSV export ───────────────────────────────────────────────

    def _export_csv(self):
        if not self.hands:
            messagebox.showinfo("Export", "No hands to export.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile="coinpoker_hands.csv")
        if not path:
            return
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Date", "Table", "Cards", "Board",
                             "HandType", "Players", "Pot", "CoinIn",
                             "CoinOut", "Result"])
            for h in self.hands:
                writer.writerow([
                    h["id"], h["date"], h["table"], h["cards"],
                    h["board"], h["hand_type"], h["players"],
                    h["pot"], h["coin_in"], h["coin_out"], h["result"]
                ])
        messagebox.showinfo("Export", f"Exported {len(self.hands)} hands to:\n{path}")


# ── Entry point ──────────────────────────────────────────────────

if __name__ == "__main__":
    app = PokerApp()
    app.mainloop()
