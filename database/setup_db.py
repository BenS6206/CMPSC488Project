from db_config import get_db_engine
from sqlalchemy import text

def setup_database():
    engine = get_db_engine()
    try:
        with engine.connect() as conn:
            # Create geographic_areas table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS geographic_areas (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    type VARCHAR(50) NOT NULL,
                    status VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))

            # Create population_data table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS population_data (
                    id SERIAL PRIMARY KEY,
                    geographic_area_id INTEGER REFERENCES geographic_areas(id),
                    year INTEGER NOT NULL,
                    population_count INTEGER,
                    estimated_base INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))

            print("Database tables created successfully!")

            # Insert some sample data
            conn.execute(text("""
                INSERT INTO geographic_areas (name, type, status)
                VALUES 
                    ('California', 'state', 'active'),
                    ('Los Angeles County', 'county', 'active'),
                    ('San Francisco', 'city', 'active')
                ON CONFLICT DO NOTHING
            """))

            conn.execute(text("""
                INSERT INTO population_data (geographic_area_id, year, population_count, estimated_base)
                VALUES 
                    (1, 2020, 39538223, 39538223),
                    (1, 2021, 39237836, 39538223),
                    (1, 2022, 39029342, 39538223)
                ON CONFLICT DO NOTHING
            """))

            conn.commit()
            print("Sample data inserted successfully!")

    except Exception as e:
        print(f"Error setting up database: {str(e)}")

if __name__ == "__main__":
    setup_database() 