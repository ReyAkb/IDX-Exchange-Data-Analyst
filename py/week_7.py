import pandas as pd
import numpy as np


# ---------- Load the data ----------

sold = pd.read_csv(r'C:\Users\oybek\Downloads\IDX\csv\sold_cleaned_with_rates_and_metrics.csv', low_memory=False)

# ---------- Business rules (always invalid) ----------

# These were already removed in week 4, so we only check that none are left
print("\nClosePrice <= 0:", (sold['ClosePrice'] <= 0).sum())
print("LivingArea <= 0:", (sold['LivingArea'] <= 0).sum())
print("DaysOnMarket < 0:", (sold['DaysOnMarket'] < 0).sum())

# ClosePrice under 1% of ListPrice looks like a price typed in thousands or millions
# (for example 675 instead of 675,000). Real cheap sales like timeshares are not caught.
sold['bad_close_price_flag'] = sold['ClosePrice'] < 0.01 * sold['ListPrice']
print("\nbad_close_price_flag:", sold['bad_close_price_flag'].sum())

# price_ratio far from 1 in either direction cannot be trusted
sold['bad_price_ratio_flag'] = (sold['price_ratio'] > 3) | (sold['price_ratio'] < 0.2)
print("bad_price_ratio_flag:", sold['bad_price_ratio_flag'].sum())

# The rows stay, only the broken ratios are set to missing
sold.loc[sold['bad_price_ratio_flag'] | sold['bad_close_price_flag'],
         ['price_ratio', 'close_to_original_list_ratio']] = np.nan

# LivingArea under 100 sq ft is a placeholder, not a real home
sold['bad_living_area_flag'] = sold['LivingArea'] < 100
print("bad_living_area_flag:", sold['bad_living_area_flag'].sum())

# price_per_sqft makes no sense for those rows
sold.loc[sold['bad_living_area_flag'] | sold['bad_close_price_flag'], 'price_per_sqft'] = np.nan

# Check for other bad values hiding near the cutoffs
print("\nLivingArea between 100 and 300:", ((sold['LivingArea'] >= 100) & (sold['LivingArea'] < 300)).sum())
print("price_ratio between 0.2 and 0.5:", ((sold['price_ratio'] >= 0.2) & (sold['price_ratio'] < 0.5)).sum())

print("\nSample of rows with price_ratio between 0.2 and 0.5:")
print(sold.loc[(sold['price_ratio'] >= 0.2) & (sold['price_ratio'] < 0.5),
               ['ClosePrice', 'OriginalListPrice', 'ListPrice']].head(10))


# ---------- Look at the percentiles first ----------

outlier_columns = ['ClosePrice', 'LivingArea', 'DaysOnMarket', 'price_per_sqft', 'price_ratio']

print("\nPercentiles:\n",
      sold[outlier_columns].describe(percentiles=[0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99]).transpose())


# ---------- How many rows each multiplier would flag ----------

# Only the three required fields are used for removing rows
required_columns = ['ClosePrice', 'LivingArea', 'DaysOnMarket']

print("\nShare of rows flagged by multiplier (three required fields):")
for k in [1.5, 2.0, 3.0]:
    flagged_any = pd.Series(False, index=sold.index)
    for col in required_columns:
        Q1, Q3 = sold[col].quantile(0.25), sold[col].quantile(0.75)
        IQR = Q3 - Q1
        flagged_any = flagged_any | (sold[col] < Q1 - k * IQR) | (sold[col] > Q3 + k * IQR)
    print("k =", k, "->", round(flagged_any.mean() * 100, 2), "% flagged")


# ---------- IQR bounds ----------

# 1.5 flags about 16% of rows (too many real sales), 3.0 flags about 6% (only the extreme ones)
MULTIPLIER = 3.0

# Bounds are calculated once on the full data, so the order of the columns does not matter
bounds = {}

for col in outlier_columns:
    Q1 = sold[col].quantile(0.25)
    Q3 = sold[col].quantile(0.75)
    IQR = Q3 - Q1
    bounds[col] = (Q1 - MULTIPLIER * IQR, Q3 + MULTIPLIER * IQR)

bounds_table = pd.DataFrame(bounds, index=['lower', 'upper']).transpose()
print("\nIQR bounds (multiplier =", MULTIPLIER, "):\n", bounds_table)


# ---------- Outlier flags (nothing is deleted here) ----------

# A missing value is not flagged, because NaN is never smaller or bigger than a number
for col in outlier_columns:
    lower, upper = bounds[col]
    sold[col + '_outlier_flag'] = (sold[col] < lower) | (sold[col] > upper)

flag_columns = [col + '_outlier_flag' for col in outlier_columns]

# Rows are removed only for the three required fields and the two business rules on the row itself
required_flags = ['ClosePrice_outlier_flag', 'LivingArea_outlier_flag', 'DaysOnMarket_outlier_flag']
sold['any_outlier_flag'] = (sold[required_flags].any(axis=1)
                            | sold['bad_living_area_flag']
                            | sold['bad_close_price_flag'])

print("\nRows flagged for each column:\n", sold[flag_columns].sum())
print("Rows flagged for removal (any_outlier_flag):", sold['any_outlier_flag'].sum())
print("Share of rows flagged: {:.2f}%".format(sold['any_outlier_flag'].mean() * 100))


# ---------- Filtered dataset ----------

sold_filtered = sold[~sold['any_outlier_flag']].copy()
print("\nRows in full flagged dataset:", len(sold))
print("Rows in filtered dataset:", len(sold_filtered))


# ---------- Before and after comparison ----------

comparison = pd.DataFrame({
    'rows_before': sold[outlier_columns].count(),
    'rows_after': sold_filtered[outlier_columns].count(),
    'median_before': sold[outlier_columns].median(),
    'median_after': sold_filtered[outlier_columns].median(),
    'mean_before': sold[outlier_columns].mean(),
    'mean_after': sold_filtered[outlier_columns].mean()
})
comparison['median_change_%'] = ((comparison['median_after'] / comparison['median_before'] - 1) * 100).round(2)
comparison['mean_change_%'] = ((comparison['mean_after'] / comparison['mean_before'] - 1) * 100).round(2)

pd.set_option('display.width', 200)
pd.set_option('display.max_columns', None)
print("\nBefore vs after filtering:\n", comparison.round(2))


# ---------- Save ----------

sold.to_csv(r'C:\Users\oybek\Downloads\IDX\csv\sold_flagged.csv', index=False)
sold_filtered.to_csv(r'C:\Users\oybek\Downloads\IDX\csv\sold_filtered.csv', index=False)
comparison.round(2).to_csv(r'C:\Users\oybek\Downloads\IDX\csv\before_after_comparison.csv')


# ---------- Summary ----------

# Method
# - IQR method with a multiplier of 3.0: lower = Q1 - 3 * IQR, upper = Q3 + 3 * IQR, calculated once on
#   the full data. I tried 1.5, 2.0 and 3.0 on ClosePrice, LivingArea and DaysOnMarket. They flagged
#   15.7%, 10.95% and 5.89% of rows. 1.5 removed many real sales (expensive homes and slow sales),
#   so I used 3.0 to catch only the extreme values.
# - Bounds at 3.0: ClosePrice up to about 3,475,000, LivingArea up to 5,132 sq ft, DaysOnMarket up to 168 days.
# - Outliers were flagged, not deleted. The full dataset keeps every row.
# - Rows are removed in the filtered dataset only for ClosePrice, LivingArea or DaysOnMarket outliers,
#   or the two business rules below. price_per_sqft and price_ratio are flagged but not used to remove rows.
# - Rows with a missing value are not flagged.

# Business rules (applied before IQR)
# - 10 rows had ClosePrice under 1% of ListPrice (price typed in thousands or millions, for example
#   675 instead of 675,000). Marked with bad_close_price_flag and removed from the filtered dataset.
#   Timeshares with low prices were kept.
# - 5 rows had LivingArea under 100 sq ft. Marked with bad_living_area_flag and removed from the filtered dataset.
# - 1,072 rows had price_ratio above 3 or below 0.2, mostly because OriginalListPrice has missing or extra
#   digits. Rows kept, price_ratio set to missing, marked with bad_price_ratio_flag.
# - Rows with price_ratio between 0.2 and 0.5 (214 rows) look like real price cuts, so they were kept.
# - 126 rows have LivingArea between 100 and 300 sq ft. I did not change them.
# - The cutoffs (1%, 100, 3, 0.2) are my choice.

# Dataset size
# - Full flagged dataset: 413,855 rows
# - Filtered dataset: 389,484 rows (24,371 removed, 5.89%)

# Medians before and after filtering
# - ClosePrice: 823,000 -> 805,000 (-2.19%)
# - LivingArea: 1,643 -> 1,611 (-1.95%)
# - DaysOnMarket: 18 -> 17 (-5.56%)
# - price_per_sqft: 537.49 -> 531.05 (-1.20%)
# - price_ratio: 1.00 -> 1.00 (+0.44%)

# Notes
# - The means changed much more than the medians (ClosePrice mean -17.64% vs median -2.19%),
#   so the extreme values were pulling the averages up.
# - Home prices and days on market are skewed to the right, so IQR also flags real expensive or
#   slow sales. This is why I did not use 1.5.
# - price_ratio_outlier_flag marks 10,760 rows, but they are not removed from the filtered dataset.

# Saved files
# - sold_flagged_week7.csv: full dataset (413,855 rows) with all flag columns, no rows removed.
#   New flag columns: bad_close_price_flag, bad_price_ratio_flag, bad_living_area_flag,
#   one IQR flag for each of ClosePrice, LivingArea, DaysOnMarket, price_per_sqft and price_ratio,
#   and any_outlier_flag (decides which rows are removed in the filtered dataset).
# - sold_filtered_week7.csv: analysis dataset (389,484 rows) without the rows where any_outlier_flag is True.
#   Same columns as the flagged file.
# - week7_before_after_comparison.csv: row counts, medians and means before and after filtering.
# - In both datasets, price_ratio and price_per_sqft are blank for rows with a bad ClosePrice,
#   bad price_ratio or bad LivingArea. The original values are still in the week 6 file
#   (sold_cleaned_with_rates_and_metrics.csv), which was not changed.
