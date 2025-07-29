import logging
from sqlalchemy.orm import Session
from . import models, schemas
from pydantic import ValidationError # Import ValidationError for specific Pydantic errors

# Configure logging
# This basic configuration will log to the console.
# In a real application, you would configure handlers for files, etc.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_todo(db: Session, todo_id: int):
    """
    Retrieves a single ToDo item by its ID.
    """
    logger.info(f"Attempting to retrieve todo with ID: {todo_id}")
    try:
        # Basic input validation for todo_id
        # Ensure todo_id is an integer and positive to prevent invalid queries.
        if not isinstance(todo_id, int) or todo_id <= 0:
            logger.warning(f"Invalid todo_id provided: {todo_id}. Must be a positive integer.")
            # Returning None for invalid input, consistent with "not found"
            return None

        db_todo = db.query(models.Todo).filter(models.Todo.id == todo_id).first()
        if db_todo:
            logger.info(f"Successfully retrieved todo with ID: {todo_id}")
        else:
            logger.warning(f"Todo with ID: {todo_id} not found.")
        return db_todo
    except Exception as e:
        logger.exception(f"An unexpected error occurred while retrieving todo with ID {todo_id}.")
        return None # Return None on error

def get_todos(db: Session, skip: int = 0, limit: int = 100):
    """
    Retrieves a list of ToDo items with pagination.
    """
    logger.info(f"Attempting to retrieve todos with skip: {skip}, limit: {limit}")
    try:
        # Basic input validation for skip and limit
        # Ensure skip is a non-negative integer.
        if not isinstance(skip, int) or skip < 0:
            logger.warning(f"Invalid skip value provided: {skip}. Must be a non-negative integer. Defaulting to 0.")
            skip = 0 # Sanitize to default
        
        # Ensure limit is a positive integer.
        if not isinstance(limit, int) or limit <= 0:
            logger.warning(f"Invalid limit value provided: {limit}. Must be a positive integer. Defaulting to 100.")
            limit = 100 # Sanitize to default
        
        # Enforce a reasonable maximum limit to prevent resource exhaustion attacks.
        MAX_LIMIT = 200
        if limit > MAX_LIMIT:
            logger.warning(f"Requested limit {limit} exceeds maximum allowed ({MAX_LIMIT}). Setting to {MAX_LIMIT}.")
            limit = MAX_LIMIT

        todos = db.query(models.Todo).offset(skip).limit(limit).all()
        logger.info(f"Successfully retrieved {len(todos)} todos.")
        return todos
    except Exception as e:
        logger.exception(f"An unexpected error occurred while retrieving todos with skip {skip}, limit {limit}.")
        return [] # Return empty list on error for consistency

def create_todo(db: Session, todo: schemas.TodoCreate):
    """
    Creates a new ToDo item.
    """
    logger.info(f"Attempting to create a new todo.")
    try:
        # Pydantic models (schemas.TodoCreate) handle their own validation
        # based on their defined types and constraints.
        # If the input 'todo' object does not conform to schemas.TodoCreate,
        # Pydantic will typically raise a ValidationError when it's instantiated
        # or when .dict() is called.
        if not isinstance(todo, schemas.TodoCreate):
            logger.warning(f"Invalid todo object provided for creation: {type(todo)}. Expected schemas.TodoCreate.")
            return None

        # For XSS and other string-based security risks, it's recommended
        # that string fields within schemas.TodoCreate (e.g., title, description)
        # are validated/sanitized either within the Pydantic model definition
        # (e.g., using regex patterns, custom validators) or at the API layer
        # before passing the data to this function.
        # This function assumes the Pydantic model has already performed
        # necessary string validation/sanitization.
        
        db_todo = models.Todo(**todo.dict())
        db.add(db_todo)
        db.commit()
        db.refresh(db_todo)
        logger.info(f"Successfully created todo with ID: {db_todo.id}")
        return db_todo
    except ValidationError as e:
        # Catch Pydantic validation errors specifically
        logger.error(f"Input validation error during todo creation: {e.errors()}")
        db.rollback() # Rollback any pending changes
        return None
    except Exception as e:
        db.rollback() # Rollback in case of any other error during commit
        logger.exception(f"An unexpected error occurred while creating a todo.")
        return None

def update_todo(db: Session, todo_id: int, todo: schemas.TodoUpdate):
    """
    Updates an existing ToDo item.
    """
    logger.info(f"Attempting to update todo with ID: {todo_id}.")
    try:
        # Basic input validation for todo_id
        if not isinstance(todo_id, int) or todo_id <= 0:
            logger.warning(f"Invalid todo_id provided for update: {todo_id}. Must be a positive integer.")
            return None

        # Pydantic model validation is handled by the model itself.
        if not isinstance(todo, schemas.TodoUpdate):
            logger.warning(f"Invalid todo object provided for update: {type(todo)}. Expected schemas.TodoUpdate.")
            return None

        db_todo = get_todo(db, todo_id) # This call is already wrapped with logging/error handling
        if not db_todo:
            logger.warning(f"Todo with ID: {todo_id} not found for update.")
            return None

        # Similar to create_todo, XSS and other string-based validation
        # should ideally be handled within the Pydantic model definition
        # or at the API layer.
        update_data = todo.dict(exclude_unset=True)
        if not update_data:
            logger.info(f"No fields provided for update for todo ID: {todo_id}. No changes made.")
            return db_todo # Return original if no updates requested

        for field, value in update_data.items():
            setattr(db_todo, field, value)
            logger.debug(f"Updating field '{field}' to '{value}' for todo ID: {todo_id}")

        db.commit()
        db.refresh(db_todo)
        logger.info(f"Successfully updated todo with ID: {todo_id}.")
        return db_todo
    except ValidationError as e:
        logger.error(f"Input validation error during todo update for ID {todo_id}: {e.errors()}")
        db.rollback()
        return None
    except Exception as e:
        db.rollback() # Rollback in case of any other error during commit
        logger.exception(f"An unexpected error occurred while updating todo with ID {todo_id}.")
        return None

def delete_todo(db: Session, todo_id: int):
    """
    Deletes a ToDo item.
    """
    logger.info(f"Attempting to delete todo with ID: {todo_id}.")
    try:
        # Basic input validation for todo_id
        if not isinstance(todo_id, int) or todo_id <= 0:
            logger.warning(f"Invalid todo_id provided for deletion: {todo_id}. Must be a positive integer.")
            return None

        db_todo = get_todo(db, todo_id) # This call is already wrapped with logging/error handling
        if not db_todo:
            logger.warning(f"Todo with ID: {todo_id} not found for deletion.")
            return None

        db.delete(db_todo)
        db.commit()
        logger.info(f"Successfully deleted todo with ID: {todo_id}.")
        return db_todo
    except Exception as e:
        db.rollback() # Rollback in case of any error during commit
        logger.exception(f"An unexpected error occurred while deleting todo with ID {todo_id}.")
        return None