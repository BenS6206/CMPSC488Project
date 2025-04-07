import pandas as pd
import requests
import json

def get_total_places_per_state():
    """Get the total number of places in each state from Census API"""
    API_KEY = "92a2cbda1ed0d269658a64e96769fc856b10656f"
    url = "https://api.census.gov/data/2020/dec/pl"
    
    # Get all state FIPS codes
    params = {
        "get": "NAME",
        "for": "state:*",
        "key": API_KEY
    }
    
    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception(f"Failed to get state FIPS codes: {response.text}")
    
    data = response.json()
    state_fips_dict = {row[0]: row[1] for row in data[1:]}  # Skip header row
    
    # Get places count for each state
    state_place_counts = {}
    for state_name, state_fips in state_fips_dict.items():
        params = {
            "get": "NAME",
            "for": "place:*",
            "in": f"state:{state_fips}",
            "key": API_KEY
        }
        
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            # Subtract 1 for header row
            state_place_counts[state_name] = len(data) - 1
        else:
            print(f"Warning: Failed to get places for {state_name}: {response.text}")
            state_place_counts[state_name] = 0
    
    return state_place_counts

def check_dataset_coverage():
    """Check how many places we have in our dataset vs total available"""
    print("Checking dataset coverage...")
    
    # Get total places per state from Census API
    total_places = get_total_places_per_state()
    total_available = sum(total_places.values())
    print(f"\nTotal places available in Census data: {total_available}")
    
    # Read our generated dataset
    try:
        df = pd.read_csv("Comprehensive_US_Places_Census_Data.csv")
        our_places = df.groupby('State').size().to_dict()
        total_collected = len(df)
        print(f"Total places in our dataset: {total_collected}")
        
        # Compare by state
        print("\nCoverage by state:")
        print("State\t\tAvailable\tCollected\tCoverage")
        print("-" * 60)
        
        for state in sorted(total_places.keys()):
            available = total_places[state]
            collected = our_places.get(state, 0)
            coverage = (collected / available * 100) if available > 0 else 0
            print(f"{state[:15]:<15}\t{available}\t\t{collected}\t\t{coverage:.1f}%")
        
        # Overall coverage
        overall_coverage = (total_collected / total_available * 100)
        print(f"\nOverall coverage: {overall_coverage:.1f}%")
        
        # Check for missing states
        missing_states = set(total_places.keys()) - set(our_places.keys())
        if missing_states:
            print("\nStates missing from our dataset:")
            for state in missing_states:
                print(f"- {state}")
        
    except Exception as e:
        print(f"Error reading dataset: {e}")

if __name__ == "__main__":
    check_dataset_coverage() 