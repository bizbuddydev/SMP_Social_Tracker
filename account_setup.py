import streamlit as st
import openai

# Initialize ChatGPT credentials
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Function to call ChatGPT
def generate_strategy(user_input):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a social media strategist specializing in Instagram."},
                {"role": "user", "content": user_input}
            ],
            max_tokens=500,
            temperature=0.7,
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error: {e}"

# App title
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
    # Compile user inputs into a prompt
    user_input = f"""
    You are a social media strategist specializing in Instagram. Based on the provided business details and goals, generate a strategy that includes these entries:

    1. **Content Plan**: Suggested content ideas tailored to the business's industry, target audience, and brand voice.
    2. **Posting Schedule**: A recommended schedule for posting content, aligned with the desired growth and content frequency.
    3. **Engagement Tips**: Specific strategies to increase audience interaction and engagement.
    4. **Feature Utilization**: Recommendations for using Instagram features like Stories, Reels, and Highlights effectively.
    5. **Performance Metrics**: Key performance indicators to track success and align with the business's goals.
    
    ### Business Details:
    
    - Business Name: {business_name}
    - Description: {business_description}
    - Industry/Category: {industry_category}
    - Products/Services: {products_services}
    - Target Audience: {target_audience}
    - Brand Voice and Tone: {brand_voice_tone}
    
    ### Social Media Goals:
    
    - Desired Growth: {desired_growth}
    - Preferred Post Types: {preferred_post_types}
    - Topics of Interest: {topics_of_interest}
    - Content Frequency: {content_frequency}
    
    Return the entries in JSON format for example:
    {
    ”Content Plan”: “Response for entry…”,
    “**Posting Schedule”: “**“Response for entry…”,
    Next entries…
    }"""
  
    # Call ChatGPT
    strategy = generate_strategy(user_input)

    # Display the strategy
    st.subheader("Generated Strategy")
    st.text(strategy)
