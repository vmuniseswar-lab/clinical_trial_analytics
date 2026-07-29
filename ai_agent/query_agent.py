import os
import anthropic
from google.cloud import bigquery
from google.oauth2 import service_account
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# BigQuery setup
credentials = service_account.Credentials.from_service_account_file(
    os.path.join(os.path.dirname(__file__), "../secrets/autonomous-rite-503820-t8-a0b9fa30e604.json")
)
bq_client = bigquery.Client(credentials=credentials, project="autonomous-rite-503820-t8")

# Anthropic setup
anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Schema context for the AI
SCHEMA_CONTEXT = """
You are a data analyst assistant. You have access to a BigQuery dataset called 
'clinical_trial_analytics' with the following Gold layer tables:

1. fct_enrollment - One row per trial with enrollment metrics
   - trial_id (STRING) - unique trial identifier
   - therapeutic_area_id (STRING) - foreign key to dim_therapeutic_area
   - sponsor_id (STRING) - foreign key to dim_sponsor
   - enrollment_target (INT) - target number of participants
   - enrollment_actual (INT) - estimated actual enrollment
   - enrollment_rate_pct (FLOAT) - percentage of target enrolled
   - enrollment_type (STRING)
   - start_date (DATE)
   - completion_date (DATE)
   - planned_duration_days (INT)
   - is_completed (BOOL)

2. dim_trial - Trial descriptive attributes
   - trial_id (STRING)
   - trial_title (STRING)
   - trial_phase (STRING) - e.g. Phase 1, Phase 2, Phase 3, Phase 4
   - trial_status (STRING) - e.g. COMPLETED, RECRUITING, TERMINATED
   - study_type (STRING)
   - stage_group (STRING) - Early Stage or Late Stage
   - duration_band (STRING) - Under 1 Year, 1-2 Years, 2-5 Years, Over 5 Years

3. dim_sponsor - Sponsor details
   - sponsor_id (STRING)
   - sponsor_name (STRING)

4. dim_therapeutic_area - Therapeutic area/condition details
   - therapeutic_area_id (STRING)
   - therapeutic_area_name (STRING)

Write a BigQuery SQL query to answer the user's question.
Return ONLY the SQL query, no explanation, no markdown, no backticks.
Use fully qualified table names: autonomous-rite-503820-t8.clinical_trial_analytics.table_name
"""

def generate_sql(question: str) -> str:
    message = anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"{SCHEMA_CONTEXT}\n\nQuestion: {question}"
            }
        ]
    )
    return message.content[0].text.strip()

def run_query(sql: str) -> list:
    query_job = bq_client.query(sql)
    results = query_job.result()
    return [dict(row) for row in results]

def summarise_results(question: str, sql: str, results: list) -> str:
    message = anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""
A user asked: "{question}"

The following SQL was run:
{sql}

The results were:
{results}

Summarise the results in 2-3 plain English sentences that directly answer the question.
"""
            }
        ]
    )
    return message.content[0].text.strip()

def ask(question: str):
    print(f"\nQuestion: {question}")
    print("Generating SQL...")
    sql = generate_sql(question)
    print(f"SQL: {sql}\n")
    print("Running query...")
    results = run_query(sql)
    print(f"Raw results: {results}\n")
    print("Summarising...")
    summary = summarise_results(question, sql, results)
    print(f"Answer: {summary}\n")

if __name__ == "__main__":
    ask("Which therapeutic area has the highest average enrollment target?")
    ask("How many trials are currently recruiting?")
    ask("Which sponsor has the most completed trials?")