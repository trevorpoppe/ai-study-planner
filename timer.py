import asyncio
from typing import List, Tuple

class SessionTimer:
    def __init__(self, schedule: List[Tuple[str, int]]):
        self.schedule = schedule  # e.g., [("study", 45), ("break", 5), ...]
        self.current_index = 0
        self.remaining = schedule[0][1] * 60  # in seconds
        self.running = False
        self._task = None

    async def _run_timer(self):
        while self.running and self.current_index < len(self.schedule):
            while self.remaining > 0 and self.running:
                await asyncio.sleep(1)
                self.remaining -= 1
            if self.running:
                self.current_index += 1
                if self.current_index < len(self.schedule):
                    self.remaining = self.schedule[self.current_index][1] * 60
                else:
                    self.running = False  # All sessions done

    def start(self):
        if not self.running:
            self.running = True
            self._task = asyncio.create_task(self._run_timer())

    def stop(self):
        self.running = False

    def status(self):
        if self.current_index >= len(self.schedule):
            return "Completed"
        return {
            "session_type": self.schedule[self.current_index][0],
            "time_remaining_seconds": self.remaining,
            "step": self.current_index + 1,
            "total_steps": len(self.schedule)
        }
