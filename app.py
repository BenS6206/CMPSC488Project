from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file
import requests
import pandas as pd
import os
import numpy as np
import json
from werkzeug.utils import secure_filename
import io
from geopy.distance import geodesic

app = Flask(__name__)

# Configure upload folder and allowed extensions
UPLOAD_FOLDER = 'uploads'
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB max file size
ALLOWED_EXTENSIONS = {'csv'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Read the Excel file for map page
try:
    # Load the comprehensive dataset for CSV page
    df_comprehensive = pd.read_csv("data/Census_Tract_Data.csv")
    print("\nLoaded comprehensive dataset with shape:", df_comprehensive.shape)
except Exception as e:
    print(f"Error reading comprehensive dataset: {e}")
    df_comprehensive = None

# Initialize df_map as None since we're not using the Excel file anymore
df_map = None

# State code to state name mapping
STATE_CODES = {
    '01': 'Alabama', '02': 'Alaska', '04': 'Arizona', '05': 'Arkansas',
    '06': 'California', '08': 'Colorado', '09': 'Connecticut', '10': 'Delaware',
    '11': 'District of Columbia', '12': 'Florida', '13': 'Georgia', '15': 'Hawaii',
    '16': 'Idaho', '17': 'Illinois', '18': 'Indiana', '19': 'Iowa',
    '20': 'Kansas', '21': 'Kentucky', '22': 'Louisiana', '23': 'Maine',
    '24': 'Maryland', '25': 'Massachusetts', '26': 'Michigan', '27': 'Minnesota',
    '28': 'Mississippi', '29': 'Missouri', '30': 'Montana', '31': 'Nebraska',
    '32': 'Nevada', '33': 'New Hampshire', '34': 'New Jersey', '35': 'New Mexico',
    '36': 'New York', '37': 'North Carolina', '38': 'North Dakota', '39': 'Ohio',
    '40': 'Oklahoma', '41': 'Oregon', '42': 'Pennsylvania', '44': 'Rhode Island',
    '45': 'South Carolina', '46': 'South Dakota', '47': 'Tennessee', '48': 'Texas',
    '49': 'Utah', '50': 'Vermont', '51': 'Virginia', '53': 'Washington',
    '54': 'West Virginia', '55': 'Wisconsin', '56': 'Wyoming'
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/map')
def map():
    return render_template('map.html')

@app.route('/csv')
def csv():
    if df_comprehensive is not None:
        # Convert DataFrame to JSON for the frontend
        data = df_comprehensive.to_dict(orient='records')
        return render_template('csv.html', data=data)
    return render_template('csv.html', data=[])

@app.route('/api/csv-data')
def get_csv_data():
    if df_comprehensive is not None:
        # Return the comprehensive dataset
        return jsonify(df_comprehensive.to_dict(orient='records'))
    return jsonify([])

@app.route('/api/search-csv')
def search_csv():
    if df_comprehensive is None:
        return jsonify([])
    
    query = request.args.get('q', '').lower()
    if not query:
        return jsonify([])
    
    # Search in both name and state
    results = df_comprehensive[
        df_comprehensive['Name'].str.lower().str.contains(query) |
        df_comprehensive['State'].str.lower().str.contains(query)
    ]
    
    return jsonify(results.to_dict(orient='records'))

@app.route('/download-template/<template_type>')
def download_template(template_type):
    if template_type == 'multiple':
        # Create template for multiple tracts
        template_data = {
            'state_code': ['06', '06', '06'],      # Example: California
            'county_code': ['075', '075', '075'],  # Example: San Francisco County
            'tract_code': ['000100', '000200', '000300']  # Example tracts
        }
        template_df = pd.DataFrame(template_data)
        filename = 'multiple_tracts_template.csv'
    elif template_type == 'range':
        # Create template for range of tracts
        template_data = {
            'from_state_code': ['06'],
            'from_county_code': ['075'],
            'from_tract_code': ['000100'],
            'to_state_code': ['06'],
            'to_county_code': ['075'],
            'to_tract_code': ['000300']
        }
        template_df = pd.DataFrame(template_data)
        filename = 'range_tracts_template.csv'
    else:
        return 'Invalid template type', 400
    
    # Create a BytesIO object to store the CSV
    output = io.BytesIO()
    template_df.to_csv(output, index=False)
    output.seek(0)
    
    return send_file(
        output,
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'})
        
        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'Invalid file format'})
        
        try:
            # Read the uploaded file
            df = pd.read_csv(file)
            print(f"Uploaded file columns: {df.columns.tolist()}")
            print(f"Uploaded file data:\n{df}")
            
            # Load both datasets
            comprehensive_data, tract_data = load_data()
            if comprehensive_data is None or tract_data is None:
                return jsonify({'error': 'Error loading data'})
            
            # Process based on file type
            if 'from_state_code' in df.columns:
                # Range of tracts
                from_tract = {
                    'state_code': df['from_state_code'].iloc[0],
                    'county_code': df['from_county_code'].iloc[0],
                    'tract_code': df['from_tract_code'].iloc[0]
                }
                to_tract = {
                    'state_code': df['to_state_code'].iloc[0],
                    'county_code': df['to_county_code'].iloc[0],
                    'tract_code': df['to_tract_code'].iloc[0]
                }
                print(f"Processing tract range: {from_tract} {to_tract}")
                results = find_tract_range(from_tract, to_tract, comprehensive_data, tract_data)
            else:
                # Multiple tracts
                tracts = []
                for _, row in df.iterrows():
                    tract = {
                        'state_code': row['state_code'],
                        'county_code': row['county_code'],
                        'tract_code': row['tract_code']
                    }
                    tracts.append(tract)
                print(f"Processing multiple tracts: {tracts}")
                results = find_multiple_tracts(tracts, comprehensive_data, tract_data)
            
            print(f"Results found: {len(results)}")
            if len(results) > 0:
                print(f"Sample result: {results.iloc[0]}")
                print(f"Results columns: {results.columns.tolist()}")
            
            return render_template('results.html', results=results.to_dict('records'))
            
        except Exception as e:
            print(f"Error processing file: {str(e)}")
            return jsonify({'error': f'Error processing file: {str(e)}'})
    
    return render_template('upload.html')

@app.route('/api/population-data')
def get_population_data():
    if df_map is None:
        df_map = load_map_data()
    if df_map is None:
        return jsonify({'error': 'Data not loaded'}), 500
    
    # Convert DataFrame to dictionary
    data = df_map.to_dict(orient='records')
    return jsonify(data)

@app.route('/api/search-locations')
def search_locations():
    try:
        # BEGIN DEFINITION OF DF
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
        #END DEFINITION OF DF

    except Exception as e:
        print(f"Error reading Excel file: {e}")
        df = None

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

        matching_locations = matching_locations[matching_locations['2023_Population'] >= min]

        matching_locations = matching_locations[matching_locations['2023_Population'] <= max]

        if (status):
            matching_locations = matching_locations[matching_locations['Status'].isin(statlist)]

        results = matching_locations.to_dict(orient='records')

        # Convert numpy integers to Python integers
        for result in results:
            for key, value in result.items():
                if isinstance(value, np.integer):
                    result[key] = int(value)

        return jsonify(results)
    return jsonify([])


'''@app.route('/api/search-locations')
def search_locations():
    if df_map is None:
        return jsonify([])
        
    query = request.args.get('q', '').lower()
    pop1 = request.args.get('p1', '')
    pop2 = request.args.get('p2', '')
    status = request.args.get('stat', '')

    if pop1 == 'Min':
        pop1 = '0'
    if pop2 == 'Max':
        pop2 = '1000000000000'

    pop1 = pop1.replace(',', '')
    pop2 = pop2.replace(',', '')

    try:
        pop1 = float(pop1)
        pop2 = float(pop2)
        
        # Filter based on search query and population range
        results = df_map[
            (df_map['Geographic_Area'].str.lower().str.contains(query, na=False)) &
            (df_map['2023_Population'] >= pop1) &
            (df_map['2023_Population'] <= pop2)
        ]
        
        # Sort by population and return top 10 results
        results = results.sort_values('2023_Population', ascending=False)
        
        # Convert results to dictionary format
        results_dict = results.head(10).to_dict(orient='records')
        
        # Add area code to each result
        for result in results_dict:
            result['Area_Code'] = result['Geographic_Area'].split(', ')[-1] if ', ' in result['Geographic_Area'] else 'US'
        
        return jsonify(results_dict)
        
    except Exception as e:
        print(f"Error in search: {e}")
        return jsonify([])
    '''

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
        
        if df_map is not None:
            # Look for matches in the Geographic_Area column
            matching_data = df_map[df_map['Geographic_Area'].str.contains(location_name, case=False, na=False)]
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
    if df_map is not None:
        # Extract states from the Geographic_Area column
        states = df_map[df_map['Geographic_Area'].str.contains('state', case=False, na=False)]['Geographic_Area'].tolist()
        return jsonify(sorted(states))
    return jsonify([])

@app.route('/api/counties/<state>')
def get_counties(state):
    if df_map is not None:
        # Filter counties for the selected state
        counties = df_map[
            (df_map['Geographic_Area'].str.contains('county', case=False, na=False)) &
            (df_map['Geographic_Area'].str.contains(state, case=False, na=False))
        ]['Geographic_Area'].tolist()
        return jsonify(sorted(counties))
    return jsonify([])

@app.route('/api/cities/<state>/<county>')
def get_cities(state, county):
    if df_map is not None:
        # Filter cities for the selected county and state
        cities = df_map[
            (~df_map['Geographic_Area'].str.contains('county|state', case=False, na=False)) &
            (df_map['Geographic_Area'].str.contains(f"{state}|{county}", case=False, na=False))
        ]['Geographic_Area'].tolist()
        return jsonify(sorted(cities))
    return jsonify([])

@app.route('/api/location-data/<location>')
def get_location_data(location):
    if df_map is not None:
        # Find the location data
        location_data = df_map[df_map['Geographic_Area'].str.contains(location, case=False, na=False)]
        if not location_data.empty:
            return jsonify(location_data.iloc[0].to_dict())
    return jsonify(None)

@app.route('/api/calculate-population', methods=['POST'])
def calculate_population():
    try:
        data = request.json
        if not data or 'area_relationships' not in data:
            return jsonify({'error': 'Missing area relationships data'}), 400

        total_population = 0
        contributions = []

        for relationship in data['area_relationships']:
            area_name = relationship.get('area')
            percentage = float(relationship.get('percentage', 0)) / 100

            # Find the reference area in our dataset
            reference_area = df_map[df_map['Geographic_Area'].str.contains(area_name, case=False, na=False)]
            
            if not reference_area.empty:
                area_population = reference_area.iloc[0]['2023_Population']
                contribution = area_population * percentage
                total_population += contribution
                
                contributions.append({
                    'area': area_name,
                    'percentage': percentage * 100,
                    'base_population': int(area_population),
                    'contribution': int(contribution)
                })

        result = {
            'estimated_population': int(total_population),
            'contributions': contributions,
            'calculation_method': 'Percentage-based estimation'
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/area-details/<area>')
def get_area_details(area):
    if df_map is not None:
        # Find the area data
        area_data = df_map[df_map['Geographic_Area'].str.contains(area, case=False, na=False)]
        if not area_data.empty:
            row = area_data.iloc[0]
            
            # Convert all numpy numbers to Python native types
            result = {}
            for column in df_map.columns:
                value = row[column]
                if isinstance(value, np.integer):
                    value = int(value)
                elif isinstance(value, np.floating):
                    value = float(value)
                result[column] = value
            
            return jsonify(result)
    return jsonify(None)

@app.route('/api/census-tract/<tract_id>')
def get_census_tract_data(tract_id):
    if df_map is not None:
        tract_data = df_map[df_map['Census_Tract_ID'] == tract_id]
        if not tract_data.empty:
            return jsonify(tract_data.iloc[0].to_dict())
    return jsonify(None)

def load_data():
    """Load tract data"""
    try:
        # Load tract-level data
        tract_data = pd.read_csv('data/Census_Tract_Data.csv')
        print(f"Loaded tract dataset with shape: {tract_data.shape}")
        print(f"Tract data columns: {tract_data.columns.tolist()}")
        
        # Ensure tract codes are strings with proper padding
        tract_data['state'] = tract_data['state'].astype(str).str.zfill(2)
        tract_data['county'] = tract_data['county'].astype(str).str.zfill(3)
        tract_data['tract'] = tract_data['tract'].astype(str).str.zfill(6)
        
        # Convert numeric columns to appropriate types
        numeric_cols = ['Total_Population', 'Hispanic_Latino', 'White_Alone', 'Black_Alone', 
                       'Asian_Alone', 'Pacific_Islander_Alone', 'High_School_Grad', 
                       'Bachelors_Degree', 'Median_Household_Income', 'Median_Home_Value']
        for col in numeric_cols:
            if col in tract_data.columns:
                tract_data[col] = pd.to_numeric(tract_data[col], errors='coerce')
        
        print(f"Sample tract data:\n{tract_data.head()}")
        print(f"Sample state codes: {tract_data['state'].unique()[:5]}")
        print(f"Sample county codes: {tract_data['county'].unique()[:5]}")
        print(f"Sample tract codes: {tract_data['tract'].unique()[:5]}")
        
        return tract_data, tract_data  # Return the same data twice since we only need tract data
    except Exception as e:
        print(f"Error loading data: {e}")
        return None, None

def find_multiple_tracts(tracts, comprehensive_data, tract_data):
    results = pd.DataFrame()
    for tract in tracts:
        # Format codes with proper leading zeros
        state_code = str(tract['state_code']).zfill(2)
        county_code = str(tract['county_code']).zfill(3)
        tract_code = str(tract['tract_code']).zfill(6)
        
        print(f"Looking for state: {state_code}, county: {county_code}, tract: {tract_code}")
        
        # Find matching tract with properly formatted codes
        matching_tracts = tract_data[
            (tract_data['state'].astype(str).str.zfill(2) == state_code) &
            (tract_data['county'].astype(str).str.zfill(3) == county_code) &
            (tract_data['tract'].astype(str).str.zfill(6) == tract_code)
        ]
        
        print(f"Found {len(matching_tracts)} matching tracts")
        if len(matching_tracts) > 0:
            # Get proper state name from STATE_CODES dictionary
            state_name = STATE_CODES.get(state_code, f'Unknown State ({state_code})')
            print(f"State code {state_code} maps to {state_name}")
            
            result = {
                'Area_Name': f'Tract {tract_code}, County {county_code}, State {state_code}',
                'State': state_name,
                'Tract_Code': tract_code,
                'Total_Population': matching_tracts['Total_Population'].iloc[0],
                'White_Percentage': f"{(matching_tracts['White_Alone'].iloc[0] / matching_tracts['Total_Population'].iloc[0] * 100):.2f}%",
                'Black_Percentage': f"{(matching_tracts['Black_Alone'].iloc[0] / matching_tracts['Total_Population'].iloc[0] * 100):.2f}%",
                'Hispanic_Percentage': f"{(matching_tracts['Hispanic_Latino'].iloc[0] / matching_tracts['Total_Population'].iloc[0] * 100):.2f}%",
                'Asian_Percentage': f"{(matching_tracts['Asian_Alone'].iloc[0] / matching_tracts['Total_Population'].iloc[0] * 100):.2f}%",
                'Age_Under_18_Pct': matching_tracts['Age_Under_18_Pct'].iloc[0],
                'Age_18_to_64_Pct': matching_tracts['Age_18_to_64_Pct'].iloc[0],
                'Age_65_and_Over_Pct': matching_tracts['Age_65_and_Over_Pct'].iloc[0],
                'High_School_Grad_Pct': matching_tracts['High_School_Grad_Pct'].iloc[0],
                'Bachelors_Degree_Pct': matching_tracts['Bachelors_Degree_Pct'].iloc[0],
                'Median_Household_Income': matching_tracts['Median_Household_Income'].iloc[0],
                'Median_Home_Value': matching_tracts['Median_Home_Value'].iloc[0],
                'Homeownership_Rate': matching_tracts['Homeownership_Rate'].iloc[0]
            }
            results = pd.concat([results, pd.DataFrame([result])], ignore_index=True)
        else:
            print(f"No matching tracts found for state: {state_code}, county: {county_code}, tract: {tract_code}")
    
    return results

def find_tract_range(from_tract, to_tract, comprehensive_data, tract_data):
    """
    Find areas within a range of census tracts
    Returns DataFrame with areas and their demographics
    """
    # Convert codes to strings with leading zeros
    state_code = str(int(from_tract['state_code'])).zfill(2)
    county_code = str(int(from_tract['county_code'])).zfill(3)
    from_tract_code = str(int(from_tract['tract_code'])).zfill(6)
    to_tract_code = str(int(to_tract['tract_code'])).zfill(6)
    
    print(f"Looking for tracts in state {state_code}, county {county_code}, from {from_tract_code} to {to_tract_code}")
    
    # Find tracts in the range
    matching_tracts = tract_data[
        (tract_data['state'] == state_code) &
        (tract_data['county'] == county_code) &
        (tract_data['tract'] >= from_tract_code) &
        (tract_data['tract'] <= to_tract_code)
    ]
    
    print(f"Found {len(matching_tracts)} matching tracts")
    
    results = []
    for _, area in matching_tracts.iterrows():
        results.append({
            'Area_Name': f"Tract {area['tract']}, County {area['county']}, State {area['state']}",
            'State': 'California',
            'Tract_Code': area['tract'],
            'Total_Population': area['Total_Population'],
            'White_Percentage': area['White_Alone_Pct'],
            'Black_Percentage': area['Black_Alone_Pct'],
            'Hispanic_Percentage': area['Hispanic_Latino_Pct'],
            'Asian_Percentage': area['Asian_Alone_Pct']
        })
    
    return pd.DataFrame(results)

def load_map_data():
    """Load and prepare data for the map view"""
    try:
        # Load the Excel file
        df = pd.read_excel("Combined Population Data.xlsx")
        
        # Print column names for debugging
        print("Excel file columns:", df.columns.tolist())
        
        # Rename columns for easier access
        df.columns = ['Geographic_Area', 'Status', '2020_Population', '2021_Population', '2022_Population', '2023_Population', 'Estimated_Base']
        
        # Remove header rows and reset index
        df = df.drop([0, 1]).reset_index(drop=True)
        
        # Convert population columns to numeric
        for col in ['2020_Population', '2021_Population', '2022_Population', '2023_Population', 'Estimated_Base']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Create a summary DataFrame for map view
        map_data = pd.DataFrame({
            'Geographic_Area': df['Geographic_Area'],
            'Status': df['Status'],
            'Total_Population': df['2023_Population'],
            'Estimated_Base': df['Estimated_Base'],
            '2020_Population': df['2020_Population'],
            '2021_Population': df['2021_Population'],
            '2022_Population': df['2022_Population'],
            '2023_Population': df['2023_Population']
        })
        
        # Add area code comments
        map_data['Area_Code'] = map_data['Geographic_Area'].apply(lambda x: 
            'US' if x == 'United States' else
            'AL' if ', Alabama' in x else
            'AK' if ', Alaska' in x else
            'AZ' if ', Arizona' in x else
            'AR' if ', Arkansas' in x else
            'CA' if ', California' in x else
            'CO' if ', Colorado' in x else
            'CT' if ', Connecticut' in x else
            'DE' if ', Delaware' in x else
            'FL' if ', Florida' in x else
            'GA' if ', Georgia' in x else
            'HI' if ', Hawaii' in x else
            'ID' if ', Idaho' in x else
            'IL' if ', Illinois' in x else
            'IN' if ', Indiana' in x else
            'IA' if ', Iowa' in x else
            'KS' if ', Kansas' in x else
            'KY' if ', Kentucky' in x else
            'LA' if ', Louisiana' in x else
            'ME' if ', Maine' in x else
            'MD' if ', Maryland' in x else
            'MA' if ', Massachusetts' in x else
            'MI' if ', Michigan' in x else
            'MN' if ', Minnesota' in x else
            'MS' if ', Mississippi' in x else
            'MO' if ', Missouri' in x else
            'MT' if ', Montana' in x else
            'NE' if ', Nebraska' in x else
            'NV' if ', Nevada' in x else
            'NH' if ', New Hampshire' in x else
            'NJ' if ', New Jersey' in x else
            'NM' if ', New Mexico' in x else
            'NY' if ', New York' in x else
            'NC' if ', North Carolina' in x else
            'ND' if ', North Dakota' in x else
            'OH' if ', Ohio' in x else
            'OK' if ', Oklahoma' in x else
            'OR' if ', Oregon' in x else
            'PA' if ', Pennsylvania' in x else
            'RI' if ', Rhode Island' in x else
            'SC' if ', South Carolina' in x else
            'SD' if ', South Dakota' in x else
            'TN' if ', Tennessee' in x else
            'TX' if ', Texas' in x else
            'UT' if ', Utah' in x else
            'VT' if ', Vermont' in x else
            'VA' if ', Virginia' in x else
            'WA' if ', Washington' in x else
            'WV' if ', West Virginia' in x else
            'WI' if ', Wisconsin' in x else
            'WY' if ', Wyoming' in x else
            'DC' if ', District of Columbia' in x else
            'PR' if ', Puerto Rico' in x else
            'Unknown'
        )
        
        print("Map data shape:", map_data.shape)
        print("Sample map data:", map_data.head())
        
        return map_data
    except Exception as e:
        print(f"Error loading map data: {e}")
        return None

# Load map data when app starts
df_map = load_map_data()

if __name__ == '__main__':
    app.run(debug=True, port=5000) 