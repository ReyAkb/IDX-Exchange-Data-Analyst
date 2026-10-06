import pandas as pd

# Load the full sold dataset
sold = pd.read_csv(r'C:\Users\oybek\Downloads\IDX\csv\sold_202401-202604.csv', low_memory=False)

# Inspect the dataset
pd.set_option('display.max_columns', None)  # Show all columns
pd.set_option('display.max_rows', None)  # Show all rows

print(sold.columns)
print()
print(sold.head())
print("\nRows and Columns:", sold.shape)
print("Data Types:\n", sold.dtypes)

# Show the count of each property type in the sold dataset
print("\nSold Property Types:", sold['PropertyType'].value_counts(dropna=False))

# Filter for Residential property types
sold_residential = sold[sold['PropertyType'] == 'Residential'].copy()
print("\nSold Residential Count: ", len(sold_residential))

# Create a table to summarize missing values
missing_table = pd.DataFrame({'Missing Values': sold_residential.isnull().sum(), '% Missing': ((sold_residential.isnull().sum() / len(sold_residential)) * 100).round(2)})
missing_table = missing_table.sort_values(by='Missing Values', ascending=False)
print("\nMissing Values Table:\n", missing_table)

# Identify columns with more than 90% missing values
missing_columns = missing_table[missing_table['% Missing'] > 90]
print("\nColumns with more than 90% missing values:\n", missing_columns)

cols = ['ClosePrice', 'LivingArea', 'DaysOnMarket']
numeric_summary = sold_residential[cols].describe([0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99]).transpose()
print("\nNumeric Summary:\n", numeric_summary)

# Save the cleaned dataset to a new CSV file
missing_table.to_csv(r'C:\Users\oybek\Downloads\IDX\csv\missing_values_summary.csv', index=True)
numeric_summary.to_csv(r'C:\Users\oybek\Downloads\IDX\csv\numeric_summary.csv', index=True)
sold_residential.to_csv(r'C:\Users\oybek\Downloads\IDX\csv\sold_residential_cleaned.csv', index=False)

# Columns over 90% missing (15 columns):
# 100%: TaxYear, FireplacesTotal, TaxAnnualAmount, AboveGradeFinishedArea,
#       ElementarySchoolDistrict, BusinessType, CoveredSpaces, MiddleOrJuniorSchoolDistrict
# 90-100%: WaterfrontYN, BelowGradeFinishedArea, BasementYN, LotSizeDimensions,
#          BuilderName, BuildingAreaTotal, CoBuyerAgentFirstName
# ClosePrice, LivingArea, and DaysOnMarket have under 1% missing values and are kept.

# Numeric summary:
# ClosePrice: median 823,000, mean 1,193,864 (pulled up by extreme values), min 0, max 989,500,000
# LivingArea: median 1,642, min 0, max 17,021,321 (not realistic)
# DaysOnMarket: median 18, min -288 (invalid), max 12,430