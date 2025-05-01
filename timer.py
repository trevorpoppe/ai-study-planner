import time
import threading
from database import get_db
from datetime import datetime, timedelta

def log_session(session_number, session_type, duration_seconds):
    db = get_db()
    start_time = datetime.now()
    end_time = start_time + timedelta(seconds=duration_seconds)
    db.execute(
        "INSERT INTO study_logs (session_number, session_type, duration_seconds, start_time, end_time) VALUES (?, ?, ?, ?, ?)",
        (session_number, session_type, duration_seconds, start_time.isoformat(), end_time.isoformat()),
    )
    db.commit()

class SessionTimer:
    def __init__(self, schedule):
        # schedule = list of (session_type, duration_in_seconds)
        self.schedule = schedule
        self.current_step = 0
        self.total_steps = len(schedule)
        self.time_remaining = schedule[0][1]
        self.running = False
        self.paused = False
        self.paused_at = None
        self.start_time = None
        self._lock = threading.Lock()
        self.logged_steps = set()  # track which steps have been logged

    def start(self):
        self.running = True
        self.start_time = time.time()
        threading.Thread(target=self._run_timer, daemon=True).start()

    def _run_timer(self):
        while self.running and self.current_step < self.total_steps:
            session_type, duration = self.schedule[self.current_step]

            # Log only once per session step
            if self.current_step not in self.logged_steps:
                log_session(self.current_step + 1, session_type, duration)
                self.logged_steps.add(self.current_step)

            while self.time_remaining > 0 and self.running:
                if self.paused:
                    time.sleep(0.5)
                    continue
                time.sleep(1)
                with self._lock:
                    self.time_remaining -= 1

            if self.running:
                self.current_step += 1
                if self.current_step < self.total_steps:
                    with self._lock:
                        self.time_remaining = self.schedule[self.current_step][1]
                        self.start_time = time.time()
                else:
                    self.running = False

    def pause(self):
        with self._lock:
            if not self.paused:
                self.paused = True
                self.paused_at = time.time()

    def resume(self):
        with self._lock:
            if self.paused:
                paused_duration = time.time() - self.paused_at
                self.start_time += paused_duration
                self.paused = False

    def stop(self):
        with self._lock:
            self.running = False
            self.paused = False

    def status(self):
        with self._lock:
            if self.current_step >= self.total_steps:
                return {"message": "Completed"}
            return {
                "session_type": self.schedule[self.current_step][0],
                "time_remaining_seconds": self.time_remaining,
                "step": self.current_step + 1,
                "total_steps": self.total_steps
            }
