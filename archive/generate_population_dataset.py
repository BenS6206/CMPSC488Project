import pandas as pd
import requests
from census import Census
from us import states
import json
import time

# Census API Key
CENSUS_API_KEY = "92a2cbda1ed0d269658a64e96769fc856b10656f"
c = Census(CENSUS_API_KEY)

def get_state_cities(state_fips):
    """Get list of cities for a given state FIPS code"""
    try:
        # Get places (cities, towns, etc.) with population > 10000
        places = c.acs5.state_place(
            ('NAME', 'B01003_001E'),  # NAME and Total Population
            state_fips,
            place=None
        )
        
        # Filter and sort by population
        cities = []
        for place in places:
            if place['B01003_001E'] and place['B01003_001E'] > 10000:  # Only include places with population > 10000
                name_parts = place['NAME'].split(',')
                if len(name_parts) >= 2:
                    city = name_parts[0].strip()
                    state = name_parts[1].strip()
                    cities.append({
                        'city': city,
                        'state': state,
                        'population': place['B01003_001E']
                    })
        
        # Sort by population
        return sorted(cities, key=lambda x: x['population'], reverse=True)
    except Exception as e:
        print(f"Error getting cities for state {state_fips}: {str(e)}")
        return []

def get_detailed_city_data(city, state):
    """Get detailed census data for a city"""
    try:
        # Get demographic data
        demographics = c.acs5.state_place(
            ('NAME',
             'B01003_001E',  # Total Population
             'B19013_001E',  # Median Household Income
             'B25001_001E',  # Total Housing Units
             'B25002_002E',  # Occupied Housing Units
             'B25003_002E',  # Owner Occupied
             'B25003_003E',  # Renter Occupied
             'B01002_001E',  # Median Age
             'B02001_002E',  # White Population
             'B02001_003E',  # Black Population
             'B02001_005E',  # Asian Population
             'B03003_003E',  # Hispanic/Latino Population
             'B23025_005E',  # Unemployed Population
             'B17001_002E',  # Population Below Poverty Level
             'B25077_001E',  # Median Home Value
             'B08136_001E',  # Total Commuters
             'B15003_022E',  # Bachelor's Degree
             'B15003_023E',  # Master's Degree
             'B15003_024E',  # Professional Degree
             'B15003_025E'   # Doctorate Degree
            ),
            states.lookup(state).fips,
            place=None
        )

        if demographics:
            data = demographics[0]
            total_pop = float(data['B01003_001E']) if data['B01003_001E'] is not None else 0
            total_higher_ed = sum(filter(None, [
                data['B15003_022E'],  # Bachelor's
                data['B15003_023E'],  # Master's
                data['B15003_024E'],  # Professional
                data['B15003_025E']   # Doctorate
            ]))

            return {
                'Geographic_Area': f"{city}, {state}",
                'Total_Population': data['B01003_001E'],
                'Median_Household_Income': data['B19013_001E'],
                'Total_Housing_Units': data['B25001_001E'],
                'Occupied_Units': data['B25002_002E'],
                'Owner_Occupied': data['B25003_002E'],
                'Renter_Occupied': data['B25003_003E'],
                'Median_Age': data['B01002_001E'],
                'White_Population': data['B02001_002E'],
                'Black_Population': data['B02001_003E'],
                'Asian_Population': data['B02001_005E'],
                'Hispanic_Latino_Population': data['B03003_003E'],
                'Unemployed_Population': data['B23025_005E'],
                'Population_Below_Poverty': data['B17001_002E'],
                'Median_Home_Value': data['B25077_001E'],
                'Total_Commuters': data['B08136_001E'],
                'Higher_Education_Population': total_higher_ed,
                'White_Pct': round(float(data['B02001_002E']) / total_pop * 100, 2) if total_pop > 0 else 0,
                'Black_Pct': round(float(data['B02001_003E']) / total_pop * 100, 2) if total_pop > 0 else 0,
                'Asian_Pct': round(float(data['B02001_005E']) / total_pop * 100, 2) if total_pop > 0 else 0,
                'Hispanic_Latino_Pct': round(float(data['B03003_003E']) / total_pop * 100, 2) if total_pop > 0 else 0,
                'Poverty_Rate': round(float(data['B17001_002E']) / total_pop * 100, 2) if total_pop > 0 else 0,
                'Employment_Rate': round((1 - float(data['B23025_005E']) / total_pop) * 100, 2) if total_pop > 0 else 0,
                'Higher_Education_Rate': round(total_higher_ed / total_pop * 100, 2) if total_pop > 0 else 0,
                'Owner_Occupied_Rate': round(float(data['B25003_002E']) / float(data['B25002_002E']) * 100, 2) if float(data['B25002_002E']) > 0 else 0,
                'Renter_Occupied_Rate': round(float(data['B25003_003E']) / float(data['B25002_002E']) * 100, 2) if float(data['B25002_002E']) > 0 else 0
            }
    except Exception as e:
        print(f"Error getting data for {city}, {state}: {str(e)}")
        return None

def generate_dataset():
    """Generate a comprehensive dataset of US cities"""
    all_data = []
    
    print("Generating dataset...")
    
    # Process each state
    for state in states.STATES:
        print(f"\nProcessing {state.name}...")
        
        # Get cities in the state
        cities = get_state_cities(state.fips)
        print(f"Found {len(cities)} cities in {state.name}")
        
        # Get detailed data for each city
        for city_info in cities:
            print(f"Processing {city_info['city']}, {state.name}")
            city_data = get_detailed_city_data(city_info['city'], state.name)
            if city_data:
                all_data.append(city_data)
            time.sleep(0.1)  # Rate limiting
    
    # Create DataFrame
    df = pd.DataFrame(all_data)
    
    # Save to Excel and CSV
    print("\nSaving data...")
    df.to_excel("US_Cities_Census_Data.xlsx", index=False)
    df.to_csv("US_Cities_Census_Data.csv", index=False)
    
    print(f"\nDataset generation complete! Generated data for {len(df)} cities.")
    print("Files saved as 'US_Cities_Census_Data.xlsx' and 'US_Cities_Census_Data.csv'")

if __name__ == "__main__":
    generate_dataset() 