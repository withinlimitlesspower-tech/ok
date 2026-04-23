# Task Manager

A full-stack CRUD Task Manager with a FastAPI backend, SQLite database, and a dark-themed HTML/CSS/JS frontend.

## Features
- Create, read, update, and delete tasks
- Dark theme modern UI
- Filter tasks by completion status
- Asynchronous frontend with vanilla JavaScript

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Run the server: `python main.py`
3. Open browser at `http://localhost:8000`

## Environment Variables
- `DATABASE_URL`: SQLite database file path (default: `tasks.db`)
- `DEBUG`: Enable debug mode (default: `false`)
- `HOST`: Server host (default: `0.0.0.0`)
- `PORT`: Server port (default: `8000`)
