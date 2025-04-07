import requests
import pandas as pd
import time
import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Any
from urllib.parse import quote
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Set up logging
logging.basicConfig(
    filename='comprehensive_census_dataset.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Configure API settings
API_KEY = os.getenv('CENSUS_API_KEY', "92a2cbda1ed0d269658a64e96769fc856b10656f")
BASE_URL = "https://api.census.gov/data/2020/dec/pl"
RATE_LIMIT_DELAY = 0.5  # seconds between requests

# Configure requests session with retries
session = requests.Session()
retries = Retry(
    total=5,
    backoff_factor=0.5,
    status_forcelist=[500, 502, 503, 504]
)
session.mount('https://', HTTPAdapter(max_retries=retries))

# Dictionary of state abbreviations
STATE_ABBR = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", "California": "CA",
    "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE", "Florida": "FL", "Georgia": "GA",
    "Hawaii": "HI", "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA",
    "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS", "Missouri": "MO",
    "Montana": "MT", "Nebraska": "NE", "Nevada": "NV", "New Hampshire": "NH", "New Jersey": "NJ",
    "New Mexico": "NM", "New York": "NY", "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH",
    "Oklahoma": "OK", "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT", "Vermont": "VT",
    "Virginia": "VA", "Washington": "WA", "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY",
    "District of Columbia": "DC", "Puerto Rico": "PR"
}

def make_api_request(url: str, params: Dict[str, str], retry_count: int = 3) -> Dict:
    """Make an API request with retries and proper error handling."""
    for attempt in range(retry_count):
        try:
            time.sleep(RATE_LIMIT_DELAY)  # Rate limiting
            response = session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"API request failed (attempt {attempt + 1}/{retry_count}): {str(e)}")
            if attempt == retry_count - 1:
                raise
            time.sleep(RATE_LIMIT_DELAY * (attempt + 1))  # Exponential backoff
    return None

def get_state_fips() -> Dict[str, str]:
    """Get FIPS codes for all states."""
    logging.info("Fetching state FIPS codes...")
    params = {
        "get": "NAME",
        "for": "state:*",
        "key": API_KEY
    }
    
    try:
        data = make_api_request(BASE_URL, params)
        if not data or len(data) < 2:
            raise ValueError("No state FIPS data received")
        return {row[0]: row[1] for row in data[1:]}  # Skip header row
    except Exception as e:
        logging.error(f"Failed to get state FIPS codes: {str(e)}")
        raise

def get_places_in_state(state_fips: str) -> List[Dict[str, Any]]:
    """Get all places (cities, towns, etc.) in a state."""
    logging.info(f"Fetching places for state FIPS {state_fips}...")
    params = {
        "get": "NAME,P1_001N",  # NAME and total population
        "for": "place:*",
        "in": f"state:{state_fips}",
        "key": API_KEY
    }
    
    try:
        data = make_api_request(BASE_URL, params)
        if not data:
            return []
        
        headers = data[0]
        places = []
        
        for row in data[1:]:  # Skip header row
            place_data = dict(zip(headers, row))
            # Only include places with population > 1000
            if int(place_data.get('P1_001N', 0)) > 1000:
                places.append(place_data)
        
        logging.info(f"Found {len(places)} places in state {state_fips}")
        return places
    except Exception as e:
        logging.error(f"Error fetching places for state {state_fips}: {str(e)}")
        return []

def get_detailed_place_data(state_fips: str, place_fips: str) -> Dict[str, Any]:
    """Get detailed demographic data for a place."""
    logging.info(f"Fetching detailed data for place {place_fips} in state {state_fips}...")
    
    variables = [
        "P1_001N",  # Total Population
        "P2_002N",  # Hispanic or Latino
        "P2_005N",  # White alone
        "P2_006N",  # Black or African American alone
        "P2_008N",  # Asian alone
        "P2_009N",  # Native Hawaiian and Other Pacific Islander alone
        "H1_001N",  # Total Housing Units
    ]
    
    params = {
        "get": f"NAME,{','.join(variables)}",
        "for": f"place:{place_fips}",
        "in": f"state:{state_fips}",
        "key": API_KEY
    }
    
    try:
        data = make_api_request(BASE_URL, params)
        if not data or len(data) < 2:
            logging.warning(f"No data found for place {place_fips} in state {state_fips}")
            return {}
        
        headers = data[0]
        values = data[1]
        return dict(zip(headers, values))
    except Exception as e:
        logging.error(f"Error fetching detailed data for place {place_fips} in state {state_fips}: {str(e)}")
        return {}

def save_checkpoint(data: List[Dict], state: str, checkpoint_file: str = "census_checkpoint.json"):
    """Save progress to a checkpoint file"""
    checkpoint = {
        "last_state": state,
        "last_update": datetime.now().isoformat(),
        "data": data
    }
    try:
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint, f)
        logging.info(f"Successfully saved checkpoint for state {state}")
    except Exception as e:
        logging.error(f"Failed to save checkpoint for state {state}: {str(e)}")

def load_checkpoint(checkpoint_file: str = "census_checkpoint.json") -> Dict:
    """Load progress from checkpoint file"""
    try:
        if os.path.exists(checkpoint_file):
            with open(checkpoint_file, 'r') as f:
                checkpoint = json.load(f)
            logging.info(f"Loaded checkpoint from {checkpoint_file}")
            return checkpoint
        logging.info("No checkpoint file found")
    except Exception as e:
        logging.error(f"Failed to load checkpoint: {str(e)}")
    return None

def save_dataset(data: List[Dict], prefix: str = "Census_Data"):
    """Save dataset to both CSV and Excel formats with error handling"""
    if not data:
        logging.warning("No data to save!")
        return

    try:
        # Convert to DataFrame
        df = pd.DataFrame(data)
        logging.info(f"Converting {len(data)} records to DataFrame")
        
        # Create directory if it doesn't exist
        if not os.path.exists('data'):
            os.makedirs('data')
        
        # Save to CSV first (it's faster and more reliable)
        csv_file = f"data/{prefix}.csv"
        df.to_csv(csv_file, index=False)
        logging.info(f"Successfully saved CSV file: {csv_file}")
        
        # Then try to save to Excel
        excel_file = f"data/{prefix}.xlsx"
        try:
            df.to_excel(excel_file, index=False)
            logging.info(f"Successfully saved Excel file: {excel_file}")
        except Exception as excel_error:
            logging.warning(f"Could not save Excel file due to: {str(excel_error)}")
            excel_file = None
        
        return excel_file, csv_file
    except Exception as e:
        logging.error(f"Failed to save dataset: {str(e)}")
        return None, None

def generate_comprehensive_dataset():
    """Generate a comprehensive dataset of US places with census data."""
    logging.info("Starting comprehensive dataset generation...")
    
    try:
        # Check for existing checkpoint
        checkpoint = load_checkpoint()
        all_places_data = []
        start_state = None
        
        if checkpoint:
            all_places_data = checkpoint["data"]
            start_state = checkpoint["last_state"]
            logging.info(f"Resuming from checkpoint after state: {start_state}")
            logging.info(f"Loaded {len(all_places_data)} existing places")
        
        # Get all state FIPS codes
        state_fips_dict = get_state_fips()
        total_states = len(state_fips_dict)
        
        # Convert to list and sort for consistent ordering
        states_to_process = sorted(state_fips_dict.items())
        
        # If resuming, find where to start
        if start_state:
            start_idx = next((i for i, (state, _) in enumerate(states_to_process) 
                            if state == start_state), -1) + 1
            states_to_process = states_to_process[start_idx:]
        
        places_processed = 0
        for idx, (state_name, state_fips) in enumerate(states_to_process, 1):
            logging.info(f"\nProcessing state {idx}/{total_states}: {state_name}")
            
            # Get all places in the state
            places = get_places_in_state(state_fips)
            
            if not places:
                logging.warning(f"No places found in {state_name}, skipping...")
                continue
            
            logging.info(f"Processing {len(places)} places in {state_name}")
            
            for place_idx, place in enumerate(places, 1):
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
                        places_processed += 1
                        
                        # Save data every 10 places
                        if places_processed % 10 == 0:
                            logging.info(f"Processed {place_idx}/{len(places)} places in {state_name}")
                            logging.info(f"Total places processed: {places_processed}")
                            excel_file, csv_file = save_dataset(all_places_data)
                            if csv_file:
                                logging.info(f"Saved progress to {csv_file}")
                            save_checkpoint(all_places_data, state_name)
                    
                except Exception as e:
                    logging.error(f"Error processing place {place.get('NAME', 'Unknown')}: {str(e)}")
                    continue
            
            # Save checkpoint after each state
            save_checkpoint(all_places_data, state_name)
        
        # Save final dataset
        if all_places_data:
            excel_file, csv_file = save_dataset(all_places_data, prefix="Census_Data_Final")
            
            if csv_file:
                logging.info("\nDataset generation completed successfully!")
                logging.info(f"Processed {len(all_places_data)} places total")
                logging.info(f"Files saved as:\n- {csv_file}")
                if excel_file:
                    logging.info(f"- {excel_file}")
            else:
                logging.error("Failed to save final dataset!")
        else:
            logging.error("No data was collected!")
    
    except Exception as e:
        logging.error(f"Error generating dataset: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        generate_comprehensive_dataset()
    except KeyboardInterrupt:
        logging.info("\nScript interrupted by user")
    except Exception as e:
        logging.error(f"Unhandled error: {str(e)}") 