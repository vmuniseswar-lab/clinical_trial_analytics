import os
import anthropic
import streamlit as st
import json
from google.oauth2 import service_account
from google.cloud import bigquery
from google.oauth2 import service_account
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="Clinical Trial Data Assistant",
    page_icon="🔬",
    layout="centered"
)

# BigQuery setup
@st.cache_resource
def get_bq_client():
    # credentials = service_account.Credentials.from_service_account_file(
    #     r"D:\clinical_trial_analytics\secrets\autonomous-rite-503820-t8-a0b9fa30e604.json"
    credentials_dict = json.loads(st.secrets["gcp_service_account"])
    credentials = service_account.Credentials.from_service_account_info(credentials_dict)
    return bigquery.Client(credentials=credentials, project="autonomous-rite-503820-t8")

# Anthropic setup
@st.cache_resource
def get_anthropic_client():
    return anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

@st.cache_resource
def get_elevenlabs_client():
    return ElevenLabs(api_key=st.secrets["ELEVENLABS_API_KEY"])

SCHEMA_CONTEXT = """
You are a data analyst assistant. You have access to a BigQuery dataset called 
'clinical_trial_analytics' with the following Gold layer tables:

1. fct_enrollment - One row per trial with enrollment metrics
   - trial_id (STRING)
   - therapeutic_area_id (STRING)
   - sponsor_id (STRING)
   - enrollment_target (INT)
   - enrollment_actual (INT)
   - enrollment_rate_pct (FLOAT)
   - enrollment_type (STRING)
   - start_date (DATE)
   - completion_date (DATE)
   - planned_duration_days (INT)
   - is_completed (BOOL)

2. dim_trial - Trial descriptive attributes
   - trial_id (STRING)
   - trial_title (STRING)
   - trial_phase (STRING)
   - trial_status (STRING)
   - study_type (STRING)
   - stage_group (STRING)
   - duration_band (STRING)

3. dim_sponsor - Sponsor details
   - sponsor_id (STRING)
   - sponsor_name (STRING)

4. dim_therapeutic_area - Therapeutic area details
   - therapeutic_area_id (STRING)
   - therapeutic_area_name (STRING)

Write a BigQuery SQL query to answer the user's question.
Return ONLY the SQL query, no explanation, no markdown, no backticks.
Use fully qualified table names: autonomous-rite-503820-t8.clinical_trial_analytics.table_name
"""

def generate_sql(question: str) -> str:
    client = get_anthropic_client()
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": f"{SCHEMA_CONTEXT}\n\nQuestion: {question}"}]
    )
    return message.content[0].text.strip()

def run_query(sql: str) -> list:
    client = get_bq_client()
    query_job = client.query(sql)
    results = query_job.result()
    return [dict(row) for row in results]

def summarise_results(question: str, sql: str, results: list) -> str:
    client = get_anthropic_client()
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": f"""
A user asked: "{question}"
The following SQL was run: {sql}
The results were: {results}
Summarise the results in 2-3 plain English sentences that directly answer the question.
"""
        }]
    )
    return message.content[0].text.strip()

def text_to_speech(text: str) -> bytes:
    client = get_elevenlabs_client()
    audio = client.text_to_speech.convert(
        voice_id="JBFqnCBsd6RMkjVDRZzb",
        text=text,
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    )
    return b"".join(audio)

# UI
st.title("🔬 Clinical Trial Data Assistant")
st.markdown("Ask any question about clinical trial data in plain English.")

# Example questions
st.markdown("**Example questions:**")
examples = [
    "Which therapeutic area has the highest average enrollment target?",
    "How many trials are currently recruiting?",
    "Which sponsor has the most completed trials?",
    "What percentage of trials are in Phase 3?",
    "Which trials have the longest planned duration?"
]
for example in examples:
    if st.button(example, key=example):
        st.session_state.question = example

# Question input
question = st.text_input(
    "Your question:",
    value=st.session_state.get("question", ""),
    placeholder="e.g. Which sponsor has the most trials?"
)

if st.button("Ask", type="primary") and question:
    with st.spinner("Generating SQL..."):
        sql = generate_sql(question)

    with st.spinner("Running query..."):
        try:
            results = run_query(sql)

            with st.spinner("Summarising..."):
                summary = summarise_results(question, sql, results)

            # Store everything so it survives reruns (e.g. clicking the audio button)
            st.session_state.last_sql = sql
            st.session_state.last_results = results
            st.session_state.last_summary = summary

        except Exception as e:
            st.error(f"Query failed: {e}")

# Display block - reads from session_state so it persists across reruns
if "last_summary" in st.session_state:
    st.subheader("Generated SQL")
    st.code(st.session_state.last_sql, language="sql")

    st.subheader("Raw Results")
    st.dataframe(st.session_state.last_results)

    st.subheader("Answer")
    st.success(st.session_state.last_summary)

    if st.button("🔊 Read answer aloud"):
        with st.spinner("Generating audio..."):
            audio_bytes = text_to_speech(st.session_state.last_summary)
        st.audio(audio_bytes, format="audio/mp3")