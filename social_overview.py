import streamlit as st
from google.oauth2 import service_account
from google.cloud import bigquery
import pandas as pd
from datetime import datetime, date, timedelta
import json

st.set_page_config(page_title="Social Overview", layout="wide")

# Load the configuration file
def load_config(file_path="config.json"):
    with open(file_path, "r") as f:
        return json.load(f)

# Load the account configuration
config = load_config()

# Set env variables
PROJECT_ID = config["PROJECT_ID"]
DATASET_ID = config["DATASET_ID"]
ACCOUNT_TABLE_ID = config["ACCOUNT_TABLE_ID"]
POST_TABLE_ID = config["POST_TABLE_ID"]

# Load credentials and project ID from st.secrets
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)

# Initialize BigQuery client
client = bigquery.Client(credentials=credentials, project=PROJECT_ID)

# Function to pull data from BigQuery
def pull_dataframes(table_id):
    
    # Build the table reference
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{table_id}"

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


def get_daily_post_counts(post_data, account_data):
    # Ensure created_time is in datetime format
    post_data['date'] = pd.to_datetime(post_data['created_time'])
    account_data['date'] = pd.to_datetime(account_data['date']).dt.date

    # Generate the last 30 days as a date range
    yesterday = datetime.today() - timedelta(days=1)
    date_range = [yesterday - timedelta(days=i) for i in range(31)]
    date_range = sorted(date_range)  # Ensure dates are in ascending order

    # Initialize an empty list to store daily counts
    daily_counts = []

    # Count posts for each day
    for day in date_range:
        # Filter posts matching the current day
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)

        post_count = post_data[(post_data['created_time'] >= day_start) & 
                               (post_data['created_time'] <= day_end)].shape[0]
        daily_counts.append({
            'date': day.date(),
            'post_count': post_count
        })

    # Convert to DataFrame
    daily_post_counts_df = pd.DataFrame(daily_counts)

    # Merge with account_data on the Date column
    merged_df = pd.merge(account_data, daily_post_counts_df, how="left", on="date")

    return merged_df


# Main function to display data and visuals
def main():
        

    # Pull data using the function
    account_data = pull_dataframes(ACCOUNT_TABLE_ID)
    post_data = pull_dataframes(POST_TABLE_ID)
    account_data = get_daily_post_counts(post_data, account_data)

    with st.expander("Account Data"):
        st.write(account_data)

    with st.expander("Post Data"):
        post_data

    # Create layout with two columns
    col1, col2 = st.columns(2)

    with col1:
        # Calculate metrics
        if account_data is not None and not account_data.empty:
            total_followers = account_data.iloc[-1]['follower_count']  # Most recent day
        else:
            total_followers = 0

        total_posts = len(post_data) if post_data is not None else 0

        avg_reach = post_data['reach'].mean() if post_data is not None and not post_data.empty else 0

        avg_likes = post_data['likes'].mean() if post_data is not None and not post_data.empty else 0

        # Display metrics
        st.metric(label="Total Followers", value=f"{total_followers:,}")
        st.metric(label="Total Posts", value=f"{total_posts:,}")
        st.metric(label="Average Reach", value=f"{avg_reach:,.0f}")
        st.metric(label="Average Likes", value=f"{avg_likes:,.0f}")

    with col2:
        # Placeholder for other visuals or information
        st.write("Other visualizations or information can go here.")


# Run the app
if __name__ == "__main__":
    main()
