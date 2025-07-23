Agent001

A Django-based SOC (Security Operations Center) application for processing alerts using a local LLM (Mistral Open Orca via Ollama).

Setup



1. Clone the repository:

git clone https://github.com/Frankenbytes/Agent001.git
cd Agent001



2. Create and activate a virtual environment:

python3 -m venv venv
source venv/bin/activate



3. Install dependencies:

pip install -r requirements.txt



4. Run migrations:

python3 manage.py migrate



5. Start the Django server:

python3 manage.py runserver

Requirements

Python 3.12.8
Django 5.2.4
Ollama with Mistral Open Orca