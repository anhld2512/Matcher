"""
Database migration script to add category and department fields
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
    """Add category and department columns to tables"""
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )
    
    cursor = conn.cursor()
    
    try:
        print("Starting migration...")
        
        # Add columns to jd_metadata
        print("Adding category and department to jd_metadata...")
        cursor.execute("""
            ALTER TABLE jd_metadata 
            ADD COLUMN IF NOT EXISTS category VARCHAR,
            ADD COLUMN IF NOT EXISTS department VARCHAR;
        """)
        
        # Add columns to evaluations
        print("Adding jd_category and jd_department to evaluations...")
        cursor.execute("""
            ALTER TABLE evaluations 
            ADD COLUMN IF NOT EXISTS jd_category VARCHAR,
            ADD COLUMN IF NOT EXISTS jd_department VARCHAR;
        """)
        
        # Create indexes for faster filtering
        print("Creating indexes...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_evaluations_jd_category 
            ON evaluations(jd_category);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_evaluations_jd_department 
            ON evaluations(jd_department);
        """)
        
        conn.commit()
        print("✅ Migration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    run_migration()
