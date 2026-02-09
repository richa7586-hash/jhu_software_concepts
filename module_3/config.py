# Configuration settings for the Flask application.
HOST = "0.0.0.0"
PORT = 8080


#DB Configurations
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "gradcafe"
DB_USER = "postgres"
DB_PASSWORD = "postgres"
TABLE_NAME = "applicant"


#Grad Cafe Configurations
BASE_URL = "https://www.thegradcafe.com/survey/"
LIST_URL_TEMPLATE = "https://www.thegradcafe.com/survey/?page={}"
DATA_FILE = "applicant_data.json"

APPLICANT_DATA_JSON_FILE = "applicant_data.json.jsonl"
INITIAL_APPLICANT_DATA_JSON_FILE = "llm_extend_applicant_data.json"