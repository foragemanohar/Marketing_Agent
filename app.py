import streamlit as st
import subprocess
import os
import time
import re
from src.agents.input_validation_agent.graph import relevance_graph
from constants import APP_TITLE, GENERATED_CONTENT_FILE, READABILITY_SUGGESTIONS_FILE, SEO_SCORE_FILE, MAX_ITERATIONS
from src.agents.input_validation_agent.nodes import blog_validation,blog_refinement
from src.agents.input_validation_agent.state import State # Import your state class
# from seo import run_seo_analysis
def read_seo_score():
    """Reads the SEO score from file and extracts the numeric value."""
    if os.path.exists(SEO_SCORE_FILE):
        with open(SEO_SCORE_FILE, "r", encoding="utf-8") as file:
            content = file.read().strip()
            try:
                # Extract numeric score
                return float(re.search(r"([\d.]+)", content).group(1))
            except (AttributeError, ValueError):
                return 0.0  # Default if extraction fails
    return 0.0


def read_readability_suggestions():
    """Reads readability suggestions from file."""
    if os.path.exists(READABILITY_SUGGESTIONS_FILE):
        with open(READABILITY_SUGGESTIONS_FILE, "r", encoding="utf-8") as file:
            return file.read()
    return None


def save_content_to_file(content):
    """Saves generated content to a file."""
    with open(GENERATED_CONTENT_FILE, "w", encoding="utf-8") as file:
        file.write(content)


def clear_generated_content():
    """Deletes the generated content file if it exists."""
    if os.path.exists(GENERATED_CONTENT_FILE):
        os.remove(GENERATED_CONTENT_FILE)


def generate_and_optimize_content(user_topic, provider, model, use_streaming, blog_placeholder, seo_placeholder):
    """Generates and optimizes content until the target SEO score is reached."""
    result = {}
    
    with st.spinner("Generating initial content..."):
        result = relevance_graph.invoke(
            {"user_topic": user_topic, "provider": provider,
                "model": model, "streaming": use_streaming}
        )

    if not result or result.get("rating", 0) < 8:
        st.error("❌ Content generation failed. Your topic might need improvement.")
        if(result.get("reasons")):
            st.warning("⚠️ **Why is your topic irrelevant?**")
            st.write(result.get("reasons"))
        st.info("💡 **How to improve your topic?**")
        st.subheader("Recommended Inputs:")
        st.write(result.get("recommendations", "No recommendations available."))
        st.markdown("🔄 **Try modifying your topic and re-run the generation.**")
        return
   

    blog_content = result.get("validated_blog", "No content generated.")
    blog_placeholder.subheader("📝 Generated Blog:")
    blog_placeholder.markdown(blog_content, unsafe_allow_html=True)
    save_content_to_file(blog_content)
    st.success("✅ Content saved! Running SEO tool now...")
    # breakpoint()
    # Run SEO for the first time
    # breakpoint()
    subprocess.run(["python", "seo.py"], check=True)
   
    time.sleep(2)
    current_seo_score = read_seo_score()
    seo_placeholder.info(f"📊 Initial SEO Score: {current_seo_score}")

    if current_seo_score >= 9.5:
        st.success(
            f"🎯 Target SEO Score ({current_seo_score}) achieved! No further optimization needed. ✅")
        return

    st.warning(
        f"⚠️ Target score not reached ({current_seo_score}). Optimizing content to reach {9.5}...")

    iteration = 1

    while iteration <= MAX_ITERATIONS:
        st.info(f"⚙️ Optimization in progress... (Iteration {iteration})")
        # clear_generated_content()
        blog_placeholder.empty()

        # Generate optimized content
        # result = relevance_graph.invoke(
        #     {"user_topic": user_topic, "provider": provider,
        #         "model": model, "streaming": use_streaming}
        # )

        # if not result or result.get("rating", 0) < 8:
        #     st.error("❌ Content generation failed. Please modify the topic.")
        #     break
        # Step 4: Validate the existing blog again (NO RE-GENERATION)

        
        seo_suggestions = read_readability_suggestions()  # Change to your actual file name
        seo_score=read_seo_score()
        state = {
        "user_topic": user_topic,
        "blog_content": blog_content,  # Use the latest validated blog content
        "seo_suggestions": seo_suggestions,  # Store extracted SEO feedback
        "seo_score": seo_score,  # Store extracted SEO score
        "provider": provider,
        "model": model,
            }
        # state = State({
        # "user_topic": user_topic,
        # "validated_blog": blog_content,
        # "seo_suggestions": seo_suggestions,
        # "seo_score": seo_score,
        # })

        validated_state = blog_validation(state,iteration,blog_content)
        blog_content = validated_state.get("validated_blog")
    
        print(blog_content,"((((()))))")
        blog_placeholder.subheader(
            f"📝 Optimized Blog - Iteration {iteration}:")
        blog_placeholder.markdown(blog_content, unsafe_allow_html=True)
        save_content_to_file(blog_content)
        st.success("✅ Content saved! Running SEO tool again...")

        # # **Re-run SEO after every optimization attempt**
        # try:
        #     # process = subprocess.run(["python", "seo.py"], check=True, capture_output=True, text=True)
        #     run_seo_analysis()
        # except subprocess.CalledProcessError as e:
        #     print(f"Error: {e}")
        #     print(f"STDOUT: {e.stdout}")
        #     print(f"STDERR: {e.stderr}")
        subprocess.run(["python", "seo.py"], check=True)
        time.sleep(2)
        current_seo_score = read_seo_score()
        seo_placeholder.info(f"📊 Updated SEO Score: {current_seo_score}")

        # Stop if we reach the target SEO score
        if current_seo_score >= 9.5:
            st.success(
                f"🎯 Optimization complete! Final SEO Score: {current_seo_score} ✅")
            return

        iteration += 1

    st.warning(
        f"⚠️ Stopped at SEO Score {current_seo_score}. Couldn't reach target ({9.5}) within {MAX_ITERATIONS} iterations.")


def main():
    """Main function to run the Streamlit app."""

    st.title(APP_TITLE)

    if "blog_placeholder" not in st.session_state:
        st.session_state.blog_placeholder = st.empty()
    if "seo_placeholder" not in st.session_state:
        st.session_state.seo_placeholder = st.empty()

    blog_placeholder = st.session_state.blog_placeholder
    seo_placeholder = st.session_state.seo_placeholder

    user_topic = st.text_area("Enter your topic:", height=100)

    models = {
        "OpenAI GPT-4o": ("openai", "gpt-4o"),
        "OpenAI GPT-4o-mini": ("openai", "gpt-4o-mini"),
        "OpenAI GPT-3.5-turbo": ("openai", "gpt-3.5-turbo"),
        "Claude 3 Opus": ("anthropic", "claude-3-opus-20240229"),
        "Claude 3 Sonnet": ("anthropic", "claude-3-7-sonnet-20250219"),
        "Claude 3 Haiku": ("anthropic", "claude-3-5-haiku-20241022"),
    }

    with st.sidebar:
        st.header(APP_TITLE)
        st.write("Forage AI Agent Application")
        with st.expander("⚙️ Settings"):
            model_name = st.radio("Select LLM Model",
                                  options=models.keys(), index=0)
            provider, model = models[model_name]
            use_streaming = st.toggle("Stream results", value=True)

    if st.button("Validate"):
        if not user_topic:
            st.warning("⚠️ Please enter a topic.")
            return
        generate_and_optimize_content(
            user_topic, provider, model, use_streaming, blog_placeholder, seo_placeholder)


if __name__ == "__main__":
    main()
