from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from . import database, models, schemas, crud

# 初始化資料庫
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Todo List API")

# 取得 DB session
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 建立 Todo
@app.post("/todos/", response_model=schemas.TodoInDB)
def create_todo(todo: schemas.TodoCreate, db: Session = Depends(get_db)):
    return crud.create_todo(db, todo)

# 讀取多筆 Todo
@app.get("/todos/", response_model=list[schemas.TodoInDB])
def read_todos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_todos(db, skip, limit)

# 讀取單筆 Todo
@app.get("/todos/{todo_id}", response_model=schemas.TodoInDB)
def read_todo(todo_id: int, db: Session = Depends(get_db)):
    db_todo = crud.get_todo(db, todo_id)
    if not db_todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return db_todo

# 更新 Todo
@app.put("/todos/{todo_id}", response_model=schemas.TodoInDB)
def update_todo(todo_id: int, todo: schemas.TodoUpdate, db: Session = Depends(get_db)):
    updated = crud.update_todo(db, todo_id, todo)
    if not updated:
        raise HTTPException(status_code=404, detail="Todo not found")
    return updated

# 刪除 Todo
@app.delete("/todos/{todo_id}", response_model=schemas.TodoInDB)
def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    deleted = crud.delete_todo(db, todo_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Todo not found")
    return deleted
