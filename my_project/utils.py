# # my_project/utils.py
# import pandas as pd
# from .database import db
# from .models import CensusData
#
# def load_estimation_data(excel_file="data/estimation.xlsx"):
#     """Load estimation.xlsx and store in PostgreSQL using Column A as county names"""
#
#     # Read Excel file WITHOUT assuming the first row is headers
#     df = pd.read_excel(excel_file, engine="openpyxl", header=None)
#
#     # Print preview to debug
#     print("Excel Data Preview:")
#     print(df.head(10))  # Print first 10 rows for inspection
#
#     # Skip metadata rows by finding the first row that contains actual county data
#     for i, row in df.iterrows():
#         if "county" in str(row.iloc[0]).lower():  # Detect header row dynamically
#             df = df.iloc[i+1:].reset_index(drop=True)
#             break
#
#     # Rename first column (Column A) to "County"
#     df.rename(columns={0: "County"}, inplace=True)
#
#     # Convert numeric columns to integers, handling missing values
#     for col in range(1, 5):  # Assuming years are in Columns B-E
#         df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
#
#     # Insert cleaned data into PostgreSQL
#     for _, row in df.iterrows():
#         record = CensusData(
#             county=row["County"],  # Use first column (Column A)
#             year_2022=row.iloc[1],  # Column B
#             year_2021=row.iloc[2],  # Column C
#             year_2020=row.iloc[3],  # Column D
#             year_2019=row.iloc[4]   # Column E
#         )
#         db.session.add(record)
#
#     db.session.commit()
#     print("✅ Successfully loaded cleaned estimation.xlsx into PostgreSQL!")
#
#
# # my_project/utils.py
# import os
# import pandas as pd
# from .database import db
# from .models import CensusData
#
#
# def load_estimation_data(excel_file="data/estimation.xlsx"):
#     """Load estimation.xlsx and store in PostgreSQL using Column A as county names"""
#
#     # Read Excel file WITHOUT assuming the first row is headers
#     df = pd.read_excel(excel_file, engine="openpyxl", header=None)
#
#     # Print preview to debug
#     print("Excel Data Preview:")
#     print(df.head(10))  # Print first 10 rows for inspection
#
#     # Skip metadata rows by finding the first row that contains actual county data
#     for i, row in df.iterrows():
#         if "county" in str(row.iloc[0]).lower():  # Detect header row dynamically
#             df = df.iloc[i + 1:].reset_index(drop=True)
#             break
#
#     # Rename first column (Column A) to "County"
#     df.rename(columns={0: "County"}, inplace=True)
#
#     # Convert numeric columns to integers, handling missing values
#     for col in range(1, 5):  # Assuming years are in Columns B-E
#         df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
#
#     # Insert cleaned data into PostgreSQL
#     for _, row in df.iterrows():
#         record = CensusData(
#             county=row["County"],  # Use first column (Column A)
#             year_2022=row.iloc[1],  # Column B
#             year_2021=row.iloc[2],  # Column C
#             year_2020=row.iloc[3],  # Column D
#             year_2019=row.iloc[4]  # Column E
#         )
#         db.session.add(record)
#
#     db.session.commit()
#     print("✅ Successfully loaded cleaned estimation.xlsx into PostgreSQL!")
#
#
# def load_census_folder(csv_folder="data/census_data"):
#     """Load all CSV files from 'census_data' folder into PostgreSQL"""
#
#     # Ensure folder exists
#     if not os.path.exists(csv_folder):
#         raise FileNotFoundError(f"❌ Folder '{csv_folder}' does not exist!")
#
#     # Get list of all CSV files
#     csv_files = [f for f in os.listdir(csv_folder) if f.endswith(".csv")]
#
#     if not csv_files:
#         raise FileNotFoundError(f"❌ No CSV files found in '{csv_folder}'!")
#
#     for filename in csv_files:
#         filepath = os.path.join(csv_folder, filename)
#
#         # Read CSV
#         df = pd.read_csv(filepath)
#
#         # Ensure at least 5 columns (County + 4 years)
#         if df.shape[1] < 5:
#             print(f"⚠️ Skipping {filename}: Not enough columns.")
#             continue
#
#         # Print preview for debugging
#         print(f"📄 Loading {filename} ...")
#         print(df.head())
#
#         # Insert data into PostgreSQL
#         for _, row in df.iterrows():
#             record = CensusData(
#                 county=row.iloc[0],  # Use first column (Column A) for county names
#                 year_2022=row.iloc[1],  # Column B
#                 year_2021=row.iloc[2],  # Column C
#                 year_2020=row.iloc[3],  # Column D
#                 year_2019=row.iloc[4]  # Column E
#             )
#             db.session.add(record)
#
#     db.session.commit()
#     print("✅ Successfully loaded all census CSV files into PostgreSQL!")


# my_project/utils.py
import os
import pandas as pd
from .database import db
from .models import CensusData

def load_estimation_data(excel_file="data/estimation.xlsx"):
    """Load estimation.xlsx and store in PostgreSQL using Column A as county names"""

    # Read Excel file WITHOUT assuming the first row is headers
    df = pd.read_excel(excel_file, engine="openpyxl", header=None)

    # Print preview to debug
    print("Excel Data Preview:")
    print(df.head(10))  # Print first 10 rows for inspection

    # Skip metadata rows by finding the first row that contains actual county data
    for i, row in df.iterrows():
        if "county" in str(row.iloc[0]).lower():  # Detect header row dynamically
            df = df.iloc[i+1:].reset_index(drop=True)
            break

    # Rename first column (Column A) to "County"
    df.rename(columns={0: "County"}, inplace=True)

    # Convert numeric columns to integers, handling missing values
    for col in range(1, 5):  # Assuming years are in Columns B-E
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # Insert cleaned data into PostgreSQL
    for _, row in df.iterrows():
        record = CensusData(
            county=row["County"],  # Use first column (Column A)
            year_2022=row.iloc[1],  # Column B
            year_2021=row.iloc[2],  # Column C
            year_2020=row.iloc[3],  # Column D
            year_2019=row.iloc[4]   # Column E
        )
        db.session.add(record)

    db.session.commit()
    print("✅ Successfully loaded cleaned estimation.xlsx into PostgreSQL!")

def load_census_data(csv_folder="data/census_data"):
    """Load all CSV files from 'census_data' folder into PostgreSQL"""

    # Ensure folder exists
    if not os.path.exists(csv_folder):
        raise FileNotFoundError(f"❌ Folder '{csv_folder}' does not exist!")

    # Get list of all CSV files
    csv_files = [f for f in os.listdir(csv_folder) if f.endswith(".csv")]

    if not csv_files:
        raise FileNotFoundError(f"❌ No CSV files found in '{csv_folder}'!")

    for filename in csv_files:
        filepath = os.path.join(csv_folder, filename)

        try:
            # Read CSV (Try different encodings if needed)
            df = pd.read_csv(filepath, low_memory=False)

            # Print preview for debugging
            print(f"📄 Loading {filename} ...")
            print(df.head(10))  # Print first 10 rows to inspect data

            # Ensure at least 5 columns (County + 4 years)
            if df.shape[1] < 5:
                print(f"⚠️ Skipping {filename}: Not enough columns.")
                continue

            # Skip metadata files automatically
            if "GEO_ID" in df.columns or "Column Name" in df.columns:
                print(f"⚠️ Skipping {filename}: Detected metadata file.")
                continue

            # Find the first row where numeric data starts
            for i, row in df.iterrows():
                if pd.to_numeric(row.iloc[1:], errors="coerce").notna().all():
                    df = df.iloc[i:].reset_index(drop=True)
                    break

            # Ensure at least 5 valid numeric columns
            if df.shape[1] < 5:
                print(f"⚠️ Skipping {filename}: Not enough data after cleanup.")
                continue

            # Convert numeric columns properly
            for col in range(1, 5):  # Assuming years are in Columns B-E
                df.iloc[:, col] = pd.to_numeric(df.iloc[:, col], errors="coerce").fillna(0).astype(int)

            # Insert data into PostgreSQL
            for _, row in df.iterrows():
                record = CensusData(
                    county=row.iloc[0],  # Use first column (Column A) for county names
                    year_2022=int(row.iloc[1]),  # Convert to integer
                    year_2021=int(row.iloc[2]),
                    year_2020=int(row.iloc[3]),
                    year_2019=int(row.iloc[4])
                )
                db.session.add(record)

        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")
            continue  # Skip problematic files

    db.session.commit()
    print("✅ Successfully loaded all cleaned census CSV files into PostgreSQL!")