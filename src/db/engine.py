import os 
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


# Load variables from .env into environment
load_dotenv()

# Read the DB URL env variable
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL is None:
    raise RuntimeError("DATABASE_URL is not set.")

def get_engine():
    """
    Return a SQLAlchemy engine connected to the Postgres DB.
    """
    engine = create_engine(DATABASE_URL, echo=False, future=True)
    return engine 

def test_connection():
    """
    Smoke test.
    """
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        value = result.scalar_one()
        print(f"DB connection OK. SELECT 1 -> {value}")