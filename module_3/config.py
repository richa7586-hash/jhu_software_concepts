# Configuration settings for the Flask application.
HOST = "0.0.0.0"
PORT = 8080
APPLICANT_DATA_JSON_FILE = "applicant_data.json.jsonl"
INITIAL_APPLICANT_DATA_JSON_FILE = "llm_extend_applicant_data.json"

#DB Configurations
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "gradcafe"
DB_USER = "postgres"
DB_PASSWORD = "postgres"
TABLE_NAME = "applicant"


#Grad Cafe Configurations
base_url = "https://www.thegradcafe.com/survey/"
list_url_template = "https://www.thegradcafe.com/survey/?page={}"
data_file = "applicant_data.json"