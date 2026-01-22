import os
from sqlalchemy import create_engine, text
from app.database import DATABASE_URL

def migrate():
    print("Starting JD Tags migration...")
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        try:
            # Check if column exists
            result = conn.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_name='jd_metadata' AND column_name='tags'"
            ))
            if result.fetchone():
                print("Column 'tags' already exists in 'jd_metadata'. Skipping.")
            else:
                print("Adding column 'tags' (JSON) to 'jd_metadata'...")
                conn.execute(text("ALTER TABLE jd_metadata ADD COLUMN tags JSON"))
                conn.commit()
                print("Migration successful!")
        except Exception as e:
            print(f"Migration failed: {e}")
            conn.rollback()

if __name__ == "__main__":
    migrate()
