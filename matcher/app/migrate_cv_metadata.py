"""
Migration script to add metadata columns to cv_metadata table
"""
import psycopg2
import os

# Database connection
POSTGRES_USER = os.getenv("POSTGRES_USER", "anhld")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "MatKhau2026")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "cvjd_matcher")

def run_migration():
    """Add email, phone, category, department to cv_metadata"""
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )
    
    cursor = conn.cursor()
    
    try:
        print("Starting CV metadata migration...")
        
        # Add columns to cv_metadata
        print("Adding columns to cv_metadata...")
        cursor.execute("""
            ALTER TABLE cv_metadata 
            ADD COLUMN IF NOT EXISTS category VARCHAR,
            ADD COLUMN IF NOT EXISTS department VARCHAR,
            ADD COLUMN IF NOT EXISTS email VARCHAR,
            ADD COLUMN IF NOT EXISTS phone VARCHAR;
        """)
        
        conn.commit()
        print("✅ CV Metadata Migration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    run_migration()
