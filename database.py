import sqlite3

def get_db():
    conn = sqlite3.connect("study_timer.db")
    conn.row_factory = sqlite3.Row
    return conn
