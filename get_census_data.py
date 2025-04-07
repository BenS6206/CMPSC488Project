import pandas as pd
import requests
import os
from dotenv import load_dotenv
import time
from tqdm import tqdm

# Load environment variables
load_dotenv()

# Get Census API key from environment variable
CENSUS_API_KEY = os.getenv('CENSUS_API_KEY')

# Dictionary of state codes
STATE_CODES = {
    'AL': '01', 'AK': '02', 'AZ': '04', 'AR': '05', 'CA': '06', 'CO': '08', 'CT': '09',
    'DE': '10', 'DC': '11', 'FL': '12', 'GA': '13', 'HI': '15', 'ID': '16', 'IL': '17',
    'IN': '18', 'IA': '19', 'KS': '20', 'KY': '21', 'LA': '22', 'ME': '23', 'MD': '24',
    'MA': '25', 'MI': '26', 'MN': '27', 'MS': '28', 'MO': '29', 'MT': '30', 'NE': '31',
    'NV': '32', 'NH': '33', 'NJ': '34', 'NM': '35', 'NY': '36', 'NC': '37', 'ND': '38',
    'OH': '39', 'OK': '40', 'OR': '41', 'PA': '42', 'RI': '44', 'SC': '45', 'SD': '46',
    'TN': '47', 'TX': '48', 'UT': '49', 'VT': '50', 'VA': '51', 'WA': '53', 'WV': '54',
    'WI': '55', 'WY': '56'
}

def get_tract_data():
    # Base URL for Census API
    base_url = "https://api.census.gov/data/2020/acs/acs5"
    
    # Variables to fetch
    variables = [
        "B01003_001E",  # Total Population
        "B03002_012E",  # Hispanic or Latino
        "B02001_002E",  # White Alone
        "B02001_003E",  # Black Alone
        "B02001_005E",  # Asian Alone
        "B02001_006E",  # Pacific Islander Alone
        # Age Distribution - Under 18
        "B01001_003E",  # Male Under 5
        "B01001_004E",  # Male 5-9
        "B01001_005E",  # Male 10-14
        "B01001_006E",  # Male 15-17
        "B01001_027E",  # Female Under 5
        "B01001_028E",  # Female 5-9
        "B01001_029E",  # Female 10-14
        "B01001_030E",  # Female 15-17
        # Age Distribution - 65 and over
        "B01001_020E",  # Male 65-66
        "B01001_021E",  # Male 67-69
        "B01001_022E",  # Male 70-74
        "B01001_023E",  # Male 75-79
        "B01001_024E",  # Male 80-84
        "B01001_025E",  # Male 85+
        "B01001_044E",  # Female 65-66
        "B01001_045E",  # Female 67-69
        "B01001_046E",  # Female 70-74
        "B01001_047E",  # Female 75-79
        "B01001_048E",  # Female 80-84
        "B01001_049E",  # Female 85+
        "B15003_017E",  # High School Graduate
        "B15003_022E",  # Bachelor's Degree
        "B15003_001E",  # Total Education Population (25 years and over)
        "B19013_001E",  # Median Household Income
        "B25077_001E",  # Median Home Value
        "B25003_002E",  # Owner Occupied Units
        "B25003_001E",  # Total Housing Units
    ]
    
    all_data = []
    print("Fetching census data for all states...")
    
    # Create progress bar for states
    for state_abbr, state_code in tqdm(STATE_CODES.items(), desc="Processing states"):
        try:
            # Parameters for the API request
            params = {
                "get": ",".join(variables),
                "for": "tract:*",
                "in": f"state:{state_code}",
                "key": CENSUS_API_KEY
            }
            
            # Make the API request
            response = requests.get(base_url, params=params)
            data = response.json()
            
            if len(data) > 1:  # Skip if no data returned
                # Add state abbreviation to the data
                for row in data[1:]:
                    row.append(state_abbr)
                all_data.extend(data[1:])
            
            # Sleep briefly to avoid hitting API rate limits
            time.sleep(0.1)
            
        except Exception as e:
            print(f"Error fetching data for {state_abbr}: {str(e)}")
            continue
    
    try:
        # Convert to DataFrame
        columns = [
            "Total_Population", "Hispanic_Latino", "White_Alone", "Black_Alone", 
            "Asian_Alone", "Pacific_Islander_Alone",
            "Male_Under_5", "Male_5_9", "Male_10_14", "Male_15_17",
            "Female_Under_5", "Female_5_9", "Female_10_14", "Female_15_17",
            "Male_65_66", "Male_67_69", "Male_70_74", "Male_75_79", "Male_80_84", "Male_85_Plus",
            "Female_65_66", "Female_67_69", "Female_70_74", "Female_75_79", "Female_80_84", "Female_85_Plus",
            "High_School_Grad", "Bachelors_Degree", "Education_Pop",
            "Median_Household_Income", "Median_Home_Value",
            "Owner_Occupied", "Total_Housing_Units",
            "state", "county", "tract", "state_abbr"
        ]
        df = pd.DataFrame(all_data, columns=columns)
        
        print(f"Processing data for {len(df)} census tracts...")
        
        # Convert numeric columns
        numeric_cols = columns[:-4]  # All except state, county, tract, state_abbr
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
        
        # Calculate percentages and derived fields
        df['Under_18'] = (
            df['Male_Under_5'] + df['Male_5_9'] + df['Male_10_14'] + df['Male_15_17'] +
            df['Female_Under_5'] + df['Female_5_9'] + df['Female_10_14'] + df['Female_15_17']
        )
        
        df['Over_65'] = (
            df['Male_65_66'] + df['Male_67_69'] + df['Male_70_74'] + df['Male_75_79'] + df['Male_80_84'] + df['Male_85_Plus'] +
            df['Female_65_66'] + df['Female_67_69'] + df['Female_70_74'] + df['Female_75_79'] + df['Female_80_84'] + df['Female_85_Plus']
        )
        
        df['Age_Under_18_Pct'] = (df['Under_18'] / df['Total_Population'] * 100).round(2)
        df['Age_65_and_Over_Pct'] = (df['Over_65'] / df['Total_Population'] * 100).round(2)
        df['Age_18_to_64_Pct'] = (100 - df['Age_Under_18_Pct'] - df['Age_65_and_Over_Pct']).round(2)
        
        df['Hispanic_Latino_Pct'] = (df['Hispanic_Latino'] / df['Total_Population'] * 100).round(2)
        df['White_Alone_Pct'] = (df['White_Alone'] / df['Total_Population'] * 100).round(2)
        df['Black_Alone_Pct'] = (df['Black_Alone'] / df['Total_Population'] * 100).round(2)
        df['Asian_Alone_Pct'] = (df['Asian_Alone'] / df['Total_Population'] * 100).round(2)
        df['Pacific_Islander_Alone_Pct'] = (df['Pacific_Islander_Alone'] / df['Total_Population'] * 100).round(2)
        
        df['High_School_Grad_Pct'] = (df['High_School_Grad'] / df['Education_Pop'] * 100).round(2)
        df['Bachelors_Degree_Pct'] = (df['Bachelors_Degree'] / df['Education_Pop'] * 100).round(2)
        
        df['Homeownership_Rate'] = (df['Owner_Occupied'] / df['Total_Housing_Units'] * 100).round(2)
        
        # Save to CSV
        print("Saving data to CSV...")
        df.to_csv('data/Census_Tract_Data.csv', index=False)
        print(f"Census tract data saved successfully! Total tracts: {len(df)}")
        
        # Print some summary statistics
        print("\nSummary Statistics:")
        print(f"Total number of states processed: {df['state_abbr'].nunique()}")
        print(f"Average population per tract: {df['Total_Population'].mean():.0f}")
        print(f"Total US population in dataset: {df['Total_Population'].sum():,}")
        
    except Exception as e:
        print(f"Error processing data: {e}")

if __name__ == "__main__":
    get_tract_data() 