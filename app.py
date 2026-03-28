from flask import Flask, render_template, request, jsonify
import spacy
import requests
import os
import docx
import fitz

app = Flask(__name__)

# Load Spacy model
nlp = spacy.load("en_core_web_md")

# Function to perform Google Custom Search and compare with online sources
def compare_with_google(input_text):
    # Google Custom Search API key and CX (Custom Search Engine ID)
    api_key = ''
    cx = 'd36fbb2b3c7414d4d'
    # Construct API request URL
    url = f'https://www.googleapis.com/customsearch/v1?q={input_text}&cx={cx}&key={api_key}'
    # Send GET request to Google Custom Search API
    try:
        response = requests.get(url)
        if response.status_code == 200:
            # Parse JSON response
            data = response.json()
            # Extract search results
            items = data.get('items', [])
            total_similarity = 0
            count = 0
            url_similarity_map = {}
            for item in items:
                title = item.get('title', '')
                link = item.get('link', '')
                snippet = item.get('snippet', '')
                # Combine title and snippet for comparison
                result_text = title + ' ' + snippet
                similarity = nlp(input_text).similarity(nlp(result_text))
                total_similarity += similarity
                count += 1
                url_similarity_map[link] = similarity
            overall_similarity = total_similarity / count if count > 0 else 0
            return overall_similarity, url_similarity_map
    except Exception as e:
        print("Error:", e)
    return 0, {}


# Function to extract text from TXT file
def extract_text_from_txt(file):
    try:
        with open(file, 'r', encoding='utf-8') as f:
            text = f.read()
        return text
    except Exception as e:
        print("Error extracting text from TXT:", e)
        return None

# Function to extract text from PDF file using PyMuPDF
def extract_text_from_pdf(file):
    try:
        text = ''
        doc = fitz.open(file)
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        print("Error extracting text from PDF:", e)
        return None


# Function to extract text from DOCX file using python-docx
def extract_text_from_docx(file):
    try:
        doc = docx.Document(file)
        text = ''
        for para in doc.paragraphs:
            text += para.text + '\n'
        return text
    except Exception as e:
        print("Error extracting text from DOCX:", e)
        return None

app.config['UPLOAD_FOLDER'] = 'uploads'

# Route for homepage
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/results.html')
def results():
    return render_template('results.html')

# Route for plagiarism detection
@app.route('/detect_plagiarism', methods=['POST'])
def detect_plagiarism():
    text_input = request.form['text_input']
    file = request.files['file_input']
    results = {}
    if text_input:
        overall_text_input_similarity, text_input_google_similarity_scores = compare_with_google(text_input)
        results['text_input_similarity'] = overall_text_input_similarity
        results['text_input_google_similarity_scores'] = text_input_google_similarity_scores

    if file:
        filename = file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        file_extension = os.path.splitext(filename)[1].lower()
        if file_extension == '.pdf':
            file_text = extract_text_from_pdf(file_path)
        elif file_extension == '.txt':
            file_text = extract_text_from_txt(file_path)
        elif file_extension == '.docx':
            file_text = extract_text_from_docx(file_path)
        else:
            file_text = None
            print("Unsupported file format:", file_extension)
        if file_text is not None:
            overall_file_similarity, file_google_similarity_scores = compare_with_google(file_text)
            results['file_similarity'] = overall_file_similarity
            results['file_google_similarity_scores'] = file_google_similarity_scores
        else:
            print("Error: Failed to extract text from file")
    return jsonify(results)


if __name__ == '__main__':
    app.run(debug=True)