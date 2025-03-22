from db_config import get_db_engine
from sqlalchemy import text

def setup_database():
    """Set up the database schema."""
    engine = get_db_engine()
    
    # Create tables
    with engine.connect() as conn:
        # Create geographic_areas table
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS geographic_areas (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            type VARCHAR(50) NOT NULL,
            status VARCHAR(50) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """))
        
        # Create population_data table
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS population_data (
            id SERIAL PRIMARY KEY,
            geographic_area_id INTEGER REFERENCES geographic_areas(id) ON DELETE CASCADE,
            year INTEGER NOT NULL,
            population_count INTEGER NOT NULL,
            estimated_base INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """))
        
        # Insert sample data
        conn.execute(text("""
        INSERT INTO geographic_areas (name, type, status) VALUES
        ('Pennsylvania', 'state', 'Active'),
        ('Centre County', 'county', 'Active'),
        ('State College', 'city', 'Active')
        ON CONFLICT DO NOTHING
        """))
        
        # Get the IDs of the inserted areas
        result = conn.execute(text("SELECT id, name FROM geographic_areas")).fetchall()
        area_ids = {row[1]: row[0] for row in result}
        
        # Insert sample population data
        for area_name, area_id in area_ids.items():
            conn.execute(text("""
            INSERT INTO population_data 
            (geographic_area_id, year, population_count, estimated_base) VALUES
            (:id, 2020, 100000 + :offset, 95000),
            (:id, 2021, 102000 + :offset, 95000),
            (:id, 2022, 103500 + :offset, 95000),
            (:id, 2023, 105000 + :offset, 95000)
            ON CONFLICT DO NOTHING
            """), {"id": area_id, "offset": area_id * 1000})
        
        conn.commit()

if __name__ == "__main__":
    setup_database()
    print("Database setup completed successfully!") 