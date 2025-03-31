import string
from flask import Flask, request, render_template, jsonify, send_file
import requests
import re
import nltk
from nltk.tokenize import word_tokenize
from bs4 import BeautifulSoup
import os

# Download NLTK data files (if not already installed)
nltk.download('punkt')

# Initialize Flask app
app = Flask(__name__)

# Ensure a directory for saving text files exists
if not os.path.exists("static/cleaned_texts"):
    os.makedirs("static/cleaned_texts")

# Function to clean text by removing unwanted content using regular expressions
def clean_text(text):
    text = re.sub(r'\[.*?\]', '', text)  # Remove citations in square brackets
    text = re.sub(r'\{.*?\}', '', text)  # Remove citations in curly brackets
    text = re.sub(r'\s+', ' ', text).strip()  # Remove extra spaces or newlines
    return text

# Function to scrape the text content from the body of a URL
def scrape_text_from_url(url):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        body_content = soup.find('body')
        if body_content:
            page_text = body_content.get_text(separator=' ', strip=True)
            return clean_text(page_text)
        else:
            return "No <body> content found."
    else:
        return f"Failed to retrieve the page. Status code: {response.status_code}"

# Function to count tokens in a text excluding punctuation
def count_tokens_from_text(text):
    try:
        tokens = word_tokenize(text)
        # Filter out tokens that are purely punctuation
        valid_tokens = [token for token in tokens if token not in string.punctuation]
        return len(valid_tokens)
    except Exception as e:
        print(f"An error occurred: {e}")
        return 0

# Route to display the input form
@app.route('/')
def index():
    return render_template('index.html')

# Route to process input and calculate the token price

@app.route('/process', methods=['POST'])
def process_input():
    input_type = request.form['input_type']
    price_per_token = float(request.form['price_per_token'])
    results = []

    if input_type == 'url':
        urls = request.form['urls'].split('\n')
        manual_text = request.form.get('manual_text', '').strip()

        # Process URLs
        for url in urls:
            url = url.strip()
            if url:
                cleaned_text = scrape_text_from_url(url)
                if "Failed to retrieve the page" not in cleaned_text:
                    token_count = count_tokens_from_text(cleaned_text)
                    total_price = token_count * price_per_token
                    file_name = f"static/cleaned_texts/{url.replace('https://', '').replace('http://', '').replace('/', '_')}.txt"
                    with open(file_name, "w", encoding="utf-8") as file:
                        file.write(cleaned_text)
                    results.append({
                        'url': url,
                        'cleaned_text': cleaned_text[:300] + '...',
                        'token_count': token_count,
                        'total_price': total_price,
                        'file_path': file_name
                    })
                else:
                    results.append({'url': url, 'error': cleaned_text})

        # Process manual text (if provided)
        if manual_text:
            cleaned_text = clean_text(manual_text)
            token_count = count_tokens_from_text(cleaned_text)
            total_price = token_count * price_per_token
            file_name = "static/cleaned_texts/manual_text_from_url.txt"
            with open(file_name, "w", encoding="utf-8") as file:
                file.write(cleaned_text)
            results.append({
                'cleaned_text': cleaned_text[:300] + '...',
                'token_count': token_count,
                'total_price': total_price,
                'file_path': file_name
            })

    elif input_type == 'text':
        text_input = request.form['text_input']
        cleaned_text = clean_text(text_input)
        token_count = count_tokens_from_text(cleaned_text)
        total_price = token_count * price_per_token
        file_name = "static/cleaned_texts/manual_text_input.txt"
        with open(file_name, "w", encoding="utf-8") as file:
            file.write(cleaned_text)
        results.append({
            'cleaned_text': cleaned_text[:300] + '...',
            'token_count': token_count,
            'total_price': total_price,
            'file_path': file_name
        })

    return jsonify({'results': results})

# Route to download a specific cleaned text file
@app.route('/download/<path:filename>')
def download_file(filename):
    return send_file(filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
