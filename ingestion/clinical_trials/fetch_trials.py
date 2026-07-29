import requests
import pandas as pd
import json
import os
from google.cloud import bigquery
from google.oauth2 import service_account
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────
BASE_URL  = "https://clinicaltrials.gov/api/v2/studies"
OUTPUT_DIR = "data/raw/clinical_trials"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── API Parameters ────────────────────────────────────────────────────────────
# Free API, no key needed. Fetching cancer trials as first therapeutic area.
params = {
    "query.cond":           "cancer",
    "filter.overallStatus": "RECRUITING,COMPLETED",
    "pageSize":             200,
    "format":               "json",
    "fields": (
        "NCTId,BriefTitle,OverallStatus,Phase,"
        "EnrollmentCount,EnrollmentType,"
        "StartDate,CompletionDate,"
        "LeadSponsorName,Condition,StudyType"
    )
}

# ── Fetch from API ────────────────────────────────────────────────────────────
print("Fetching trials from ClinicalTrials.gov...")
response = requests.get(BASE_URL, params=params, timeout=30)
response.raise_for_status()  # throws an error if the API call failed
data     = response.json()
studies  = data.get("studies", [])
print(f"Retrieved {len(studies)} studies")

# ── Save raw JSON — this is your bronze layer ─────────────────────────────────
# Bronze = untouched, exactly as the source gave it to you
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
raw_path  = f"{OUTPUT_DIR}/trials_raw_{timestamp}.json"

with open(raw_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

print(f"Raw JSON saved → {raw_path}")

# ── Flatten nested JSON to CSV ────────────────────────────────────────────────
# The API returns deeply nested dicts — we extract the fields we need
# into a flat structure that dbt can read easily
records = []
for study in studies:
    ps         = study.get("protocolSection", {})
    id_mod     = ps.get("identificationModule", {})
    status_mod = ps.get("statusModule", {})
    design_mod = ps.get("designModule", {})
    sponsor_mod= ps.get("sponsorCollaboratorsModule", {})
    cond_mod   = ps.get("conditionsModule", {})

    records.append({
        "trial_id":        id_mod.get("nctId"),
        "trial_title":     id_mod.get("briefTitle"),
        "overall_status":  status_mod.get("overallStatus"),
        "phase":           ", ".join(design_mod.get("phases", [])),
        "enrollment_count":design_mod.get("enrollmentInfo", {}).get("count"),
        "enrollment_type": design_mod.get("enrollmentInfo", {}).get("type"),
        "start_date":      status_mod.get("startDateStruct", {}).get("date"),
        "completion_date": status_mod.get("completionDateStruct", {}).get("date"),
        "sponsor_name":    sponsor_mod.get("leadSponsor", {}).get("name"),
        "condition":       ", ".join(cond_mod.get("conditions", [])[:3]),
        "study_type":      design_mod.get("studyType"),
    })

df = pd.DataFrame(records)
print(f"Flattened {len(df)} records")
print("\nSample rows:")
print(df.head(3).to_string())

# ── Save flat CSV ─────────────────────────────────────────────────────────────
csv_path = f"{OUTPUT_DIR}/trials_flat_{timestamp}.csv"
df.to_csv(csv_path, index=False, encoding="utf-8")
print(f"\nFlat CSV saved → {csv_path}")

# ── Quick data quality summary ────────────────────────────────────────────────
print("\n── Data Quality Summary ─────────────────────────────────────────────")
print(f"Total trials fetched  : {len(df)}")
print(f"Null trial_id         : {df['trial_id'].isnull().sum()}")
print(f"Null enrollment_count : {df['enrollment_count'].isnull().sum()}")
print(f"Status breakdown:")
print(df['overall_status'].value_counts().to_string())
print(f"\nPhase breakdown:")
print(df['phase'].value_counts().to_string())
print("\nDone. Bronze layer complete.")

# ── Load into BigQuery Bronze table ───────────────────────────────────────────
print("\nLoading into BigQuery...")

credentials = service_account.Credentials.from_service_account_file(
    "D:/clinical_trial_analytics/secrets/autonomous-rite-503820-t8-a0b9fa30e604.json"
)
client = bigquery.Client(project="autonomous-rite-503820-t8", credentials=credentials)
table_id = "autonomous-rite-503820-t8.clinical_trial_analytics.raw_clinical_trials"

df["extracted_at"] = datetime.now().isoformat()
job = client.load_table_from_dataframe(df, table_id)
job.result()
print(f"Loaded {len(df)} rows into {table_id}")