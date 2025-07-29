import logging
from sqlalchemy import Column, Integer, String, Boolean
from .database import Base

# Configure logging for this module
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Input Validation Note ---
# This code defines a SQLAlchemy ORM model. Input validation, especially for security risks
# like XSS (Cross-Site Scripting) or SQL injection (though SQLAlchemy ORM largely prevents
# direct SQL injection), is typically performed at the application layer (e.g., API endpoints,
# web forms, business logic) *before* data is passed to the ORM for storage.
#
# The ORM model itself defines the schema and data types (e.g., String, Integer). It does not
# inherently perform content validation or sanitization on user-provided values. For example,
# a 'String' column will store any string, including those containing malicious scripts,
# if not sanitized upstream.
#
# Therefore, no direct input validation can be added within this model definition itself,
# as it's purely a schema definition. Validation logic should reside where user input
# is first received and processed.
# --- End Input Validation Note ---

try:
    logger.info("Attempting to define the Todo model class.")

    class Todo(Base):
        __tablename__ = "todos"

        id = Column(Integer, primary_key=True, index=True)
        title = Column(String, index=True)
        description = Column(String, nullable=True)
        completed = Column(Boolean, default=False)

    logger.info("Todo model class defined successfully.")

except Exception as e:
    # Catch any exceptions that might occur during class definition (e.g., issues with imports, syntax errors)
    logger.critical(f"Failed to define the Todo model class: {e}", exc_info=True)
    # Depending on the application, you might want to re-raise the exception or handle it gracefully
    # For a critical error like this, re-raising might be appropriate to prevent the application from starting incorrectly.
    raise # Re-raise the exception after logging it