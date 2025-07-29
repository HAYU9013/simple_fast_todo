from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Define the database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./todo.db"

# --- Start of added security and error handling ---

# Initialize variables to None. This ensures they are always defined,
# even if an error occurs during setup, preventing NameErrors later.
engine = None
SessionLocal = None
Base = None

# Basic input validation for SQLALCHEMY_DATABASE_URL.
# Although it's a constant, this demonstrates a check for its type and non-emptiness.
# XSS (Cross-Site Scripting) is not directly applicable here as this is a backend
# configuration string, not user-rendered content. However, ensuring the input
# is a valid string type helps guard against unexpected behavior or potential
# injection if this URL were dynamically sourced in a different context.
if not isinstance(SQLALCHEMY_DATABASE_URL, str) or not SQLALCHEMY_DATABASE_URL.strip():
    print("ERROR: SQLALCHEMY_DATABASE_URL is not a valid string or is empty. Database setup aborted.")
else:
    print(f"INFO: Attempting to set up database connection using URL: '{SQLALCHEMY_DATABASE_URL}'")
    try:
        # Create the database engine
        # This is a critical step and is wrapped in a try-except block to catch
        # potential issues like malformed URLs, missing drivers, or connection errors.
        engine = create_engine(
            SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
        )
        print("INFO: Database engine created successfully.")

        # Create a sessionmaker for database interactions
        # This also depends on the engine, so it's part of the protected block.
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        print("INFO: SessionLocal configured successfully.")

        # Declare a base for declarative models
        # This is generally less prone to errors but included for completeness
        # within the database setup context.
        Base = declarative_base()
        print("INFO: Declarative base initialized successfully.")

    except Exception as e:
        # Catch any exceptions that occur during the database setup process.
        # This provides robust error handling and prevents the application from crashing.
        print(f"ERROR: An unexpected error occurred during database setup: {e}")
        # In case of an error, explicitly set the variables to None.
        # This signals that the database setup failed and prevents subsequent code
        # from attempting to use uninitialized or partially initialized objects.
        engine = None
        SessionLocal = None
        Base = None

# --- End of added security and error handling ---