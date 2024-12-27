import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
import json

# Load the configuration file
def load_config(file_path="config.json"):
    with open(file_path, "r") as f:
        return json.load(f)

# Load the account configuration
config = load_config()

# Set env variables
ACCOUNT_NAME = config["ACCOUNT_NAME"]
PROJECT_ID = config["PROJECT_ID"]
DATASET_ID = config["DATASET_ID"]
IDEAS_TABLE_ID = config["IDEAS_TABLE_ID"]

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
        FROM `{PROJECT_ID}.{DATASET_ID}.{IDEAS_TABLE_ID}`
        ORDER BY date ASC
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
