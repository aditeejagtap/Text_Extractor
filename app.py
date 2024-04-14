from flask import Flask, request, send_from_directory, render_template, redirect, url_for
import pdfplumber
import docx
import pandas as pd
import os
import tempfile
import re

app = Flask(__name__, template_folder='templates')
app.config['Sample2'] = tempfile.mkdtemp()  # Temporary folder for uploads

# Helper functions to process documents
def extract_text_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = ''.join(page.extract_text() or '' for page in pdf.pages)
    return text

def extract_text_from_docx(docx_path):
    doc = docx.Document(docx_path)
    text = '\n'.join(paragraph.text for paragraph in doc.paragraphs)
    return text

def extract_email_and_phone(text):
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    phone_pattern = r'\b(\d{5}[-\s]?\d{5}|\d{3}-\d{3}-\d{4})\b'
    emails = re.findall(email_pattern, text)
    phones = re.findall(phone_pattern, text)
    return emails[0] if emails else None, phones[0] if phones else None

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        files = request.files.getlist('file')
        data = []
        for file in files:
            filename = file.filename
            ext = os.path.splitext(filename)[1].lower()
            file_path = os.path.join(app.config['Sample2'], filename)
            file.save(file_path)
            text = None
            if ext == '.pdf':
                text = extract_text_from_pdf(file_path)
            elif ext == '.docx':
                text = extract_text_from_docx(file_path)
            if text:
                email, phone = extract_email_and_phone(text)
                data.append({'Filename': filename, 'Email': email, 'Phone': phone, 'Text': text})
            os.remove(file_path)  # Clean up file after processing

        # Convert data to DataFrame and save as Excel
        df = pd.DataFrame(data)
        excel_path = os.path.join(app.config['Sample2'], 'Extracted_CV_Data.xlsx')
        df.to_excel(excel_path, index=False)
        return redirect(url_for('download_file', filename='Extracted_CV_Data.xlsx'))
    return render_template('upload.html')

@app.route('/downloads/<filename>')
def download_file(filename):
    return send_from_directory(app.config['Sample2'], filename, as_attachment=True)

if __name__ == "__main__":
    app.run()
