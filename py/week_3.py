import pandas as pd

# Load the sold residential and listings residential datasets
sold = pd.read_csv(r'C:\Users\oybek\Downloads\IDX\csv\sold_residential_202401-202604.csv', low_memory=False)
listings = pd.read_csv(r'C:\Users\oybek\Downloads\IDX\csv\listing_residential_202401-202604.csv', low_memory=False)

# Fetch the mortgage rate data from FRED
url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=MORTGAGE30US"
mortgage = pd.read_csv(url, parse_dates=['observation_date'])
mortgage.columns = ['date', 'rate_30yr_fixed']

# Resample weekly rates to monthly averages
mortgage['year_month'] = mortgage['date'].dt.to_period('M')
mortgage_monthly = (mortgage.groupby('year_month')['rate_30yr_fixed'].mean().reset_index())

print("\nMortgage Monthly Rates:\n", mortgage_monthly.head())

# Create a matching year_month key on the MLS datasets

# Sold dataset — key off CloseDate
sold['year_month'] = pd.to_datetime(sold['CloseDate']).dt.to_period('M')

# Listings dataset — key off ListingContractDate
listings['year_month'] = pd.to_datetime(listings['ListingContractDate']).dt.to_period('M')

# Merge
sold_with_rates = sold.merge(mortgage_monthly, on='year_month', how='left')
listings_with_rates = listings.merge(mortgage_monthly, on='year_month', how='left')

# Validate the merge

# Check for any unmatched rows (rate should not be null)
print("\nSold rows with missing rates:", sold_with_rates['rate_30yr_fixed'].isnull().sum())
print("Listings rows with missing rates:", listings_with_rates['rate_30yr_fixed'].isnull().sum())

# Preview
print("\nSold Data with Mortgage Rates:")
print(sold_with_rates[['CloseDate', 'year_month', 'ClosePrice', 'rate_30yr_fixed']].head())
print("\nListings Data with Mortgage Rates:")
print(listings_with_rates[['ListingContractDate', 'year_month', 'ListPrice', 'rate_30yr_fixed']].head())

sold_with_rates.to_csv(r'C:\Users\oybek\Downloads\IDX\csv\sold_with_rates.csv', index=False)
listings_with_rates.to_csv(r'C:\Users\oybek\Downloads\IDX\csv\listings_with_rates.csv', index=False)

# ---------- SUMMARY ----------

# Mortgage rate merge (FRED MORTGAGE30US, weekly -> monthly average)
# Sold keyed on CloseDate, listings keyed on ListingContractDate (year_month)
# Validation: 0 null rates in sold_with_rates and listings_with_rates
