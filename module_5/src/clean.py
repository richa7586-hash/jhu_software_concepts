"""Load and clean applicant data using the LLM cleaning script."""

import json
import subprocess
import os
import config


def load_data(file_path=None):
    """Load applicant data from JSON file"""
    if file_path is None:
        file_path = config.DATA_FILE

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"Loaded {len(data):,} records from {file_path}")
        return data
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return []
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"Error loading data: {e}")
        return []


def clean_data(input_file=None, llm_script_path="../llm_hosting/app.py", output_file=None):
    """Clean applicant data using LLM by calling external Python script"""
    if input_file is None:
        input_file = config.DATA_FILE
    if output_file is None:
        output_file = config.APPLICANT_DATA_JSON_FILE

    if not os.path.exists(input_file):
        print(f"Input file not found: {input_file}")
        return False

    if not os.path.exists(llm_script_path):
        print(f"LLM script not found: {llm_script_path}")
        return False

    print(f"Cleaning data from {input_file}...")

    try:
        # Call the LLM cleaning script
        command = ["python", llm_script_path, "--file", input_file, "--out", output_file]
        result = subprocess.run(command, capture_output=True, text=True, check=True)

        if result.stdout:
            print(result.stdout)

        print("Data cleaning completed")
        return True

    except subprocess.CalledProcessError as e:
        print(f"Error running LLM script: {e}")
        if e.stderr:
            print(e.stderr)
        return False
    except (OSError, subprocess.SubprocessError) as e:
        print(f"Error: {e}")
        return False


if __name__ == '__main__':
    # Example usage
    applicant_data = load_data()
    if applicant_data:
        clean_data()
