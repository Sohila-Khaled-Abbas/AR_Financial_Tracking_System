<div align="center">

# 📊 AR Financial Tracking System

<img src="https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge" alt="Status"/>
<img src="https://img.shields.io/badge/Records-950K%2B-blueviolet?style=for-the-badge&logo=databricks&logoColor=white" alt="Records"/>
<img src="https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
<img src="https://img.shields.io/badge/Pandas%20%7C%20NumPy-Engine-150458?style=for-the-badge&logo=pandas&logoColor=white" alt="Pandas"/>
<img src="https://img.shields.io/badge/Power%20Query-ETL-F2A900?style=for-the-badge&logo=microsoftexcel&logoColor=white" alt="Power Query"/>
<img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License"/>

<br/>

> **An end-to-end Accounts Receivable data engineering pipeline** — synthetic data generation at scale (950K+ records), Power Query ETL transformation, Star Schema modeling, and collection follow-up simulation — built for real-world AR analytics scenarios.

<br/>

---

</div>

## 📋 Table of Contents

- [🎯 Project Overview](#-project-overview)
- [🏗️ Architecture & Data Flow](#%EF%B8%8F-architecture--data-flow)
- [📁 Repository Structure](#-repository-structure)
- [🗄️ Data Model — Star Schema](#%EF%B8%8F-data-model--star-schema)
- [📓 Notebooks](#-notebooks)
- [⚙️ ETL Engine](#%EF%B8%8F-etl-engine)
- [⚡ Performance](#-performance)
- [🚀 Getting Started](#-getting-started)
- [📈 Key Metrics & KPIs](#-key-metrics--kpis)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)

---

## 🎯 Project Overview

The **AR Financial Tracking System** is a data engineering project that simulates and tracks an enterprise Accounts Receivable lifecycle — from synthetic invoice generation through ETL transformation to collection activity simulation.

The pipeline generates **950,000 invoices** across **10,000 customers** with realistic financial distributions, models them in a **Star Schema**, transforms them through **Power Query M-language**, and simulates **collection team follow-up activity** with human-like comments and promised payment dates.

### 🔑 What This System Does

| Layer | What Happens |
|-------|-------------|
| 🏭 **Data Generation** | Vectorized synthetic dataset creation — 950K invoices, 10K customers, ~399K bank documents |
| 🔄 **ETL Processing** | Power Query cleans, joins, and enriches raw CSVs into an analytical data model |
| 🎭 **Activity Simulation** | Realistic AR collection follow-up notes, collector assignments, and promise-to-pay dates |
| 📊 **Star Schema** | Fact + Dimension tables structured for BI consumption |

---

## 🏗️ Architecture & Data Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                       END-TO-END PIPELINE                                │
└──────────────────────────────────────────────────────────────────────────┘

  ┌──────────────────────────┐
  │   data_generator.ipynb   │  NumPy · Pandas · Faker
  │   (950K record engine)   │
  └────────────┬─────────────┘
               │  generates 3 CSV files
               ▼
  ┌────────────────────────────────────────────────┐
  │                 data/raw/                      │
  │  ┌─────────────────────────────────────────┐   │
  │  │  AR_Invoices_950K.csv        ~58 MB     │   │  ← Fact Table
  │  │  Customers_Master.csv        ~295 KB    │   │  ← Dimension Table
  │  │  Bank_Documents_Tracking.csv ~24 MB     │   │  ← Tracking Table
  │  └─────────────────────────────────────────┘   │
  └────────────────────┬───────────────────────────┘
                       │
               ┌───────▼────────┐
               │  etl/          │  Power Query M-Language
               │  Data_Model_   │  Clean · Join · Transform
               │  Engine.xlsx   │  Aging · DSO · Status flags
               └───────┬────────┘
                       │
          ┌────────────┴────────────┐
          │                         │
  ┌───────▼────────┐      ┌─────────▼──────────────┐
  │  Dashboards    │      │  user_comments_         │
  │  (BI Layer)    │      │  generator.ipynb        │
  │                │      │  5K sampled follow-ups  │
  └────────────────┘      └────────────────────────-┘
                                     │
                            ┌────────▼────────┐
                            │  data/output/   │
                            │ User_Comments   │
                            │    .xlsx        │
                            └─────────────────┘
```

---

## 📁 Repository Structure

```
AR_Financial_Tracking_System/
│
├── 📓 notebooks/
│   ├── data_generator.ipynb          # Stage 1: Synthetic data pipeline (950K records)
│   ├── user_comments_generator.ipynb # Stage 2: AR follow-up activity simulation
│   └── paths.py                      # Shared path configuration (OS-agnostic)
│
├── 📂 data/
│   ├── raw/                          # Generated CSVs (git-ignored — large files)
│   │   ├── AR_Invoices_950K.csv      # Fact table · 950,000 rows · ~58 MB
│   │   ├── Customers_Master.csv      # Customer dimension · 10,000 rows · ~295 KB
│   │   └── Bank_Documents_Tracking.csv # Bank submission tracking · ~399K rows · ~24 MB
│   ├── mappings/                     # Reference & dimension lookup tables
│   └── output/                       # Notebook exports (auto-created)
│       └── User_Comments.xlsx        # 5,000 simulated follow-up records
│
├── ⚙️  etl/
│   └── Data_Model_Engine.xlsx        # Power Query ETL workbook (~47 MB)
│
├── 📊 dashboards/                    # Dashboard files (coming soon)
│
├── 📄 README.md
├── 📄 .gitignore
└── 📄 LICENSE
```

> [!NOTE]
> `data/raw/` files are excluded from Git via `.gitignore` (files exceed 50MB). Run `data_generator.ipynb` to regenerate them locally in under 15 seconds.

---

## 🗄️ Data Model — Star Schema

```
                    ┌─────────────────────────┐
                    │   dim_Customers          │
                    │─────────────────────────│
                    │  CustomerID  (PK)        │
                    │  CustomerName            │
                    │  PaymentTerms            │
                    │  (30 / 60 / 90 / 120 d) │
                    └────────────┬────────────┘
                                 │ 1
                                 │
                                 │ N
          ┌──────────────────────▼───────────────────────┐
          │              fact_AR_Invoices                 │
          │──────────────────────────────────────────────│
          │  InvoiceID    (PK)   INV-0000001 … INV-0950000│
          │  CustomerID   (FK)                            │
          │  PostingDate         2024-04-20 → 2026-04-20  │
          │  Amount              $100 – $150,000          │
          │  Status              Open · Partial · Cleared │
          └───────────────┬──────────────────────────────┘
                          │ 1
                          │
                          │ N (70% of Open/Partial)
          ┌───────────────▼──────────────────────────────┐
          │          fact_Bank_Documents                  │
          │──────────────────────────────────────────────│
          │  DocID          (PK)   DOC-000001 …           │
          │  InvoiceID      (FK)                          │
          │  BankSubmissionDate                           │
          │  DocStatus      Under Review · Accepted ·     │
          │                 Rejected (60/30/10%)          │
          └──────────────────────────────────────────────┘
```

### Schema Statistics

| Table | Rows | Size | Role |
|-------|------|------|------|
| `fact_AR_Invoices` | 950,000 | ~58 MB | Core fact table |
| `dim_Customers` | 10,000 | ~295 KB | Customer dimension |
| `fact_Bank_Documents` | ~399,000 | ~24 MB | Bank tracking fact |
| `User_Comments` (output) | 5,000 | — | Follow-up simulation |

### Invoice Status Distribution

| Status | Probability | Description |
|--------|-------------|-------------|
| `Open` | 40% | Unpaid, awaiting collection |
| `Cleared` | 40% | Fully paid and settled |
| `Partial` | 20% | Partially paid, balance remaining |

---

## 📓 Notebooks

### 1️⃣ `data_generator.ipynb` — Synthetic Data Pipeline

Generates the entire dataset using **high-performance vectorized operations**.

**Pipeline steps:**

```
Install deps (pandas · numpy · faker)
        │
        ▼
[1] Environment Setup
    └─ Import libraries, start timer, init Faker
        │
        ▼
[2] Dimension Table — Customers (10,000 records)
    └─ Faker-generated company names
    └─ Random payment terms: 30 / 60 / 90 / 120 days
        │
        ▼
[3] Fact Table — AR Invoices (950,000 records)  ← NumPy vectorized
    └─ Invoice IDs: INV-0000001 to INV-0950000
    └─ Random posting dates over 730-day window
    └─ Invoice amounts: $100 – $150,000 (uniform)
    └─ Status: Open(40%) · Partial(20%) · Cleared(40%)
        │
        ▼
[4] Bank Documents Tracking (~399K records)
    └─ 70% of Open/Partial invoices submitted to bank
    └─ DocStatus: Under Review(60%) · Accepted(30%) · Rejected(10%)
        │
        ▼
[5] Export to CSV → data/raw/
    └─ AR_Invoices_950K.csv
    └─ Customers_Master.csv
    └─ Bank_Documents_Tracking.csv
        │
        ▼
[6] Data Quality Assurance (DQA)
    └─ Record count validation
    └─ Referential integrity check (0 orphan invoices)
    └─ Statistical summary (describe)
```

**DQA Results (last run):**

| Check | Result |
|-------|--------|
| Invoices Count | ✅ 950,000 |
| Customers Count | ✅ 10,000 |
| Bank Documents | ✅ ~399,219 |
| Referential Integrity Issues | ✅ 0 |
| Execution Time | ✅ ~10.76 seconds |

---

### 2️⃣ `user_comments_generator.ipynb` — Collection Activity Simulation

Simulates realistic **AR collection team activity** by generating follow-up notes for open/partial invoices.

**Pipeline steps:**

```
[1] Load Data
    └─ Reads AR_Invoices_950K.csv via paths.py (OS-agnostic)
    └─ Filters for Status ∈ {Open, Partial}
        │
        ▼
[2] Sampling
    └─ Randomly samples 5,000 invoices
    └─ Simulates realistic team workload
        │
        ▼
[3] Synthetic Comment Generation
    └─ Follow-up templates (4 types)
    └─ Promise-to-pay dates (1–14 days ahead)
    └─ Collector assignment (Ahmed · Sara · Omar · Nour)
        │
        ▼
[4] Export → data/output/User_Comments.xlsx
```

**Output schema:**

| Column | Description | Example |
|--------|-------------|---------|
| `InvoiceID` | Linked invoice | `INV-0123456` |
| `FollowUpNote` | Collector's comment | `"Customer promised to pay next Thursday"` |
| `PromisedDate` | Expected payment date | `2026-04-27` |
| `CollectorName` | Team member assigned | `Sara` |

**Follow-up note templates:**

```
• "Customer promised to pay next Thursday"
• "Waiting for manager approval"
• "Dispute over quantity, reviewing with sales"
• "Payment initiated, waiting for bank clearance"
```

---

### 🔧 `paths.py` — Shared Path Configuration

Eliminates hardcoded Windows backslash paths across all notebooks. Import once, use everywhere.

```python
from paths import RAW_DATA_DIR, OUTPUT_DIR, MAPPINGS_DIR

# Example usage
file_path = RAW_DATA_DIR / "AR_Invoices_950K.csv"
output    = OUTPUT_DIR   / "User_Comments.xlsx"
```

---

## ⚙️ ETL Engine

**File:** `etl/Data_Model_Engine.xlsx` (~47 MB)

The Power Query ETL workbook connects to the raw CSVs and applies the full transformation pipeline:

| Step | Operation |
|------|-----------|
| 1️⃣ | Load all three raw CSV files |
| 2️⃣ | Clean data types (dates, decimals, IDs) |
| 3️⃣ | Join `fact_AR_Invoices` ↔ `dim_Customers` |
| 4️⃣ | Calculate **aging buckets** (0–30 / 31–60 / 61–90 / 90+ days) |
| 5️⃣ | Compute **Days Outstanding** per invoice |
| 6️⃣ | Flag overdue invoices for collections |
| 7️⃣ | Join bank document status |
| 8️⃣ | Output analytical model for dashboard consumption |

> [!TIP]
> To refresh: open `Data_Model_Engine.xlsx` → **Data tab** → **Refresh All**. Ensure the raw CSVs are present in `data/raw/` first.

---

## ⚡ Performance

The data generation pipeline is built for **high throughput** using vectorized NumPy operations instead of row-by-row loops:

| Technique | Benefit |
|-----------|---------|
| `np.random.choice` / `np.random.uniform` | Generates millions of values in milliseconds |
| `pd.to_timedelta` vectorized date arithmetic | No Python-level date loops |
| Faker used only for small dimension tables | Avoids slow iteration on large volumes |
| Single-pass DataFrame construction | Minimizes memory allocations |

**Benchmark:** 950,000 invoices + 10,000 customers + ~399,000 bank docs generated and exported in **~10.76 seconds** on a standard laptop.

---

## 🚀 Getting Started

### Prerequisites

```bash
python --version      # 3.8+ required (tested on 3.13.1)
pip install pandas numpy faker openpyxl
```

### Step 1 — Clone

```bash
git clone https://github.com/Sohila-Khaled-Abbas/AR_Financial_Tracking_System.git
cd AR_Financial_Tracking_System
```

### Step 2 — Generate the Raw Data

Open and run **all cells** in `notebooks/data_generator.ipynb`.

This creates the three CSV files in `data/raw/`:
```
data/raw/AR_Invoices_950K.csv          (~58 MB)
data/raw/Customers_Master.csv          (~295 KB)
data/raw/Bank_Documents_Tracking.csv   (~24 MB)
```

### Step 3 — Run the ETL

Open `etl/Data_Model_Engine.xlsx` and click **Data → Refresh All**.

### Step 4 — Simulate Collection Activity

Run `notebooks/user_comments_generator.ipynb`.

Output: `data/output/User_Comments.xlsx`

### Step 5 — Explore Dashboards

Open files in the `dashboards/` folder (coming soon).

> [!IMPORTANT]
> `data/raw/` is in `.gitignore` — raw CSVs are never committed. Always regenerate locally using `data_generator.ipynb`.

---

## 📈 Key Metrics & KPIs

### Aging Bucket Analysis

```
Invoice Age          Volume           Action
─────────────────────────────────────────────────────────────
0  – 30  days   │████████████████│  Monitor
31 – 60  days   │████████████    │  Soft follow-up
61 – 90  days   │████████        │  Escalate to collector
90+      days   │████            │  ⚠️ Legal / write-off risk
```

### Key KPIs Tracked

| KPI | Formula |
|-----|---------|
| **Total AR Outstanding** | `SUM(Amount WHERE Status IN (Open, Partial))` |
| **Days Sales Outstanding (DSO)** | `(AR Balance / Credit Sales) × Days in Period` |
| **Collection Rate** | `Cleared / (Cleared + Open + Partial) × 100` |
| **Bank Acceptance Rate** | `Accepted / Total Bank Docs × 100` |
| **Overdue Rate** | `Invoices > 60 days / Total Open × 100` |

---

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/your-feature`
3. **Commit** using conventional commits: `git commit -m "feat: add aging bucket logic"`
4. **Push**: `git push origin feature/your-feature`
5. **Open** a Pull Request

### Commit Convention

| Prefix | Use Case |
|--------|----------|
| `feat:` | New notebook, ETL step, or pipeline stage |
| `fix:` | Bug fix in data logic |
| `data:` | Schema or column changes |
| `docs:` | README or docstring updates |
| `refactor:` | Code cleanup without behavior change |
| `perf:` | Performance improvements |

---

## 📄 License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.

---

<div align="center">

Built with ❤️ by [Sohila Khaled Abbas](https://github.com/Sohila-Khaled-Abbas)

**[⬆ Back to Top](#-ar-financial-tracking-system)**

</div>
