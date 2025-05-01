import time
import threading
from database import get_db
from datetime import datetime

def log_session(session_number, session_type, duration):
    db = get_db()
    start_time = datetime.now().isoformat()
    end_time = (datetime.now() + duration).isoformat()
    db.execute(
        "INSERT INTO study_logs (session_number, session_type, duration_seconds, start_time, end_time) VALUES (?, ?, ?, ?, ?)",
        (session_number, session_type, duration.total_seconds(), start_time, end_time),
    )
    db.commit()

class SessionTimer:
    def __init__(self, schedule):
        self.schedule = schedule  # List of (session_type, duration_minutes)
        self.current_index = 0
        self.remaining = schedule[0][1]
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
                        self.remaining = self.schedule[self.current_index][1]
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
