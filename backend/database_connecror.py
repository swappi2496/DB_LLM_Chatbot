from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import logging
from dotenv import load_dotenv
import os
import psycopg2
import pymongo

load_dotenv()

app = Flask(__name__)
CORS(app)

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GPT_MODEL = 'gpt-4'

# PostgreSQL connection details from environment variables
PG_HOST = os.getenv('PG_HOST')
PG_PORT = os.getenv('PG_PORT')
PG_USER = os.getenv('PG_USER')
PG_PASSWORD = os.getenv('PG_PASSWORD')
PG_DB = os.getenv('PG_DB')

# MongoDB connection details from environment variables
MONGO_URI = os.getenv('MONGO_URI')

logging.basicConfig(level=logging.INFO)

@app.route('/connect/postgresql', methods=['POST'])
def connect_postgresql():
    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            user=PG_USER,
            password=PG_PASSWORD,
            database=PG_DB
        )
        conn.close()
        return jsonify({"message": "Successfully connected to PostgreSQL"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/connect/mongodb', methods=['POST'])
def connect_mongodb():
    try:
        client = pymongo.MongoClient(MONGO_URI)
        client.server_info()  # Trigger a server info request to test the connection
        client.close()
        return jsonify({"message": "Successfully connected to MongoDB"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message')

    if not message:
        return jsonify({'error': 'No message provided'}), 400

    try:
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {OPENAI_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'model': GPT_MODEL,
                'messages': [{'role': 'user', 'content': message}],
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

    # Assuming some logic to extract visualization data from bot_message
    visualization_data = None
    if 'some condition to detect visualization' in bot_message:
        visualization_data = extract_visualization_data(bot_message)

    return jsonify({'message': bot_message, 'visualizationData': visualization_data})

def extract_visualization_data(message):
    # Implement your logic to extract visualization data from the message
    return {'example': 'data'}

if __name__ == '__main__':
    app.run(port=5000, debug=True)
