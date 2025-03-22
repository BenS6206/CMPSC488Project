from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import pandas as pd
import json
import os
from database.db_config import get_db_engine
from sqlalchemy import text
import io
import csv
import requests
import numpy as np
from datetime import datetime

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure upload directory exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Sample data for the map view
SAMPLE_DATA = {
    'areas': [
        {
            'name': 'Sample County, State',
            'status': 'Estimated',
            'estimates_base': 100000,
            'estimates': {
                '2020': 100000,
                '2021': 102000,
                '2022': 104500,
                '2023': 107000
            },
            'location': {'lat': 40.7128, 'lng': -74.0060}
        }
    ]
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'csv', 'xlsx'}

def process_file(file):
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath)
        
        # Basic validation
        required_columns = {'name', 'population', 'year', 'latitude', 'longitude'}
        if not all(col in df.columns for col in required_columns):
            raise ValueError("Missing required columns")
        
        # Convert to list of dictionaries
        data = df.to_dict('records')
        
        # Clean up
        os.remove(filepath)
        
        return {'success': True, 'data': data}
    
    except Exception as e:
        # Clean up on error
        if os.path.exists(filepath):
            os.remove(filepath)
        return {'success': False, 'error': str(e)}

@app.route('/')
def index():
    return render_template('index.html', data=SAMPLE_DATA)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400
        
        result = process_file(file)
        if result['success']:
            return jsonify({'data': result['data']})
        else:
            return jsonify({'error': result['error']}), 400
    
    return render_template('upload.html')

@app.route('/api/areas')
def get_areas():
    try:
        # For now, return sample data
        sample_data = [
            {
                'id': 1,
                'name': 'Sample County, State',
                'population': 1000000,
                'year': 2020,
                'latitude': 39.8283,
                'longitude': -98.5795
            }
        ]
        return jsonify(sample_data)
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