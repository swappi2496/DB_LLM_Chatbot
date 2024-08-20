from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import logging
from dotenv import load_dotenv
import os
import psycopg2
import pymongo
import mysql.connector
import sqlite3
import decimal

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Allow CORS for all routes

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GPT_MODEL = 'gpt-4'

logging.basicConfig(level=logging.INFO)

# Global dictionary to hold connections
connections = {}

def normalize_db_type(db_type):
    return db_type.lower() if db_type else None

def reconnect_mysql():
    conn_info = {
        'host': os.getenv('MYSQL_HOST'),
        'port': os.getenv('MYSQL_PORT'),
        'user': os.getenv('MYSQL_USER'),
        'password': os.getenv('MYSQL_PASSWORD'),
        'database': os.getenv('MYSQL_DATABASE')
    }
    try:
        conn = mysql.connector.connect(**conn_info)
        connections['mysql'] = conn
        logging.info("Reconnected to MySQL.")
    except Exception as e:
        logging.error(f"Error reconnecting to MySQL: {e}")

def execute_query_and_reconnect_if_needed(db_type, query_func):
    try:
        return query_func()
    except (psycopg2.OperationalError, pymongo.errors.ServerSelectionTimeoutError, mysql.connector.Error) as e:
        logging.warning(f"Reconnection needed for {db_type}: {e}")
        if db_type == 'mysql':
            reconnect_mysql()
        return query_func()

@app.route('/connect/postgresql', methods=['POST'])
def connect_postgresql():
    data = request.json
    try:
        conn = psycopg2.connect(
            host=data['host'],
            port=data['port'],
            user=data['user'],
            password=data['password'],
            database=data['database']
        )
        connections['postgresql'] = conn
        logging.info("PostgreSQL connection established and stored.")
        return jsonify({"message": "Successfully connected to PostgreSQL"}), 200
    except Exception as e:
        logging.error(f"Error connecting to PostgreSQL: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/connect/mongodb', methods=['POST'])
def connect_mongodb():
    data = request.json
    try:
        client = pymongo.MongoClient(f"mongodb://{data['user']}:{data['password']}@{data['host']}:{data['port']}/{data['database']}")
        client.server_info()  # Trigger a server info request to test the connection
        connections['mongodb'] = client
        logging.info("MongoDB connection established and stored.")
        return jsonify({"message": "Successfully connected to MongoDB"}), 200
    except Exception as e:
        logging.error(f"Error connecting to MongoDB: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/connect/mysql', methods=['POST'])
def connect_mysql():
    data = request.json
    try:
        conn = mysql.connector.connect(
            host=data['host'],
            port=data['port'],
            user=data['user'],
            password=data['password'],
            database=data['database']
        )
        connections['mysql'] = conn
        logging.info("MySQL connection established and stored.")
        return jsonify({"message": "Successfully connected to MySQL"}), 200
    except Exception as e:
        logging.error(f"Error connecting to MySQL: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/connect/sqlite', methods=['POST'])
def connect_sqlite():
    data = request.json
    try:
        conn = sqlite3.connect(data['database'])
        connections['sqlite'] = conn
        logging.info("SQLite connection established and stored.")
        return jsonify({"message": "Successfully connected to SQLite"}), 200
    except Exception as e:
        logging.error(f"Error connecting to SQLite: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/tables', methods=['GET'])
def get_tables():
    db_type = normalize_db_type(request.args.get('db'))
    logging.info(f"Request for tables with db_type: {db_type}")
    logging.info(f"Current connections: {connections}")

    if not db_type or db_type not in connections or connections[db_type] is None:
        logging.error("No connection found for the given database type")
        return jsonify({"error": "No connection found for the given database type"}), 400

    def query_func():
        if db_type == 'mysql':
            conn = connections['mysql']
            cur = conn.cursor()
            cur.execute('SHOW TABLES')
            tables = cur.fetchall()
            table_names = [table[0] for table in tables]
            return jsonify({"tables": table_names}), 200
        elif db_type == 'postgresql':
            conn = connections['postgresql']
            cur = conn.cursor()
            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
            tables = cur.fetchall()
            table_names = [table[0] for table in tables]
            return jsonify({"tables": table_names}), 200
        elif db_type == 'sqlite':
            conn = connections['sqlite']
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cur.fetchall()
            table_names = [table[0] for table in tables]
            return jsonify({"tables": table_names}), 200
        elif db_type == 'mongodb':
            client = connections['mongodb']
            db = client.get_database()
            collections = db.list_collection_names()
            return jsonify({"tables": collections}), 200

    return execute_query_and_reconnect_if_needed(db_type, query_func)

@app.route('/api/dbinfo', methods=['GET'])
def dbinfo():
    db_type = normalize_db_type(request.args.get('db'))
    logging.info(f"Request for DB info with db_type: {db_type}")
    logging.info(f"Current connections: {connections}")

    if not db_type or db_type not in connections or connections[db_type] is None:
        logging.error("No connection found for the given database type")
        return jsonify({"error": "No connection found for the given database type"}), 400

    def query_func():
        if db_type == 'postgresql':
            conn = connections['postgresql']
            cur = conn.cursor()
            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
            tables = cur.fetchall()
            return jsonify({"info": {"tables": [table[0] for table in tables]}}), 200
        elif db_type == 'mysql':
            conn = connections['mysql']
            cur = conn.cursor()
            cur.execute("SHOW TABLES")
            tables = cur.fetchall()
            return jsonify({"info": {"tables": [table[0] for table in tables]}}), 200
        elif db_type == 'sqlite':
            conn = connections['sqlite']
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cur.fetchall()
            return jsonify({"info": {"tables": [table[0] for table in tables]}}), 200
        elif db_type == 'mongodb':
            client = connections['mongodb']
            db = client.get_database()
            collections = db.list_collection_names()
            return jsonify({"info": {"tables": collections}}), 200

    return execute_query_and_reconnect_if_needed(db_type, query_func)

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message')
    db_type = normalize_db_type(data.get('db_type'))

    if not message or not db_type:
        return jsonify({'error': 'No message or database type provided'}), 400

    if db_type not in connections or connections[db_type] is None:
        return jsonify({'error': 'No connection found for the given database type'}), 400
    
    few_shot_examples = [
    {
        "role": "system",
        "content": "You are a helpful assistant that generates SQL queries based on user input."
    },
    {
        "role": "user",
        "content": "Show all students who are 15 years old."
    },
    {
        "role": "assistant",
        "content": "SELECT name FROM students WHERE age = 15;"
    },
    {
        "role": "user",
        "content": "Show the names of students enrolled in English."
    },
    {
        "role": "assistant",
        "content": "SELECT students.name FROM students JOIN enrollments ON students.student_id = enrollments.student_id JOIN courses ON enrollments.course_id = courses.course_id WHERE courses.course_name = 'English Literature';"
    },
    {
        "role": "user",
        "content": "List the names and grades of students who are in grade 12."
    },
    {
        "role": "assistant",
        "content": "SELECT name, grade FROM students WHERE grade = 12;"
    },
    {
        "role": "user",
        "content": "Count the number of students in each grade."
    },
    {
        "role": "assistant",
        "content": "SELECT grade, COUNT(*) FROM students GROUP BY grade;"
    },
    {
        "role": "user",
        "content": "List students who scored above 90 in Science."
    },
    {
        "role": "assistant",
        "content": "SELECT students.name FROM students JOIN exam_results ON students.student_id = exam_results.student_id WHERE exam_results.subject = 'Biology' AND exam_results.score > 90;"
    },
    {
        "role": "user",
        "content": "Show the names of students who took exams after 2023-01-01."
    },
    {
        "role": "assistant",
        "content": "SELECT students.name FROM students JOIN exam_results ON students.student_id = exam_results.student_id WHERE exam_results.exam_date > '2023-01-01';"
    },
    {
        "role": "user",
        "content": "List students who are in grade 11 and scored below 50 in Mathematics."
    },
    {
        "role": "assistant",
        "content": "SELECT students.name FROM students JOIN exam_results ON students.student_id = exam_results.student_id WHERE students.grade = 11 AND exam_results.subject = 'Algebra I' AND exam_results.score < 50;"
    },
    {
        "role": "user",
        "content": "Show names of students who are in grade 10 and have taken both Science and English."
    },
    {
        "role": "assistant",
        "content": "SELECT students.name FROM students JOIN enrollments e1 ON students.student_id = e1.student_id JOIN courses c1 ON e1.course_id = c1.course_id JOIN enrollments e2 ON students.student_id = e2.student_id JOIN courses c2 ON e2.course_id = c2.course_id WHERE students.grade = 10 AND c1.course_name = 'Biology' AND c2.course_name = 'English Literature';"
    },
    {
        "role": "user",
        "content": "List the names of students who have never scored below 60 in any exam."
    },
    {
        "role": "assistant",
        "content": "SELECT name FROM students WHERE student_id NOT IN (SELECT student_id FROM exam_results WHERE score < 60);"
    },
    {
        "role": "user",
        "content": "Show the average score of each student in Mathematics."
    },
    {
        "role": "assistant",
        "content": "SELECT students.name, AVG(exam_results.score) AS average_score FROM students JOIN exam_results ON students.student_id = exam_results.student_id WHERE exam_results.subject = 'Algebra I' GROUP BY students.name;"
    },
    {
        "role": "user",
        "content": "Create a new table named 'teachers' with columns 'teacher_id', 'name', and 'subject'."
    },
    {
        "role": "assistant",
        "content": "CREATE TABLE teachers (teacher_id INT PRIMARY KEY, name VARCHAR(100), subject VARCHAR(100));"
    },
    {
        "role": "user",
        "content": "Add a new column 'email' to the 'students' table."
    },
    {
        "role": "assistant",
        "content": "ALTER TABLE students ADD COLUMN email VARCHAR(100);"
    },
    {
        "role": "user",
        "content": "Delete all records of students who scored below 40 in any exam."
    },
    {
        "role": "assistant",
        "content": "DELETE FROM students WHERE student_id IN (SELECT student_id FROM exam_results WHERE score < 40);"
    },
    {
        "role": "user",
        "content": "List the names of teachers who teach more than one subject."
    },
    {
        "role": "assistant",
        "content": "SELECT teachers.name FROM teachers JOIN courses ON teachers.teacher_id = courses.teacher_id GROUP BY teachers.name HAVING COUNT(DISTINCT courses.course_name) > 1;"
    },
    {
        "role": "user",
        "content": "Retrieve the names of all students and their corresponding courses."
    },
    {
        "role": "assistant",
        "content": "SELECT students.name AS student_name, courses.course_name FROM students JOIN enrollments ON students.student_id = enrollments.student_id JOIN courses ON enrollments.course_id = courses.course_id;"
    },
    {
        "role": "user",
        "content": "Show the names of students and the names of their teachers."
    },
    {
        "role": "assistant",
        "content": "SELECT students.name AS student_name, teachers.name AS teacher_name FROM students JOIN enrollments ON students.student_id = enrollments.student_id JOIN courses ON enrollments.course_id = courses.course_id JOIN teachers ON courses.teacher_id = teachers.teacher_id;"
    },
    {
        "role": "user",
        "content": "Update the grade level of students who scored above 95 in all exams to the next grade."
    },
    {
        "role": "assistant",
        "content": "UPDATE students SET grade = grade + 1 WHERE student_id IN (SELECT student_id FROM exam_results GROUP BY student_id HAVING MIN(score) > 95);"
    },
    {
        "role": "user",
        "content": "Show the names of students along with their total exam scores."
    },
    {
        "role": "assistant",
        "content": "SELECT students.name, SUM(exam_results.score) AS total_score FROM students JOIN exam_results ON students.student_id = exam_results.student_id GROUP BY students.name;"
    },
    {
        "role": "user",
        "content": "Find the average score for each subject."
    },
    {
        "role": "assistant",
        "content": "SELECT exam_results.subject, AVG(exam_results.score) AS average_score FROM exam_results GROUP BY exam_results.subject;"
    },
    {
        "role": "user",
        "content": "Find the average score for each student in the exam results."
    },
    {
        "role": "assistant",
        "content": "SELECT students.name AS student_name, AVG(exam_results.score) AS average_score FROM students JOIN exam_results ON students.student_id = exam_results.student_id GROUP BY students.name;"
    },
    {
        "role": "user",
        "content": "List the names and departments of all teachers who teach courses that have enrollments."
    },
    {
        "role": "assistant",
        "content": "SELECT DISTINCT teachers.name AS teacher_name, teachers.department FROM teachers JOIN courses ON teachers.teacher_id = courses.teacher_id JOIN enrollments ON courses.course_id = enrollments.course_id;"
    },
    {
        "role": "user",
        "content": "Get the names of all students who have taken an exam in 'Algebra I'."
    },
    {
        "role": "assistant",
        "content": "SELECT students.name FROM students JOIN exam_results ON students.student_id = exam_results.student_id JOIN courses ON exam_results.subject = courses.course_name WHERE courses.course_name = 'Algebra I';"
    },
    {
        "role": "user",
        "content": "List all courses along with the names of the teachers who teach them."
    },
    {
        "role": "assistant",
        "content": "SELECT courses.course_name, teachers.name AS teacher_name FROM courses JOIN teachers ON courses.teacher_id = teachers.teacher_id;"
    },
    {
        "role": "user",
        "content": "Find the highest score achieved in each subject."
    },
    {
        "role": "assistant",
        "content": "SELECT subject, MAX(score) AS highest_score FROM exam_results GROUP BY subject;"
    },
    {
        "role": "user",
        "content": "Retrieve the contact details (email and phone) of teachers who teach 'Science' department courses."
    },
    {
        "role": "assistant",
        "content": "SELECT teachers.name, teachers.email, teachers.phone FROM teachers WHERE teachers.department = 'Science';"
    },
    {
        "role": "user",
        "content": "Get the names of students and their grades who scored above 90 in any exam."
    },
    {
        "role": "assistant",
        "content": "SELECT students.name, students.grade FROM students JOIN exam_results ON students.student_id = exam_results.student_id WHERE exam_results.score > 90;"
    },
    {
        "role": "user",
        "content": "List all students along with their family IDs."
    },
    {
        "role": "assistant",
        "content": "SELECT name, family_id FROM students;"
    },
    {
        "role": "user",
        "content": "Retrieve the names and scores of students who scored the highest in each subject."
    },
    {
        "role": "assistant",
        "content": "WITH max_scores AS (SELECT subject, MAX(score) AS highest_score FROM exam_results GROUP BY subject) SELECT students.name, exam_results.subject, exam_results.score FROM exam_results JOIN students ON exam_results.student_id = students.student_id JOIN max_scores ON exam_results.subject = max_scores.subject AND exam_results.score = max_scores.highest_score;"
    },
     {
        "role": "user",
        "content": "Design a table for student feedback with feedback_id, student_id, course_id, feedback_text, and feedback_date."
    },
    {
        "role": "assistant",
        "content": "CREATE TABLE student_feedback ( feedback_id INT PRIMARY KEY,  student_id INT NOT NULL,course_id INT NOT NULL,  feedback_text TEXT NOT NULL, feedback_date DATE NOT NULL, FOREIGN KEY (student_id) REFERENCES students(student_id), FOREIGN KEY (course_id) REFERENCES courses(course_id) );"
    },
    {
        "role": "user",
        "content": "Create a table to keep track of teacher schedules with schedule_id, teacher_id, course_id, day_of_week, and time_slot."
    },
    {
        "role": "assistant",
        "content": "CREATE TABLE teacher_schedules (schedule_id INT PRIMARY KEY,teacher_id INT NOT NULL,course_id INT NOT NULL,day_of_week VARCHAR(20) NOT NULL,time_slot VARCHAR(20) NOT NULL,FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id),FOREIGN KEY (course_id) REFERENCES courses(course_id));"
    },
    {
        "role": "user",
        "content": "Create a table to log student library usage with usage_id, student_id, book_id, borrow_date, and return_date."
    },
    {
        "role": "assistant",
        "content": "CREATE TABLE library_usage (usage_id INT PRIMARY KEY,student_id INT NOT NULL,book_id INT NOT NULL,borrow_date DATE NOT NULL,return_date DATE,FOREIGN KEY (student_id) REFERENCES students(student_id),FOREIGN KEY (book_id) REFERENCES library_books(book_id));"
    },
    {
        "role": "user",
        "content": "Design a table for storing information about school facilities with facility_id, facility_name, location, and capacity."
    },
    {
        "role": "assistant",
        "content": "CREATE TABLE school_facilities (facility_id INT PRIMARY KEY,facility_name VARCHAR(100) NOT NULL, location VARCHAR(100) NOT NULL, capacity INT NOT NULL);"
    },
    {
        "role": "user",
        "content": "Design a table for storing sports team information with team_id, team_name, coach_name, and sport."
    },
    {
        "role": "assistant",
        "content": "CREATE TABLE sports_teams (team_id INT PRIMARY KEY,team_name VARCHAR(100) NOT NULL,coach_name VARCHAR(100) NOT NULL,sport VARCHAR(50) NOT NULL);"
    }
]

    user_message = {"role": "user", "content": message}
    messages = few_shot_examples + [user_message]

    try:
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {OPENAI_API_KEY}'
            },
            json={
                'model': GPT_MODEL,
                'messages': messages,
                'max_tokens': 200,
                'temperature': 0.7,
                'top_p': 0.9,
                'frequency_penalty': 0,
                'presence_penalty': 0.6
            }
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f'Error communicating with OpenAI: {e}')
        return jsonify({'error': 'Failed to communicate with OpenAI'}), 500

    response_data = response.json()
    bot_message = response_data['choices'][0]['message']['content'].strip()

    # Extract SQL query from the response
    logging.info(f"Received response: {bot_message}")

    # We assume the first code block in the response is the SQL query
    try:
        query_start = bot_message.index("```") + 3
        query_end = bot_message.index("```", query_start)
        query = bot_message[query_start:query_end].strip()
    except ValueError:
        # If no code block is found, we assume the whole response is the query
        query = bot_message.strip()
    
    if query.lower().startswith("sql"):
        query = query[3:].strip()

    logging.info(f"Generated query: {query}")
    return jsonify({'query': query}), 200

def convert_decimal_to_float(data):
    """Recursively convert Decimal objects to floats."""
    if isinstance(data, decimal.Decimal):
        return float(data)
    elif isinstance(data, dict):
        return {key: convert_decimal_to_float(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_decimal_to_float(item) for item in data]
    return data

@app.route('/api/execute_query', methods=['POST'])
def execute_query():
    data = request.json
    query = data.get('query')
    db_type = normalize_db_type(data.get('db_type'))

    if not query or not db_type:
        return jsonify({'error': 'No query or database type provided'}), 400

    if db_type not in connections or connections[db_type] is None:
        return jsonify({'error': 'No connection found for the given database type'}), 400

    logging.info(f"Executing query on {db_type}: {query}")

    def query_func():
        try:
            result = []
            columns = []

            if db_type == 'postgresql':
                conn = connections['postgresql']
                cur = conn.cursor()
                cur.execute(query)
                result = cur.fetchall()
                columns = [desc[0] for desc in cur.description]
                cur.close()
            elif db_type == 'mysql':
                conn = connections['mysql']
                cur = conn.cursor()
                cur.execute(query)
                result = cur.fetchall()
                columns = [desc[0] for desc in cur.description]
                cur.close()
            elif db_type == 'sqlite':
                conn = connections['sqlite']
                cur = conn.cursor()
                cur.execute(query)
                result = cur.fetchall()
                columns = [desc[0] for desc in cur.description]
                cur.close()
            elif db_type == 'mongodb':
                client = connections['mongodb']
                db = client.get_database()
                collection_name = query.split('.')[1]
                query_body = query.split('find(')[1][:-1]
                collection = db[collection_name]
                result = list(collection.find(eval(query_body)))
                if result:
                    columns = result[0].keys()
                    result = [list(r.values()) for r in result]
                else:
                    columns = []
            else:
                return jsonify({'error': 'Unsupported database type'}), 400

            result = [convert_decimal_to_float(row) for row in result]
            return jsonify({'query': query, 'columns': columns, 'result': result}), 200
        
        except Exception as e:
            logging.error(f"Error executing query: {str(e)}")
            return jsonify({'error': str(e)}), 500

    return execute_query_and_reconnect_if_needed(db_type, query_func)


if __name__ == '__main__':
    app.run(port=5000, debug=True)

