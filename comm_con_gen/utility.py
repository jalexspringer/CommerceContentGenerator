import os
import json
import markdown
import re
from datetime import datetime, date
from bs4 import BeautifulSoup
import requests

import streamlit as st
from anthropic import Anthropic

llm_models = {
        "Claude 3.5 Sonnet": "claude-3-5-sonnet-20241022",
        "Claude 3.5 Haiku": "claude-3-5-haiku-20241022",
        "Claude 3 Opus": "claude-3-opus-20240229",
        "Claude 3 Sonnet": "claude-3-sonnet-20240229",
        "Claude 3 Haiku": "claude-3-haiku-20240307"
    }

def load_webpage(url: str) -> str:
    """
    Load content from a webpage.
    
    Args:
        url: URL to load content from
        
    Returns:
        str: The webpage content
    """
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()
    return soup.get_text()

def get_voice_examples(url):
    # Extract the top-level domain from the URL
    domain = re.search(r"https?://(?:www\.)?([^/]+)", url).group(1)
    voice_file = f"comm_con_gen/voices/{domain.split('.')[0]}.txt"

    if os.path.exists(voice_file):
        with open(voice_file, "r") as f:
            return f.read()
    else:
        # Initialize Anthropic client
        client = Anthropic(api_key=st.session_state.anthropic_api_key)

        # Load the webpage content
        page_content = load_webpage(url)

        # Load the voice prompt template
        with open("comm_con_gen/prompts/get_voice_prompt.txt", "r") as f:
            voice_prompt_template = f.read()

        # Create message with system and user prompts
        message = client.messages.create(
            model=llm_models["Claude 3 Haiku"],
            temperature=0.2,
            max_tokens=1000,
            system=voice_prompt_template,
            messages=[{
                "role": "user",
                "content": f"Summarise the voice of the following: {page_content}"
            }]
        )

        voice_summary = message.content[0].text

        # Save the voice summary to a file
        with open(voice_file, "w") as f:
            f.write(voice_summary)

        return voice_summary

def load_guide(article_type: str) -> str:
    """
    Load the guide content based on the article type.

    Args:
        article_type (str): The type of article.

    Returns:
        str: The content of the guide.
    """
    guide_files = {
        "Gift Guide": "comm_con_gen/guides/giftguide.txt",
        "Product Review": "comm_con_gen/guides/product_review.txt",
        "How To": "comm_con_gen/guides/howto.txt",
        "Listicle": "comm_con_gen/guides/listicle.txt",
        "Deal Radar": "comm_con_gen/guides/dealradar.txt"
    }
    with open(guide_files[article_type], 'r') as f:
        return f.read()


def load_products(product: str) -> dict:
    """
    Load the product details from a JSON file.

    Args:
        product (str): The name of the product.

    Returns:
        dict: The product details.
    """
    with open(f"comm_con_gen/test_products/{product}.json") as f:
        products = json.load(f)
    return products


def create_article(article_type: str, audience_country: str, publishing_date: str, article_word_length: int,
                   product: str, language: str, style: str, partner_id: int, llm_model: str, event_name: str) -> tuple[str, str]:
    # Initialize Anthropic client
    client = Anthropic(api_key=st.session_state.anthropic_api_key)
    
    guide_overview = load_guide(article_type)
    products = load_products(product)

    system_prompt = f"""You are a creative writer for a popular editorial website, crafting engaging articles in the
        style of {style}. Write in a friendly, upbeat tone while focusing on informative content. 
        Seamlessly integrate product mentions and affiliate links into the article. Ensure that headers and content reference the correct number of products (for example if there are 3 products) 
        the title would be something like "3 Smashing Trainers to Gift This Summer 2024"
        Use local language, currency, and slang to connect with the target audience. For example, if the target audience is in the UK, use "trainers" instead of sneakers."""

    if event_name != "":
        event_prompting = f"Focus on a theme relevant to {event_name}."
    else:
        event_prompting = f"Focus on a theme relevant to {publishing_date}, such as a holiday or annual event"

    prompt_input = f"""
        Write a {article_word_length}-word {article_type} article in {language} for {audience_country}, targeting a broad 
        demographic. {event_prompting}. The article will be published {publishing_date}.

        Article Format:
        {guide_overview}
        The max length of the article should be {article_word_length} words.
        Output the article in markdown format with no commentary - just output the article. 

        Products to feature:
        """

    for k, v in products.items():
        prompt_input += f"{k}: {v}\n"

    # Create message with system and user prompts
    message = client.messages.create(
        model=llm_model,
        temperature=0.2,
        max_tokens=2048,
        system=system_prompt,
        messages=[{
            "role": "user",
            "content": prompt_input
        }]
    )

    article = message.content[0].text

    # Append partner ID to links
    article = append_partner_id(article, partner_id)

    event_name_formatted = event_name.replace(' ', '-').lower() if event_name else "no-event"

    file_properties = {
        "product": product,
        "article_type": article_type,
        "audience_country": audience_country,
        "language": language,
        "publishing_date": publishing_date,
        "style": style,
        "llm_model": llm_model,
        "event_name": event_name_formatted
    }
    
    return article, file_properties


def append_partner_id(article: str, partner_id: int) -> str:
    """
    Append the partner ID to the affiliate links in the article.

    Args:
        article (str): The article content.
        partner_id (int): The partner ID to append.

    Returns:
        str: The article with partner ID appended to the links.
    """
    # Find all markdown links in the article
    link_pattern = r'\[.*?\]\((.*?)\)'
    links = re.findall(link_pattern, article)

    # Append partner ID to each link
    for link in links:
        if '?' in link:
            new_link = f"{link}&subid={partner_id}"
        else:
            new_link = f"{link}?subid={partner_id}"
        article = article.replace(link, new_link)

    return article

def save_article(article: str, file_properties: dict) -> None:
    """
    Save the article to a file and update the articles.json file.

    Args:
        article (str): The article content.
        file_properties (dict): The file properties dictionary.
    """
    os.makedirs("comm_con_gen/outputs", exist_ok=True)
    filename = f"{file_properties['product']}_{file_properties['article_type'].lower()}_{file_properties['audience_country'].lower()}_{file_properties['language'].lower()}_{file_properties['publishing_date']}_{file_properties['style']}_{file_properties['llm_model']}_{file_properties.get('event_name', 'no-event').replace(' ', '-').lower()}.md"
    with open(f"comm_con_gen/outputs/{filename}", "w") as f:
        f.write(article)
    
    # Load existing articles from articles.json
    articles_file = "comm_con_gen/articles.json"
    if os.path.exists(articles_file):
        with open(articles_file, "r") as f:
            articles = json.load(f)
    else:
        articles = {}
    
    # Add the new article to the articles dictionary
    file_properties["generated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Add timestamp
    if isinstance(file_properties["publishing_date"], datetime):
        file_properties["publishing_date"] = file_properties["publishing_date"].strftime("%Y-%m-%d")  # Convert publishing_date to string if it's a datetime object
    
    # Ensure all date objects are converted to strings
    for key, value in file_properties.items():
        if isinstance(value, (datetime, date)):
            file_properties[key] = value.strftime("%Y-%m-%d")
    
    articles[filename] = file_properties
    
    # Save the updated articles dictionary to articles.json
    with open(articles_file, "w") as f:
        json.dump(articles, f, indent=4)

def get_output_files() -> list[str]:
    """
    Get a list of output files in the "outputs" directory.

    Returns:
        list[str]: A list of output filenames.
    """
    articles_file = "comm_con_gen/articles.json"
    if os.path.exists(articles_file):
        try:
            with open(articles_file, "r") as f:
                articles = json.load(f)
            return list(articles.keys())
        except json.JSONDecodeError as e:
            print(f"Invalid JSON in {articles_file}: {str(e)}")
    return []


def format_filename(filename: str) -> str:
    """
    Format the filename for display.

    Args:
        filename (str): The filename to format.

    Returns:
        str: The formatted filename.
    """
    articles_file = "comm_con_gen/articles.json"
    if os.path.exists(articles_file):
        with open(articles_file, "r") as f:
            articles = json.load(f)
        if filename in articles:
            file_properties = articles[filename]
            product = file_properties['product'].replace("-", " ").title()
            article_type = file_properties['article_type'].replace("_", " ").title()
            audience_country = file_properties['audience_country'].title()
            language = file_properties['language'].title()
            publishing_date = file_properties['publishing_date']
            style = file_properties['style'].title()
            llm_model = file_properties['llm_model'].replace("-", " ").title()
            generated_at = file_properties['generated_at']  # Add generated_at to the formatted filename
            return f"{product} {article_type} for {audience_country} Audience in {language}, {publishing_date} - {style} Style, {llm_model}, Generated at {generated_at}"
    return filename

def markdown_to_html(markdown_text: str) -> str:
    """
    Convert markdown text to HTML.

    Args:
        markdown_text (str): The markdown text to convert.

    Returns:
        str: The converted HTML.
    """
    # Convert markdown to HTML
    html = markdown.markdown(markdown_text)
    
    # Parse the HTML with BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    
    # Return the prettified HTML
    return soup.prettify()


def save_html(html_output: str, filename: str) -> None:
    """
    Save the HTML output to a file.

    Args:
        html_output (str): The HTML content to save.
        filename (str): The filename to save the HTML.
    """
    os.makedirs("comm_con_gen/html_outputs", exist_ok=True)
    with open(f"comm_con_gen/html_outputs/{filename}", "w") as f:
        f.write(html_output)



def get_publishing_calendar(country: str) -> dict:
    """
    Generate a publishing calendar with important dates and their names for the specified country.

    Args:
        country (str): The country for which to generate the publishing calendar.

    Returns:
        dict: A dictionary with dates as keys and event names as values.
    """
    # Initialize Anthropic client
    client = Anthropic(api_key=st.session_state.anthropic_api_key)

    # Load the calendar prompt template
    with open("comm_con_gen/prompts/country_events.txt", "r") as f:
        calendar_prompt_template = f.read()
    

    today = datetime.now().strftime("%Y-%m-%d")
    # Create message with system and user prompts
    message = client.messages.create(
        model=llm_models["Claude 3.5 Haiku"],
        temperature=0.2,
        max_tokens=1000,
        system=calendar_prompt_template,
        messages=[{
            "role": "user",
            "content": f"Return a comma seperated list of important dates and their names for {country}, starting from {today} and covering the following year."
        }]
    )
  
    calendar_summary = message.content[0].text
    # Convert the summary to a dictionary
    calendar_dict = {}
    for line in calendar_summary.split('\n'):
        if line.strip():
            parts = line.split(',', 1)
            if len(parts) == 2:
                date, event = parts
                calendar_dict[date.strip()] = event.strip()
            else:
                continue
    
    return calendar_dict