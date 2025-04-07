import pandas as pd
import requests
import json
import os
from datetime import datetime

API_KEY = "92a2cbda1ed0d269658a64e96769fc856b10656f"

def get_total_places():
    """Get total number of places from Census API"""
    url = "https://api.census.gov/data/2020/dec/pl"
    params = {
        "get": "NAME",
        "for": "place:*",
        "key": API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()
    return len(data) - 1  # Subtract header row

def check_progress():
    """Check current progress of dataset generation"""
    try:
        # Get file modification time
        csv_file = "Comprehensive_US_Places_Census_Data.csv"
        if os.path.exists(csv_file):
            last_modified = datetime.fromtimestamp(os.path.getmtime(csv_file))
            print(f"\nLast update time: {last_modified.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Load current dataset
        df = pd.read_csv(csv_file)
        current_count = len(df)
        
        # Get total available places
        total_places = get_total_places()
        
        # Calculate progress
        progress = (current_count / total_places) * 100
        
        print(f"\nCurrent Progress:")
        print(f"Total places in dataset: {current_count}")
        print(f"Total places available: {total_places}")
        print(f"Progress: {progress:.2f}%")
        
        # Check by state
        print("\nProgress by state:")
        state_counts = df['State'].value_counts()
        for state, count in state_counts.items():
            print(f"{state}: {count} places")
            
    except Exception as e:
        print(f"Error checking progress: {e}")

if __name__ == "__main__":
    check_progress() 