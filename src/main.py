import pandas as pd

def main():
    try:
        # Read the CSV file
        df = pd.read_csv('ad_viz_plotval_data.csv')
        
        # Print first 10 rows
        print("\nFirst 10 rows of your CSV file:")
        print(df.head(10))
        
    except FileNotFoundError:
        print("Error: CSV file not found. Make sure 'ad_viz_plotval_data.csv' is in the correct directory.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main() 