# Data Lineage — AR Financial Tracking System

> **Document:** `docs/datalineage.md`  
> **Version:** 1.3 · 2026-04-20  
> **Scope:** End-to-end column-level data lineage from synthetic generation through ETL to output layer

---

## Overview

```
Source (Synthetic)          Raw Layer (Parquet)    ETL Layer                    Output Layer
─────────────────           ──────────             ─────────                    ────────────
Faker · NumPy         →   data/raw/*.parquet  →   Data_Model_Engine.xlsx   →   Dashboards
                            (pyarrow engine)    →   (Power Query M)            →   User_Comments.xlsx
Nager Date API        →   Dynamic_Holidays     →   dim_Date                 →   Analytical Model
(scripts/daily_updates.py) (Parquet · pyarrow)      (date dimension)

Daily Delta (CDC)     →   AR_Invoices_950K     (Upsert · dedup · overwrite)
(scripts/daily_updates.py) .parquet master file
```

| Layer | Location | Format | Owner |
|-------|----------|--------|-------|
| **Generation** | `notebooks/data_generator.ipynb` | In-memory (Pandas) | Python |
| **Raw (Parquet)** | `data/raw/` | Parquet (pyarrow) | File system |
| **ETL / Model** | `etl/Data_Model_Engine.xlsx` | Excel / Power Query | Power Query M |
| **Holidays API** | Nager Date API (`/api/v3/PublicHolidays/{year}/EG`) | JSON → Parquet | External / Python |
| **Daily Updates** | `scripts/daily_updates.py` | Python → Parquet | Python |
| **Activity** | `notebooks/user_comments_generator.ipynb` | In-memory → XLSX | Python |
| **Output** | `data/output/` | XLSX | File system |

---

## Stage 1 — Data Generation (`data_generator.ipynb`)

### 1.1 dim_Customers → `Customers_Master.parquet`

| Column | Source | Generation Method | Notes |
|--------|--------|-------------------|-------|
| `CustomerID` | Computed | `f'C-{(i+1):05d}'` for i in 0…9,999 | Sequential, zero-padded |
| `CustomerName` | Faker | `Faker().company()` | Random company names |
| `PaymentTerms` | NumPy | `np.random.choice([30, 60, 90, 120])` | Uniform distribution |

**Output:** `data/raw/Customers_Master.parquet` — 10,000 rows · ~0.2 MB

---

### 1.2 fact_AR_Invoices → `AR_Invoices_950K.parquet`

| Column | Source | Generation Method | Notes |
|--------|--------|-------------------|-------|
| `InvoiceID` | Computed | `f'INV-{(i+1):07d}'` for i in 0…949,999 | Sequential, zero-padded |
| `CustomerID` | Sampled | `np.random.choice(customers_df['CustomerID'])` | FK → dim_Customers |
| `PostingDate` | Vectorized | `start_date + pd.to_timedelta(random_days, unit='D')` | Uniform over 730-day window |
| `Amount` | Vectorized | `np.round(np.random.uniform(100.0, 150000.0), 2)` | Uniform distribution |
| `Status` | Vectorized | `np.random.choice(['Open','Partial','Cleared'], p=[0.4,0.2,0.4])` | Weighted probability |

**Date window:** today − 730 days → today  
**Output:** `data/raw/AR_Invoices_950K.parquet` — 950,000 rows · ~13 MB (was ~58 MB as CSV)

---

### 1.3 fact_Bank_Documents → `Bank_Documents_Tracking.parquet`

| Column | Source | Generation Method | Notes |
|--------|--------|-------------------|-------|
| `DocID` | Computed | `f'DOC-{(i+1):06d}'` for i in 0…NUM_BANK_DOCS | Sequential |
| `InvoiceID` | Filtered + Sampled | `np.random.choice(pending_invoices, replace=False)` | FK → fact_AR_Invoices; only Open/Partial |
| `BankSubmissionDate` | Derived | `posting_dates[:N] + pd.to_timedelta(random 5–30 days)` | PostingDate + offset |
| `DocStatus` | Vectorized | `np.random.choice(['Under Review','Accepted','Rejected'], p=[0.6,0.3,0.1])` | Weighted probability |

**Filter rule:** `Status IN ('Open', 'Partial')` → 70% of those rows selected  
**Output:** `data/raw/Bank_Documents_Tracking.parquet` — ~399,219 rows · ~5 MB (was ~24 MB as CSV)

---

### 1.4 DQA Gate (inline in notebook)

| Check | Logic | Expected Result |
|-------|-------|-----------------|
| Invoice count | `len(invoices_df)` | 950,000 |
| Customer count | `len(customers_df)` | 10,000 |
| Bank doc count | `len(bank_docs_df)` | ~399,219 |
| Referential integrity | `invoices_df[~invoices_df['CustomerID'].isin(customers_df['CustomerID'])]` | 0 orphan rows |

---

## Stage 2 — ETL Transformation (`etl/Data_Model_Engine.xlsx`)

Powered by **Power Query M-Language**. Connects directly to `data/raw/` Parquet files.

### 2.1 Load Queries

| Query Name | Source File | Row Count | Load Mode |
|------------|-------------|-----------|-----------|
| `raw_Invoices` | `data/raw/AR_Invoices_950K.parquet` | 950,000 | Connection only |
| `raw_Customers` | `data/raw/Customers_Master.parquet` | 10,000 | Connection only |
| `raw_BankDocs` | `data/raw/Bank_Documents_Tracking.parquet` | ~399,219 | Connection only |

---

### 2.2 Transformation — Column Lineage

#### `fact_AR_Invoices` (enriched)

| Output Column | Source Column | Transformation | Step |
|---------------|---------------|----------------|------|
| `InvoiceID` | `raw_Invoices[InvoiceID]` | Type cast → `text` | Clean |
| `CustomerID` | `raw_Invoices[CustomerID]` | Type cast → `text` | Clean |
| `CustomerName` | `raw_Customers[CustomerName]` | Merge join on `CustomerID` | Join |
| `PaymentTerms` | `raw_Customers[PaymentTerms]` | Merge join on `CustomerID` | Join |
| `PostingDate` | `raw_Invoices[PostingDate]` | Type cast → `datetime` | Clean |
| `Amount` | `raw_Invoices[Amount]` | Type cast → `decimal` | Clean |
| `Status` | `raw_Invoices[Status]` | Type cast → `text` | Clean |
| `DaysOutstanding` | `PostingDate` | `Date.From(DateTime.LocalNow()) - Date.From([PostingDate])` | Enrich |
| `AgingBucket` | `DaysOutstanding` | `if [DaysOutstanding] <= 30 then "0-30d" else if [DaysOutstanding] <= 60 then "31-60d" else if [DaysOutstanding] <= 90 then "61-90d" else "90+d"` | Enrich |
| `IsOverdue` | `DaysOutstanding`, `Status` | `[DaysOutstanding] > 60 and [Status] <> "Cleared"` | Flag |

---

#### `fact_Bank_Documents` (enriched)

| Output Column | Source Column | Transformation | Step |
|---------------|---------------|----------------|------|
| `DocID` | `raw_BankDocs[DocID]` | Type cast → `text` | Clean |
| `InvoiceID` | `raw_BankDocs[InvoiceID]` | Type cast → `text` | Clean |
| `BankSubmissionDate` | `raw_BankDocs[BankSubmissionDate]` | Type cast → `datetime` | Clean |
| `DocStatus` | `raw_BankDocs[DocStatus]` | Type cast → `text` | Clean |
| `Amount` | `fact_AR_Invoices[Amount]` | Merge join on `InvoiceID` | Join |
| `PostingDate` | `fact_AR_Invoices[PostingDate]` | Merge join on `InvoiceID` | Join |
| `SubmissionLag` | `BankSubmissionDate`, `PostingDate` | `Date.From([BankSubmissionDate]) - Date.From([PostingDate])` | Enrich |

---

### 2.3 KPI Measures (computed in Power Query / data model)

| KPI | Formula | Source Columns |
|-----|---------|----------------|
| `Total AR Outstanding` | `SUM(Amount WHERE Status IN ('Open','Partial'))` | `Amount`, `Status` |
| `Days Sales Outstanding (DSO)` | `(AR Balance / Credit Sales) × Days in Period` | `Amount`, `PostingDate` |
| `Collection Rate %` | `COUNT(Cleared) / COUNT(*) × 100` | `Status` |
| `Bank Acceptance Rate %` | `COUNT(DocStatus='Accepted') / COUNT(*) × 100` | `DocStatus` |
| `Overdue Rate %` | `COUNT(IsOverdue=true) / COUNT(Open+Partial) × 100` | `IsOverdue`, `Status` |

---

### 2.4 ETL Step Order

```
Step 1:  Load raw_Customers         → 10,000 rows
Step 2:  Load raw_Invoices          → 950,000 rows
Step 3:  Load raw_BankDocs          → ~399,219 rows
Step 4:  Clean types — Invoices     → cast Date, Decimal, Text
Step 5:  Clean types — Customers    → cast Int, Text
Step 6:  Clean types — BankDocs     → cast DateTime, Text
Step 7:  Join Invoices ← Customers  → LEFT JOIN on CustomerID → +CustomerName, +PaymentTerms
Step 8:  Compute DaysOutstanding    → adds column
Step 9:  Compute AgingBucket        → adds column (conditional)
Step 10: Flag IsOverdue             → adds boolean column
Step 11: Join BankDocs ← Invoices   → LEFT JOIN on InvoiceID → +Amount, +PostingDate
Step 12: Compute SubmissionLag      → adds column
Step 13: Fetch Dynamic_Holidays     → API call for EG public holidays (current + prior year)
Step 14: Build dim_Date             → calendar from PostingDate range; join holidays
Step 15: Load to data model         → available for dashboard queries
```

---

## Stage 2.5 — Power Query: `Dynamic_Holidays`

Fetches Egyptian public holidays from the **Nager Date API** for the current and previous year. Implemented with fault-tolerant `try…otherwise null` to avoid query failures when the API is offline.

### Column Lineage

| Output Column | Source | Transformation | Step |
|---------------|--------|----------------|------|
| `Date` | `Nager Date API[date]` | `Table.ExpandRecordColumn` → cast `type date` | Expand + TypeCast |
| `HolidayName` | `Nager Date API[name]` | `Table.ExpandRecordColumn` → cast `type text` | Expand + TypeCast |

### Query Step Sequence

| # | Step Name | M Operation | Output |
|---|-----------|-------------|--------|
| 1 | `CurrentYear` | `Date.Year(DateTime.LocalNow())` | Int — current year |
| 2 | `YearsList` | `{CurrentYear - 1, CurrentYear}` | List of 2 years |
| 3 | `GetHolidays` | `(Year) => try Json.Document(Web.Contents(ApiUrl)) otherwise null` | Function |
| 4 | `FetchData` | `List.Transform(YearsList, each GetHolidays(_))` | List of 2 responses |
| 5 | `RemoveNulls` | `List.RemoveNulls(FetchData)` | List (no failed calls) |
| 6 | `CombinedList` | `List.Combine(RemoveNulls)` | Flat list of records |
| 7 | `ConvertedToTable` | `Table.FromList(CombinedList, ...)` | Table[Column1] |
| 8 | `ExpandedColumn` | `Table.ExpandRecordColumn(... {"date","name"} ...)` | Table[Date, HolidayName] |
| 9 | `ChangedType` | `Table.TransformColumnTypes(... type date, type text)` | **Final output** |

> **Load mode:** Connection only (not loaded to data model — consumed by `dim_Date`).

---

## Stage 2.6 — Power Query: `dim_Date`

Builds a **dynamic date dimension** spanning whole calendar years (Jan 1 → Dec 31) derived from `Fact_AR_Invoices[PostingDate]`. Merges `Dynamic_Holidays` to flag public holidays, and applies Egyptian banking weekend logic (Fri = day 5, Sat = day 6).

### Column Lineage

| Output Column | Source | Transformation | Step |
|---------------|--------|----------------|------|
| `Date` | `List.Dates(StartDate, DayCount, ...)` | Generated sequence → `type date` | Generate |
| `Year` | `[Date]` | `Date.Year([Date])` | Derived |
| `MonthNum` | `[Date]` | `Date.Month([Date])` | Derived |
| `DayOfWeekNum` | `[Date]` | `Date.DayOfWeek([Date], Day.Sunday)` | Derived (0=Sun … 6=Sat) |
| `DayName` | `[Date]` | `Date.DayOfWeekName([Date], "en-US")` | Derived |
| `IsWeekend` | `[DayOfWeekNum]` | `= 5 OR = 6` (Fri/Sat) → `type logical` | Flag |
| `HolidayName` | `Dynamic_Holidays[HolidayName]` | `LeftOuter Join` on `Date`; `null` → `"Working Day"` or `"Weekend"` | Join + Replace |
| `IsBankingWorkingDay` | `[IsWeekend]`, `[HolidayName]` | `NOT (IsWeekend OR HolidayName <> null)` → `type logical` | Flag |

### Query Step Sequence

| # | Step Name | M Operation | Output |
|---|-----------|-------------|--------|
| 1 | `BufferedDates` | `List.Buffer(Fact_AR_Invoices[PostingDate])` | In-memory date list |
| 2 | `MinFactDate / MaxFactDate` | `List.Min / List.Max(BufferedDates)` | Boundary dates |
| 3 | `StartDate / EndDate` | `#date(Year, 1, 1)` / `#date(Year, 12, 31)` | Full-year boundaries |
| 4 | `DayCount` | `Duration.Days(EndDate - StartDate) + 1` | Integer count |
| 5 | `SourceList` | `List.Dates(StartDate, DayCount, #duration(1,0,0,0))` | List of dates |
| 6 | `CalendarBase` | `Table.FromList → TransformColumnTypes(type date)` | Table[Date] |
| 7 | `InsertYear … InsertDayName` | `Table.AddColumn` × 4 | +Year, +MonthNum, +DayOfWeekNum, +DayName |
| 8 | `InsertIsWeekend` | `DayOfWeekNum = 5 OR = 6` | +IsWeekend (logical) |
| 9 | `MergeHolidays` | `Table.NestedJoin(... Dynamic_Holidays ... LeftOuter)` | +nested HolidayData |
| 10 | `ExpandHolidays` | `Table.ExpandTableColumn(... {"HolidayName"})` | +HolidayName |
| 11 | `InsertIsWorkingDay` | `NOT (IsWeekend OR HolidayName <> null)` | +IsBankingWorkingDay |
| 12 | `ReplaceNullHolidays` | `Table.ReplaceValue(null → "Weekend" / "Working Day")` | HolidayName filled |
| 13 | `#"Changed Type"` | `TransformColumnTypes(HolidayName → type text)` | **Final output** |

> **Load mode:** Loaded to data model. Joins to `fact_AR_Invoices` on `PostingDate = Date`.

---

## Stage 3 — Collection Activity (`user_comments_generator.ipynb`)

### 3.1 Input

| Source | Column(s) Used | Filter Applied |
|--------|---------------|----------------|
| `data/raw/AR_Invoices_950K.parquet` | `InvoiceID`, `Status` | `Status IN ('Open', 'Partial')` → ~570,313 rows |

---

### 3.2 Column Lineage → `User_Comments.xlsx`

| Output Column | Source | Generation Method | Notes |
|---------------|--------|-------------------|-------|
| `InvoiceID` | `AR_Invoices_950K.parquet[InvoiceID]` | `np.random.choice(open_invoices, 5000, replace=False)` | Sampled without replacement |
| `ContactDate` | System | `datetime.today().date()` | Run date |
| `FollowUpNote` | Constant list | `np.random.choice(follow_up_templates)` | 8 templates, uniform |
| `PromisedDate` | `ContactDate` | `ContactDate + timedelta(days=randint(1,14))` | 1–14 days ahead |
| `CollectorName` | Constant list | `np.random.choice(['Ahmed','Sara','Omar','Nour','Yasmin'])` | 5 collectors, uniform |

**Output:** `data/output/User_Comments.xlsx` — 5,000 rows

---

### 3.3 Sampling Logic

```
total invoices        = 950,000
eligible (Open/Partial) ≈ 570,313  (40% + 20% = ~60%)
sampled               = 5,000       (0.88% of eligible)
method                = np.random.choice(..., replace=False)
seed                  = np.random.seed(42)  [reproducible]
```

---

## Stage 4 — Daily Updates (`scripts/daily_updates.py`)

A standalone Python script that runs **outside** the notebook pipeline on a daily schedule (or on demand). It performs two independent tasks:

### 4.1 `update_holidays()` — Live Holiday Refresh

Fetches Egyptian public holidays from the **Nager Date API** and persists them as a Parquet file, replacing the Power Query-only approach with a Python-owned artefact.

| Output Column | Source | Transformation | Notes |
|---------------|--------|----------------|-------|
| `Date` | `Nager Date API[date]` | `pd.to_datetime(...).dt.date` | Cast to `date` (no time) |
| `HolidayName` | `Nager Date API[name]` | Column rename | Official EN holiday name |

**Output:** `data/raw/Dynamic_Holidays.parquet` — varies (~20–25 rows per year × 2 years)

**Fault tolerance:** `requests.exceptions.RequestException` is caught per year; only successful years are written. If both years fail, no file is written and a warning is printed.

---

### 4.2 `apply_cdc()` — Change Data Capture Upsert

Simulates a daily **SAP extraction report** and applies CDC (upsert) logic to the master invoice Parquet file.

#### `generate_daily_delta()` — Daily Delta Simulation

| Operation | Description | Volume |
|-----------|-------------|--------|
| Status update | Sample 500 `Open` invoices → set `Status = 'Cleared'` | 500 rows updated |
| New invoices | Generate 500 fresh `INV-NEW-{7-digit}` invoices with today's date | 500 rows inserted |
| Deduplication | `drop_duplicates(subset='InvoiceID', keep='last')` applied to delta | Ensures clean delta |

#### `apply_cdc()` — Upsert Logic

```
1. Load master   →  pd.read_parquet(AR_Invoices_950K.parquet)
2. Concat        →  pd.concat([master_df, daily_df], ignore_index=True)
3. Dedup/Upsert  →  drop_duplicates(subset='InvoiceID', keep='last')
                    ↑ updates existing rows (daily overrides master)
                    ↑ inserts new rows (not in master → kept)
4. Overwrite     →  final_df.to_parquet(MASTER_FILE, engine='pyarrow')
```

**Net effect per daily run:** ~500 invoices updated (Open → Cleared) + ~500 new invoices inserted → master grows by ~500 rows net.

---

## Full Column-Level Lineage Map

```
Faker.company()           ──→  Customers_Master.parquet[CustomerName]
                                        │
                                        ▼ JOIN (CustomerID)
np.random.uniform()       ──→  AR_Invoices_950K.parquet[Amount]           ──→  fact_AR_Invoices[Amount]
np.random.choice(Status)  ──→  AR_Invoices_950K.parquet[Status]           ──→  fact_AR_Invoices[Status]
pd.to_timedelta()         ──→  AR_Invoices_950K.parquet[PostingDate]       ──→  fact_AR_Invoices[PostingDate]
                                        │                                             │
                                        │ (filter: Open/Partial × 0.7)               │ PostingDate range
                                        ▼                                             ▼
np.random.choice(status)  ──→  Bank_Documents_Tracking.parquet[DocStatus] ──→  fact_Bank_Documents[DocStatus]
posting_dates + offset    ──→  Bank_Documents_Tracking.parquet[BankSubmissionDate]   │
                                                                                      │
                                  Date.Now() - PostingDate ──────────────→  DaysOutstanding (computed)
                                  conditional   ───────────────────────→  AgingBucket     (computed)
                                  DaysOutstanding > 60  ──────────────→  IsOverdue       (computed)

Nager Date API (/EG)      ──→  Dynamic_Holidays.parquet[Date, HolidayName]   (scripts/daily_updates.py)
  also Power Query        ──→  Dynamic_Holidays helper query                  (etl/Data_Model_Engine.xlsx)
                                        │
                                        ▼ LEFT JOIN on Date
fact_AR_Invoices[PostingDate] ──→  dim_Date[Date]           (boundary source)
List.Dates(...)            ──→  dim_Date[Date]           (generated sequence)
Date.Year/Month/DayOfWeek  ──→  dim_Date[Year, MonthNum, DayOfWeekNum, DayName]
DayOfWeekNum ∈ {5,6}       ──→  dim_Date[IsWeekend]
Dynamic_Holidays[HolidayName] ──→  dim_Date[HolidayName]
NOT(IsWeekend OR Holiday)  ──→  dim_Date[IsBankingWorkingDay]

AR_Invoices_950K.parquet  ──→  [filter Open/Partial, sample 5K]
  [InvoiceID]             ──→  User_Comments.xlsx[InvoiceID]
datetime.today()          ──→  User_Comments.xlsx[ContactDate]
templates list            ──→  User_Comments.xlsx[FollowUpNote]
ContactDate + randint()   ──→  User_Comments.xlsx[PromisedDate]
collectors list           ──→  User_Comments.xlsx[CollectorName]

── CDC (daily_updates.py) ────────────────────────────────────────────────────
AR_Invoices_950K.parquet  ──→  sample 500 Open  ──→  Status='Cleared'  (update)
INV-NEW-{random}           ──→  500 new invoices ──→  Status='Open'     (insert)
combined + dedup           ──→  AR_Invoices_950K.parquet                (overwrite)
```

---

## File Dependency Graph

```
data_generator.ipynb
    │
    ├──→ data/raw/Customers_Master.parquet
    │           │
    │           └──→ etl/Data_Model_Engine.xlsx  ──→  Analytical Model
    │                           ▲
    ├──→ data/raw/AR_Invoices_950K.parquet ──┤
    │           │               ▲         │
    │           │               │         └──── [PostingDate boundaries] ──→ dim_Date
    │           │
    │           ├──→ user_comments_generator.ipynb
    │           │               │
    │           │               └──→ data/output/User_Comments.xlsx
    │           │
    │           └──→ scripts/daily_updates.py  (CDC Upsert)
    │                           │
    │                           └──→ data/raw/AR_Invoices_950K.parquet  (overwrite)
    │
    ├──→ data/raw/Bank_Documents_Tracking.parquet ──→ etl/Data_Model_Engine.xlsx
    │
    └── Nager Date API ──→ scripts/daily_updates.py
                                  │
                                  ├──→ data/raw/Dynamic_Holidays.parquet
                                  │
                                  └── Power Query ──→ Dynamic_Holidays (helper)
                                                               │
                                                               └──→ dim_Date  ──→  etl/
```

---

## Data Contracts

### `Customers_Master.parquet`

| Column | Type | Nullable | Unique | Range / Values |
|--------|------|----------|--------|----------------|
| `CustomerID` | VARCHAR(10) | No | Yes (PK) | `C-00001` … `C-10000` |
| `CustomerName` | VARCHAR(255) | No | No | Faker company names |
| `PaymentTerms` | INT | No | No | `{30, 60, 90, 120}` |

### `AR_Invoices_950K.parquet` (master — updated by CDC)

| Column | Type | Nullable | Unique | Range / Values |
|--------|------|----------|--------|----------------|
| `InvoiceID` | VARCHAR(15) | No | Yes (PK) | `INV-0000001` … `INV-0950000`; `INV-NEW-{7-digit}` for CDC inserts |
| `CustomerID` | VARCHAR(10) | No | No (FK) | Must exist in Customers_Master |
| `PostingDate` | DATETIME | No | No | today−730d … today |
| `Amount` | FLOAT | No | No | 100.00 … 150,000.00 |
| `Status` | VARCHAR(10) | No | No | `Open` \| `Partial` \| `Cleared` |

### `Bank_Documents_Tracking.parquet`

| Column | Type | Nullable | Unique | Range / Values |
|--------|------|----------|--------|----------------|
| `DocID` | VARCHAR(12) | No | Yes (PK) | `DOC-000001` … |
| `InvoiceID` | VARCHAR(15) | No | No (FK) | Must be Open/Partial invoice |
| `BankSubmissionDate` | DATETIME | No | No | PostingDate + 5d … +30d |
| `DocStatus` | VARCHAR(15) | No | No | `Under Review` \| `Accepted` \| `Rejected` |

### `Dynamic_Holidays.parquet` (Python-owned — written by `daily_updates.py`)

| Column | Type | Nullable | Unique | Range / Values |
|--------|------|----------|--------|----------------|
| `Date` | DATE | No | Yes (PK within year) | Egyptian public holiday dates |
| `HolidayName` | TEXT | No | No | Official Egyptian holiday names (English) |

> Source: `https://date.nager.at/api/v3/PublicHolidays/{year}/EG` — current year & prior year. Fault-tolerant: failed years are silently skipped.

### `Dynamic_Holidays` (Power Query — connection only)

| Column | Type | Nullable | Unique | Range / Values |
|--------|------|----------|--------|----------------|
| `Date` | DATE | No | Yes (PK within year) | Egyptian public holiday dates |
| `HolidayName` | TEXT | No | No | Official Egyptian holiday names (English) |

> Source: `https://date.nager.at/api/v3/PublicHolidays/{year}/EG` — current year & prior year combined.

### `dim_Date` (Power Query — loaded to data model)

| Column | Type | Nullable | Unique | Range / Values |
|--------|------|----------|--------|----------------|
| `Date` | DATE | No | Yes (PK) | Jan 1 of min fact year → Dec 31 of max fact year |
| `Year` | INT64 | No | No | e.g. `2024`, `2025`, `2026` |
| `MonthNum` | INT64 | No | No | 1 … 12 |
| `DayOfWeekNum` | INT64 | No | No | 0 (Sun) … 6 (Sat) |
| `DayName` | TEXT | No | No | `"Sunday"` … `"Saturday"` (en-US) |
| `IsWeekend` | LOGICAL | No | No | `true` if DayOfWeekNum ∈ {5, 6} (Fri/Sat) |
| `HolidayName` | TEXT | No | No | Holiday name \| `"Weekend"` \| `"Working Day"` |
| `IsBankingWorkingDay` | LOGICAL | No | No | `false` if weekend or public holiday; else `true` |

### `User_Comments.xlsx`

| Column | Type | Nullable | Unique | Range / Values |
|--------|------|----------|--------|----------------|
| `InvoiceID` | VARCHAR(15) | No | Yes (sampled) | Subset of Open/Partial invoices |
| `ContactDate` | DATE | No | No | Run date |
| `FollowUpNote` | VARCHAR(255) | No | No | 8 template values |
| `PromisedDate` | DATE | No | No | ContactDate + 1d … +14d |
| `CollectorName` | VARCHAR(20) | No | No | `Ahmed` \| `Sara` \| `Omar` \| `Nour` \| `Yasmin` |

---

## Refresh & Re-run Order

1. **Run** `notebooks/data_generator.ipynb` — regenerates all three raw Parquet files
2. **Refresh** `etl/Data_Model_Engine.xlsx` → Data → Refresh All
3. **Run** `notebooks/user_comments_generator.ipynb` — regenerates `User_Comments.xlsx`
4. **Run** `scripts/daily_updates.py` — (daily / on-demand) fetches holidays from API and applies CDC upsert to master invoice file

> [!IMPORTANT]
> Step 1 must complete before Steps 2, 3, and 4. Steps 2, 3, and 4 are independent of each other.

> [!NOTE]
> `data/raw/` is excluded from version control (`.gitignore`). Always regenerate locally before running the ETL. Generation takes ~10.76 seconds on a standard laptop.

> [!TIP]
> Step 4 (`daily_updates.py`) is designed to be re-run daily. Each run appends ~500 new invoices and resolves ~500 Open → Cleared updates via CDC upsert. It is safe to run multiple times — deduplication ensures idempotency for existing `InvoiceID`s.

---

*Generated for [AR Financial Tracking System](https://github.com/Sohila-Khaled-Abbas/AR_Financial_Tracking_System)*
