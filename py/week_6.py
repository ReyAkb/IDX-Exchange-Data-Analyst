import numpy as np
import pandas as pd
import geopandas as gpd


# ---------- Load the data ----------

sold = pd.read_csv(r'C:\Users\oybek\Downloads\IDX\csv\sold_cleaned_with_rates.csv', low_memory=False)

# ---------- Convert date columns ----------

# Dates become text again when saved to CSV, so convert them again after reading
date_columns = ['CloseDate', 'PurchaseContractDate', 'ListingContractDate', 'ContractStatusChangeDate']

for col in date_columns:
    sold[col] = pd.to_datetime(sold[col], errors='coerce')


# ---------- Price metrics ----------

# Check if OriginalListPrice has invalid values (less than or equal to 0)
print("\nOriginalListPrice invalid values:", (sold['OriginalListPrice'] <= 0).sum())
valid_original_list_price = sold['OriginalListPrice'] > 0

# Rows with OriginalListPrice <= 0 get NaN for the ratio (not removed), so we never divide by 0
sold['price_ratio'] = sold['ClosePrice'] / sold['OriginalListPrice'].where(valid_original_list_price)

# The handbook lists close_to_original_list_ratio with the same formula as price_ratio
sold['close_to_original_list_ratio'] = sold['price_ratio']

sold['price_per_sqft'] = sold['ClosePrice'] / sold['LivingArea']


# ---------- Date metrics ----------

sold['year'] = sold['CloseDate'].dt.year
sold['month'] = sold['CloseDate'].dt.month
sold['YrMo'] = sold['CloseDate'].dt.to_period('M').astype(str)

sold['listing_to_contract_days'] = (sold['PurchaseContractDate'] - sold['ListingContractDate']).dt.days
sold['contract_to_close_days'] = (sold['CloseDate'] - sold['PurchaseContractDate']).dt.days


# ---------- Checks on the new columns ----------

print("\nInfinite values:\n", np.isinf(sold[['price_ratio', 'price_per_sqft']]).sum())

print("\nMissing values in new columns:\n",
      sold[['price_ratio', 'price_per_sqft', 'listing_to_contract_days', 'contract_to_close_days']].isnull().sum())

print("\nNegative listing_to_contract_days:", (sold['listing_to_contract_days'] < 0).sum())
print("Negative contract_to_close_days:", (sold['contract_to_close_days'] < 0).sum())


# ---------- Sample table ----------

print("\nSample of new columns:")
print(sold[['CloseDate', 'YrMo', 'ClosePrice', 'OriginalListPrice', 'price_ratio',
            'LivingArea', 'price_per_sqft', 'listing_to_contract_days',
            'contract_to_close_days']].head(10))


# ---------- Same-day listings check ----------

# Some rows have the same ListingContractDate and CloseDate
same_day = sold['ListingContractDate'] == sold['CloseDate']
print("\nSame day listing and close:", same_day.sum())
print("  of which purchase after close:", (same_day & sold['purchase_after_close_flag']).sum())

print("\nlisting_to_contract_days for same-day rows:\n", sold.loc[same_day, 'listing_to_contract_days'].describe())
print("Same-day rows with listing_to_contract_days == 0:",
      (sold.loc[same_day, 'listing_to_contract_days'] == 0).sum())
print("Same-day, purchase before listing:", (sold.loc[same_day, 'listing_to_contract_days'] < 0).sum())

sold['same_day_listing_flag'] = same_day


# ---------- School districts ----------

districts = gpd.read_file(r'C:\Users\oybek\Downloads\IDX\DistrictAreas2425\DistrictAreas2425.shp')
districts['geometry'] = districts.geometry.make_valid()   # 7 polygons have invalid geometry
districts = districts.to_crs(epsg=4326)                   # same system as Latitude/Longitude

# Only use rows with usable coordinates
good_coords = ~(sold['missing_coordinates_flag'] | sold['zero_coordinates_flag'] |
                sold['positive_longitude_flag'] | sold['out_of_state_flag'])

points = gpd.GeoDataFrame(
    sold.loc[good_coords, ['Latitude', 'Longitude']],
    geometry=gpd.points_from_xy(sold.loc[good_coords, 'Longitude'], sold.loc[good_coords, 'Latitude']),
    crs='EPSG:4326')


def find_district(points, district_types, new_col):
    """Find the district for each home. Returns the district names and the homes in overlapping districts."""
    layer = districts[districts['DistrictTy'].isin(district_types)][['DistrictNa', 'DistrictTy', 'geometry']]
    joined = gpd.sjoin(points, layer, how='left', predicate='within')

    overlap_index = joined.index[joined.index.duplicated(keep=False)].unique()
    print(new_col, "- homes in overlapping districts:", len(overlap_index))

    # When a home matches two districts, keep the Elementary (or High) one, not the Unified one
    joined['priority'] = (joined['DistrictTy'] == 'Unified').astype(int)
    joined = joined.sort_values('priority')
    joined = joined[~joined.index.duplicated(keep='first')].sort_index()

    return joined['DistrictNa'].rename(new_col), overlap_index


sold['school_district'], overlap_elem = find_district(points, ['Elementary', 'Unified'], 'school_district')
sold['high_school_district'], overlap_high = find_district(points, ['High', 'Unified'], 'high_school_district')
sold['school_district_overlap_flag'] = sold.index.isin(overlap_elem)

print("\nRows with usable coordinates:", good_coords.sum())
print("school_district missing:", sold['school_district'].isnull().sum())
print("high_school_district missing:", sold['high_school_district'].isnull().sum())
print("\nschool_district value counts:\n", sold['school_district'].value_counts().head(10))


# ---------- Segment summaries ----------

def segment_summary(column):
    """Sales, median price, price per sqft, price ratio and days on market for each group of a column."""
    return sold.groupby(column).agg(
        sales=('ClosePrice', 'count'),
        median_close_price=('ClosePrice', 'median'),
        median_price_per_sqft=('price_per_sqft', 'median'),
        median_price_ratio=('price_ratio', 'median'),
        median_days_on_market=('DaysOnMarket', 'median')
    ).sort_values('sales', ascending=False)


# PropertyType shows only Residential because week 1 already filtered the other types
print("\nSummary by property type:\n", segment_summary('PropertyType'))
print("\nSummary by property subtype:\n", segment_summary('PropertySubType'))
print("\nSummary by county:\n", segment_summary('CountyOrParish').head(10))
print("\nSummary by MLS area (major):\n", segment_summary('MLSAreaMajor').head(10))
print("\nSummary by listing office:\n", segment_summary('ListOfficeName').head(10))
print("\nSummary by buyer office:\n", segment_summary('BuyerOfficeName').head(10))
print("\nSummary by school district:\n", segment_summary('school_district').head(10))


# ---------- Save ----------

sold.to_csv(r'C:\Users\oybek\Downloads\IDX\csv\sold_cleaned_with_rates_and_metrics.csv', index=False)

# ---------- Summary ----------

# New columns
# - price_ratio = ClosePrice / OriginalListPrice
#   (close_to_original_list_ratio is the same formula, as listed in the handbook)
# - price_per_sqft = ClosePrice / LivingArea
# - year, month, YrMo (from CloseDate)
# - listing_to_contract_days, contract_to_close_days
# - same_day_listing_flag, school_district, high_school_district, school_district_overlap_flag

# Checks
# - 2 rows had OriginalListPrice <= 0, so price_ratio is NaN for them (not removed). No infinite values.
# - Missing values come from missing inputs: price_ratio 760, price_per_sqft 236,
#   listing_to_contract_days 195, contract_to_close_days 194.
# - Negative day counts match the week 4 date flags: 239 negative contract_to_close_days
#   (= purchase_after_close_flag), and 267 + 239 = 506 (= negative_timeline_flag).
#   They were not removed. Outliers are handled in week 7.

# Same-day listings (ListingContractDate == CloseDate): 3,815 rows
# - 3,530 have listing_to_contract_days = 0 (listed, contracted and closed the same day)
# - 230 have PurchaseContractDate after CloseDate (230 of the 239 purchase_after_close rows)
# - 51 have PurchaseContractDate before ListingContractDate
# - 4 have no PurchaseContractDate
# - The cause of the odd rows is unknown. Rows were not removed, only flagged.

# School districts (CDE boundaries, 2024-25 school year; sales are Jan 2024 - Apr 2026)
# - Joined only the 409,649 rows with usable coordinates (not missing, zero,
#   positive longitude, or out of state). The other 4,206 rows have no district.
# - 110 of the 409,649 had no Elementary/Unified district, and 484 had no High district.
# - 1,678 homes are inside two overlapping districts (an Elementary district inside a Unified one,
#   for example Bass Lake Joint Union Elementary / Yosemite Unified). I kept the Elementary
#   district and marked these rows with school_district_overlap_flag. I did not check which is correct.
# - High school districts had no overlaps.

# Segment summaries (county, MLS area, property subtype, offices, school district)
# - Bay Area counties (Santa Clara, Alameda, San Mateo) have a median price_ratio above 1.
#   Inland counties (Riverside, San Bernardino) are below 1 and have more days on market.
# - 'PropertyType' shows only Residential because the week 1 filter already removed the other types.
# - groupby skips rows with a missing group name (for example, about 13% of rows have no MLSAreaMajor).
# - '699 - Not Defined' is the largest MLS area (43,422 sales). It is not a real area.
# - Some offices appear under two names (for example 'eXp Realty of California Inc' and
#   'eXp Realty of California, Inc.'). I did not merge them.
