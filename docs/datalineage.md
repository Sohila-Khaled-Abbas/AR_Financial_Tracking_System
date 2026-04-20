# Data Lineage — AR Financial Tracking System

> **Document:** `docs/datalineage.md`  
> **Version:** 1.0 · 2026-04-20  
> **Scope:** End-to-end column-level data lineage from synthetic generation through ETL to output layer

---

## Overview

```
Source (Synthetic)          Raw Layer              ETL Layer              Output Layer
─────────────────           ──────────             ─────────              ────────────
Faker · NumPy         →   data/raw/*.csv    →   Data_Model_Engine   →   Dashboards
                                            →   .xlsx (Power Query)  →   User_Comments.xlsx
                                                                     →   Analytical Model
```

| Layer | Location | Format | Owner |
|-------|----------|--------|-------|
| **Generation** | `notebooks/data_generator.ipynb` | In-memory (Pandas) | Python |
| **Raw** | `data/raw/` | CSV | File system |
| **ETL / Model** | `etl/Data_Model_Engine.xlsx` | Excel / Power Query | Power Query M |
| **Activity** | `notebooks/user_comments_generator.ipynb` | In-memory → XLSX | Python |
| **Output** | `data/output/` | XLSX | File system |

---

## Stage 1 — Data Generation (`data_generator.ipynb`)

### 1.1 dim_Customers → `Customers_Master.csv`

| Column | Source | Generation Method | Notes |
|--------|--------|-------------------|-------|
| `CustomerID` | Computed | `f'C-{(i+1):05d}'` for i in 0…9,999 | Sequential, zero-padded |
| `CustomerName` | Faker | `Faker().company()` | Random company names |
| `PaymentTerms` | NumPy | `np.random.choice([30, 60, 90, 120])` | Uniform distribution |

**Output:** `data/raw/Customers_Master.csv` — 10,000 rows · ~295 KB

---

### 1.2 fact_AR_Invoices → `AR_Invoices_950K.csv`

| Column | Source | Generation Method | Notes |
|--------|--------|-------------------|-------|
| `InvoiceID` | Computed | `f'INV-{(i+1):07d}'` for i in 0…949,999 | Sequential, zero-padded |
| `CustomerID` | Sampled | `np.random.choice(customers_df['CustomerID'])` | FK → dim_Customers |
| `PostingDate` | Vectorized | `start_date + pd.to_timedelta(random_days, unit='D')` | Uniform over 730-day window |
| `Amount` | Vectorized | `np.round(np.random.uniform(100.0, 150000.0), 2)` | Uniform distribution |
| `Status` | Vectorized | `np.random.choice(['Open','Partial','Cleared'], p=[0.4,0.2,0.4])` | Weighted probability |

**Date window:** today − 730 days → today  
**Output:** `data/raw/AR_Invoices_950K.csv` — 950,000 rows · ~58 MB

---

### 1.3 fact_Bank_Documents → `Bank_Documents_Tracking.csv`

| Column | Source | Generation Method | Notes |
|--------|--------|-------------------|-------|
| `DocID` | Computed | `f'DOC-{(i+1):06d}'` for i in 0…NUM_BANK_DOCS | Sequential |
| `InvoiceID` | Filtered + Sampled | `np.random.choice(pending_invoices, replace=False)` | FK → fact_AR_Invoices; only Open/Partial |
| `BankSubmissionDate` | Derived | `posting_dates[:N] + pd.to_timedelta(random 5–30 days)` | PostingDate + offset |
| `DocStatus` | Vectorized | `np.random.choice(['Under Review','Accepted','Rejected'], p=[0.6,0.3,0.1])` | Weighted probability |

**Filter rule:** `Status IN ('Open', 'Partial')` → 70% of those rows selected  
**Output:** `data/raw/Bank_Documents_Tracking.csv` — ~399,219 rows · ~24 MB

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

Powered by **Power Query M-Language**. Connects directly to `data/raw/` CSVs.

### 2.1 Load Queries

| Query Name | Source File | Row Count | Load Mode |
|------------|-------------|-----------|-----------|
| `raw_Invoices` | `data/raw/AR_Invoices_950K.csv` | 950,000 | Connection only |
| `raw_Customers` | `data/raw/Customers_Master.csv` | 10,000 | Connection only |
| `raw_BankDocs` | `data/raw/Bank_Documents_Tracking.csv` | ~399,219 | Connection only |

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
Step 13: Load to data model         → available for dashboard queries
```

---

## Stage 3 — Collection Activity (`user_comments_generator.ipynb`)

### 3.1 Input

| Source | Column(s) Used | Filter Applied |
|--------|---------------|----------------|
| `data/raw/AR_Invoices_950K.csv` | `InvoiceID`, `Status` | `Status IN ('Open', 'Partial')` → ~570,313 rows |

---

### 3.2 Column Lineage → `User_Comments.xlsx`

| Output Column | Source | Generation Method | Notes |
|---------------|--------|-------------------|-------|
| `InvoiceID` | `AR_Invoices_950K.csv[InvoiceID]` | `np.random.choice(open_invoices, 5000, replace=False)` | Sampled without replacement |
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

## Full Column-Level Lineage Map

```
Faker.company()           ──→  Customers_Master.csv[CustomerName]
                                        │
                                        ▼ JOIN (CustomerID)
np.random.uniform()       ──→  AR_Invoices_950K.csv[Amount]         ──→  fact_AR_Invoices[Amount]
np.random.choice(Status)  ──→  AR_Invoices_950K.csv[Status]         ──→  fact_AR_Invoices[Status]
pd.to_timedelta()         ──→  AR_Invoices_950K.csv[PostingDate]     ──→  fact_AR_Invoices[PostingDate]
                                        │                                          │
                                        │ (filter: Open/Partial × 0.7)            │ Date.Now() - PostingDate
                                        ▼                                          ▼
np.random.choice(status)  ──→  Bank_Documents_Tracking.csv[DocStatus] ──→  fact_Bank_Documents[DocStatus]
posting_dates + offset    ──→  Bank_Documents_Tracking.csv[BankSubmissionDate]     │
                                                                                    ▼
                                                                    DaysOutstanding (computed)
                                                                    AgingBucket     (computed)
                                                                    IsOverdue       (computed)

AR_Invoices_950K.csv      ──→  [filter Open/Partial, sample 5K]
  [InvoiceID]             ──→  User_Comments.xlsx[InvoiceID]
datetime.today()          ──→  User_Comments.xlsx[ContactDate]
templates list            ──→  User_Comments.xlsx[FollowUpNote]
ContactDate + randint()   ──→  User_Comments.xlsx[PromisedDate]
collectors list           ──→  User_Comments.xlsx[CollectorName]
```

---

## File Dependency Graph

```
data_generator.ipynb
    │
    ├──→ data/raw/Customers_Master.csv
    │           │
    │           └──→ etl/Data_Model_Engine.xlsx  ──→  Analytical Model
    │                           ▲
    ├──→ data/raw/AR_Invoices_950K.csv ──┤
    │           │               ▲
    │           └──→ user_comments_generator.ipynb
    │                           │
    │                           └──→ data/output/User_Comments.xlsx
    │
    └──→ data/raw/Bank_Documents_Tracking.csv ──→ etl/Data_Model_Engine.xlsx
```

---

## Data Contracts

### `Customers_Master.csv`

| Column | Type | Nullable | Unique | Range / Values |
|--------|------|----------|--------|----------------|
| `CustomerID` | VARCHAR(10) | No | Yes (PK) | `C-00001` … `C-10000` |
| `CustomerName` | VARCHAR(255) | No | No | Faker company names |
| `PaymentTerms` | INT | No | No | `{30, 60, 90, 120}` |

### `AR_Invoices_950K.csv`

| Column | Type | Nullable | Unique | Range / Values |
|--------|------|----------|--------|----------------|
| `InvoiceID` | VARCHAR(15) | No | Yes (PK) | `INV-0000001` … `INV-0950000` |
| `CustomerID` | VARCHAR(10) | No | No (FK) | Must exist in Customers_Master |
| `PostingDate` | DATETIME | No | No | today−730d … today |
| `Amount` | FLOAT | No | No | 100.00 … 150,000.00 |
| `Status` | VARCHAR(10) | No | No | `Open` \| `Partial` \| `Cleared` |

### `Bank_Documents_Tracking.csv`

| Column | Type | Nullable | Unique | Range / Values |
|--------|------|----------|--------|----------------|
| `DocID` | VARCHAR(12) | No | Yes (PK) | `DOC-000001` … |
| `InvoiceID` | VARCHAR(15) | No | No (FK) | Must be Open/Partial invoice |
| `BankSubmissionDate` | DATETIME | No | No | PostingDate + 5d … +30d |
| `DocStatus` | VARCHAR(15) | No | No | `Under Review` \| `Accepted` \| `Rejected` |

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

1. **Run** `notebooks/data_generator.ipynb` — regenerates all three raw CSVs
2. **Refresh** `etl/Data_Model_Engine.xlsx` → Data → Refresh All
3. **Run** `notebooks/user_comments_generator.ipynb` — regenerates `User_Comments.xlsx`

> [!IMPORTANT]
> Step 1 must complete before Steps 2 and 3. Steps 2 and 3 are independent of each other.

> [!NOTE]
> `data/raw/` is excluded from version control (`.gitignore`). Always regenerate locally before running the ETL. Generation takes ~10.76 seconds on a standard laptop.

---

*Generated for [AR Financial Tracking System](https://github.com/Sohila-Khaled-Abbas/AR_Financial_Tracking_System)*
