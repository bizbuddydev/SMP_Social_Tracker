import streamlit as st
from openai import OpenAI

# Initialize the OpenAI client
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# Function to call ChatGPT
def generate_strategy(business_details, social_media_goals):
    try:
        # Construct the full prompt
        full_prompt = f"""
        Based on the provided business details and goals, generate a strategy that includes:

        1. **Content Plan**: Suggested content ideas tailored to the business's industry, target audience, and brand voice.
        2. **Posting Schedule**: A recommended schedule for posting content, aligned with the desired growth and content frequency.
        3. **Engagement Tips**: Specific strategies to increase audience interaction and engagement.
        4. **Feature Utilization**: Recommendations for using Instagram features like Stories, Reels, and Highlights effectively.
        5. **Performance Metrics**: Key performance indicators to track success and align with the business's goals.

        ### Business Details:
        {business_details}

        ### Social Media Goals:
        {social_media_goals}
        """

        # Call the OpenAI ChatGPT API
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a social media strategist specializing in Instagram."},
                {"role": "user", "content": full_prompt}
            ],
            max_tokens=500,
            temperature=0.7,
        )

        # Extract the response content
        answer = response.choices[0].message.content
        return answer

    except Exception as e:
        return f"Error: {e}"

# Streamlit App
st.title("Instagram Strategy Generator")

# Form for user input
with st.form("strategy_form"):
    st.subheader("Enter Business Details")
    business_name = st.text_input("Business Name")
    business_description = st.text_area("Description of Business and Instagram Goals")
    industry_category = st.text_input("Industry/Category")
    products_services = st.text_area("Products/Services Offered")
    target_audience = st.text_area("Target Audience (demographics, interests, behaviors)")
    brand_voice_tone = st.text_input("Brand Voice and Tone (e.g., professional, casual, humorous)")
    
    st.subheader("Enter Social Media Goals")
    desired_growth = st.selectbox("Desired Growth", ["Aggressive", "Moderate", "Maintain"])
    preferred_post_types = st.text_area("Preferred Post Types (e.g., videos, infographics, memes)")
    topics_of_interest = st.text_area("Topics of Interest")
    content_frequency = st.selectbox("Content Frequency", ["Daily", "Weekly", "Monthly"])

    # Submit button
    submitted = st.form_submit_button("Generate Strategy")

# Handle form submission
if submitted:
    # Compile inputs into structured sections
    business_details = f"""
    - Business Name: {business_name}
    - Description: {business_description}
    - Industry/Category: {industry_category}
    - Products/Services: {products_services}
    - Target Audience: {target_audience}
    - Brand Voice and Tone: {brand_voice_tone}
    """

    social_media_goals = f"""
    - Desired Growth: {desired_growth}
    - Preferred Post Types: {preferred_post_types}
    - Topics of Interest: {topics_of_interest}
    - Content Frequency: {content_frequency}
    """

    # Generate strategy
    strategy = generate_strategy(business_details, social_media_goals)

    # Display the strategy
    st.subheader("Generated Strategy")
    st.text(strategy)
