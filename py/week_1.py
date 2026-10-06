# At the moment, data covers Jan 2024 to Apr 2026, the latest months available on the FTP server.
import os
import pandas as pd

folder = r'C:\Users\oybek\Downloads\IDX\csv'  # Replace with your folder path

# Get a list of all files in the folder
all_files = os.listdir(folder)

# ---------- SOLD FILES ----------

sold_list = []

# Loop through all files and filter for sold files between 202401 and 202604
for file in all_files:
    if file.startswith('CRMLSSold') and file.endswith('.csv'):
        month = file[9:15]  # Extract the month from the file name

        if month >= '202401' and month <= '202604':
            df = pd.read_csv(os.path.join(folder, file), low_memory=False)
            sold_list.append(df)

print("Sold files between 202401 and 202604:", len(sold_list))

# Before concat, add the rows of all small files
rows_before_concat = 0

# Count the number of rows in each sold file before concatenation
for df in sold_list:
    rows_before_concat += len(df)
print("Sold rows before concatenation:", rows_before_concat)

# Count the number of rows in the concatenated DataFrame
sold = pd.concat(sold_list, ignore_index=True)
print("Sold rows after concatenation:", len(sold))

# ---------- LISTING FILES ----------

listing_list = []

# Loop through all files and filter for listing files between 202401 and 202604
for file in all_files:
    if file.startswith('CRMLSListing') and file.endswith('.csv'):
        month = file[12:18]  # Extract the month from the file name

        if month >= '202401' and month <= '202604':
            df = pd.read_csv(os.path.join(folder, file), low_memory=False)
            listing_list.append(df)

print("\nListing files between 202401 and 202604:", len(listing_list))

# Before concat, add the rows of all small files
rows_before_concat_listing = 0

# Count the number of rows in each listing file before concatenation
for df in listing_list:
    rows_before_concat_listing += len(df)
print("Listing rows before concatenation:", rows_before_concat_listing)

# Count the number of rows in the concatenated DataFrame
listing = pd.concat(listing_list, ignore_index=True)
print("Listing rows after concatenation:", len(listing))

# ---------- FILTER RESIDENTIAL FILES ----------

print("\nSold Property Types:", sold['PropertyType'].unique())
print("\nListing Property Types:", listing['PropertyType'].unique())

print("\nSold Count Before Filtering: ", len(sold))
print("Listing Count Before Filtering: ", len(listing))

sold_residential = sold[sold['PropertyType'] == 'Residential']
listing_residential = listing[listing['PropertyType'] == 'Residential']

print("\nSold Residential: ", len(sold_residential))
print("Listing Residential: ", len(listing_residential))

# ---------- SAVE TO CSV ----------
sold.to_csv(os.path.join(folder, 'sold_202401-202604.csv'), index=False)
listing.to_csv(os.path.join(folder, 'listing_202401-202604.csv'), index=False)

sold_residential.to_csv(os.path.join(folder, 'sold_residential_202401-202604.csv'), index=False)
listing_residential.to_csv(os.path.join(folder, 'listing_residential_202401-202604.csv'), index=False)

# ---------- SUMMARY ----------

# Row counts (Jan 2024 - Apr 2026)
# Sold: before concat = 615707, after concat = 615707
# Sold: before Residential filter = 615707, after = 414054
# Listing: before concat = 822087, after concat = 822087
# Listing: before Residential filter = 822087, after = 522931
# Filter logic: Sold and Listing files contain only Residential property types, so the filter is applied to both datasets.