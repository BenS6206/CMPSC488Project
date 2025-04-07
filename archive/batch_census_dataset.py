import pandas as pd
import requests
import json
import time
import os
import logging
from datetime import datetime
from typing import List, Dict, Any

# Set up logging
logging.basicConfig(
    filename='census_dataset.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Census API key
API_KEY = "92a2cbda1ed0d269658a64e96769fc856b10656f"

# State abbreviations mapping
STATE_ABBREVIATIONS = {
    'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
    'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
    'DC': 'District of Columbia', 'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii',
    'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa',
    'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine',
    'MD': 'Maryland', 'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota',
    'MS': 'Mississippi', 'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska',
    'NV': 'Nevada', 'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico',
    'NY': 'New York', 'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio',
    'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island',
    'SC': 'South Carolina', 'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas',
    'UT': 'Utah', 'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington',
    'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming', 'PR': 'Puerto Rico'
}

def get_state_fips() -> Dict[str, str]:
    """Get FIPS codes for all states"""
    url = "https://api.census.gov/data/2020/dec/pl"
    params = {
        "get": "NAME",
        "for": "state:*",
        "key": API_KEY
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        state_fips = {}
        for row in data[1:]:  # Skip header row
            state_name = row[0]
            fips_code = row[1]
            state_fips[fips_code] = state_name
        return state_fips
    except Exception as e:
        logging.error(f"Error getting state FIPS codes: {e}")
        return None

def get_places_in_state(state_fips: str) -> List[Dict[str, str]]:
    """Get all places in a state with their FIPS codes"""
    url = "https://api.census.gov/data/2020/dec/pl"
    params = {
        "get": "NAME",
        "for": "place:*",
        "in": f"state:{state_fips}",
        "key": API_KEY
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        places = []
        for row in data[1:]:  # Skip header row
            place_name = row[0].split(',')[0].strip()
            place_fips = row[-1]  # Last element is the place FIPS code
            places.append({
                "name": place_name,
                "fips": place_fips
            })
        return places
    except Exception as e:
        logging.error(f"Error getting places for state {state_fips}: {e}")
        return []

def get_batch_data(state_fips: str, places: List[Dict[str, str]], batch_size: int = 20) -> List[Dict[str, Any]]:
    """Get data for a batch of places"""
    base_url = "https://api.census.gov/data/2020/dec/pl"
    all_data = []
    
    # Split places into batches
    for i in range(0, len(places), batch_size):
        batch = places[i:i + batch_size]
        place_clause = "+".join([f"place:{place['fips']}" for place in batch])
        
        params = {
            "get": "NAME,P1_001N,P1_003N,P1_004N,P1_005N,P1_006N,P1_007N,P1_008N,P1_009N,P1_010N",
            "for": place_clause,
            "in": f"state:{state_fips}",
            "key": API_KEY
        }
        
        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            for row in data[1:]:  # Skip header row
                place_name = row[0].split(',')[0].strip()
                state_name = row[0].split(',')[1].strip()
                
                place_data = {
                    "Name": place_name,
                    "State": state_name,
                    "Total Population": int(row[1]),
                    "White": int(row[2]),
                    "Black": int(row[3]),
                    "American Indian": int(row[4]),
                    "Asian": int(row[5]),
                    "Native Hawaiian": int(row[6]),
                    "Other": int(row[7]),
                    "Two or More": int(row[8]),
                    "Hispanic": int(row[9]),
                    "FIPS": f"{state_fips}{row[-1]}",
                    "Census_Data": json.dumps({
                        "population": int(row[1]),
                        "demographics": {
                            "white": int(row[2]),
                            "black": int(row[3]),
                            "native": int(row[4]),
                            "asian": int(row[5]),
                            "hawaiian": int(row[6]),
                            "other": int(row[7]),
                            "two_or_more": int(row[8]),
                            "hispanic": int(row[9])
                        }
                    })
                }
                
                # Calculate percentages
                total = place_data["Total Population"]
                if total > 0:
                    place_data["White_Percent"] = (place_data["White"] / total) * 100
                    place_data["Black_Percent"] = (place_data["Black"] / total) * 100
                    place_data["American_Indian_Percent"] = (place_data["American Indian"] / total) * 100
                    place_data["Asian_Percent"] = (place_data["Asian"] / total) * 100
                    place_data["Native_Hawaiian_Percent"] = (place_data["Native Hawaiian"] / total) * 100
                    place_data["Other_Percent"] = (place_data["Other"] / total) * 100
                    place_data["Two_or_More_Percent"] = (place_data["Two or More"] / total) * 100
                    place_data["Hispanic_Percent"] = (place_data["Hispanic"] / total) * 100
                
                all_data.append(place_data)
            
            # Rate limiting
            time.sleep(1)
            
        except Exception as e:
            logging.error(f"Error processing batch: {e}")
            time.sleep(5)  # Longer delay on error
    
    return all_data

def main():
    """Main function to generate the dataset"""
    logging.info("Starting dataset generation...")
    
    # Initialize empty DataFrame with all required columns
    columns = [
        "Name", "State", "Total Population", "White", "Black", "American Indian",
        "Asian", "Native Hawaiian", "Other", "Two or More", "Hispanic", "FIPS",
        "Census_Data", "White_Percent", "Black_Percent", "American_Indian_Percent",
        "Asian_Percent", "Native_Hawaiian_Percent", "Other_Percent",
        "Two_or_More_Percent", "Hispanic_Percent"
    ]
    df = pd.DataFrame(columns=columns)
    
    # Try to load existing data
    try:
        if os.path.exists("Comprehensive_US_Places_Census_Data.csv"):
            df = pd.read_csv("Comprehensive_US_Places_Census_Data.csv")
            logging.info(f"Loaded existing dataset with {len(df)} places")
    except Exception as e:
        logging.error(f"Error loading existing dataset: {e}")
        df = pd.DataFrame(columns=columns)
    
    # Get all state FIPS codes
    state_fips_codes = get_state_fips()
    if not state_fips_codes:
        logging.error("Failed to get state FIPS codes")
        return
    
    # Process each state
    for state_fips, state_name in state_fips_codes.items():
        # Check if state is already processed
        if not df.empty and state_name in df['State'].unique():
            logging.info(f"Skipping {state_name} (already processed)")
            continue
        
        logging.info(f"Processing {state_name}...")
        
        # Get all places in the state
        places = get_places_in_state(state_fips)
        if not places:
            logging.warning(f"No places found for {state_name}")
            continue
        
        logging.info(f"Found {len(places)} places in {state_name}")
        
        # Process in batches
        batch_data = get_batch_data(state_fips, places)
        if batch_data:
            new_df = pd.DataFrame(batch_data)
            df = pd.concat([df, new_df], ignore_index=True)
            
            # Save progress after each state
            try:
                df.to_csv("Comprehensive_US_Places_Census_Data.csv", index=False)
                df.to_excel("Comprehensive_US_Places_Census_Data.xlsx", index=False)
                logging.info(f"Saved {len(df)} places to dataset")
            except Exception as e:
                logging.error(f"Error saving dataset: {e}")
        
        # Rate limiting between states
        time.sleep(2)
    
    # Final save
    try:
        df.to_csv("Comprehensive_US_Places_Census_Data.csv", index=False)
        df.to_excel("Comprehensive_US_Places_Census_Data.xlsx", index=False)
        logging.info(f"Final dataset saved with {len(df)} places")
    except Exception as e:
        logging.error(f"Error saving final dataset: {e}")

if __name__ == "__main__":
    main() 