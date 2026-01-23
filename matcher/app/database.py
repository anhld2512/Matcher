import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Database URL from environment
POSTGRES_USER = os.getenv("POSTGRES_USER", "anhld")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "MatKhau2026")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "cvjd_matcher")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Create engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Models
class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True)
    jd_name = Column(String, nullable=False, index=True)
    cv_name = Column(String, nullable=False, index=True)
    score = Column(Float, nullable=True)
    status = Column(String, default="pending")  # pending, completed, failed
    report_file = Column(String, nullable=True)
    task_id = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    details = Column(JSON, nullable=True)  # Store full AI analysis (strengths, weaknesses, etc.)
    # Denormalized fields for faster filtering
    jd_category = Column(String, nullable=True, index=True)  # e.g., "Backend", "Frontend"
    jd_department = Column(String, nullable=True, index=True)  # e.g., "Engineering", "Sales"


class CVMetadata(Base):
    __tablename__ = "cv_metadata"

    filename = Column(String, primary_key=True)
    upload_date = Column(DateTime, default=datetime.utcnow)
    file_size = Column(Integer)
    file_type = Column(String)
    last_evaluated_at = Column(DateTime, nullable=True)
    evaluation_count = Column(Integer, default=0)
    category = Column(String, nullable=True)  # e.g., "Backend Developer", "Frontend Developer"
    department = Column(String, nullable=True)  # e.g., "Engineering", "Design"
    email = Column(String, nullable=True)  # Candidate email
    phone = Column(String, nullable=True)  # Candidate phone number


class JDMetadata(Base):
    __tablename__ = "jd_metadata"

    filename = Column(String, primary_key=True)
    upload_date = Column(DateTime, default=datetime.utcnow)
    file_size = Column(Integer)
    usage_count = Column(Integer, default=0)
    category = Column(String, nullable=True)  # e.g., "Backend", "Frontend", "DevOps"
    department = Column(String, nullable=True)  # e.g., "Engineering", "Marketing", "Sales"
    tags = Column(JSON, nullable=True)  # List of criteria/tags e.g. ["Python", "5 years"]


class AISettings(Base):
    __tablename__ = "ai_settings"
    
    id = Column(Integer, primary_key=True)
    provider = Column(String, nullable=False)  # gemini, chatgpt, deepseek, huggingface
    model_name = Column(String, nullable=False)
    api_key = Column(Text, nullable=True)  # Encrypted API key
    host = Column(String, nullable=True)  # Legacy field, not used
    port = Column(Integer, nullable=True)  # Legacy field, not used
    is_active = Column(Integer, default=1)  # Boolean: 1=active, 0=inactive
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Database initialization
def init_db():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
