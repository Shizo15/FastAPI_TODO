from typing import Optional
from fastapi import FastAPI, HTTPException, status, Depends
from datetime import datetime, timedelta
from sqlmodel import Field, Session, SQLModel, create_engine, select

app = FastAPI()

class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=300)
    status: str = Field(default="do wykonania", regex="^(do wykonania|w trakcie|zakończone)$")


class PomodoroTimer(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: int = Field(foreign_key="task.id")
    start_time: datetime
    end_time: Optional[datetime] = None
    completed: bool = Field(default=False)


DATABASE_URL = "sqlite:///Database/database.db"
engine = create_engine(DATABASE_URL)

SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


@app.get("/")
async def root():
    return "I hope it works :S"

@app.get("/tasks")
def load_all_tasks(status_sort: Optional[str] = None, session: Session = Depends(get_session)):
    query = select(Task)
    if status_sort:
        query = query.where(Task.status == status_sort)

    tasks = session.exec(query).all()
    if not tasks:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tasks with specified status not found")
    return tasks


@app.get("/tasks/{task_id}")
def get_task_by_id(task_id: int, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task with specified id not found")
    return task


@app.post("/tasks", response_model=Task)
def create_task(new_task: Task, session: Session = Depends(get_session)):
    task_exists = session.exec(select(Task).where(Task.title == new_task.title)).first()
    if task_exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Task with specified title already exists")

    session.add(new_task)
    session.commit()
    session.refresh(new_task)
    return new_task


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task with specified id doesn't exist")

    session.delete(task)
    session.commit()
    return {"message": f"Task with ID:{task_id} was deleted successfully"}


@app.put("/tasks/{task_id}")
def update_task(task_id: int, updated_task: Task, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task with specified id doesn't exist")

    duplicate_task = session.exec(select(Task).where(Task.title == updated_task.title, Task.id != task_id)).first()
    if duplicate_task:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Task with specified title already exists")

    task.title = updated_task.title
    task.description = updated_task.description
    task.status = updated_task.status

    session.add(task)
    session.commit()
    session.refresh(task)
    return {"message": f"Task with ID:{task_id} was updated successfully", "task": task}


@app.post("/pomodoro", response_model=PomodoroTimer)
def create_pomodoro_timer(task_id: int, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task with specified id not found")

    active_timer = session.exec(
        select(PomodoroTimer).where(PomodoroTimer.task_id == task_id, PomodoroTimer.completed == False)
    ).first()

    if active_timer:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Timer for that task has been already set")

    timer_end_time = datetime.now() + timedelta(minutes=25)
    new_timer = PomodoroTimer(
        task_id=task_id,
        start_time=datetime.now(),
        end_time=timer_end_time,
        completed=False,
    )
    session.add(new_timer)
    session.commit()
    session.refresh(new_timer)
    return new_timer


@app.post("/pomodoro/{task_id}/stop")
def stop_pomodoro_timer(task_id: int, session: Session = Depends(get_session)):
    active_timer = session.exec(
        select(PomodoroTimer).where(PomodoroTimer.task_id == task_id, PomodoroTimer.completed == False)
    ).first()

    if not active_timer:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="No active timer found for the given task ID")

    active_timer.completed = True
    session.add(active_timer)
    session.commit()
    session.refresh(active_timer)
    return {"message": f"Timer for task ID {task_id} has been stopped successfully", "timer": active_timer}


@app.get("/pomodoro/stats")
def pomodoro_stats(session: Session = Depends(get_session)):
    timers = session.exec(select(PomodoroTimer).where(PomodoroTimer.completed == True)).all()

    stats = {}
    total_time = 0
    for timer in timers:
        task_id = timer.task_id
        if task_id not in stats:
            stats[task_id] = 0

        session_time = (timer.end_time - timer.start_time).seconds
        stats[task_id] += session_time
        total_time += session_time

    return {
        "per_task_minutes": {f"ID:{task_id}": round(time / 60, 2) for task_id, time in stats.items()},
        "total_time_minutes": round(total_time / 60, 2),
    }
