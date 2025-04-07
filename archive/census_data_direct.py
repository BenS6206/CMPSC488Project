import requests
import pandas as pd
import time
import json
from typing import Dict, List, Any

API_KEY = "92a2cbda1ed0d269658a64e96769fc856b10656f"

def get_state_fips() -> Dict[str, str]:
    """Get FIPS codes for all states."""
    print("Fetching state FIPS codes...")
    url = "https://api.census.gov/data/2020/dec/pl"
    params = {
        "get": "NAME",
        "for": "state:*",
        "key": API_KEY
    }
    
    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception(f"Failed to get state FIPS codes: {response.text}")
    
    data = response.json()
    # Create dictionary of state name to FIPS code
    return {row[0]: row[1] for row in data[1:]}  # Skip header row

def get_places_in_state(state_fips: str) -> List[Dict[str, Any]]:
    """Get all places (cities, towns, etc.) in a state."""
    print(f"Fetching places for state FIPS {state_fips}...")
    url = "https://api.census.gov/data/2020/dec/pl"
    params = {
        "get": "NAME,P1_001N",  # NAME and total population
        "for": "place:*",
        "in": f"state:{state_fips}",
        "key": API_KEY
    }
    
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(f"Warning: Failed to get places for state {state_fips}: {response.text}")
        return []
    
    data = response.json()
    headers = data[0]
    places = []
    
    for row in data[1:]:  # Skip header row
        place_data = dict(zip(headers, row))
        # Only include places with population > 1000
        if int(place_data.get('P1_001N', 0)) > 1000:
            places.append(place_data)
    
    return places

def get_detailed_place_data(state_fips: str, place_fips: str) -> Dict[str, Any]:
    """Get detailed demographic data for a place."""
    print(f"Fetching detailed data for place {place_fips} in state {state_fips}...")
    
    # Define the variables we want to retrieve
    variables = [
        "P1_001N",  # Total Population
        "P2_002N",  # Hispanic or Latino
        "P2_005N",  # White alone
        "P2_006N",  # Black or African American alone
        "P2_008N",  # Asian alone
        "P2_009N",  # Native Hawaiian and Other Pacific Islander alone
        "H1_001N",  # Total Housing Units
    ]
    
    url = "https://api.census.gov/data/2020/dec/pl"
    params = {
        "get": f"NAME,{','.join(variables)}",
        "for": f"place:{place_fips}",
        "in": f"state:{state_fips}",
        "key": API_KEY
    }
    
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(f"Warning: Failed to get detailed data: {response.text}")
        return {}
    
    data = response.json()
    if len(data) < 2:  # No data found
        return {}
    
    headers = data[0]
    values = data[1]
    return dict(zip(headers, values))

def generate_dataset():
    """Generate a comprehensive dataset of US cities with census data."""
    print("Starting dataset generation...")
    
    try:
        # Get all state FIPS codes
        state_fips_dict = get_state_fips()
        
        all_places_data = []
        
        for state_name, state_fips in state_fips_dict.items():
            print(f"\nProcessing state: {state_name}")
            
            # Get all places in the state
            places = get_places_in_state(state_fips)
            print(f"Found {len(places)} places in {state_name}")
            
            for place in places:
                try:
                    place_fips = place.get('place', '')
                    detailed_data = get_detailed_place_data(state_fips, place_fips)
                    
                    if detailed_data:
                        # Combine basic and detailed data
                        place_entry = {
                            'Name': detailed_data.get('NAME', ''),
                            'State': state_name,
                            'Total_Population': int(detailed_data.get('P1_001N', 0)),
                            'Hispanic_Latino': int(detailed_data.get('P2_002N', 0)),
                            'White_Alone': int(detailed_data.get('P2_005N', 0)),
                            'Black_Alone': int(detailed_data.get('P2_006N', 0)),
                            'Asian_Alone': int(detailed_data.get('P2_008N', 0)),
                            'Pacific_Islander_Alone': int(detailed_data.get('P2_009N', 0)),
                            'Total_Housing_Units': int(detailed_data.get('H1_001N', 0)),
                            'State_FIPS': state_fips,
                            'Place_FIPS': place_fips
                        }
                        
                        # Calculate percentages
                        total_pop = place_entry['Total_Population']
                        if total_pop > 0:
                            place_entry['Hispanic_Latino_Pct'] = round(place_entry['Hispanic_Latino'] / total_pop * 100, 2)
                            place_entry['White_Alone_Pct'] = round(place_entry['White_Alone'] / total_pop * 100, 2)
                            place_entry['Black_Alone_Pct'] = round(place_entry['Black_Alone'] / total_pop * 100, 2)
                            place_entry['Asian_Alone_Pct'] = round(place_entry['Asian_Alone'] / total_pop * 100, 2)
                            place_entry['Pacific_Islander_Alone_Pct'] = round(place_entry['Pacific_Islander_Alone'] / total_pop * 100, 2)
                        
                        all_places_data.append(place_entry)
                        
                        # Add a small delay to avoid hitting API rate limits
                        time.sleep(0.1)
                    
                except Exception as e:
                    print(f"Error processing place: {str(e)}")
                    continue
        
        # Create DataFrame and save to files
        if all_places_data:
            df = pd.DataFrame(all_places_data)
            
            # Save to Excel
            print("\nSaving to Excel...")
            df.to_excel("US_Cities_Census_Data.xlsx", index=False)
            
            # Save to CSV
            print("Saving to CSV...")
            df.to_csv("US_Cities_Census_Data.csv", index=False)
            
            print(f"\nSuccessfully processed {len(all_places_data)} places!")
            print("Files saved as:")
            print("- US_Cities_Census_Data.xlsx")
            print("- US_Cities_Census_Data.csv")
        else:
            print("No data was collected!")
    
    except Exception as e:
        print(f"Error generating dataset: {str(e)}")

if __name__ == "__main__":
    generate_dataset() 