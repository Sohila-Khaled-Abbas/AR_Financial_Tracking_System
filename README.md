<div align="center">

# 📊 AR Financial Tracking System

<img src="https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge&logo=statuspage&logoColor=white" alt="Status"/>
<img src="https://img.shields.io/badge/Domain-Data%20Engineering-blueviolet?style=for-the-badge&logo=databricks&logoColor=white" alt="Domain"/>
<img src="https://img.shields.io/badge/Source-SAP-0FAAFF?style=for-the-badge&logo=sap&logoColor=white" alt="SAP"/>
<img src="https://img.shields.io/badge/ETL-Power%20Query-F2A900?style=for-the-badge&logo=microsoftexcel&logoColor=white" alt="Power Query"/>
<img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge&logo=opensourceinitiative&logoColor=white" alt="License"/>

<br/>

> **A robust, end-to-end Accounts Receivable financial tracking pipeline** — from raw SAP extracts through ETL transformation to interactive dashboards — enabling real-time insights into cash flow, aging buckets, and collection performance.

<br/>

---

</div>

## 📋 Table of Contents

- [🎯 Project Overview](#-project-overview)
- [🏗️ Architecture](#%EF%B8%8F-architecture)
- [📁 Repository Structure](#-repository-structure)
- [⚙️ Tech Stack](#%EF%B8%8F-tech-stack)
- [🚀 Getting Started](#-getting-started)
- [📊 Data Pipeline](#-data-pipeline)
- [📈 Dashboards & KPIs](#-dashboards--kpis)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)

---

## 🎯 Project Overview

The **AR Financial Tracking System** is a data engineering project designed to automate and streamline the end-to-end monitoring of Accounts Receivable operations. It ingests raw financial data extracted from **SAP ERP**, applies structured ETL transformations via **Power Query**, and delivers actionable intelligence through business dashboards.

### 🔑 Key Objectives

| Objective | Description |
|-----------|-------------|
| 📥 **Data Ingestion** | Automate extraction of AR data from SAP into structured raw datasets |
| 🔄 **ETL Processing** | Clean, transform, and enrich data using Power Query M-language pipelines |
| 📊 **Reporting** | Build interactive dashboards covering aging, DSO, and collection KPIs |
| 🗂️ **Governance** | Maintain mapping tables for consistent business entity classification |

### 💡 Business Value

- ⏱️ Reduce manual reporting effort from **hours to minutes**
- 🎯 Track outstanding invoices with **aging bucket analysis** (0–30, 31–60, 61–90, 90+ days)
- 💰 Monitor **Days Sales Outstanding (DSO)** and payment trends
- 🚨 Proactively flag **overdue accounts** for collections follow-up

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DATA FLOW ARCHITECTURE                       │
└─────────────────────────────────────────────────────────────────────┘

  ┌───────────┐     Export      ┌──────────────────┐
  │  SAP ERP  │ ─────────────► │  Raw SAP Extracts │  (CSV / XLSX)
  └───────────┘                └────────┬─────────┘
                                        │
                               ┌────────▼─────────┐
                               │  Mapping Tables   │  (Customer / GL Code)
                               └────────┬─────────┘
                                        │
                               ┌────────▼──────────┐
                               │  Power Query ETL   │  (Clean · Join · Transform)
                               └────────┬──────────┘
                                        │
                               ┌────────▼──────────┐
                               │   Analytical       │
                               │   Notebooks        │  (EDA · Validation)
                               └────────┬──────────┘
                                        │
                               ┌────────▼──────────┐
                               │   Dashboards       │  (KPIs · Charts · Trends)
                               └───────────────────┘
```

---

## 📁 Repository Structure

```
AR_Financial_Tracking_System/
│
├── 📓 notebooks/                    # Jupyter notebooks for EDA & analysis
│   └── (exploratory analysis, validation scripts)
│
├── 📂 data/                         # All data assets
│   ├── raw/                         # Unmodified SAP ERP exports
│   │   └── (CSV/XLSX extracts from SAP modules)
│   └── mappings/                    # Reference & dimension tables
│       └── (customer master, GL codes, cost centers)
│
├── ⚙️  etl/                          # Power Query M-language ETL scripts
│   └── (transformation queries, connection configs)
│
├── 📊 dashboards/                   # Dashboard files & templates
│   └── (Excel / Power BI / report files)
│
├── 📄 README.md                     # Project documentation (this file)
├── 📄 .gitignore                    # Git ignore rules
└── 📄 LICENSE                       # MIT License
```

> [!NOTE]
> Folder names follow a clean, lowercase convention for cross-platform compatibility and professional repository standards.

---

## ⚙️ Tech Stack

<div align="center">

| Layer | Technology | Purpose |
|-------|-----------|---------|
| 🏢 **Source System** | SAP ERP (FI/AR Module) | Source of truth for financial transactions |
| 🔄 **ETL Engine** | Microsoft Power Query (M Language) | Data transformation and loading |
| 📓 **Analysis** | Python · Jupyter Notebooks | Exploratory data analysis & validation |
| 📊 **Visualization** | Excel / Power BI | Dashboards and reporting |
| 🗄️ **Data Format** | CSV · XLSX · Flat Files | Lightweight, portable data storage |
| 🔧 **Version Control** | Git · GitHub | Source code and artifact management |

</div>

---

## 🚀 Getting Started

### Prerequisites

Ensure you have the following installed:

```bash
# Python 3.8+
python --version

# Jupyter (for notebooks)
pip install jupyter pandas openpyxl xlrd

# Git
git --version
```

### Clone the Repository

```bash
git clone https://github.com/<your-username>/AR_Financial_Tracking_System.git
cd AR_Financial_Tracking_System
```

### Repository Layout After Clone

```
AR_Financial_Tracking_System/
├── notebooks/
├── data/
│   ├── raw/
│   └── mappings/
├── etl/
└── dashboards/
```

> [!IMPORTANT]
> Raw data files (SAP extracts) are **excluded from version control** via `.gitignore` to protect sensitive financial information. Place your exported files inside `data/raw/` locally.

---

## 📊 Data Pipeline

### Step 1 — SAP Data Extraction

Export the following from SAP using standard transaction codes:

| SAP T-Code | Description | Output |
|------------|-------------|--------|
| `FBL5N` | Customer Line Items | Open/cleared AR items |
| `FD10N` | Customer Balance | Account balances |
| `F.31` | Credit Management | Credit exposure report |
| `S_ALR_87012178` | AR Aging Analysis | Aging bucket breakdown |

Save exports to: `data/raw/`

### Step 2 — Power Query ETL

Open the ETL workbook in `etl/` and refresh all queries. The pipeline:

```
Raw Extract
    │
    ├── [Step 1] Remove blank rows & fix data types
    ├── [Step 2] Join with customer master mapping table
    ├── [Step 3] Classify invoices into aging buckets
    ├── [Step 4] Calculate DSO and overdue flags
    └── [Step 5] Output clean analytical table
```

### Step 3 — Dashboard Refresh

Open the dashboard file in `dashboards/` and refresh to load the latest transformed data.

---

## 📈 Dashboards & KPIs

### Key Performance Indicators Tracked

| KPI | Formula | Target |
|-----|---------|--------|
| 💰 **Total AR Outstanding** | Sum of all open invoices | — |
| 📅 **Days Sales Outstanding (DSO)** | (AR Balance / Total Credit Sales) × Days | < 45 days |
| ⚠️ **Overdue Rate** | Overdue invoices / Total open invoices | < 10% |
| 🏆 **Collection Effectiveness Index (CEI)** | (Beginning AR + Sales − Ending AR) / (Beginning AR + Sales) | > 85% |

### Aging Bucket Breakdown

```
┌─────────────┬──────────────┬──────────────┬──────────────┐
│   Current   │   31–60 Days │   61–90 Days │   90+ Days   │
│  (0–30 Days)│              │              │  ⚠️ Overdue  │
└─────────────┴──────────────┴──────────────┴──────────────┘
```

---

## 🤝 Contributing

Contributions, suggestions, and improvements are welcome!

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/your-feature-name`
3. **Commit** your changes: `git commit -m 'feat: add new aging bucket logic'`
4. **Push** to the branch: `git push origin feature/your-feature-name`
5. **Open** a Pull Request

### Commit Convention

This project uses [Conventional Commits](https://www.conventionalcommits.org/):

| Prefix | Use Case |
|--------|----------|
| `feat:` | New feature or pipeline step |
| `fix:` | Bug fix in ETL logic |
| `docs:` | Documentation updates |
| `refactor:` | Code restructure without behavior change |
| `data:` | Data file updates or schema changes |

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

Made with ❤️ for Data Engineering excellence

**[⬆ Back to Top](#-ar-financial-tracking-system)**

</div>
