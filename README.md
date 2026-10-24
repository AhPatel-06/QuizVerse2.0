# QuizVerse Full-Stack Demo (Laptop-ready)

This version is designed for a college project demonstration. It includes a working web frontend, Python HTTP API, SQLite database, separate student/admin experiences, persistent quiz attempts, and server-side scoring. It uses only Python's standard library; no `pip install` or MySQL setup is required.

## Run on Windows (recommended)
1. Extract the ZIP to a normal folder such as `Desktop\QuizVerse_FullStack`.
2. Install Python 3.9+ if it is not already installed. During installation, tick **Add Python to PATH**.
3. Double-click **START_QUIZVERSE.bat**.
4. Keep the black terminal window open.
5. Open **http://localhost:8000** in Chrome or Edge.
6. Use one of the demo accounts below.

If double-click does not work, open Command Prompt in this folder and run:
`py -3 server.py`
If `py` is unavailable, try `python server.py`.

## Demo accounts
- Admin portal: `admin` / `Admin@123`
- Student portal: `student` / `Student@123`

These are demonstration credentials. Change them before using the project outside a controlled demo.

## Included functionality

### Student
- Sign in with role-based access.
- Browse available quizzes.
- Take timed quizzes with previous/next and question-map navigation.
- Submit answers; server calculates score and stores the attempt.
- Automatic submission when time expires.
- View correct/incorrect answers and explanations after submission.
- View personal attempt history and a database-backed leaderboard.

### Admin
- Separate admin-only dashboard.
- See student count, quiz count, total attempts and average score.
- Create/publish new quizzes with a title, category, duration and JSON questions.
- Add extra questions to an existing quiz from the separate “Add questions to an existing quiz” panel; the updated quiz is immediately available to students.
- List and delete quizzes (quizzes referenced by attempts cannot be deleted, to preserve history).
- View student accounts and recent attempts/scores.

### Backend and database
- Python standard-library HTTP server at `http://localhost:8000`.
- JSON API endpoints under `/api`.
- SQLite database saved at `data/quizverse.db`; it survives restarts.
- Passwords are stored as salted PBKDF2 hashes, not plaintext.
- Quiz answers are not sent to the student browser before submission.
- Server-side scoring checks the submitted answers against database answer keys.

## Add a quiz from the admin page
Sign in as admin, open **Create a quiz**, and use this JSON format (answer index is zero-based: 0=A, 1=B, 2=C, 3=D):

```json
[
  {
    "q": "What does CPU stand for?",
    "o": ["Central Processing Unit", "Computer Power Unit", "Core Program Utility", "Control Processing User"],
    "a": 0,
    "e": "CPU stands for Central Processing Unit."
  }
]
```

Each question must have question text, exactly four non-empty options, an answer index 0–3, and an optional explanation.

## Important demo limitations
- This is a local laptop demo, not a production-ready public service. It listens only on `127.0.0.1`, so it is intended to be shown on the same laptop.
- The built-in demo credentials are fixed for convenience. Do not expose this app to the internet with these credentials.
- Session tokens are held in server memory and are cleared if the server restarts.
- No self-registration, password reset, class/course management, remote multi-device access, or deployed hosting is included.
- SQLite is a real relational database, but it is not MySQL. If the presentation specifically names MySQL, explain that SQLite is being used for a portable demo database.
- The original Java API starter and C++ scoring module are retained in `reference_modules/`; this live website uses the Python/SQLite API so the complete flow works without multiple runtime setups.

## API endpoints
- `GET /api/health`
- `POST /api/login`
- `POST /api/logout`
- `GET /api/me`
- `GET /api/quizzes`
- `POST /api/quizzes` (admin only)
- `POST /api/quizzes/{id}/questions` (admin only; append questions to an existing quiz)
- `DELETE /api/quizzes/{id}` (admin only)
- `POST /api/attempts`
- `GET /api/my-attempts`
- `GET /api/leaderboard`
- `GET /api/admin/summary` (admin only)
