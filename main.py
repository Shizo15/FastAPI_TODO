from typing import Optional
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

app = FastAPI()

class Task(BaseModel):
    id:int
    title: str = Field(...,min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=300)
    status: str = Field(default="do wykonania", pattern="^(do wykonania|w trakcie|zakończone)$")

class PomodoroTimer(BaseModel):
    task_id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    completed: bool = False

tasks = [
{
"id": 1,
"title": "Nauka FastAPI",
"description": "Przygotować przykładowe API z dokumentacją",
"status": "do wykonania",
}
]

pomodoro_sessions = [
{
"task_id": 1,
"start_time": "2025-01-11T12:00:00",
"end_time": "2025-01-11T12:25:00",
"completed": True,
}
]

@app.get("/tasks")
async def load_all_tasks(status_sort:Optional[str] = None):
    if status_sort:
        filtered_tasks=[]

        for task in tasks:
            if task["status"] == status_sort:
                filtered_tasks.append(task)

        if not filtered_tasks:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tasks with specified status not found")

        return filtered_tasks
    return tasks

@app.get("/tasks/{task_id}")
async def get_task_by_id(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            return task
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task with specified id not found")

@app.post("/tasks")
async def create_task(new_task: Task):
    for task in tasks:
        if new_task.title == task["title"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Task with specified title already exists")

    new_task.id = max([task["id"] for task in tasks], default=0) + 1 # id sie samo ustawia nawet jak podany jakies inne niz default
    tasks.append(
        {"id": new_task.id,
         "title": new_task.title,
         "description": new_task.description,
         "status": new_task.status
         })
    return new_task

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            tasks.remove(task)
            return {"message": f"Task with ID:{task_id} was deleted successfully"}
    #mechanism for deleting timers related with task should be added in the future :)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task with specified id doesn't exist")

@app.put("/tasks/{task_id}")
async def update_task(task_id: int, updated_task: Task):
    for task in tasks:
        if task["id"] == task_id:
            for t in tasks:
                if t["title"] ==updated_task.title:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Task with specified title already exists")
            task["title"] = updated_task.title
            task["description"] = updated_task.description
            task["status"] = updated_task.status
            return {"message": f"Task with ID:{task_id} was updated successfully", "task": task}

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task with specified id doesn't exist")

def checking_task_id(task_id):
    for task in tasks:
        if task["id"] == task_id:
            return task
    return None

def checking_task_status(task_id):
    for timer in pomodoro_sessions:
        if timer["task_id"] == task_id and not timer["completed"]:
            return timer
    return None

@app.get("/pomodoro")
async def get_pomodoro(): #w celach testowych
    return pomodoro_sessions

@app.post("/pomodoro")
async def create_pomodoro_timer(task_id:int):

    if checking_task_id(task_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task with specified id not found")

    if checking_task_status(task_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Timer for that task has been already set")

    timer_end_time=datetime.now() + timedelta(minutes=25)

    session={
        "task_id": task_id,
        "start_time": datetime.now().isoformat(),
        "end_time": timer_end_time.isoformat(),
        "completed": False,
    }
    pomodoro_sessions.append(session)
    return {"created timer":session, "all timers":pomodoro_sessions}

@app.post("/pomodoro/{task_id}/stop")
async def stop_pomodoro_timer(task_id: int):
    active_timer = None
    for timer in pomodoro_sessions:
        if timer["task_id"] == task_id and not timer["completed"]:
            end_time = datetime.fromisoformat(timer["end_time"])
            if end_time > datetime.now():
                active_timer = timer
                break

    if not active_timer:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active timer found for the given task ID")

    active_timer["completed"] = True
    #function for changing task status after stopping timer could be added

    return {"message": f"Timer for task ID {task_id} has been stopped successfully", "timer": active_timer}

@app.get("/pomodoro/stats")
async def pomodoro_stats():
    stats = {}
    total_time = 0
    for session in pomodoro_sessions:
        if session["completed"]:
            task_id = session["task_id"]
            if task_id not in stats:
                stats[task_id] = 0

            start_time=datetime.fromisoformat(session["start_time"])
            end_time=datetime.fromisoformat(session["end_time"])

            session_time = (end_time-start_time).seconds
            stats[task_id] += session_time
            total_time += session_time
    return {
        "per_task_minutes": {f"ID:{task}": round(time / 60, 2) for task, time in stats.items()},
        "total_time_minutes": round(total_time / 60, 2),
    }

