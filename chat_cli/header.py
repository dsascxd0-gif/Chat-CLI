import asyncio
from datetime import datetime
from textual.widgets import Static
from textual.containers import Horizontal


class HeaderBar(Static):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._time_widget = None
        self._date_widget = None

    def compose(self):
        with Horizontal():
            yield Static("2026-04-25", id="header-date")
            yield Static("00:00:00", id="header-time")
            yield Static("CHAT CLI", id="header-tokens")

    def on_mount(self):
        self._date_widget = self.query_one("#header-date", Static)
        self._time_widget = self.query_one("#header-time", Static)
        self._update_time()
        self._task = asyncio.create_task(self._run_clock())

    async def _run_clock(self):
        while True:
            await asyncio.sleep(1)
            self._update_time()

    def _update_time(self):
        now = datetime.now()
        self._date_widget.update(now.strftime("%Y-%m-%d"))
        self._time_widget.update(now.strftime("%H:%M:%S"))

    async def update_token_count(self, count: int):
        self.query_one("#header-tokens", Static).update(f"CHAT CLI")

    def on_unmount(self):
        if hasattr(self, "_task"):
            self._task.cancel()