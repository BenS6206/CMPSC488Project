-- ===============================
-- COMPLETE SQL SCHEMA SCRIPT
-- ===============================

-- 1) EXTENSIONS & ENUM TYPES
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create enum types for area and status
CREATE TYPE IF NOT EXISTS area_type AS ENUM ('state', 'county', 'city', 'other');
CREATE TYPE IF NOT EXISTS status_type AS ENUM ('Estimate', 'Census', 'Other');

-- 2) SEQUENCES (for ID auto-increment)
CREATE SEQUENCE IF NOT EXISTS geographic_areas_id_seq;

-- 3) TABLE: geographic_areas
DROP TABLE IF EXISTS geographic_areas CASCADE;

CREATE TABLE IF NOT EXISTS geographic_areas (
    id INTEGER PRIMARY KEY DEFAULT nextval('geographic_areas_id_seq'),
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    type area_type NOT NULL,
    status status_type,
    parent_area_id INTEGER REFERENCES geographic_areas(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_area_name_type UNIQUE (name, type)
);

-- 4) TABLE: population_data
DROP TABLE IF EXISTS population_data CASCADE;

CREATE TABLE IF NOT EXISTS population_data (
    id SERIAL PRIMARY KEY,
    geographic_area_id INTEGER REFERENCES geographic_areas(id) ON DELETE CASCADE,
    year INTEGER NOT NULL,
    population_count INTEGER,
    estimated_base INTEGER,
    confidence_level DECIMAL(5,2),
    data_source VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_area_year UNIQUE (geographic_area_id, year)
);

-- 5) INDEXES
CREATE INDEX IF NOT EXISTS idx_geographic_areas_name 
    ON geographic_areas (name);

CREATE INDEX IF NOT EXISTS idx_geographic_areas_type 
    ON geographic_areas (type);

CREATE INDEX IF NOT EXISTS idx_population_data_year 
    ON population_data (year);

CREATE INDEX IF NOT EXISTS idx_population_data_geo_year 
    ON population_data (geographic_area_id, year);

-- 6) VIEWS

-- 6.1) Basic population summary
CREATE OR REPLACE VIEW population_summary AS
SELECT 
    ga.name AS geographic_area,
    ga.type AS area_type,
    ga.status,
    pd.year,
    pd.population_count,
    pd.estimated_base
FROM geographic_areas ga
JOIN population_data pd 
    ON ga.id = pd.geographic_area_id;

-- 6.2) Population change analysis
CREATE OR REPLACE VIEW population_change_analysis AS
SELECT 
    ga.name AS geographic_area,
    ga.type AS area_type,
    pd.year,
    pd.population_count,
    pd.population_count 
        - LAG(pd.population_count) OVER (PARTITION BY ga.id ORDER BY pd.year) 
        AS yearly_change,
    ROUND(
        (
           (pd.population_count 
            - LAG(pd.population_count) OVER (PARTITION BY ga.id ORDER BY pd.year)
           )::DECIMAL
           /
           NULLIF(LAG(pd.population_count) OVER (PARTITION BY ga.id ORDER BY pd.year), 0)
        ) * 100,
        2
    ) AS percentage_change
FROM geographic_areas ga
JOIN population_data pd 
    ON ga.id = pd.geographic_area_id
ORDER BY ga.name, pd.year;

-- 6.3) State-level summary
CREATE OR REPLACE VIEW state_population_summary AS
SELECT 
    ga.name AS state_name,
    pd.year,
    pd.population_count AS state_population,
    COUNT(DISTINCT c.id) AS number_of_counties,
    SUM(cp.population_count) AS total_county_population
FROM geographic_areas ga
JOIN population_data pd 
    ON ga.id = pd.geographic_area_id
LEFT JOIN geographic_areas c 
    ON c.parent_area_id = ga.id
LEFT JOIN population_data cp 
    ON cp.geographic_area_id = c.id 
    AND cp.year = pd.year
WHERE ga.type = 'state'
GROUP BY 
    ga.name, 
    pd.year, 
    pd.population_count
ORDER BY ga.name, pd.year;

-- 7) TRIGGERS & FUNCTIONS

-- 7.1) Timestamp auto-update function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 7.2) Triggers to update 'updated_at'
DROP TRIGGER IF EXISTS update_geographic_areas_updated_at ON geographic_areas;
CREATE TRIGGER update_geographic_areas_updated_at
    BEFORE UPDATE ON geographic_areas
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_population_data_updated_at ON population_data;
CREATE TRIGGER update_population_data_updated_at
    BEFORE UPDATE ON population_data
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 8) ANALYTICAL FUNCTIONS

-- 8.1) Compound annual growth rate
CREATE OR REPLACE FUNCTION calculate_growth_rate(
    area_id INTEGER,
    start_year INTEGER,
    end_year INTEGER
)
RETURNS DECIMAL AS $$
DECLARE
    start_pop INTEGER;
    end_pop INTEGER;
    years INTEGER;
BEGIN
    SELECT population_count 
    INTO start_pop
    FROM population_data
    WHERE geographic_area_id = area_id 
      AND year = start_year
    LIMIT 1;

    SELECT population_count 
    INTO end_pop
    FROM population_data
    WHERE geographic_area_id = area_id 
      AND year = end_year
    LIMIT 1;

    years := end_year - start_year;

    IF start_pop IS NULL OR end_pop IS NULL OR start_pop = 0 OR years <= 0 THEN
        RETURN 0;
    END IF;

    RETURN ROUND(
        (
            (end_pop::DECIMAL / start_pop) ^ (1.0 / years) - 1
        ) * 100,
        2
    );
END;
$$ LANGUAGE plpgsql;

-- 8.2) Top growing areas
CREATE OR REPLACE FUNCTION get_top_growing_areas(
    p_year INTEGER,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    area_name VARCHAR,
    area_type area_type,
    growth_rate DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ga.name,
        ga.type,
        ROUND(
            ((pd2.population_count::DECIMAL / pd1.population_count) - 1) * 100,
            2
        ) AS growth_rate
    FROM geographic_areas ga
    JOIN population_data pd1 ON ga.id = pd1.geographic_area_id
    JOIN population_data pd2 ON ga.id = pd2.geographic_area_id
    WHERE pd1.year = p_year - 1
      AND pd2.year = p_year
      AND pd1.population_count > 0
    ORDER BY growth_rate DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- 9) GRANT PERMISSIONS (adjust 'your_app_user' to match your actual role/user)
GRANT SELECT, INSERT, UPDATE ON TABLE geographic_areas TO your_app_user;
GRANT SELECT, INSERT, UPDATE ON TABLE population_data TO your_app_user;
GRANT USAGE ON SEQUENCE geographic_areas_id_seq TO your_app_user;

-- 10) COMMENTS
COMMENT ON TABLE geographic_areas IS 
    'Stores information about geographic areas (states, counties, cities, etc.)';
COMMENT ON TABLE population_data IS 
    'Stores population data for geographic areas across different years';
COMMENT ON VIEW population_summary IS 
    'Provides a simplified view of population data with geographic information';
COMMENT ON VIEW population_change_analysis IS 
    'Analyzes year-over-year population changes and growth rates';
COMMENT ON VIEW state_population_summary IS 
    'Summarizes population data at the state level with county totals';
COMMENT ON FUNCTION calculate_growth_rate IS 
    'Calculates compound annual growth rate (CAGR) between two years for a specified area';
COMMENT ON FUNCTION get_top_growing_areas IS 
    'Returns the top growing areas for a specific year based on year-over-year growth';
