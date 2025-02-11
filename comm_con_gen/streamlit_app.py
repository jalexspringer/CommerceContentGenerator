import os
import time
import streamlit as st
import streamlit.components.v1 as components
from comm_con_gen.countries import country_languages
from comm_con_gen.utility import *

# Initialize session state for API key
if "anthropic_api_key" not in st.session_state:
    st.session_state["anthropic_api_key"] = ""

st.markdown("""
## Commerce Content Generator
The iCCG is a project that generates branded content articles based on user-specified parameters. It supports various article types, languages, and advertiser products.
""")

# API Key input in sidebar
with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input("Anthropic API Key", 
                           type="password", 
                           value=st.session_state.anthropic_api_key,
                           help="Enter your Anthropic API key to use the content generator")
    if api_key:
        st.session_state.anthropic_api_key = api_key

# Main content
if not st.session_state.anthropic_api_key:
    st.warning("⚠️ Please enter your Anthropic API key in the sidebar to use the content generator.")
    st.stop()

st.markdown("""
### Features
- Generate listicles, product reviews, gift guides, deal roundups, and how-to articles
- Customize voice, length, language, and advertiser products
- Enrich generated copy with product mentions and link placements
- Output copy for review, editing, and commenting
- Convert final copy to HTML with affiliate links
- Get a calendar of local events for a given country and use them in your article generation
- Utilize predefined writing styles or generate a new style summary from a provided URL
            
### Feature Instructions""")


with st.expander("Writing Styles"):
    st.markdown("""
    #### Writing Style
    - Select from predefined writing styles or generate a new style summary from a provided URL.
    - If selecting "Other" for the writing style, enter a URL of a writing style example and click "Get Style" to generate a new style summary.
    - The generated style summary will be displayed below the selection.
    """)
with st.expander("Product Data"):
    st.markdown("""
    #### Selected Product Data
    - View the selected product data in a table format.
    - The table includes the product name, price, discount, brand, color, and affiliate link.
    """)
with st.expander("Publishing Calendar"):
    st.markdown("""
    #### Publishing Calendar
    - Click "Get Event Calendar" to generate a publishing calendar with important dates and their names for the selected audience country.
    - Select the desired events from the generated calendar to theme the article around those events.
    - If no specific event is selected, a single article will be generated for the specified publishing date.
    """)
with st.expander("Article Editor"):
    st.markdown("""
    #### Generated Article Editor
    - Select a generated article from the dropdown menu to view and edit it.
    - Make changes to the article in the text area and click "Save Changes" to update the file.
    - Click "Delete Article" to remove the selected article.
    - Select the desired download format (Markdown or HTML) and click "Download" to download the article in the chosen format.
    - The downloaded HTML file will be saved in the html_outputs directory.
    """)

st.markdown("### Content Generation Options")

col1, col2, col3 = st.columns(3)
with col1:

    impact_partner_id = st.number_input("Impact.com Partner ID", min_value=0, step=1, value=12345)

    audience_country = st.selectbox("Audience Country", list(country_languages.keys()), key="audience_country")
    language = st.selectbox("Language", country_languages[audience_country] + ["English"] if "English" not in country_languages[audience_country] else country_languages[audience_country])
with col2:
    publishing_date = st.date_input("Publishing Date")
    article_word_length = st.number_input("Article Max Word Length", min_value=500, max_value=3000, value=2000, step=100)
    llm_model = st.selectbox("LLM Model", list(llm_models.values()))

with col3:
    article_type = st.selectbox("Article Type", ["Gift Guide", "Product Review", "How To", "Listicle", "Deal Radar"])

    product_options = []
    for file in os.listdir("comm_con_gen/test_products"):
        if file.endswith(".json"):
            product_name = file[:-5]  # Remove .json extension
            product_options.append(product_name)
    product = st.selectbox("Product", product_options)
    

with st.expander("Additional Options", expanded=True):
    tab1, tab2, tab3 = st.tabs(["Writing Style", "Selected Product Data", "Publishing Calendar"])
    with tab1:
        st.subheader("Select Writing Style")

        style_options = []
        for file in os.listdir("comm_con_gen/voices"):
            if file.endswith(".txt"):
                style_name = file[:-4].capitalize()  # Remove .txt extension and capitalize
                style_options.append(style_name)

        style_options.append("Other")
        style = st.selectbox("Writing Style", style_options)

        if style == "Other":
            style_url = st.text_input("Enter the URL of the writing style example:")

            if st.button("Get Style"):
                if style_url:
                    with st.spinner("Generating voice..."):
                        start_time = time.time()
                        style = get_voice_examples(style_url)
                        end_time = time.time()
                        duration = int(end_time - start_time)
                        st.success(f"Voice generated in {duration} seconds.")
                    print(style_url)
                    print(style)
                else:
                    st.warning("Please enter a URL to get the writing style.")
                    style = None
        else:
            style_url = None
            voice_file = f"comm_con_gen/voices/{style.lower()}.txt"
            if os.path.exists(voice_file):
                with open(voice_file, "r") as f:
                    style_summary = f.read()
                    st.markdown(style_summary)
            else:
                st.warning("No summary available for the selected style.")

    with tab2:
        product_data = load_products(product)
        
        table_data = []
        
        for product_name, product_info in product_data.items():
            name = product_info["name"]
            price = product_info["price"]
            discount = product_info["discount"]
            brand = product_info["brand"]
            color = product_info["color"]
            link = product_info["link"]
            
            table_data.append([name, price, discount, brand, color, link])
        
        st.table(table_data)

    with tab3:
        if st.button(f"Get Event Calendar for {audience_country}"):
            publishing_calendar = get_publishing_calendar(audience_country)
            st.session_state.publishing_calendar = publishing_calendar
        selected_events = []
        if "publishing_calendar" in st.session_state:
            st.markdown(f"#### Events for {audience_country}")
            publishing_calendar = st.session_state.publishing_calendar
            col1, col2 = st.columns(2)
            
            events = list(publishing_calendar.items())
            mid = len(events) // 2
            with col1:
                for date, event in events[:mid]:
                    if st.checkbox(f"{date}: {event}"):
                        selected_events.append(f"{date}: {event}")
            with col2:
                for date, event in events[mid:]:
                    if st.checkbox(f"{date}: {event}"):
                        selected_events.append(f"{date}: {event}")
            selected_event = ", ".join(selected_events)

st.markdown("### Summary")
st.write(f"You are generating a {article_word_length} word {article_type} article in {language} for {audience_country} audience. The article will feature {product} products and be written in the {style} writing style.")

if selected_events:
    st.write("The article will be themed around the following event(s):")
    for event in selected_events:
        st.write(f"- {event}")
else:
    st.write("No specific event selected for the article theme. A single article will be generated for the specified publishing date.")
if st.button("Generate Articles"):
    if style == "Other" and style_url is None:
        st.warning("Please get the writing style first before generating the articles.")
    else:
        with st.spinner("Generating article(s)..."):
            start_time = time.time()
            if selected_events:
                event_dates_names = [event.split(": ") for event in selected_events]
                event_dates = [date for date, name in event_dates_names]
                event_names = [name for date, name in event_dates_names]
                concatenated_events = ", ".join(selected_events)
                article, file_properties = create_article(article_type, audience_country, ", ".join(event_dates),
                                                           article_word_length, product, language, style,
                                                           impact_partner_id, llm_model, concatenated_events)
                save_article(article, file_properties)
                st.success(f"Article for events '{', '.join(event_names)}' generated and saved.")
            else:
                article, file_properties = create_article(article_type, audience_country, publishing_date,
                                                           article_word_length, product, language, style,
                                                           impact_partner_id, llm_model, "")
                save_article(article, file_properties)
                st.success(f"Article generated and saved.")
            end_time = time.time()
            duration = int(end_time - start_time)
            st.success(f"Article(s) generated in {duration} seconds.")

output_files = get_output_files()
st.markdown("## Generated Article Editor")
if output_files:
    articles_file = "comm_con_gen/articles.json"
    with open(articles_file, "r") as f:
        articles = json.load(f)
    
    # Sort output_files by the 'generated_at' datetime in descending order
    sorted_output_files = sorted(output_files, key=lambda x: datetime.strptime(articles[x]['generated_at'], "%Y-%m-%d %H:%M:%S"), reverse=True)
    
    pretty_output_files = [format_filename(file) for file in sorted_output_files]
    selected_file_index = st.selectbox("Select a generated article", pretty_output_files, index=0)
    selected_file = sorted_output_files[pretty_output_files.index(selected_file_index)]
else:
    selected_file = None

if selected_file:
    with open(f"comm_con_gen/outputs/{selected_file}", "r", encoding="utf-8") as f:
        article_text = f.read()

    articles_file = "comm_con_gen/articles.json"
    with open(articles_file, "r") as f:
        articles = json.load(f)
    file_properties = articles[selected_file]

    with st.expander("Article Properties"):
        col1, col2 = st.columns(2)
        keys = list(file_properties.keys())
        mid = len(keys) // 2
        with col1:
            for key in keys[:mid]:
                st.write(f"**{key.capitalize()}:** {file_properties[key]}")
        with col2:
            for key in keys[mid:]:
                st.write(f"**{key.capitalize()}:** {file_properties[key]}")

    col1, col2 = st.columns(2)
    with col1:
        edited_article_text = st.text_area("Edit the article", value=article_text, height=600)
        acol1, acol2 = st.columns(2)
        with acol1:
            if st.button("Save Changes"):
                with open(f"comm_con_gen/outputs/{selected_file}", "w", encoding="utf-8") as f:
                    f.write(edited_article_text)
                articles[selected_file]["content"] = edited_article_text
                with open(articles_file, "w") as f:
                    json.dump(articles, f, indent=4)
                st.success("Changes saved successfully!")
        with acol2:
            if st.button("Delete Article"):
                os.remove(f"comm_con_gen/outputs/{selected_file}")
                del articles[selected_file]
                with open(articles_file, "w") as f:
                    json.dump(articles, f, indent=4)
                st.success("Article deleted successfully!")
                st.rerun()

    download_options = ["Markdown", "HTML"]
    download_format = st.selectbox("Select download format", download_options)
    html_output = markdown_to_html(edited_article_text)
    if st.download_button("Download", edited_article_text if download_format == "Markdown" else html_output,
                           file_name=f"{selected_file[:-3]}.{download_format.lower()}"):
        if download_format == "HTML":
            html_filename = f"{selected_file[:-3]}.html"
            save_html(html_output, html_filename)
        st.success(f"{download_format} file downloaded as {selected_file[:-3]}.{download_format.lower()}")

    with col2:
        components.html(html_output, height=600, scrolling=True)




with open("README.md", "r") as f:
    readme_content = f.read()
with st.expander("Click to view README"):
    st.markdown(readme_content)
