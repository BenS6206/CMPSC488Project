from enum import nonmember

from flask import Flask, render_template, request, jsonify, redirect, url_for
import requests
import pandas as pd
import os
import numpy as np
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Read the Excel file starting from row 4 and with correct column names
try:
    df = pd.read_excel("Combined Population Data.xlsx", skiprows=3)
    df.columns = ['Geographic_Area', 'Status', 'Estimated_Base', '2020_Population', 
                  '2021_Population', '2022_Population', '2023_Population']
    
    # Clean up any potential NaN values and convert numeric columns to regular Python integers
    df = df.fillna('')
    numeric_columns = ['Estimated_Base', '2020_Population', '2021_Population', '2022_Population', '2023_Population']
    for col in numeric_columns:
        df[col] = df[col].apply(lambda x: int(x) if pd.notnull(x) and x != '' else '')
    
    print("\nFirst 10 rows of the data:")
    print("===========================")
    print(df.head(10))
    
except Exception as e:
    print(f"Error reading Excel file: {e}")
    df = None

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/map')
def map():
    return render_template('map.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No file uploaded', 400
        
        file = request.files['file']
        if file.filename == '':
            return 'No file selected', 400
        
        filename = secure_filename(file.filename)
        file_ext = os.path.splitext(filename)[1].lower()
        
        try:
            if file_ext == '.csv':
                # Read CSV file
                df = pd.read_csv(file)
                
                # Verify required columns
                required_columns = ['Geographic_Area', 'Status', 'Population', 'Latitude', 'Longitude']
                missing_columns = [col for col in required_columns if col not in df.columns]
                if missing_columns:
                    return f'Missing required columns: {", ".join(missing_columns)}', 400
                
                # Convert population to integer
                df['Population'] = pd.to_numeric(df['Population'], errors='coerce').fillna(0).astype(int)
                
                # Save as Excel file for compatibility
                df.to_excel('Combined Population Data.xlsx', index=False)
                
            elif file_ext == '.geojson':
                # Read GeoJSON file
                geojson_data = json.load(file)
                
                # Extract features and create DataFrame
                features = geojson_data.get('features', [])
                data = []
                
                for feature in features:
                    properties = feature.get('properties', {})
                    geometry = feature.get('geometry', {})
                    
                    # Extract coordinates from geometry
                    coordinates = None
                    if geometry.get('type') == 'Point':
                        coordinates = geometry.get('coordinates', [])
                    elif geometry.get('type') in ['Polygon', 'MultiPolygon']:
                        # For polygons, use the centroid
                        coords = geometry.get('coordinates', [])
                        if coords:
                            # Simple centroid calculation for demonstration
                            # In production, you might want to use a proper geometry library
                            flat_coords = [coord for poly in coords for coord in poly[0]]
                            if flat_coords:
                                lat = sum(coord[1] for coord in flat_coords) / len(flat_coords)
                                lon = sum(coord[0] for coord in flat_coords) / len(flat_coords)
                                coordinates = [lon, lat]
                    
                    if coordinates:
                        data.append({
                            'Geographic_Area': properties.get('name', ''),
                            'Status': properties.get('status', ''),
                            'Population': int(properties.get('population', 0)),
                            'Latitude': coordinates[1],
                            'Longitude': coordinates[0]
                        })
                
                # Create DataFrame and save as Excel
                df = pd.DataFrame(data)
                df.to_excel('Combined Population Data.xlsx', index=False)
                
            else:
                return 'Invalid file type. Please upload a CSV or GeoJSON file.', 400
            
            return redirect(url_for('map'))
            
        except Exception as e:
            return f'Error processing file: {str(e)}', 400
    
    return render_template('upload.html')

@app.route('/api/population-data')
def get_population_data():
    if df is None:
        return jsonify({'error': 'Data not loaded'}), 500
    
    # Convert DataFrame to dictionary
    data = df.to_dict(orient='records')
    return jsonify(data)

@app.route('/api/search-locations')
def search_locations():
    query = request.args.get('q', '').lower()
    pop1 = request.args.get('p1', '')
    pop2 = request.args.get('p2', '')
    status = request.args.get('stat', '')

    statlist = status.split(',')

    if pop1 == 'Min':
        pop1 = '0'
    if pop2 == 'Max':
        pop2 = '1000000000000'

    pop1 = pop1.replace(',', '')
    pop2 = pop2.replace(',', '')

    min = int(pop1)
    max = int(pop2)

    if not query:
        return jsonify([])
    
    if df is not None:
        # Search in Geographic_Area column
        matching_locations = df[df['Geographic_Area'].str.lower().str.contains(query, na=False)]

        matching_locations = matching_locations[matching_locations['2023_Population']>=min]

        matching_locations = matching_locations[matching_locations['2023_Population']<=max]

        if(status):
            matching_locations = matching_locations[matching_locations['Status'].isin(statlist)]

        results = matching_locations.to_dict(orient='records')

        # Convert numpy integers to Python integers
        for result in results:
            for key, value in result.items():
                if isinstance(value, np.integer):
                    result[key] = int(value)
        
        return jsonify(results)
    return jsonify([])

@app.route('/api/search-location')
def search_location():
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'No query provided'}), 400

    # Search using Nominatim API
    search_url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': query,
        'format': 'json',
        'polygon_geojson': 1,
        'limit': 1
    }
    headers = {
        'User-Agent': 'YourAppName/1.0'
    }

    try:
        response = requests.get(search_url, params=params, headers=headers)
        data = response.json()
        
        if not data:
            return jsonify({'error': 'Location not found'}), 404

        result = data[0]
        
        # Try to find population data for this location
        location_name = result.get('display_name').split(',')[0].strip()
        population_data = None
        
        if df is not None:
            # Look for matches in the Geographic_Area column
            matching_data = df[df['Geographic_Area'].str.contains(location_name, case=False, na=False)]
            if not matching_data.empty:
                row = matching_data.iloc[0]
                population_data = {
                    'Geographic_Area': row['Geographic_Area'],
                    'Status': row['Status'],
                    'Estimated_Base': row['Estimated_Base'],
                    '2020_Population': row['2020_Population'],
                    '2021_Population': row['2021_Population'],
                    '2022_Population': row['2022_Population'],
                    '2023_Population': row['2023_Population']
                }
                # Convert any numpy integers to Python integers
                population_data = {k: int(v) if isinstance(v, np.integer) else v 
                                 for k, v in population_data.items()}

        return jsonify({
            'name': result.get('display_name'),
            'lat': float(result.get('lat')),
            'lon': float(result.get('lon')),
            'bbox': result.get('boundingbox'),
            'geojson': result.get('geojson'),
            'population_data': population_data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/states')
def get_states():
    if df is not None:
        # Extract states from the Geographic_Area column
        states = df[df['Geographic_Area'].str.contains('state', case=False, na=False)]['Geographic_Area'].tolist()
        return jsonify(sorted(states))
    return jsonify([])

@app.route('/api/counties/<state>')
def get_counties(state):
    if df is not None:
        # Filter counties for the selected state
        counties = df[
            (df['Geographic_Area'].str.contains('county', case=False, na=False)) &
            (df['Geographic_Area'].str.contains(state, case=False, na=False))
        ]['Geographic_Area'].tolist()
        return jsonify(sorted(counties))
    return jsonify([])

@app.route('/api/cities/<state>/<county>')
def get_cities(state, county):
    if df is not None:
        # Filter cities for the selected county and state
        cities = df[
            (~df['Geographic_Area'].str.contains('county|state', case=False, na=False)) &
            (df['Geographic_Area'].str.contains(f"{state}|{county}", case=False, na=False))
        ]['Geographic_Area'].tolist()
        return jsonify(sorted(cities))
    return jsonify([])

@app.route('/api/location-data/<location>')
def get_location_data(location):
    if df is not None:
        # Find the location data
        location_data = df[df['Geographic_Area'].str.contains(location, case=False, na=False)]
        if not location_data.empty:
            return jsonify(location_data.iloc[0].to_dict())
    return jsonify(None)

if __name__ == '__main__':
    app.run(debug=True, port=5000) 