import time
import threading

class SessionTimer:
    def __init__(self, schedule):
        self.schedule = schedule  # e.g., [("study", 45), ("break", 5), ...]
        self.current_index = 0
        self.remaining = schedule[0][1] * 60  # in seconds
        self.running = False
        self._lock = threading.Lock()

    def start(self):
        self.running = True
        threading.Thread(target=self._run_timer, daemon=True).start()

    def _run_timer(self):
        while self.running and self.current_index < len(self.schedule):
            while self.remaining > 0 and self.running:
                time.sleep(1)
                with self._lock:
                    self.remaining -= 1
            if self.running:
                self.current_index += 1
                if self.current_index < len(self.schedule):
                    with self._lock:
                        self.remaining = self.schedule[self.current_index][1] * 60
                else:
                    self.running = False  # All sessions complete

    def stop(self):
        self.running = False

    def status(self):
        with self._lock:
            if self.current_index >= len(self.schedule):
                return {"message": "Completed"}
            return {
                "session_type": self.schedule[self.current_index][0],
                "time_remaining_seconds": self.remaining,
                "step": self.current_index + 1,
                "total_steps": len(self.schedule)
            }
