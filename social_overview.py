import streamlit as st
from google.oauth2 import service_account
from google.cloud import bigquery
import pandas as pd
from datetime import date, timedelta
import json

st.set_page_config(page_title="Social Overview", layout="wide")

# Load the configuration file
def load_config(file_path="config.json"):
    with open(file_path, "r") as f:
        return json.load(f)

# Load the account configuration
config = load_config()

st.write("config loaded")

# Set env variables
PROJECT_ID = config["PROJECT_ID"]
DATASET_ID = config["DATASET_ID"]
TABLE_ID = config["ACCOUNT_TABLE_ID"]

st.write("variables loaded")

# Load credentials and project ID from st.secrets
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)

st.write("secrets loaded")

# Initialize BigQuery client
client = bigquery.Client(credentials=credentials, project=PROJECT_ID)

st.write("client loaded")

# Function to pull data from BigQuery
def pull_account_data():
    
    # Build the table reference
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

    st.write(table_ref)

    # Query to fetch all data from the table
    query = f"SELECT * FROM `{table_ref}`"
    
    try:
        # Execute the query
        query_job = client.query(query)
        result = query_job.result()
        # Convert the result to a DataFrame
        data = result.to_dataframe()
        return data
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

# Main function to display data and visuals
def main():
    st.title("Instagram Account Overview")
    st.write("Fetching account data...")

    # Pull data using the function
    data = pull_account_data()

    if data is not None:
        # Display the raw data as a table
        st.subheader("Account Data")
        st.dataframe(data)

        # Placeholder for visuals (to be built next)
        st.subheader("Visualizations")
        st.write("Visualizations will go here!")
    else:
        st.write("No data available or error in fetching data.")

# Run the app
if __name__ == "__main__":
    main()
