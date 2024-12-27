import streamlit as st
from google.oauth2 import service_account
from google.cloud import bigquery
import pandas as pd
from datetime import datetime, date, timedelta
import json

#For Viz
import seaborn as sns
import matplotlib.pyplot as plt

st.set_page_config(page_title="Social Overview", layout="wide")

# Define links to other pages
PAGES = {
    "Overview": "https://smp-bizbuddy-accountoverview.streamlit.app/",
    "Posts": "https://smp-bizbuddy-postoverview.streamlit.app",
    "Scheduler": "https://smp-bizbuddy-postscheduler.streamlit.app/",
}

# Sidebar navigation
st.sidebar.title("Navigation")
for page, url in PAGES.items():
    st.sidebar.markdown(f"[**{page}**]({url})", unsafe_allow_html=True)

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


def generate_ig_metrics(time_frame, account_data, post_data):    
    #Generate a DataFrame of Instagram metrics for a given time frame and the previous period.

    # Define date ranges
    today = datetime.today()
    current_period_start = today - timedelta(days=time_frame)
    previous_period_start = current_period_start - timedelta(days=time_frame)
    previous_period_end = current_period_start - timedelta(days=1)

    # Filter data for the current period
    current_account_data = account_data[
        (account_data['date'] >= current_period_start.date()) & 
        (account_data['date'] <= today.date())
    ]
    current_post_data = post_data[
        (post_data['created_time'] >= current_period_start) & 
        (post_data['created_time'] <= today)
    ]

    # Filter data for the previous period
    previous_account_data = account_data[
        (account_data['date'] >= previous_period_start.date()) & 
        (account_data['date'] <= previous_period_end.date())
    ]
    previous_post_data = post_data[
        (post_data['created_time'] >= previous_period_start) & 
        (post_data['created_time'] <= previous_period_end)
    ]

    # Calculate metrics for a given dataset
    def calculate_metrics(account_data, post_data):
        total_posts = len(post_data)
        followers_gained = account_data['follower_count'].sum() if 'follower_count' in account_data else 0
        total_reach = account_data['reach'].sum() if 'reach' in account_data else 0
        total_likes = post_data['like_count'].sum() if 'like_count' in post_data else 0
        total_comments = post_data['comments_count'].sum() if 'comments_count' in post_data else 0
        like_rate = total_likes / total_reach if total_reach > 0 else 0
        average_reach = total_reach / total_posts if total_posts > 0 else 0
        average_likes = total_likes / total_posts if total_posts > 0 else 0

        return {
            'Total Posts': total_posts,
            'Followers Gained': followers_gained,
            'Total Reach': total_reach,
            'Total Likes': total_likes,
            'Total Comments': total_comments,
            'Like Rate': like_rate,
            'Average Reach': average_reach,
            'Average Likes': average_likes,
        }

    # Create dataframes for current and previous periods
    current_metrics = calculate_metrics(current_account_data, current_post_data)
    previous_metrics = calculate_metrics(previous_account_data, previous_post_data)

    current_period_df = pd.DataFrame([current_metrics])
    previous_period_df = pd.DataFrame([previous_metrics])

    return current_period_df, previous_period_df

def calculate_percentage_diff_df(current_df, previous_df):
    
    #Calculate the percentage difference between two DataFrames.

    # Ensure the two DataFrames have the same structure
    if not current_df.columns.equals(previous_df.columns):
        raise ValueError("Both DataFrames must have the same columns.")

    # Convert all columns to numeric, coercing errors to NaN
    current_df = current_df.apply(pd.to_numeric, errors='coerce')
    previous_df = previous_df.apply(pd.to_numeric, errors='coerce')

    # Initialize an empty DataFrame for percentage differences
    percentage_diff_df = pd.DataFrame(columns=current_df.columns)

    # Calculate percentage differences for each column
    for column in current_df.columns:
        current_values = current_df[column]
        previous_values = previous_df[column]

        # Compute the percentage difference
        percentage_diff = []
        for current, previous in zip(current_values, previous_values):
            if pd.isna(current) or pd.isna(previous):
                diff = None  # Handle missing values
            elif current == previous:
                diff = 0  # Return 0 if the values are the same
            elif previous == 0:
                diff = None  # Handle division by zero (no valid percentage diff)
            else:
                diff = ((current - previous) / previous) * 100
                diff = round(diff, 2)  # Round to 2 decimal places
            percentage_diff.append(diff)

        # Add the percentage difference as a column
        percentage_diff_df[column] = percentage_diff

    return percentage_diff_df


# Main function to display data and visuals
def main():

    st.markdown(f"<h1 style='text-align: center;'>{ACCOUNT_NAME}</h1>", unsafe_allow_html=True)

    # Pull data using the function
    account_data = pull_dataframes(ACCOUNT_TABLE_ID)
    post_data = pull_dataframes(POST_TABLE_ID)
    post_data = post_data.sort_values(by='created_time', ascending=True)


    # Get daily posts
    account_data = get_daily_post_counts(post_data, account_data)
    account_data = account_data.sort_values(by='date', ascending=True)

    #Get Post Metrics
    time_frame = 7
    l7_igmetrics, p7_igmetrics = generate_ig_metrics(time_frame, account_data, post_data)
    l7_perdiff = calculate_percentage_diff_df(l7_igmetrics, p7_igmetrics)
    
    # Create layout with two columns
    col_left, col_right = st.columns(2)

    with col_left:

        st.subheader("All Time")
        # Columns for scorecards
        coll1, coll2 = st.columns(2) 
        
        # Calculate metrics
        if account_data is not None and not account_data.empty:
            total_followers = account_data.iloc[-1]['total_followers']  # Most recent day
        else:
            total_followers = 0

        total_posts = len(post_data) if post_data is not None else 0
        avg_reach = post_data['reach'].mean() if post_data is not None and not post_data.empty else 0
        avg_likes = post_data['like_count'].mean() if post_data is not None and not post_data.empty else 0

        #All Time
        # Display metrics
        with coll1:
            st.metric(label="Total Followers", value=f"{total_followers:,}")
        with coll2:
            st.metric(label="Total Posts", value=f"{total_posts:,}")

        st.subheader("Last 7 days")
         # Columns for scorecards
        coll3, coll4, coll5, coll6  = st.columns(4) 
        
        with coll3:
            st.metric(label="Total Posts", value=f"{l7_igmetrics.iloc[0]["Total Posts"]:,.0f}")
            diff = l7_perdiff.iloc[0]["Total Posts"]
            color = "green" if diff > 0 else "red" if diff < 0 else "gray"
            diff_text = f"<i style='color:{color};'>{diff:+.2f}%</i>"
            st.markdown(diff_text, unsafe_allow_html=True)
        with coll4:
            st.metric(label="Followers Gained", value=f"{l7_igmetrics.iloc[0]["Followers Gained"]:,.0f}")
            diff = l7_perdiff.iloc[0]["Followers Gained"]
            color = "green" if diff > 0 else "red" if diff < 0 else "gray"
            diff_text = f"<i style='color:{color};'>{diff:+.2f}%</i>"
            st.markdown(diff_text, unsafe_allow_html=True)
        with coll5:
            st.metric(label="Average Reach", value=f"{l7_igmetrics.iloc[0]["Average Reach"]:,.0f}")
            diff = l7_perdiff.iloc[0]["Average Reach"]
            color = "green" if diff > 0 else "red" if diff < 0 else "gray"
            diff_text = f"<i style='color:{color};'>{diff:+.2f}%</i>"
            st.markdown(diff_text, unsafe_allow_html=True)
        with coll6:
            st.metric(label="Average Likes", value=f"{l7_igmetrics.iloc[0]["Average Likes"]:,.0f}")
            diff = l7_perdiff.iloc[0]["Average Likes"]
            color = "green" if diff > 0 else "red" if diff < 0 else "gray"
            diff_text = f"<i style='color:{color};'>{diff:+.2f}%</i>"
            st.markdown(diff_text, unsafe_allow_html=True)

        account_data.rename(columns={"total_followers": "Total Followers", "follower_count", : "Followers Gained", "reach": "Reach", "impressions": "Impressions"}, inplace=True)
        
        # Dropdown for selecting metric
        metric_options = ['Total Followers', 'Followers Gained', 'Reach', 'Impressions']
        selected_metric = st.selectbox("Select Metric for Chart", metric_options)

        # Line chart for total followers over time
        if account_data is not None and not account_data.empty:
            account_data['date'] = pd.to_datetime(account_data['date'])
            account_data = account_data.sort_values(by='date', ascending=True)
        
            # Create the line plot
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.set_style("whitegrid")  # Set a friendly grid style
            sns.lineplot(data=account_data, x='date', y=selected_metric, ax=ax, color="royalblue", linewidth=2)
        
            # Customize the plot
            ax.set_title(f'{selected_metric} Over Time', fontsize=16, fontweight='bold')
            ax.set_xlabel('Date', fontsize=12)
            ax.set_ylabel(selected_metric, fontsize=12)
            ax.tick_params(axis='x', rotation=45)  # Rotate x-axis labels
            ax.grid(alpha=0.5)  # Adjust grid transparency
        
            # Enhance readability with larger font sizes
            ax.title.set_fontsize(18)
            ax.xaxis.label.set_fontsize(12)
            ax.yaxis.label.set_fontsize(12)
            ax.tick_params(axis='both', which='major', labelsize=10)
        
            # Display the plot in Streamlit
            st.pyplot(fig)


    with col_right:
        # Placeholder for other visuals or information
        st.header("AI Analysis of recent performance")
        st.write("- Strategic Recommendations")
        st.write("- Upcoming Posts")
        st.write("")


        st.header("Demographic Breakdown")
        st.write("")
        
        st.header("Calendar")
        st.write("")


# Run the app
if __name__ == "__main__":
    main()
