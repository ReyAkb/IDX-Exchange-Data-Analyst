import pandas as pd

listing = pd.read_csv(r'C:\Users\oybek\Downloads\IDX\csv\listings_with_rates.csv', low_memory=False)
#print(listing.columns.to_list())

# Identify and drop duplicate columns (those ending with '.1')
duplicate_columns = [col for col in listing.columns if col.endswith('.1')]
print(f"\nDuplicate columns: {duplicate_columns}")

# Drop the duplicate columns
listing = listing.drop(columns=duplicate_columns)
print("Columns left after dropping duplicates:", listing.shape[1])

rows_start = len(listing)

# Convert data columns to datetime
data_columns = ['CloseDate', 'PurchaseContractDate', 'ListingContractDate', 'ContractStatusChangeDate']
for col in data_columns:
    listing[col] = pd.to_datetime(listing[col], errors='coerce')
print("\nData types after conversion:\n", listing[data_columns].dtypes)
print("\nMissing dates after conversion:\n", listing[data_columns].isnull().sum())

# Drop columns with more than 90% missing values, but keep core columns
missing_threshold = listing.isnull().mean() *100
drop_columns = missing_threshold[missing_threshold > 90].index.tolist()
print(missing_threshold[['ClosePrice', 'CloseDate', 'PurchaseContractDate', 'DaysOnMarket']])

core_columns = ['ClosePrice', 'CloseDate', 'PurchaseContractDate', 'ContractStatusChangeDate',
                'ListingContractDate', 'ListPrice', 'LivingArea', 'Latitude', 'Longitude']
drop_columns = [c for c in drop_columns if c not in core_columns]
print(f"\nColumns to drop (more than 90% missing): {drop_columns}")
listing = listing.drop(columns=drop_columns)

# Check if numeric columns are numbers
numeric_columns = ['ClosePrice', 'ListPrice', 'OriginalListPrice', 'LivingArea', 'LotSizeAcres',
            'BedroomsTotal', 'BathroomsTotalInteger', 'DaysOnMarket', 'YearBuilt']

for col in numeric_columns:
    listing[col] = pd.to_numeric(listing[col], errors='coerce')
print("\nData types after numeric conversion:\n", listing[numeric_columns].dtypes)

# Count invalid values for each numeric column
print("\nClosePrice invalid values:", (listing['ClosePrice'] <= 0).sum())
print("LivingArea invalid values:", (listing['LivingArea'] <= 0).sum())
print("DaysOnMarket invalid values:", (listing['DaysOnMarket'] < 0).sum())
print("BedroomsTotal invalid values:", (listing['BedroomsTotal'] < 0).sum())
print("BathroomsTotalInteger invalid values:", (listing['BathroomsTotalInteger'] < 0).sum())
print("ListPrice invalid values:", (listing['ListPrice'] <= 0).sum())

# Mark the invalid rows for removal
invalid_rows = (listing['ClosePrice'] <= 0) | (listing['LivingArea'] <= 0) | (listing['DaysOnMarket'] < 0) | \
               (listing['BedroomsTotal'] < 0) | (listing['BathroomsTotalInteger'] < 0) | (listing['ListPrice'] <= 0)
print(f"\nInvalid rows to remove: {invalid_rows.sum()}")

# Remove invalid rows
listing = listing[~invalid_rows].copy()
print(f"\nRows remaining after removing invalid values: {len(listing)}")

# Validate the logical order of data fields
listing['listing_after_close_flag'] = listing['ListingContractDate'] > listing['CloseDate']
listing['purchase_after_close_flag'] = listing['PurchaseContractDate'] > listing['CloseDate']
listing['negative_timeline_flag'] = (listing['ListingContractDate'] > listing['PurchaseContractDate']) | \
                                 (listing['PurchaseContractDate'] > listing['CloseDate']) | (listing['ListingContractDate'] > listing['CloseDate']) # True if any of the dates are out of order

print("Listing after close count:", listing['listing_after_close_flag'].sum())
print("Purchase after close count:", listing['purchase_after_close_flag'].sum())
print("Negative timeline count:", listing['negative_timeline_flag'].sum())

# Check for invalid latitude and longitude values
listing['missing_coordinates_flag'] = listing['Latitude'].isnull() | listing['Longitude'].isnull()
listing['zero_coordinates_flag'] = (listing['Latitude'] == 0) | (listing['Longitude'] == 0)
listing['positive_longitude_flag'] = listing['Longitude'] > 0  # Longitude should be negative in the US

# Out of state flag
has_coordinates = ~(listing['missing_coordinates_flag'])
state_not_ca = listing['StateOrProvince'] != 'CA'
state_missing = listing['StateOrProvince'].isnull()
outside_california = has_coordinates & ((listing['Longitude'] > -114.1312) | (listing['Longitude'] < -124.4096) | (listing['Latitude'] < 32.5343) | (listing['Latitude'] > 42.0095))
listing['out_of_state_flag'] = outside_california | state_not_ca

# Geographic validation 
print("\nGeographic validation counts:")
print("Missing coordinates:", listing['missing_coordinates_flag'].sum())
print("Zero coordinates:", listing['zero_coordinates_flag'].sum())
print("Positive longitude:", listing['positive_longitude_flag'].sum())
print("Out of state:", listing['out_of_state_flag'].sum())

# Out of state breakdown
print("\nOut of state breakdown:")
print("State is not CA:", state_not_ca.sum())
print("  - state is missing:", state_missing.sum())
print("  - state is another value:", (state_not_ca & ~state_missing).sum())
print("Coordinates outside the California box:", outside_california.sum())
print("In both groups:", (state_not_ca & outside_california).sum())
print("Total flagged (out_of_state_flag):", listing['out_of_state_flag'].sum())

print("\nTop state values:\n", listing['StateOrProvince'].value_counts(dropna=False).head())

print(f"\nInitial listing dataset rows: {rows_start}")
print(f"\nFinal listing dataset rows after all cleaning: {len(listing)}")
listing.to_csv(r'C:\Users\oybek\Downloads\IDX\csv\listing_cleaned_with_rates.csv', index=False)

# Duplicate columns
# - All raw listing files have 11 column names repeated in the header
#   (BuyerOfficeName, CloseDate, DaysOnMarket, Latitude, ListAgentFirstName, ListAgentLastName,
#   ListPrice, LivingArea, Longitude, PropertyType, UnparsedAddress).
# - Pandas renamed the second copies to .1. The values matched the main columns
#   (only 1 row differed, in BuyerOfficeName), so I dropped the .1 copies and kept
#   the originals (75 columns left).

# Row counts
# - Started with 522,931 rows.
# - Removed 367 rows with invalid values, so 522,564 rows are left.
#   (346 rows had LivingArea <= 0, 21 rows had DaysOnMarket < 0)
# - No row had ClosePrice <= 0, ListPrice <= 0, or a negative number of bedrooms or bathrooms.

# Columns
# - Dropped 13 columns that were more than 90% empty.
# - Kept the core columns even if many values are missing (the handbook says to do this).

# Listing status
# - Closed: 122,435 | Active: 272,296 | Pending: 84,665
#   ActiveUnderContract: 41,358 | ComingSoon: 1,810
# - Most listings have not closed yet, so CloseDate is about 73% missing.

# Missing dates
# - CloseDate: 379,433 missing
# - PurchaseContractDate: 280,340 missing
# - ContractStatusChangeDate: 6,106 missing
# - ListingContractDate: none missing

# Date order checks (I only flagged these rows, I did not delete them)
# - listing_after_close_flag: 71 rows
# - purchase_after_close_flag: 243 rows
# - negative_timeline_flag: 499 rows
#   This flag is True when the dates are in the wrong order
#   (listing -> purchase -> close). If a date is missing, the row is not flagged,
#   so the close date checks only apply to listings that closed.

# Coordinate checks (also only flagged, not deleted)
# - Missing latitude or longitude: 73,194 rows (about 14%)
# - Latitude or longitude equal to 0: 64 rows
# - Positive longitude: 71 rows
# - Out of state or outside the California area: 346 rows
#   - 197 rows have a state that is not CA (51 of them have a missing state)
#   - 303 rows have coordinates outside the California box
#   - 154 rows are in both groups, so 43 + 149 + 154 = 346
#   - Rows with a missing state are flagged only because the state is unknown.