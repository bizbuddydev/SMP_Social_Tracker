import streamlit as st
from google.oauth2 import service_account
from google.cloud import bigquery
import pandas as pd
from datetime import date, timedelta
import json

st.set_page_config(page_title="Social Overview", layout="wide")

# Function to pull data from BigQuery
def pull_account_data():
    # Load configuration details from config.json
    with open("config.json", "r") as file:
        config = json.load(file)
    
    PROJECT_ID = config["PROJECT_ID"]
    DATASET_ID = config["DATASET_ID"]
    TABLE_ID = config["ACCOUNT_TABLE_ID"]

    # Build the table reference
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    
    # Initialize BigQuery client
    client = bigquery.Client()

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
