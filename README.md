
# Shrek: Who Killed the King?

An interactive detective story REST API built with **Python**, **FastAPI**, and **Pydantic**.

Players take the role of Shrek and investigate the mysterious death of King Harold. They can explore story scenes, make decisions, discover clues, accuse suspects, and receive different endings depending on their investigation progress.

## Features

- **Story & Scenes:** Create, retrieve, update, and delete story scenes and choices.
- **Player Progress:** Start and manage player sessions, make story choices, and track progress.
- **Investigation:** Manage suspects and clues, discover evidence, and accuse suspects.
- **Multiple Endings:** Get different story endings based on discovered clues and accusation results.
- **Data Validation:** Pydantic schemas validate incoming requests.
- **Error Handling:** The API returns appropriate HTTP status codes for invalid or conflicting operations.

## Technologies

- Python
- FastAPI
- Pydantic
- Uvicorn
- Pytest
- In-memory data storage (Python dictionaries)

## Project Structure

```text
oneChoiceAway/
│
├── app/
│   ├── data/
│   │   ├── investigation_data.py
│   │   ├── progress_data.py
│   │   └── story_data.py
│   │
│   ├── routers/
│   │   ├── investigation.py
│   │   ├── progress.py
│   │   └── story.py
│   │
│   ├── schemas/
│   │   ├── investigation.py
│   │   ├── progress.py
│   │   └── story.py
│   │
│   ├── services/
│   │   ├── investigation_service.py
│   │   ├── progress_service.py
│   │   └── story_service.py
│   │
│   └── main.py
│
├── tests/
│   ├── test_investigation.py
│   ├── test_progress.py
│   └── test_story_api.py
│
├── requirements.txt
└── README.md
```

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
```

2. Navigate to the project directory:

```bash
cd oneChoiceAway
```

3. Create and activate a virtual environment (recommended):

```bash
python -m venv venv
```

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

4. Install dependencies:

```bash
pip install -r requirements.txt
```

## Run the Application

Start the development server:

```bash
uvicorn app.main:app --reload
```

The API will be available at:

`http://127.0.0.1:8000`

Interactive API documentation (Swagger UI):

`http://127.0.0.1:8000/docs`

## Main API Endpoints

All API endpoints use the `/api` prefix.

### Story & Scenes

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/story` | Get story information |
| GET | `/api/scenes` | Get all scenes |
| GET | `/api/scenes/{scene_id}` | Get a scene |
| POST | `/api/scenes` | Create a scene |
| PATCH | `/api/scenes/{scene_id}` | Update a scene |
| DELETE | `/api/scenes/{scene_id}` | Delete a scene |
| GET | `/api/scenes/{scene_id}/choices` | Get choices for a scene |
| POST | `/api/scenes/{scene_id}/choices` | Create a choice |
| PATCH | `/api/choices/{choice_id}` | Update a choice |
| DELETE | `/api/choices/{choice_id}` | Delete a choice |

### Investigation

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/suspects` | Get suspects |
| POST | `/api/suspects` | Create a suspect |
| GET | `/api/suspects/{suspect_id}` | Get a suspect |
| PATCH | `/api/suspects/{suspect_id}` | Update a suspect |
| DELETE | `/api/suspects/{suspect_id}` | Delete a suspect |
| GET | `/api/clues` | Get clues |
| POST | `/api/clues` | Create a clue |
| GET | `/api/clues/{clue_id}` | Get a clue |
| PATCH | `/api/clues/{clue_id}` | Update a clue |
| DELETE | `/api/clues/{clue_id}` | Delete a clue |
| POST | `/api/investigations/{session_id}/discover` | Discover a clue |
| POST | `/api/investigations/{session_id}/accuse` | Accuse a suspect |

### Player Progress & Endings

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/sessions` | Start a player session |
| GET | `/api/sessions/{session_id}` | Get player progress |
| PATCH | `/api/sessions/{session_id}` | Update player information |
| DELETE | `/api/sessions/{session_id}` | Delete a session |
| POST | `/api/sessions/{session_id}/choices` | Submit a story choice |
| GET | `/api/sessions/{session_id}/ending` | Calculate and retrieve the ending |

## Running Tests

Run the complete test suite:

```bash
pytest -v
```

The tests cover API functionality, validation, successful operations, and error scenarios.

## Data Storage

This project uses in-memory Python dictionaries to store story data, clues, suspects, and player sessions.

**Note:** Data is not stored permanently. It is reset when the application process restarts.

## Team Project

Developed as a collaborative REST API project using FastAPI and Python.