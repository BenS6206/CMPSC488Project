from flask import Flask, render_template, request, jsonify, send_file
from database.db_config import get_db_engine
import pandas as pd
from sqlalchemy import text
import io
import csv
import requests
import json

app = Flask(__name__)
engine = get_db_engine()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload')
def upload():
    return render_template('upload.html')

@app.route('/api/upload', methods=['POST'])
def handle_upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'Only CSV files are allowed'}), 400
    
    try:
        # Read CSV file
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        df = pd.read_csv(stream)
        
        # Validate required columns
        required_columns = ['Geographic_Area', 'Status', 'Estimated_Base', '2020_Population', 
                          '2021_Population', '2022_Population', '2023_Population']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return jsonify({'error': f'Missing required columns: {", ".join(missing_columns)}'}), 400
        
        # Convert to preview format
        preview_data = {
            'headers': df.columns.tolist(),
            'rows': df.head(10).to_dict('records')
        }
        
        return jsonify(preview_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/import', methods=['POST'])
def import_data():
    try:
        data = request.json
        df = pd.DataFrame(data['rows'])
        
        with engine.begin() as conn:
            # Insert each row into the database
            for _, row in df.iterrows():
                # Insert geographic area
                result = conn.execute(text("""
                INSERT INTO geographic_areas (name, type, status)
                VALUES (%(name)s, 'area', %(status)s)
                RETURNING id
                """), {
                    'name': row['Geographic_Area'],
                    'status': row['Status']
                })
                area_id = result.fetchone()[0]
                
                # Insert population data
                for year in range(2020, 2024):
                    conn.execute(text("""
                    INSERT INTO population_data 
                    (geographic_area_id, year, population_count, estimated_base)
                    VALUES (%(area_id)s, %(year)s, %(population)s, %(base)s)
                    """), {
                        'area_id': area_id,
                        'year': year,
                        'population': row[f'{year}_Population'],
                        'base': row['Estimated_Base']
                    })
        
        return jsonify({'message': 'Data imported successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download')
def download_data():
    try:
        query = """
        SELECT ga.name as Geographic_Area, ga.status as Status,
               pd.estimated_base as Estimated_Base,
               MAX(CASE WHEN pd.year = 2020 THEN pd.population_count END) as "2020_Population",
               MAX(CASE WHEN pd.year = 2021 THEN pd.population_count END) as "2021_Population",
               MAX(CASE WHEN pd.year = 2022 THEN pd.population_count END) as "2022_Population",
               MAX(CASE WHEN pd.year = 2023 THEN pd.population_count END) as "2023_Population"
        FROM geographic_areas ga
        JOIN population_data pd ON ga.id = pd.geographic_area_id
        GROUP BY ga.id, ga.name, ga.status, pd.estimated_base
        """
        df = pd.read_sql(query, engine)
        
        # Create CSV in memory
        output = io.StringIO()
        df.to_csv(output, index=False)
        
        # Create response
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name='census_data.csv'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search')
def search():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    
    try:
        # Search in our database
        db_query = """
        SELECT ga.*, 
               json_agg(json_build_object(
                   'year', pd.year,
                   'population_count', pd.population_count,
                   'estimated_base', pd.estimated_base
               )) as population_data
        FROM geographic_areas ga
        LEFT JOIN population_data pd ON ga.id = pd.geographic_area_id
        WHERE ga.name ILIKE %(query)s
        GROUP BY ga.id
        ORDER BY ga.name
        LIMIT 5
        """
        df = pd.read_sql(db_query, engine, params={'query': f'%{query}%'})
        results = df.to_dict('records')
        
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/area-boundary/<int:area_id>')
def get_area_boundary(area_id):
    try:
        # Get area name
        query = "SELECT name FROM geographic_areas WHERE id = %(id)s"
        df = pd.read_sql(query, engine, params={'id': area_id})
        if df.empty:
            return jsonify({'error': 'Area not found'}), 404
        
        area_name = df.iloc[0]['name']
        
        # Search using Nominatim API
        search_url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': area_name,
            'format': 'json',
            'polygon_geojson': 1,
            'limit': 1
        }
        headers = {
            'User-Agent': 'CensusDataExplorer/1.0'
        }
        
        response = requests.get(search_url, params=params, headers=headers)
        data = response.json()
        
        if not data:
            return jsonify({'error': 'Boundary not found'}), 404
        
        return jsonify({
            'name': area_name,
            'geojson': data[0]['geojson']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5003) 