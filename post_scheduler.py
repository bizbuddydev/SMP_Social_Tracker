import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
from datetime import datetime, timedelta
import openai
import json

st.set_page_config(page_title="Post Scheduler", layout="wide")

# Load the configuration file
def load_config(file_path="config.json"):
    with open(file_path, "r") as f:
        return json.load(f)

# Load the account configuration
config = load_config()

# Set env variables
ACCOUNT_NAME = config["ACCOUNT_NAME"]
PROJECT_ID = config["PROJECT_ID"]
ACCOUNT_DATASET_ID = config["ACCOUNT_DATASET_ID"]
IDEAS_TABLE_ID = config["IDEAS_TABLE_ID"]

# Load credentials and project ID from st.secrets
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)

# Load BQ Client
bq_client = bigquery.Client(credentials=credentials, project=PROJECT_ID)

openai.api_key = st.secrets["openai"]["api_key"]

# Initialize OpenAI client
client = openai


# Function to fetch the latest date and calculate the next post date
def fetch_latest_date():
    """
    Fetch the latest date from the smp_postideas table and return 3 days after it.

    Returns:
        datetime: The calculated next post date.
    """
    query = """
        SELECT MAX(date) as latest_date
        FROM `bizbuddydemo-v1.strategy_data.smp_postideas`
    """
    query_job = bq_client.query(query)
    result = query_job.result()
    latest_date = result.to_dataframe().iloc[0]["latest_date"]
    return latest_date + timedelta(days=3)

# Function to generate a single post idea
def generate_post_idea(strategy):
    """
    Generate a single post idea using the provided strategy.

    Args:
        strategy (dict): A dictionary containing the social media strategy.

    Returns:
        pd.DataFrame: A dataframe containing the generated post idea.
    """
    prompt = (
        f"Based on this social media strategy: {strategy}, generate 1 post idea. "
        "Each idea should include the post Date, caption content, post type (e.g., Reel, Story, Static Post), "
        "themes (from the strategy), and tone. Ensure that the returned JSON object only has these columns with the exact names: "Date", "caption", "post_type", "themes", "tone", "source". Ensure the idea aligns with the strategy and introduces a mix of concepts. "
        "Format as a JSON object."
    )

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a social media manager with expertise in creating engaging content."},
            {"role": "user", "content": prompt}
        ]
    )

    idea_json = response.choices[0].message.content.strip()

    # Convert the JSON idea to a DataFrame
    idea_df = pd.read_json(idea_json, typ="series").to_frame().T

    # Assign a date to the post
    idea_df["Date"] = fetch_latest_date()

    return idea_df

# Function to add a row to the smp_postideas table in BigQuery
def add_post_to_bigquery(post_df):
    """
    Add a generated post idea to the smp_postideas table in BigQuery.

    Args:
        post_df (pd.DataFrame): The dataframe containing the post idea to be added.
    """
    table_id = "bizbuddydemo-v1.strategy_data.smp_postideas"

    # Insert the DataFrame row directly into BigQuery
    job = bq_client.load_table_from_dataframe(post_df, table_id)
    job.result()  # Wait for the load job to complete

    if job.errors:
        raise Exception(f"Failed to insert row into BigQuery: {job.errors}")


def fetch_post_data():
    """Fetch post data from BigQuery."""
    query = f"""
        SELECT date, caption, post_type, themes, tone, source
        FROM `{PROJECT_ID}.{ACCOUNT_DATASET_ID}.{IDEAS_TABLE_ID}`
        ORDER BY date ASC
    """
    query_job = bq_client.query(query)
    return query_job.to_dataframe()

def main():
    st.title("Instagram Post Ideas Dashboard")

    # Add functionality to generate and add a post
    if st.button("Add Post"):
        with st.spinner("Generating and adding post..."):
            # Load strategy data (placeholder example)
            strategy = {
                "content_plan": [
                    "Testimonials from clients who have improved their performance through your services.",
                    "Short videos or animated infographics explaining different concepts in sports psychology.",
                    "Case studies showing how mental performance can affect sports outcomes.",
                    "Behind-the-scenes content showing what a 1 on 1 session may look like.",
                    "Inspirational quotes about mental resilience and strength.",
                    "Regular Q&A's or AMA (Ask Me Anything) sessions to address common questions or misconceptions about sports psychology."
                ],
                "tone": ["Inspirational", "Educational", "Casual"],
                "post_types": ["Reel", "Story", "Static Post"],
                "past_posts_summary": """Final Summary: This Instagram account primarily focuses on mental performance coaching in sports, offering insights, strategies, and examples of successful athletes who utilize these techniques. Posts often delve into specific mental strategies like visualization, self-talk, positive affirmations, and maintaining focus on the present moment or process rather than the outcome. The account also emphasizes the importance of resilience, confidence, body language, and optimal arousal levels for peak performance. The strategists also discuss the value of reframing negative experiences as learning opportunities and the role of good sleep habits in cognitive function. Teamwork in sports is frequently highlighted, with a focus on football and volleyball. Engagement with followers is encouraged through calls to action, such as following the page or sending direct messages for additional information or inquiries about one-on-one coaching sessions."""
            }

            # Generate a post idea
            post_df = generate_post_idea(strategy)

            # Add the post to BigQuery
            add_post_to_bigquery(post_df)

        st.success("Post successfully added!")

    # Fetch data from BigQuery
    posts = fetch_post_data()

    # Display posts
    st.subheader("Upcoming Posts")

    for index, row in posts.iterrows():
        with st.expander(f"{row['date']}, {row['post_type']}: {row['caption'][:50]}..."):
            st.markdown(f"**Date:** {row['date']}")
            st.markdown(f"**Caption:** {row['caption']}")
            st.markdown(f"**Post Type:** {row['post_type']}")
            st.markdown(f"**Themes:** {row['themes']}")
            st.markdown(f"**Tone:** {row['tone']}")
            st.markdown(f"**Source:** {row['source']}")

if __name__ == "__main__":
    main()
