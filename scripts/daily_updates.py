import os
import requests
import pandas as pd
import numpy as np
from datetime import datetime
from paths import RAW_DATA_DIR

# ── 1. Fetch Holidays from API ────────────────────────────────────────────────

def update_holidays():
    print("Fetching Holidays from API...")
    current_year = datetime.now().year
    years_to_fetch = [current_year - 1, current_year]
    holidays_data = []

    for year in years_to_fetch:
        url = f"https://date.nager.at/api/v3/PublicHolidays/{year}/EG"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                holidays_data.extend(response.json())
        except requests.exceptions.RequestException as e:
            print(f"API Error for year {year}: {e}")

    # Convert data to DataFrame and save as Parquet
    if holidays_data:
        holidays_df = pd.DataFrame(holidays_data)[['date', 'name']]
        holidays_df.rename(columns={'date': 'Date', 'name': 'HolidayName'}, inplace=True)
        
        # Ensure data type and export
        holidays_df['Date'] = pd.to_datetime(holidays_df['Date']).dt.date
        
        holidays_file = RAW_DATA_DIR / 'Dynamic_Holidays.parquet'
        holidays_df.to_parquet(holidays_file, engine='pyarrow', index=False)
        print(f"Holidays updated successfully and saved to {holidays_file.name}.")
    else:
        print("Failed to fetch holidays. Historical data will be used if available.")


# ── 2. Change Data Capture (CDC) ──────────────────────────────────────────────

MASTER_FILE = RAW_DATA_DIR / 'AR_Invoices_950K.parquet'

def generate_daily_delta():
    """Simulate daily SAP extraction report (~1000 new/updated invoices)"""
    print("Generating Daily Delta...")
    
    if not MASTER_FILE.exists():
        print(f"Error: Master file not found at {MASTER_FILE}")
        return pd.DataFrame()
        
    # 1. Read a subset of historical data to change status (simulate customer payments)
    master_df = pd.read_parquet(MASTER_FILE)
    open_invoices_mask = master_df['Status'] == 'Open'
    
    # Check if we have enough open invoices
    if master_df[open_invoices_mask].shape[0] < 500:
        open_invoices = master_df[open_invoices_mask]
    else:
        open_invoices = master_df[open_invoices_mask].sample(500)
        
    open_invoices['Status'] = 'Cleared' # Update status
    
    # 2. Generate new invoices for the current day
    start_idx = len(master_df) + 1
    new_invoices = pd.DataFrame({
        'InvoiceID': [f"INV-NEW-{np.random.randint(1000000, 9999999)}" for _ in range(500)],
        'CustomerID': np.random.choice(master_df['CustomerID'].unique(), 500),
        'PostingDate': pd.to_datetime('today').normalize(),
        'Amount': np.round(np.random.uniform(1000.0, 50000.0, 500), 2),
        'Status': 'Open'
    })
    
    # Ensure new InvoiceIDs are unique
    new_invoices.drop_duplicates(subset='InvoiceID', inplace=True)
    
    # Combine updates and new invoices into "daily report"
    daily_delta = pd.concat([open_invoices, new_invoices])
    # Ensure delta has no internal duplicate InvoiceIDs
    daily_delta.drop_duplicates(subset='InvoiceID', keep='last', inplace=True)
    return daily_delta

def apply_cdc(daily_df):
    """Apply Change Data Capture logic to update the master file"""
    if daily_df.empty:
        print("No daily delta to apply.")
        return
        
    print("Applying CDC (Upsert)...")
    
    if MASTER_FILE.exists():
        # Load historical data
        master_df = pd.read_parquet(MASTER_FILE)
        
        # Append the new/updated records to the bottom
        combined_df = pd.concat([master_df, daily_df], ignore_index=True)
        
        # Drop duplicates across 'InvoiceID', keeping the last (newest/updated) one
        final_df = combined_df.drop_duplicates(subset='InvoiceID', keep='last').reset_index(drop=True)
    else:
        # If file does not exist, daily delta becomes the baseline
        final_df = daily_df.reset_index(drop=True)
        
    # Overwrite the Parquet file
    final_df.to_parquet(MASTER_FILE, engine='pyarrow', index=False)
    print(f"CDC Complete. Total records in Master: {len(final_df)}")

# ── Execution ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Fetch Holidays
    update_holidays()
    
    print("-" * 50)
    
    # 1. Generate daily report (Simulating SAP)
    daily_report = generate_daily_delta()
    
    # 2. Apply updates to the database (Parquet Master)
    apply_cdc(daily_report)
