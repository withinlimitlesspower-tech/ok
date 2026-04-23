import os
import sqlite3
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.requests import Request
from pydantic import BaseModel, Field
from contextlib import contextmanager
import uvicorn

# Environment variables for configuration
DATABASE_URL = os.getenv("DATABASE_URL", "tasks.db")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# Pydantic models
class TaskCreate(BaseModel):
    """Schema for creating a new task."""
    title: str = Field(..., min_length=1, max_length=200, description="Task title")
    description: Optional[str] = Field(None, max_length=500, description="Optional description")
    completed: bool = Field(False, description="Completion status")

class TaskUpdate(BaseModel):
    """Schema for updating an existing task. All fields optional."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    completed: Optional[bool] = None

class TaskOut(BaseModel):
    """Schema for task response (includes id and created_at)."""
    id: int
    title: str
    description: Optional[str] = None
    completed: bool
    created_at: str

# Database setup
@contextmanager
def get_db():
    """Context manager for database connection. Handles commit/rollback and closing."""
    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row  # Access columns by name
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    """Initialize the database and create the tasks table if not exists."""
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                completed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )

# FastAPI app
app = FastAPI(title="Task Manager", debug=DEBUG)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize database on startup
@app.on_event("startup")
def on_startup():
    """Run database initialization when the application starts."""
    init_db()

# Helper to convert sqlite row to dict with correct types
def row_to_task(row: sqlite3.Row) -> dict:
    """Convert a sqlite row to a dictionary with proper boolean and string types."""
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "completed": bool(row["completed"]),
        "created_at": row["created_at"]
    }

# ---- CRUD Endpoints ----
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    """Serve the main index page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/tasks", response_model=List[TaskOut])
def list_tasks(completed: Optional[bool] = Query(None, description="Filter by completion status")):
    """
    Retrieve all tasks. Optionally filter by completion status.
    """
    try:
        with get_db() as conn:
            if completed is not None:
                cursor = conn.execute(
                    "SELECT * FROM tasks WHERE completed = ? ORDER BY created_at DESC",
                    (int(completed),)
                )
            else:
                cursor = conn.execute("SELECT * FROM tasks ORDER BY created_at DESC")
            tasks = [row_to_task(row) for row in cursor.fetchall()]
            return tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/tasks/{task_id}", response_model=TaskOut)
def get_task(task_id: int):
    """Retrieve a single task by its ID."""
    try:
        with get_db() as conn:
            cursor = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            row = cursor.fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Task not found")
            return row_to_task(row)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/tasks", response_model=TaskOut, status_code=201)
def create_task(task: TaskCreate):
    """Create a new task."""
    try:
        with get_db() as conn:
            cursor = conn.execute(
                "INSERT INTO tasks (title, description, completed) VALUES (?, ?, ?)",
                (task.title, task.description, int(task.completed))
            )
            conn.commit()
            # Retrieve the newly created task
            new_id = cursor.lastrowid
            cursor = conn.execute("SELECT * FROM tasks WHERE id = ?", (new_id,))
            row = cursor.fetchone()
            return row_to_task(row)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")

@app.put("/tasks/{task_id}", response_model=TaskOut)
def update_task(task_id: int, task: TaskUpdate):
    """Update an existing task. Only provided fields are updated."""
    try:
        with get_db() as conn:
            # Check if task exists
            cursor = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            existing = cursor.fetchone()
            if existing is None:
                raise HTTPException(status_code=404, detail="Task not found")

            # Build update fields dynamically
            updates = {}
            if task.title is not None:
                updates["title"] = task.title
            if task.description is not None:
                updates["description"] = task.description
            if task.completed is not None:
                updates["completed"] = int(task.completed)

            if not updates:
                # No fields to update, return existing
                return row_to_task(existing)

            set_clause = ", ".join(f"{key} = ?" for key in updates.keys())
            values = list(updates.values())
            values.append(task_id)
            conn.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?", values)
            conn.commit()

            # Retrieve updated task
            cursor = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            row = cursor.fetchone()
            return row_to_task(row)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update task: {str(e)}")

@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    """Delete a task by its ID."""
    try:
        with get_db() as conn:
            cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Task not found")
            conn.commit()
            return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete task: {str(e)}")

# Start server when run directly
if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)
