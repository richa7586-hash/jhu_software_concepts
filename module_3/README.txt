# JHED ID A68B60

# jhu_software_concepts - Module 3 - Database Queries Assignment Experiment - Due by Feb 8, 2026


# How It Works
Load collected data into a PostgreSQL database using psycopg
Carry out data analysis using SQL queries to answer questions about submission entries to grad café.
Created a flask page to display the query results
Also added two buttons on the page to allow users to pull latest data, clean it and then insert in DB.

# Requirements
- Python 3.10+
- pip

# Setup
1) Change into the app folder:
   cd module3
2) Create and activate a virtual environment (optional but recommended):
   python -m venv venv
   source venv/bin/activate
3) Install dependencies:
   pip install -r requirements.txt

4) to run the web app:
    python run.py

    Navigate to http://127.0.0.1:5000/

5) To load data to the database:
    python load_data.py

6) To query data from the database:
    python query_data.py


