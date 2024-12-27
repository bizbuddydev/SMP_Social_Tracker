import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd

# Table details
PROJECT_ID = "bizbuddydemo-v1"
DATASET_ID = "strategy_data"
TABLE_ID = "smp_postideas"

st.set_page_config(page_title="Post Scheduler", layout="wide")

# Load credentials and project ID from st.secrets
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)

# Initialize BigQuery client
client = bigquery.Client(credentials=credentials, project=PROJECT_ID)


def fetch_post_data():
    """Fetch post data from BigQuery."""
    query = f"""
        SELECT date, caption, post_type, themes, tone, source
        FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
        ORDER BY date DESC
    """
    query_job = client.query(query)
    return query_job.to_dataframe()

def main():
    st.title("Instagram Post Ideas Dashboard")

    # Fetch data from BigQuery
    posts = fetch_post_data()

    # Display posts
    st.subheader("Upcoming Posts")

    for index, row in posts.iterrows():
        with st.expander(f"{row['date']}: {row['caption'][:50]}..."):
            st.markdown(f"**Date:** {row['date']}")
            st.markdown(f"**Caption:** {row['caption']}")
            st.markdown(f"**Post Type:** {row['post_type']}")
            st.markdown(f"**Themes:** {row['themes']}")
            st.markdown(f"**Tone:** {row['tone']}")
            st.markdown(f"**Source:** {row['source']}")

if __name__ == "__main__":
    main()
