from flask import Flask, jsonify, request, send_from_directory, g
from flask_cors import CORS
import sqlite3
from datetime import datetime
from openai import OpenAI
import os
import re
import time

# Initialize OpenAI client with DeepSeek configuration
client = OpenAI(
    api_key=os.getenv('DEEPSEEK_API_KEY'),
    base_url="https://api.deepseek.com"
)

def format_response(response_text):
    """Format the DeepSeek response into clear points"""
    # Convert numbered lists to bullet points
    response_text = re.sub(r'(\d+\.)\s+', r'• ', response_text)
    
    # Split into points based on common patterns
    points = re.split(r'[\n•]+', response_text)
    
    # Clean and format each point
    formatted_points = []
    for point in points:
        point = point.strip()
        if not point:
            continue
        # Ensure proper capitalization
        point = point[0].upper() + point[1:]
        # Add bullet point if not already present
        if not point.startswith('•'):
            point = '• ' + point
        formatted_points.append(point)
    
    # Join with double newlines for clear separation
    formatted_text = '\n\n'.join(formatted_points)
    
    # Add spacing after colons for better readability
    formatted_text = re.sub(r':\s*', ':\n\n', formatted_text)
    
    return formatted_text.strip()

def generate_healthcare_response(user_message):
    """Generate a healthcare-focused response using DeepSeek"""
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a helpful healthcare assistant. Provide accurate, professional medical advice. Always recommend consulting a doctor for serious concerns."},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=500,
            stream=False
        )
        raw_response = response.choices[0].message.content
        return format_response(raw_response)
    except Exception as e:
        return f"Sorry, I'm having trouble responding right now. Please try again later. Error: {str(e)}"

app = Flask(__name__)
CORS(app)

# Database setup
DATABASE = 'healthcare_bot.db'

def get_db():
    if not hasattr(g, '_database'):
        # Increase timeout and enable WAL mode for better concurrency
        g._database = sqlite3.connect(DATABASE, timeout=60)
        g._database.row_factory = sqlite3.Row
        # Enable WAL mode for better concurrency
        g._database.execute('PRAGMA journal_mode=WAL')
        # Set busy timeout
        g._database.execute('PRAGMA busy_timeout=60000')
    return g._database

def execute_with_retry(db, query, params=(), retries=3):
    """Execute SQL query with retry logic for concurrency issues"""
    for attempt in range(retries):
        try:
            return db.execute(query, params)
        except sqlite3.OperationalError as e:
            if 'locked' in str(e) and attempt < retries - 1:
                time.sleep(0.1 * (attempt + 1))
                continue
            raise

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.executescript(f.read())
        db.commit()

@app.route('/')
def index():
    return send_from_directory('..', 'healthcare-bot.html')

@app.route('/api/chats', methods=['GET'])
def get_chats():
    db = get_db()
    chats = db.execute('''
        SELECT c.*, 
               (SELECT COUNT(*) FROM messages WHERE chat_id = c.id) as message_count,
               (SELECT MAX(timestamp) FROM messages WHERE chat_id = c.id) as last_message
        FROM chats c
        ORDER BY last_message DESC
    ''').fetchall()
    return jsonify([dict(chat) for chat in chats])

@app.route('/api/chats', methods=['POST'])
def create_chat():
    data = request.json
    if not data or not data.get('title'):
        return jsonify({'error': 'Chat title is required'}), 400
        
    db = get_db()
    cursor = db.execute('INSERT INTO chats (title) VALUES (?)', (data['title'],))
    chat_id = cursor.lastrowid
    
    # Add initial bot message
    db.execute('''
        INSERT INTO messages (chat_id, content, is_bot, timestamp)
        VALUES (?, ?, ?, ?)
    ''', (chat_id, "Hello! I'm your AI Healthcare Bot. How can I assist you today?", True, datetime.now()))
    
    db.commit()
    return jsonify({
        'id': chat_id,
        'title': data['title']
    })

@app.route('/api/chats/<int:chat_id>/messages', methods=['GET'])
def get_messages(chat_id):
    db = get_db()
    messages = db.execute('''
        SELECT * FROM messages 
        WHERE chat_id = ?
        ORDER BY timestamp ASC
    ''', (chat_id,)).fetchall()
    return jsonify([dict(message) for message in messages])

@app.route('/api/chats/<int:chat_id>/messages', methods=['POST'])
def send_message(chat_id):
    data = request.json
    if not data or not data.get('content'):
        return jsonify({'error': 'Message content is required'}), 400
        
    db = get_db()
    # Save user message
    db.execute('''
        INSERT INTO messages (chat_id, content, is_bot, timestamp)
        VALUES (?, ?, ?, ?)
    ''', (chat_id, data['content'], False, datetime.now()))
    
    # Generate and save AI response
    ai_response = generate_healthcare_response(data['content'])
    db.execute('''
        INSERT INTO messages (chat_id, content, is_bot, timestamp)
        VALUES (?, ?, ?, ?)
    ''', (chat_id, ai_response, True, datetime.now()))
    
    db.commit()
    
    return jsonify({
        'status': 'success',
        'user_message': data['content'],
        'ai_response': ai_response,
        'chat_id': chat_id
    })

@app.route('/api/chats', methods=['DELETE'])
def clear_conversations():
    db = get_db()
    try:
        # Delete all messages first to maintain referential integrity
        db.execute('DELETE FROM messages')
        # Then delete all chats
        db.execute('DELETE FROM chats')
        db.commit()
        
        # Create a new default chat
        cursor = db.execute('INSERT INTO chats (title) VALUES (?)', ('New Chat',))
        db.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'All conversations cleared',
            'new_chat_id': cursor.lastrowid
        })
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
