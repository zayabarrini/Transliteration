How to Deploy

Option 1: Local Development
chmod +x deploy.sh
./deploy.sh
source venv/bin/activate
python app.py

Option 2: Docker
docker-compose up --build

Option 3: Production with Gunicorn
pip install gunicorn
gunicorn -c gunicorn_config.py wsgi:app

Features Included
Modern Web Interface: Drag & drop file upload with responsive design

File Type Detection: Automatic operation options based on file type

Multiple Operations:

EPUB: Split sentences and transliteration

SRT/ZIP: Create ebook and transliteration

Text files (TXT, MD, CSV): Create ebook and transliteration

Multiple Transliteration Types: Common, CJK, Weird CJK, Hindi, Japanese, Russian, Arabic

Progress Indicators: Loading states and result feedback

Error Handling: Comprehensive error messages and validation

The application will be available at http://localhost:5000 after deployment.
