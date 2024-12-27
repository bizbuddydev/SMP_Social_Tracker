import streamlit as st
import openai
import pandas as pd
from datetime import datetime, timedelta
from google.cloud import bigquery

# Initialize OpenAI API
openai.api_key = st.secrets["openai_api_key"]

# Initialize OpenAI client
client = openai

# Initialize BigQuery client
bq_client = bigquery.Client()

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
        "Each idea should include the post date, caption content, post type (e.g., Reel, Story, Static Post), "
        "themes (from the strategy), and tone. Ensure the idea aligns with the strategy and introduces a mix of concepts. "
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

# This file is referenced elsewhere, no main function needed
