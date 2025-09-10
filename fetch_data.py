import yfinance as yf

# Download last 5 days of NIFTY 50, 1-minute interval
print("Fetching NIFTY 1-min data...")
df = yf.download("^NSEI", interval="1m", period="5d")

# Save to data/nifty_1min.csv
output_file = "data/nifty_1min.csv"
df.to_csv(output_file)
print(f"Saved {len(df)} rows to {output_file}")
