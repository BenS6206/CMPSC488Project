import os
import pandas as pd
import shutil

def update_flask_app():
    """Update the Flask application to use the new census dataset"""
    print("Updating Flask application to use the new census dataset...")
    
    # Check if the new dataset file exists
    if os.path.exists("Major_US_Cities_Census_Data.xlsx"):
        print("Found new dataset file!")
        
        # Create a backup of the original app.py file
        if os.path.exists("app.py"):
            shutil.copy2("app.py", "app.py.backup")
            print("Created backup of app.py as app.py.backup")
        
        # Read the new dataset
        try:
            df = pd.read_excel("Major_US_Cities_Census_Data.xlsx")
            print(f"Successfully read dataset with {len(df)} cities")
            
            # Update the app.py file
            with open("app.py", "r") as f:
                app_code = f.read()
            
            # Modify the code to use the new dataset
            # 1. Update the data loading section
            old_data_loading = """# Read the Excel file starting from row 4 and with correct column names
try:
    df = pd.read_excel("Combined Population Data.xlsx", skiprows=3)
    df.columns = ['Geographic_Area', 'Status', 'Estimated_Base', '2020_Population', 
                  '2021_Population', '2022_Population', '2023_Population']
    
    # Clean up any potential NaN values and convert numeric columns to regular Python integers
    df = df.fillna('')
    numeric_columns = ['Estimated_Base', '2020_Population', '2021_Population', '2022_Population', '2023_Population']
    for col in numeric_columns:
        df[col] = df[col].apply(lambda x: int(x) if pd.notnull(x) and x != '' else '')
    
    print("\\nFirst 10 rows of the data:")
    print("===========================")
    print(df.head(10))
    
except Exception as e:
    print(f"Error reading Excel file: {e}")
    df = None"""
            
            new_data_loading = """# Read the Census data Excel file
try:
    df = pd.read_excel("Major_US_Cities_Census_Data.xlsx")
    
    # Clean up any potential NaN values
    df = df.fillna('')
    
    # Add legacy columns for compatibility with existing code
    if 'Status' not in df.columns:
        df['Status'] = 'City'
    if 'Estimated_Base' not in df.columns:
        df['Estimated_Base'] = df['Total_Population']
    if '2020_Population' not in df.columns:
        df['2020_Population'] = df['Total_Population']
    if '2021_Population' not in df.columns:
        df['2021_Population'] = df['Total_Population']
    if '2022_Population' not in df.columns:
        df['2022_Population'] = df['Total_Population']
    if '2023_Population' not in df.columns:
        df['2023_Population'] = df['Total_Population']
    
    print("\\nLoaded Census data for", len(df), "cities")
    print("Columns available:", df.columns.tolist())
    
except Exception as e:
    print(f"Error reading Census Excel file: {e}")
    df = None"""
            
            app_code = app_code.replace(old_data_loading, new_data_loading)
            
            # 2. Add a new route for census-based population calculation
            new_route = """
@app.route('/api/census-calculate', methods=['POST'])
def census_calculate_population():
    try:
        data = request.json
        if not data or 'area_relationships' not in data:
            return jsonify({'error': 'Missing area relationships data'}), 400

        total_population = 0
        contributions = []
        demographic_totals = {
            'White_Population': 0,
            'Black_Population': 0, 
            'Asian_Population': 0,
            'Native_American_Population': 0,
            'Hispanic_Latino_Population': 0
        }
        housing_totals = {
            'Total_Housing_Units': 0,
            'Owner_Occupied_Units': 0,
            'Renter_Occupied_Units': 0
        }
        income_total = 0
        income_contributors = 0

        for relationship in data['area_relationships']:
            area_name = relationship.get('area')
            percentage = float(relationship.get('percentage', 0)) / 100

            # Find the reference area in our dataset
            reference_area = df[df['Geographic_Area'].str.contains(area_name, case=False, na=False)]
            
            if not reference_area.empty:
                area_data = reference_area.iloc[0]
                area_population = area_data['Total_Population']
                contribution = area_population * percentage
                total_population += contribution
                
                # Add demographic contributions
                for key in demographic_totals.keys():
                    if key in area_data and area_data[key]:
                        demographic_totals[key] += area_data[key] * percentage
                
                # Add housing contributions
                for key in housing_totals.keys():
                    if key in area_data and area_data[key]:
                        housing_totals[key] += area_data[key] * percentage
                
                # Add income contribution (weighted average)
                if 'Median_Household_Income' in area_data and area_data['Median_Household_Income']:
                    income_total += area_data['Median_Household_Income'] * contribution
                    income_contributors += contribution
                
                contributions.append({
                    'area': area_name,
                    'percentage': percentage * 100,
                    'base_population': int(area_population),
                    'contribution': int(contribution)
                })

        # Calculate demographic percentages
        demographics = {}
        if total_population > 0:
            for key, value in demographic_totals.items():
                percentage_key = key.replace('Population', 'Percentage')
                demographics[key] = int(value)
                demographics[percentage_key] = round(value / total_population * 100, 2)
        
        # Calculate housing statistics
        housing = {}
        for key, value in housing_totals.items():
            housing[key] = int(value)
        
        if housing['Total_Housing_Units'] > 0:
            housing['Occupancy_Rate'] = round((housing['Owner_Occupied_Units'] + housing['Renter_Occupied_Units']) / 
                                              housing['Total_Housing_Units'] * 100, 2)
        
        if (housing['Owner_Occupied_Units'] + housing['Renter_Occupied_Units']) > 0:
            total_occupied = housing['Owner_Occupied_Units'] + housing['Renter_Occupied_Units']
            housing['Owner_Occupancy_Rate'] = round(housing['Owner_Occupied_Units'] / total_occupied * 100, 2)
            housing['Renter_Occupancy_Rate'] = round(housing['Renter_Occupied_Units'] / total_occupied * 100, 2)
        
        # Calculate median income
        income = 0
        if income_contributors > 0:
            income = int(income_total / income_contributors)

        result = {
            'estimated_population': int(total_population),
            'contributions': contributions,
            'demographics': demographics,
            'housing': housing,
            'median_household_income': income,
            'calculation_method': 'Census-based percentage estimation'
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500"""
            
            # Find where to insert the new route
            route_insertion_point = "@app.route('/api/area-details/<area>')"
            app_code = app_code.replace(route_insertion_point, new_route + "\n\n" + route_insertion_point)
            
            # Write the updated code back to app.py
            with open("app.py", "w") as f:
                f.write(app_code)
            
            print("Successfully updated app.py!")
        except Exception as e:
            print(f"Error updating app.py: {e}")
    else:
        print("New dataset file not found. Please run sample_census_dataset.py first.")

if __name__ == "__main__":
    update_flask_app() 