import pandas as pd

sold = pd.read_csv(r'C:\Users\oybek\Downloads\IDX\csv\sold_with_rates.csv', low_memory=False)
rows_start = len(sold)

# Convert data columns to datetime
data_columns = ['CloseDate', 'PurchaseContractDate', 'ListingContractDate', 'ContractStatusChangeDate']

for col in data_columns:
    sold[col] = pd.to_datetime(sold[col], errors='coerce')
print("\nData types after conversion:\n", sold[data_columns].dtypes)
print("\nMissing dates after conversion:\n", sold[data_columns].isnull().sum())

# Drop columns with more than 90% missing values
missing_threshold = sold.isnull().mean() *100
drop_columns = missing_threshold[missing_threshold > 90].index.tolist()
print(f"\nColumns to drop (more than 90% missing): {drop_columns}")
sold = sold.drop(columns=drop_columns)

# Check if numeric columns are numbers
numeric_columns = ['ClosePrice', 'ListPrice', 'OriginalListPrice', 'LivingArea', 'LotSizeAcres',
            'BedroomsTotal', 'BathroomsTotalInteger', 'DaysOnMarket', 'YearBuilt']

for col in numeric_columns:
    sold[col] = pd.to_numeric(sold[col], errors='coerce')
print("\nData types after numeric conversion:\n", sold[numeric_columns].dtypes)

# Count invalid values for each numeric column
print("\nClosePrice invalid values:", (sold['ClosePrice'] <= 0).sum())
print("LivingArea invalid values:", (sold['LivingArea'] <= 0).sum())
print("DaysOnMarket invalid values:", (sold['DaysOnMarket'] < 0).sum())
print("BedroomsTotal invalid values:", (sold['BedroomsTotal'] < 0).sum())
print("BathroomsTotalInteger invalid values:", (sold['BathroomsTotalInteger'] < 0).sum())

# Mark the invalid rows for removal
invalid_rows = (sold['ClosePrice'] <= 0) | (sold['LivingArea'] <= 0) | (sold['DaysOnMarket'] < 0) | \
               (sold['BedroomsTotal'] < 0) | (sold['BathroomsTotalInteger'] < 0)
print(f"\nInvalid rows to remove: {invalid_rows.sum()}")

# Remove invalid rows
sold = sold[~invalid_rows].copy()
print(f"\nRows remaining after removing invalid values: {len(sold)}")

# Validate the logical order of data fields
sold['listing_after_close_flag'] = sold['ListingContractDate'] > sold['CloseDate']
sold['purchase_after_close_flag'] = sold['PurchaseContractDate'] > sold['CloseDate']
sold['negative_timeline_flag'] = (sold['ListingContractDate'] > sold['PurchaseContractDate']) | \
                                 (sold['PurchaseContractDate'] > sold['CloseDate']) | (sold['ListingContractDate'] > sold['CloseDate']) # True if any of the dates are out of order

print("Listing after close count:", sold['listing_after_close_flag'].sum())
print("Purchase after close count:", sold['purchase_after_close_flag'].sum())
print("Negative timeline count:", sold['negative_timeline_flag'].sum())

# Geographic validation: Check for invalid latitude and longitude values
sold['missing_coordinates_flag'] = sold['Latitude'].isnull() | sold['Longitude'].isnull()
sold['zero_coordinates_flag'] = (sold['Latitude'] == 0) | (sold['Longitude'] == 0)
sold['positive_longitude_flag'] = sold['Longitude'] > 0  # Longitude should be negative in the US

has_coordinates = ~(sold['missing_coordinates_flag'])
outside_california = has_coordinates & ((sold['Longitude'] > -114.1312) | (sold['Longitude'] < -124.4096) | (sold['Latitude'] < 32.5343) | (sold['Latitude'] > 42.0095))
sold['out_of_state_flag'] = outside_california | (sold['StateOrProvince'] != 'CA')

print("\nGeographic validation counts:")
print("Missing coordinates:", sold['missing_coordinates_flag'].sum())
print("Zero coordinates:", sold['zero_coordinates_flag'].sum())
print("Positive longitude:", sold['positive_longitude_flag'].sum())
print("Out of state:", sold['out_of_state_flag'].sum())

print(f"\nInitial sold dataset rows: {rows_start}")
print(f"\nFinal sold dataset rows after all cleaning: {len(sold)}")
sold.to_csv(r'C:\Users\oybek\Downloads\IDX\csv\sold_cleaned_with_rates.csv', index=False)

# Row counts
# - Started with 414,054 rows.
# - Removed 199 rows with invalid values, so 413,855 rows are left.
#   (1 row had ClosePrice <= 0, 150 rows had LivingArea <= 0, 48 rows had DaysOnMarket < 0)
# - No row had a negative number of bedrooms or bathrooms.

# Columns
# - Dropped 15 columns that were more than 90% empty.

# Missing dates
# - PurchaseContractDate: 194 missing
# - ListingContractDate: 1 missing
# - ContractStatusChangeDate: 594 missing
# - CloseDate: none missing

# Date order checks (I only flagged these rows, I did not delete them)
# - listing_after_close_flag: 61 rows
# - purchase_after_close_flag: 239 rows
# - negative_timeline_flag: 506 rows
#   This flag is True when the dates are in the wrong order
#   (listing -> purchase -> close). If a date is missing, the row is not flagged.

# Coordinate checks (also only flagged, not deleted)
# - Missing latitude or longitude: 4,102 rows
# - Latitude or longitude equal to 0: 27 rows
# - Positive longitude: 31 rows
# - Out of state or outside the California area: 104 rows