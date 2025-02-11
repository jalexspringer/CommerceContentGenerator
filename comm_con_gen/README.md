# impact.com Commerce Content Generator

This project generates branded content articles based on user-specified parameters. It supports various article types, languages, and advertiser products.

Live Demo: https://commercecontentgenerator-azd6mpn6hmkqn4fuquexkm.streamlit.app/ 

Ask Alex Springer - alex.springer@impact.com - for access to the live demo.

### Features
- Generate listicles, product reviews, gift guides, deal roundups, and how-to articles
- Customize voice, length, language, and advertiser products
- Enrich generated copy with product mentions and link placements
- Output copy for review, editing, and commenting
- Convert final copy to HTML with affiliate links
- Utilize predefined writing styles or generate a new style summary from a provided URL
    

## Requirements

- Python 3.7+
- Streamlit
- Langchain
- BeautifulSoup4

## Installation

1. Clone the repository
2. Install the required packages:
    pip install -r requirements.txt


3. Set up API keys:
   - Create a `.streamlit/secrets.toml` file with your API keys:
   
    ```toml
    ANTHROPIC_API_KEY = "your_api_key_here"
    localhost = true
    password = ""
    ```
    - Note that setting localhost to true removes the password requirement - **do not deploy publicly without setting it to false it and adding a password!**
## Usage

1. Run the Streamlit app:
    streamlit run app.py


2. Select the desired parameters:
   - Voice (BuzzFeed to CNN)
   - Length
   - Article type
   - Language
   - Advertiser products

3. Click "Generate" to create the initial copy.

4. Review and edit the generated copy, adding comments as needed.

5. Click "Finalize" to convert the copy to HTML with affiliate links.

6. The final HTML file will be saved in the `html_outputs` directory.

## Project Structure

- `app.py`: Main Streamlit application
- `utility.py`: Utility functions for article generation and processing
- `countries.py`: Country-specific language mappings
- `guides/`: Article format guides
- `test_products/`: Sample advertiser product data in JSON format. Each file represents a product category (e.g., `grills.json`) and contains a dictionary of products with their details such as name, description, price, discount, brand, color, and affiliate link.
- `outputs/`: Generated markdown articles
- `html_outputs/`: Final HTML articles with affiliate links

## Contributing

## TODO
- Formatting of images
- Integrated into impact.com product catalog format
- CTA to create an impact.com account?
- Adding more article types
- Adding more languages
- Adding more advertiser products
- Adding more styles
- Adding more LLM models
