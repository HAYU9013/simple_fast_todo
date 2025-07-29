from sqlalchemy.orm import Session
from . import models, schemas

def get_todo(db: Session, todo_id: int):
    return db.query(models.Todo).filter(models.Todo.id == todo_id).first()

def get_todos(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Todo).offset(skip).limit(limit).all()

def create_todo(db: Session, todo: schemas.TodoCreate):
    db_todo = models.Todo(**todo.dict())
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo

def update_todo(db: Session, todo_id: int, todo: schemas.TodoUpdate):
    db_todo = get_todo(db, todo_id)
    if not db_todo:
        return None
    for field, value in todo.dict(exclude_unset=True).items():
        setattr(db_todo, field, value)
    db.commit()
    db.refresh(db_todo)
    return db_todo

def delete_todo(db: Session, todo_id: int):
    db_todo = get_todo(db, todo_id)
    if not db_todo:
        return None
    db.delete(db_todo)
    db.commit()
    return db_todo
