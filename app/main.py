import logging
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

# Assuming . import database, models, schemas, crud are available and correctly set up
from . import database, models, schemas, crud

# --- Logging Configuration ---
# Configure logging at the top of the file
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Database Initialization ---
# 初始化資料庫
try:
    models.Base.metadata.create_all(bind=database.engine)
    logger.info("Database tables created or already exist.")
except SQLAlchemyError as e:
    logger.critical(f"Failed to initialize database due to SQLAlchemy error: {e}", exc_info=True)
    # In a production environment, you might want to exit the application if DB init fails critically
    # import sys; sys.exit(1)
except Exception as e:
    logger.critical(f"An unexpected error occurred during database initialization: {e}", exc_info=True)
    # import sys; sys.exit(1)

app = FastAPI(title="Todo List API")

# 取得 DB session
def get_db():
    db = database.SessionLocal()
    try:
        logger.debug("Attempting to get database session.")
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Database error during session yield: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database connection error.")
    except Exception as e:
        logger.error(f"An unexpected error occurred during database session yield: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while managing database session.")
    finally:
        logger.debug("Closing database session.")
        db.close()

# 建立 Todo
@app.post("/todos/", response_model=schemas.TodoInDB)
def create_todo(todo: schemas.TodoCreate, db: Session = Depends(get_db)):
    logger.info(f"Received request to create todo: {todo.title}")
    # Input validation: FastAPI and Pydantic automatically handle type validation
    # for 'todo' (schemas.TodoCreate). If the input data does not conform to the
    # schema (e.g., wrong types, missing required fields), FastAPI will return
    # a 422 Unprocessable Entity error automatically.
    # For XSS and other injection risks, the primary defense for an API is
    # proper output encoding on the client side when displaying the data.
    # If storing sanitized data is a strict requirement, a library like 'bleach'
    # could be used here, but it would alter the original input data.
    try:
        db_todo = crud.create_todo(db, todo)
        logger.info(f"Successfully created todo with ID: {db_todo.id}")
        return db_todo
    except IntegrityError as e:
        logger.error(f"Integrity error when creating todo (e.g., duplicate entry): {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A todo with similar details might already exist or a database constraint was violated.")
    except SQLAlchemyError as e:
        logger.error(f"Database error when creating todo: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database operation failed during todo creation.")
    except Exception as e:
        logger.error(f"An unexpected error occurred while creating todo: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")

# 讀取多筆 Todo
@app.get("/todos/", response_model=list[schemas.TodoInDB])
def read_todos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    logger.info(f"Received request to read todos with skip={skip}, limit={limit}")
    # Input validation: FastAPI automatically validates 'skip' and 'limit' as integers.
    # If they are not integers, FastAPI returns a 422 Unprocessable Entity.
    try:
        todos = crud.get_todos(db, skip, limit)
        logger.info(f"Successfully retrieved {len(todos)} todos.")
        return todos
    except SQLAlchemyError as e:
        logger.error(f"Database error when reading todos: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database operation failed during todo retrieval.")
    except Exception as e:
        logger.error(f"An unexpected error occurred while reading todos: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")

# 讀取單筆 Todo
@app.get("/todos/{todo_id}", response_model=schemas.TodoInDB)
def read_todo(todo_id: int, db: Session = Depends(get_db)):
    logger.info(f"Received request to read todo with ID: {todo_id}")
    # Input validation: FastAPI automatically validates 'todo_id' as an integer.
    # If it's not an integer, FastAPI returns a 422 Unprocessable Entity.
    try:
        db_todo = crud.get_todo(db, todo_id)
        if not db_todo:
            logger.warning(f"Todo with ID {todo_id} not found.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
        logger.info(f"Successfully retrieved todo with ID: {todo_id}")
        return db_todo
    except HTTPException: # Re-raise FastAPI's own HTTPExceptions (like 404)
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error when reading todo ID {todo_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database operation failed during single todo retrieval.")
    except Exception as e:
        logger.error(f"An unexpected error occurred while reading todo ID {todo_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")

# 更新 Todo
@app.put("/todos/{todo_id}", response_model=schemas.TodoInDB)
def update_todo(todo_id: int, todo: schemas.TodoUpdate, db: Session = Depends(get_db)):
    logger.info(f"Received request to update todo with ID: {todo_id}")
    # Input validation: FastAPI validates 'todo_id' as an integer and 'todo'
    # against schemas.TodoUpdate.
    try:
        updated = crud.update_todo(db, todo_id, todo)
        if not updated:
            logger.warning(f"Todo with ID {todo_id} not found for update.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
        logger.info(f"Successfully updated todo with ID: {todo_id}")
        return updated
    except HTTPException: # Re-raise FastAPI's own HTTPExceptions (like 404)
        raise
    except IntegrityError as e:
        logger.error(f"Integrity error when updating todo ID {todo_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Update would violate a unique constraint.")
    except SQLAlchemyError as e:
        logger.error(f"Database error when updating todo ID {todo_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database operation failed during todo update.")
    except Exception as e:
        logger.error(f"An unexpected error occurred while updating todo ID {todo_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")

# 刪除 Todo
@app.delete("/todos/{todo_id}", response_model=schemas.TodoInDB)
def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    logger.info(f"Received request to delete todo with ID: {todo_id}")
    # Input validation: FastAPI validates 'todo_id' as an integer.
    try:
        deleted = crud.delete_todo(db, todo_id)
        if not deleted:
            logger.warning(f"Todo with ID {todo_id} not found for deletion.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
        logger.info(f"Successfully deleted todo with ID: {todo_id}")
        return deleted
    except HTTPException: # Re-raise FastAPI's own HTTPExceptions (like 404)
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error when deleting todo ID {todo_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database operation failed during todo deletion.")
    except Exception as e:
        logger.error(f"An unexpected error occurred while deleting todo ID {todo_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")