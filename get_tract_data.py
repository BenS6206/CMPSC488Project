import pandas as pd
import requests
import json

def get_tract_data():
    # Census API Key
    API_KEY = "92a2cbda1ed0d269658a64e96769fc856b10656f"
    
    # Base URL for Census API
    base_url = "https://api.census.gov/data/2020/dec/pl"
    
    # Variables we want to get
    variables = [
        "P1_001N",  # Total Population
        "P2_002N",  # Hispanic or Latino
        "P2_005N",  # White alone
        "P2_006N",  # Black alone
        "P2_008N",  # Asian alone
        "P2_009N"   # Pacific Islander alone
    ]
    
    # Get data for California (state code 06)
    state = "06"
    
    # Construct the API URL
    url = f"{base_url}?get={','.join(variables)}&for=tract:*&in=state:{state}%20county:*&key={API_KEY}"
    
    print("Downloading tract data...")
    print(f"Using URL: {url}")
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad status codes
        
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.text[:500]}...")  # Print first 500 chars of response
        
        data = response.json()
        
        # Convert to DataFrame
        columns = ['Total_Population', 'Hispanic_Latino', 'White_Alone', 'Black_Alone', 
                  'Asian_Alone', 'Pacific_Islander_Alone', 'state', 'county', 'tract']
        df = pd.DataFrame(data[1:], columns=columns)
        
        # Calculate percentages
        df['Hispanic_Latino_Pct'] = (df['Hispanic_Latino'].astype(float) / df['Total_Population'].astype(float)) * 100
        df['White_Alone_Pct'] = (df['White_Alone'].astype(float) / df['Total_Population'].astype(float)) * 100
        df['Black_Alone_Pct'] = (df['Black_Alone'].astype(float) / df['Total_Population'].astype(float)) * 100
        df['Asian_Alone_Pct'] = (df['Asian_Alone'].astype(float) / df['Total_Population'].astype(float)) * 100
        df['Pacific_Islander_Alone_Pct'] = (df['Pacific_Islander_Alone'].astype(float) / df['Total_Population'].astype(float)) * 100
        
        print(f"\nDataFrame shape: {df.shape}")
        print("\nFirst few rows:")
        print(df.head())
        
        # Save to CSV
        df.to_csv('data/Census_Tract_Data.csv', index=False)
        print("\nTract data saved to Census_Tract_Data.csv")
        
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status code: {e.response.status_code}")
            print(f"Response content: {e.response.text}")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == '__main__':
    get_tract_data() 