import config
import psycopg

# Database connection parameters
DB_CONFIG = {
    "dbname": config.DB_NAME,
    "user": config.DB_USER,
    "password": config.DB_PASSWORD,
    "host": config.DB_HOST,
    "port": config.DB_PORT
}

# Question and sql dic
question_sql_dict = dict()

question_sql_dict["How many entries do you have in your database who have applied for Fall 2026?"] = \
    f"""
        SELECT COUNT(*) 
        FROM {config.TABLE_NAME} 
        WHERE term = 'Fall 2026';
    """
question_sql_dict[("What percentage of entries are from international students (not American or Other) (to two decimal "
                   "places)?")] = \
    f"""
        SELECT ROUND(COUNT(CASE WHEN us_or_international NOT IN ('American', 'Other') THEN 1 END) * 100.0 / COUNT(*), 2)
        FROM {config.TABLE_NAME};
    """

question_sql_dict["What is the average GPA, GRE, GRE V, GRE AW of applicants who provide these metrics?"] = \
    f"""
        SELECT AVG(gpa) AS avg_gpa, AVG(gre) AS avg_gre, AVG(gre_v) AS avg_gre_v, AVG(gre_aw) AS avg_gre_aw
        FROM {config.TABLE_NAME}
        WHERE gpa IS NOT NULL OR gre IS NOT NULL OR gre_v IS NOT NULL OR gre_aw IS NOT NULL;
    """

question_sql_dict["What is their average GPA of American students in Fall 2026?"] = \
    f"""
        SELECT AVG(gpa) AS avg_gpa
        FROM {config.TABLE_NAME}
        WHERE us_or_international = 'American' AND term = 'Fall 2026';
    """

question_sql_dict["What percent of entries for Fall 2026 are Acceptances (to two decimal places)?"] = \
    f"""
        SELECT ROUND(COUNT(CASE WHEN status = 'Accepted' THEN 1 END) * 100.0 / COUNT(*), 2)
        FROM {config.TABLE_NAME}
        WHERE term = 'Fall 2026';
    """

question_sql_dict["What is the average GPA of applicants who applied for Fall 2026 who are Acceptances?"] = \
    f"""
        SELECT AVG(gpa) AS avg_gpa
        FROM {config.TABLE_NAME}
        WHERE term = 'Fall 2026' AND status = 'Accepted';
    """

question_sql_dict[
    "How many entries are from applicants who applied to JHU for a masters degrees in Computer Science?"] = \
    f"""
        SELECT COUNT(*) 
        FROM {config.TABLE_NAME}
        WHERE (program LIKE '%Computer Science%' OR llm_generated_program LIKE '%Computer Science%')
            AND degree = 'Masters' AND 
                (llm_generated_university like '%Johns Hopkins%' OR llm_generated_university like '%John Hopkins%'
            OR llm_generated_university like '%JHU%');
    """

question_sql_dict[("How many entries from 2026 are acceptances from applicants who applied to Georgetown University, "
                   "MIT, Stanford University, or Carnegie Mellon University for a PhD in Computer Science?")] = \
    f"""
        SELECT COUNT(*) AS phd_cs_acceptances_count
        FROM {config.TABLE_NAME}
        WHERE term LIKE '%2026%'
          AND status = 'Accepted'
          AND (program LIKE '%Computer Science%')
          AND (degree LIKE '%PhD%')
          AND ( LIKE '%Georgetown%'
               OR program LIKE '%MIT%'
               OR program LIKE '%Massachusetts Institute of Technology%'
               OR program LIKE '%Stanford%'
               OR program LIKE '%Carnegie Mellon%'
               OR program LIKE '%CMU%');

    """

question_sql_dict[("Do you numbers for question 8 change if you use LLM Generated Fields (rather than your downloaded "
                   "fields)?")] = \
    f"""
        SELECT COUNT(*) AS phd_cs_acceptances_count
        FROM {config.TABLE_NAME}
        WHERE term LIKE '%2026%'
          AND status = 'Accepted'
          AND (llm_generated_program LIKE '%Computer Science%')
          AND (degree LIKE '%PhD%')
          AND ( LIKE '%Georgetown%'
               OR llm_generated_university LIKE '%MIT%'
               OR llm_generated_university LIKE '%Massachusetts Institute of Technology%'
               OR llm_generated_university LIKE '%Stanford%'
               OR llm_generated_university LIKE '%Carnegie Mellon%'
               OR llm_generated_university LIKE '%CMU%');

    """

question_sql_dict["Which universities have the highest acceptance rates in Fall 2026?"] = \
    f"""
        SELECT llm_generated_university, ROUND(COUNT(CASE WHEN status = 'Accepted' THEN 1 END) * 100.0 / COUNT(*), 2) AS acceptance_rate
        FROM {config.TABLE_NAME}
        WHERE term = 'Fall 2026'
        GROUP BY llm_generated_university
        ORDER BY acceptance_rate DESC
        LIMIT 5;
    """

question_sql_dict["What are the top 10 distinct programs applied for Fall 2026?"] = \
    f"""
        SELECT DISTINCT program
        FROM {config.TABLE_NAME}
        WHERE term = 'Fall 2026'
        ORDER BY program
        LIMIT 10;
    """


def main():
    with psycopg.connect(**DB_CONFIG) as conn:
        # Open a cursor to execute SQL queries
        cur = conn.cursor()

        # Execute each query and print the result
        for question, query in question_sql_dict.items():
            print(f"Question: {question}")
            cur.execute(query)
            result = cur.fetchall()
            for row in result:
                print(row)
            print("\n")

        # Close the cursor
        cur.close()


if __name__ == "__main__":
    main()
