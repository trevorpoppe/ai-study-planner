# AI-Study-Planner

---

The AI Study Planner is a productivity tool designed to help students structure focused study sessions with built-in break periods based on customizable preferences. The tool includes a web-based user interface and backend timer logic, enabling students to personalize their work/rest cycles and improve time management. It leverages Python, FastAPI, and a lightweight timer engine to alternate between study and break intervals.

---

# Folder Structure

```plaintext
ai-study-planner/
├── main.py                # FastAPI backend
├── timer.py               # Timer logic
├── static/
│   └── study-timer.html   # Frontend UI
├── .env                   # Environment variables
├── requirements.txt       # Python dependencies
└── README.md              # Documentation
```
---

# main.py Overview

The main.py file is the core API server for the application. Here's a breakdown of its key components:

- Imports and Environment Setup
  - Loads environment variables using dotenv
  - Sets up OpenAI API key for future AI-enhanced features
- FastAPI Configuration
  - Adds CORS middleware to allow cross-origin requests from the frontend
  - Serves static HTML files from the static/ directory
- Timer Logic
  - Initializes a global SessionTimer instance (imported from timer.py)
  - Provides endpoints for:
    - Serving the frontend (GET /)
    - Accepting user input and processing study session data (POST /generate schedule, or similar)
    - Future enhancement: AI-generated study schedule recommendations

---

# How to Use UI

1. Download the Project
  - Clone the repository: git clone https://github.com/your-username/ai-study-planner.git
cd ai-study-planner

2. Launch App
  - Start FastAPI server: uvicorn main:app --reload

3. In browser, go to http://127.0.0.1:8000

4. Set Your Preferences & Start
  - Input your desired study and break durations.
  - Use the timer controls to begin your session.
  - The timer will automatically alternate between focus and rest periods.






