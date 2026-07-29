arkdown
# Clinical Trial Analytics Platform

An end-to-end data pipeline built using **Python**, **dbt Core**, **DuckDB**, and a **medallion architecture** (Bronze → Silver → Gold), consuming real clinical trial data from the ClinicalTrials.gov v2 API.

## Architecture

ClinicalTrials.gov API
│
▼
Python Ingestion (fetch_trials.py)
│ requests · pandas
▼
Bronze Layer (raw JSON / CSV)
│
▼
Silver Layer — dbt staging models
(cleaning, type casting, field standardisation)
│
▼
Gold Layer — dbt mart models
(dimensional model: fact + dimension tables)
│
▼
Parquet export → Power BI


## Tech Stack

| Layer | Tool |
|---|---|
| Ingestion | Python (requests, pandas) |
| Transformation | dbt Core |
| Warehouse | DuckDB |
| Orchestration | Apache Airflow (local) |
| Serving | Parquet → Power BI |

## Project Structure

clinical_trial_analytics/
├── ingestion/clinical_trials/
│ ├── fetch_trials.py # Pulls data from ClinicalTrials.gov v2 API
│ └── export_parquet.py # Exports Gold layer to Parquet for Power BI
├── clinical_trials_dbt/
│ ├── models/
│ │ ├── staging/ # Silver layer: clean, typed source data
│ │ └── marts/ # Gold layer: dimensional model
│ │ ├── dim_sponsor.sql
│ │ ├── dim_therapeutic_area.sql
│ │ ├── dim_trial.sql
│ │ └── fct_enrollment.sql
│ └── dbt_project.yml
└── data/gold/ # Parquet outputs (dim + fact tables)


## dbt Models

### Staging
- `staging_clinical_trials` — standardises raw API data: type casting, field renaming, null handling

### Marts (Gold Layer)
| Model | Description |
|---|---|
| `dim_trial` | Core trial attributes (status, phase, start/end dates) |
| `dim_sponsor` | Lead sponsor details |
| `dim_therapeutic_area` | Condition/disease area classification |
| `fct_enrollment` | Enrollment targets per trial |

### Data Quality Tests
Schema tests are defined across all models:
- `not_null` on all primary keys and critical fields
- `unique` on all surrogate keys

## Key Design Decisions

- **DuckDB** used as a lightweight local warehouse — no infrastructure required, runs fully in-process
- **Parquet export** added to resolve a DuckDB/Power BI concurrency constraint, enabling reliable self-service BI access
- **Medallion architecture** enforces clear separation between raw ingestion, cleaning, and analytics-ready outputs

## Running the Project

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Fetch data from ClinicalTrials.gov API
python ingestion/clinical_trials/fetch_trials.py

# 3. Run dbt transformations
cd clinical_trials_dbt
dbt run
dbt test

# 4. Export Gold layer to Parquet
python ingestion/clinical_trials/export_parquet.py
```

## Data Source

[ClinicalTrials.gov v2 API](https://clinicaltrials.gov/data-api/api) — publicly available registry of clinical studies.
