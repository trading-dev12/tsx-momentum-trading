"""
System Health Panel

Displays paper-trading service health using real Tkinter
foreground colours instead of colour emoji characters.
"""

import tkinter as tk


HEALTHY_COLOUR = "#168821"
WAITING_COLOUR = "#b36b00"
ERROR_COLOUR = "#c62828"
TEXT_COLOUR = "#202124"
BACKGROUND_COLOUR = "#e8f0fe"


class SystemHealthPanel(tk.Frame):
    def __init__(self, parent):
        super().__init__(
            parent,
            bg=BACKGROUND_COLOUR,
            padx=8,
            pady=4,
        )

        self.status_labels = {}

        title = tk.Label(
            self,
            text="SYSTEM HEALTH",
            font=("Consolas", 9, "bold"),
            bg=BACKGROUND_COLOUR,
            fg=TEXT_COLOUR,
        )
        title.pack(side="left", padx=(0, 12))

        self._add_status("scanner", "Scanner")
        self._add_status("execution", "Auto Execution")
        self._add_status("eod", "Auto EOD")
        self._add_status("monitor", "Position Monitor")
        self._add_status("journal", "Trade Journal")

        self.counts_label = tk.Label(
            self,
            text=(
                "Pending: 0 | Open: 0 | "
                "Closed: 0 | Last Refresh: --"
            ),
            font=("Consolas", 9),
            bg=BACKGROUND_COLOUR,
            fg=TEXT_COLOUR,
        )
        self.counts_label.pack(
            side="left",
            padx=(14, 0),
        )

    def _add_status(self, key, title):
        container = tk.Frame(
            self,
            bg=BACKGROUND_COLOUR,
        )
        container.pack(
            side="left",
            padx=(0, 12),
        )

        indicator = tk.Label(
            container,
            text="●",
            font=("Arial", 11, "bold"),
            bg=BACKGROUND_COLOUR,
            fg=WAITING_COLOUR,
        )
        indicator.pack(side="left")

        text_label = tk.Label(
            container,
            text=f"{title}: WAITING",
            font=("Consolas", 9),
            bg=BACKGROUND_COLOUR,
            fg=TEXT_COLOUR,
        )
        text_label.pack(
            side="left",
            padx=(3, 0),
        )

        self.status_labels[key] = {
            "indicator": indicator,
            "text": text_label,
            "title": title,
        }

    def set_status(self, key, status):
        if key not in self.status_labels:
            return

        normalized_status = str(status).upper()

        if normalized_status in {
            "RUNNING",
            "READY",
            "ACTIVE",
        }:
            colour = HEALTHY_COLOUR

        elif normalized_status in {
            "WAITING",
            "REFRESHING",
            "NOT DUE",
        }:
            colour = WAITING_COLOUR

        else:
            colour = ERROR_COLOUR

        item = self.status_labels[key]

        item["indicator"].config(
            fg=colour,
        )

        item["text"].config(
            text=(
                f"{item['title']}: "
                f"{normalized_status}"
            )
        )

    def update_counts(
        self,
        pending_trades,
        open_positions,
        closed_trades,
        last_refresh,
    ):
        self.counts_label.config(
            text=(
                f"Pending: {pending_trades} | "
                f"Open: {open_positions} | "
                f"Closed: {closed_trades} | "
                f"Last Refresh: {last_refresh or '--'}"
            )
        )