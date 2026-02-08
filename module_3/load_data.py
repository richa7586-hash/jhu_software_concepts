import json
import psycopg
import config

# Database connection parameters
DB_CONFIG = {
    "dbname": "gradcafe",
    "user": "richa",
    "password": "richa",
    "host": "localhost",
    "port": 5432
}


def create_table_if_not_exists(conn):
    """Create the applicant table if it doesn't exist"""
    create_table_query = """
    CREATE TABLE IF NOT EXISTS applicant (
        p_id SERIAL PRIMARY KEY,
        program TEXT,
        comments TEXT,
        date_added DATE,
        url TEXT UNIQUE,
        status TEXT,
        term TEXT,
        us_or_international TEXT,
        gpa FLOAT,
        gre FLOAT,
        gre_v FLOAT,
        gre_aw FLOAT,
        degree TEXT,
        llm_generated_program TEXT,
        llm_generated_university TEXT
    );
    """
    with conn.cursor() as cursor:
        cursor.execute(create_table_query)
    conn.commit()
    print("Table 'applicant' created or already exists.")


def load_jsonl_data(filepath):
    """Load and parse JSONL file"""
    records = []
    with open(filepath, 'r') as f:
        for line in f:
            record = json.loads(line)
            records.append((
                record.get('program'),
                record.get('comments'),
                record.get('date_added'),
                record.get('url'),
                record.get('status'),
                record.get('term'),
                record.get('us_or_international'),
                record.get('gpa'),
                record.get('gre'),
                record.get('gre_v'),
                record.get('gre_aw'),
                record.get('degree'),
                record.get('llm_generated_program'),
                record.get('llm_generated_university')
            ))
    return records


def bulk_insert_with_skip_duplicates(conn, records):
    """Bulk insert data with ON CONFLICT DO NOTHING"""
    insert_query = """
    INSERT INTO applicant (
        program, comments, date_added, url, status, term,
        us_or_international, gpa, gre, gre_v, gre_aw, degree,
        llm_generated_program, llm_generated_university
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (url) DO NOTHING
    """

    with conn.cursor() as cursor:
        cursor.executemany(insert_query, records)

    conn.commit()
    print(f"Successfully processed {len(records)} records (duplicates skipped).")


def main():
    """Main function to load data from JSONL to PostgreSQL"""
    try:
        # Connect to PostgreSQL
        print("Connecting to database...")
        with psycopg.connect(**DB_CONFIG) as conn:

            # Create table if not exists
            create_table_if_not_exists(conn)

            # Load JSONL data
            print("Loading JSONL data...")
            records = load_jsonl_data('applicant_data.jsonl')
            print(f"Loaded {len(records)} records from JSONL file.")

            # Bulk insert with duplicate handling
            print("Inserting data into database...")
            bulk_insert_with_skip_duplicates(conn, records)

            print("Data loading completed successfully!")

    except psycopg.Error as e:
        print(f"Database error: {e}")
    except FileNotFoundError:
        print("Error: applicant_data.jsonl file not found.")
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
