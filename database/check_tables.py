from db_config import get_db_engine
from sqlalchemy import text

def check_tables():
    engine = get_db_engine()
    try:
        with engine.connect() as conn:
            # Check if tables exist
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in result]
            print("Existing tables:", tables)

            # Check geographic_areas structure
            if 'geographic_areas' in tables:
                result = conn.execute(text("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'geographic_areas'
                """))
                print("\ngeographic_areas columns:")
                for row in result:
                    print(f"- {row[0]}: {row[1]}")

            # Check population_data structure
            if 'population_data' in tables:
                result = conn.execute(text("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'population_data'
                """))
                print("\npopulation_data columns:")
                for row in result:
                    print(f"- {row[0]}: {row[1]}")

    except Exception as e:
        print(f"Error checking tables: {str(e)}")

if __name__ == "__main__":
    check_tables() 