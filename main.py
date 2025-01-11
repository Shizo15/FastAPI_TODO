from typing import Optional
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

app = FastAPI()

class Task(BaseModel):
    id:int
    title: str = Field(...,min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=300)
    status: str = Field(default="do wykonania", pattern="^(do wykonania|w trakcie|zakończone)$")


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


# dodać możliwośc filtrowania po statusie zadania
# zrobić optional zmienna jako parametr metody i szukać po wartości tego parametru
# i wtedy wyświetlają się taski tylko o określonym statusie

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

