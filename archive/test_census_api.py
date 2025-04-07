from census import Census
import requests
import json

API_KEY = "92a2cbda1ed0d269658a64e96769fc856b10656f"

def test_direct_api():
    print("Testing direct API access...")
    base_url = "https://api.census.gov/data/2020/dec/pl"
    params = {
        "get": "NAME,P1_001N",  # P1_001N is total population
        "for": "state:*",
        "key": API_KEY
    }
    
    try:
        response = requests.get(base_url, params=params)
        if response.status_code == 200:
            print("✓ Direct API test successful!")
            data = response.json()
            print(f"Sample data (first state): {data[1]}")  # data[0] is headers
        else:
            print(f"✗ API request failed with status code: {response.status_code}")
            print(f"Error message: {response.text}")
    except Exception as e:
        print(f"✗ Error making API request: {str(e)}")

def test_census_wrapper():
    print("\nTesting Census wrapper library...")
    try:
        c = Census(API_KEY)
        # Get 2020 population for first state
        data = c.pl.state(('NAME', 'P1_001N'), year=2020)
        if data:
            print("✓ Census wrapper test successful!")
            print(f"Sample data: {data[0]}")
        else:
            print("✗ No data returned from Census wrapper")
    except Exception as e:
        print(f"✗ Error using Census wrapper: {str(e)}")

if __name__ == "__main__":
    print("Census API Test Script")
    print("=====================")
    test_direct_api()
    test_census_wrapper() 