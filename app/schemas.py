import logging
import re
from pydantic import BaseModel, validator, ValidationError
from typing import Optional

# Configure basic logging. If no logging setup exists, this provides a default.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Basic XSS pattern for input validation.
# This is a simple check and not a comprehensive XSS prevention mechanism.
# For robust XSS protection, consider using dedicated sanitization libraries
# (e.g., Bleach) or a strict allow-list approach for HTML content.
XSS_PATTERN = re.compile(r'<script.*?>|onerror=|javascript:|data:text/html', re.IGNORECASE)

try:
    class TodoBase(BaseModel):
        title: str
        description: Optional[str] = None

        @validator('title', 'description', pre=True, always=True)
        def validate_no_xss(cls, v):
            """
            Validator to check for basic XSS patterns in string fields.
            This validator runs before Pydantic's default type validation (due to pre=True).
            Raises ValueError if potential XSS content is detected.
            """
            if v is None:  # Allow None for Optional fields
                return v
            if not isinstance(v, str):
                # If it's not a string, let Pydantic's default validation handle the type error.
                # Log a warning if an unexpected type reaches this validator.
                logging.warning(f"Non-string type '{type(v).__name__}' passed to XSS validator for field: '{v}'")
                return v

            if XSS_PATTERN.search(v):
                logging.warning(f"Potential XSS detected in field: '{v}'")
                raise ValueError("Input contains potentially malicious content.")
            return v

    class TodoCreate(TodoBase):
        pass

    class TodoUpdate(BaseModel):
        title: Optional[str] = None
        description: Optional[str] = None
        completed: Optional[bool] = None

        @validator('title', 'description', pre=True, always=True)
        def validate_no_xss_update(cls, v):
            """
            Validator to check for basic XSS patterns in string fields for updates.
            This validator runs before Pydantic's default type validation (due to pre=True).
            Raises ValueError if potential XSS content is detected.
            """
            if v is None:  # Allow None for Optional fields
                return v
            if not isinstance(v, str):
                # If it's not a string, let Pydantic's default validation handle the type error.
                logging.warning(f"Non-string type '{type(v).__name__}' passed to XSS validator for update field: '{v}'")
                return v

            if XSS_PATTERN.search(v):
                logging.warning(f"Potential XSS detected in update field: '{v}'")
                raise ValueError("Input contains potentially malicious content.")
            return v

    class TodoInDB(TodoBase):
        id: int
        completed: bool

        class Config:
            orm_mode = True

    # Log successful definition of models
    logging.info("Pydantic models defined successfully.")

except Exception as e:
    # Catch any unexpected exceptions that occur during the definition of the models.
    # This is a broad catch-all for issues during module loading/class creation.
    logging.error(f"An unexpected error occurred during Pydantic model definition: {e}", exc_info=True)
    # Depending on the application's needs, you might want to re-raise the exception
    # or handle it more gracefully if the application can proceed without these models.