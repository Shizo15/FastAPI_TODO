from typing import Optional
from fastapi import FastAPI, HTTPException, status ,Query
from pydantic import BaseModel, Field

app = FastAPI()

class Task(BaseModel):
    id:int
    title: str = Field(...,min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=300)
    status: str = Field(default="do wykonania", pattern="^(do wykonania|w trakie|zakończone)$")


tasks = [
{
"id": 1,
"title": "Nauka FastAPI",
"description": "Przygotować przykładowe API z dokumentacją",
"status": "TODO",
}
]

@app.get("/tasks")
async def load_all_tasks():
    return tasks

@app.get("/tasks/{task_id}")
async def get_task_by_id(task_id: int):
    return tasks[task_id]

@app.post("/tasks")
async def create_task(new_task: Task):
    for task in tasks:
        if new_task.title == task["title"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Task with specified title already exists")

    new_task.id = len(tasks) + 1
    tasks.append({"id": new_task.id, "title": new_task.title, "description": new_task.description, "status": new_task.status})
    return new_task


@app.delete("/")
async def delete_task():
    return "DELETED"

@app.put("/")
async def update_task():
    return "UPDATED"


