from flask import Flask, render_template, request, jsonify, session, send_file, redirect, url_for
import random
import json
import os
import re
import csv
from io import BytesIO, StringIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import warnings

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'fallback-secret-key-change-in-production')

warnings.filterwarnings("ignore", category=DeprecationWarning)

# Configuration
TXT_FILE_PATH = "japanese_characters.txt"
JSON_FILE_PATH_EN_TO_JP = "selected_characters_english_to_japanese.json"
JSON_FILE_PATH_JP_TO_EN = "selected_characters_japanese_to_english.json"
NUM_ROUNDS_FILE = "num_rounds.txt"
USERS_FILE = "users.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

def save_num_rounds(num_rounds, username):
    with open(f"{username}-{NUM_ROUNDS_FILE}", "w") as f:
        f.write(str(num_rounds))

def load_num_rounds(username):
    if os.path.exists(f"{username}-{NUM_ROUNDS_FILE}"):
        with open(f"{username}-{NUM_ROUNDS_FILE}", "r") as f:
            return int(f.read())
    return None

def load_numbers_from_file(file_path, num_rows):
    characters = []
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            for i, line in enumerate(file):
                if i >= num_rows:
                    break
                match = re.search(r'^(.+?)\s+"[^"]*\s+([^\s]+)\s+Lesson:', line)
                if match:
                    meaning = match.group(1).strip()
                    character = match.group(2).strip()
                    characters.append((i + 1, character, meaning))
    except Exception as e:
        print(f"Error reading file: {e}")
    return characters

def load_selected_characters(direction, username):
    file_name = f"{username}-{JSON_FILE_PATH_EN_TO_JP}" if direction == "English → Japanese" else f"{username}-{JSON_FILE_PATH_JP_TO_EN}"
    if os.path.exists(file_name):
        with open(file_name, "r") as file:
            return json.load(file)
    return {}

def save_selected_characters(direction, selected_characters, username):
    file_name = f"{username}-{JSON_FILE_PATH_EN_TO_JP}" if direction == "English → Japanese" else f"{username}-{JSON_FILE_PATH_JP_TO_EN}"
    with open(file_name, "w") as file:
        json.dump(selected_characters, file)

def select_random_character(available_characters, selected_characters):
    remaining_characters = [char for _, char, _ in available_characters if char not in selected_characters]
    if not remaining_characters:
        return None
    return random.choice(remaining_characters)

def calculate_score(selected_characters):
    if not selected_characters:
        return 0
    total = len(selected_characters)
    correct = sum(selected_characters.values())
    return round((correct / total) * 100, 2)

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        users = load_users()
        if username in users and users[username] == password:
            session['username'] = username
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Invalid credentials'})
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        users = load_users()
        if username in users:
            return jsonify({'success': False, 'message': 'Username already exists'})
        
        users[username] = password
        save_users(users)
        return jsonify({'success': True})
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/start_game', methods=['POST'])
def start_game():
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    num_chars = data.get('num_chars', 2200)
    direction = data.get('direction', 'Japanese → English')
    
    username = session['username']
    save_num_rounds(num_chars, username)
    
    available_characters = load_numbers_from_file(TXT_FILE_PATH, num_chars)
    selected_characters = load_selected_characters(direction, username)
    
    session['available_characters'] = available_characters
    session['selected_characters'] = selected_characters
    session['quiz_direction'] = direction
    session['num_chars'] = num_chars
    
    return get_next_character()

@app.route('/get_character')
def get_next_character():
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    available_characters = session.get('available_characters', [])
    selected_characters = session.get('selected_characters', {})
    
    selected = select_random_character(available_characters, selected_characters)
    if not selected:
        return jsonify({'no_more_characters': True})
    
    char_number, char, meaning = next((n, c, m) for n, c, m in available_characters if c == selected)
    
    return jsonify({
        'char_number': char_number,
        'character': char,
        'meaning': meaning,
        'direction': session.get('quiz_direction', 'Japanese → English')
    })

@app.route('/answer', methods=['POST'])
def answer():
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    character = data.get('character')
    is_correct = data.get('is_correct')
    
    username = session['username']
    selected_characters = session.get('selected_characters', {})
    selected_characters[character] = 1 if is_correct else 0
    session['selected_characters'] = selected_characters
    
    save_selected_characters(session.get('quiz_direction'), selected_characters, username)
    
    return jsonify({'success': True})

@app.route('/get_progress')
def get_progress():
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    available_characters = session.get('available_characters', [])
    selected_characters = session.get('selected_characters', {})
    
    total_characters = len(available_characters)
    shown_characters = len(selected_characters)
    progress_percentage = (shown_characters / total_characters * 100) if total_characters > 0 else 0
    score_percentage = calculate_score(selected_characters)
    
    incorrect_characters = []
    for char, score in selected_characters.items():
        if score == 0:
            meaning = next((m for _, c, m in available_characters if c == char), "No meaning found")
            incorrect_characters.append({'character': char, 'meaning': meaning})
    
    return jsonify({
        'total_characters': total_characters,
        'shown_characters': shown_characters,
        'progress_percentage': round(progress_percentage, 2),
        'score_percentage': score_percentage,
        'incorrect_characters': incorrect_characters
    })

@app.route('/reset_progress', methods=['POST'])
def reset_progress():
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    username = session['username']
    direction = session.get('quiz_direction', 'Japanese → English')
    
    session['selected_characters'] = {}
    save_selected_characters(direction, {}, username)
    
    if os.path.exists(f"{username}-{NUM_ROUNDS_FILE}"):
        os.remove(f"{username}-{NUM_ROUNDS_FILE}")
    
    return jsonify({'success': True})

@app.route('/download_csv')
def download_csv():
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    available_characters = session.get('available_characters', [])
    selected_characters = session.get('selected_characters', {})
    username = session['username']
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Character Number", "Character", "Meaning", "Status"])
    
    for char_number, char, meaning in available_characters:
        if char in selected_characters:
            status = "Correct" if selected_characters[char] == 1 else "Incorrect"
            writer.writerow([char_number, char, meaning, status])
    
    csv_data = output.getvalue().encode('utf-8')
    output.close()
    
    return send_file(BytesIO(csv_data), as_attachment=True, download_name=f"{username}-japanese_characters.csv", mimetype='text/csv')

@app.route('/download_pdf')
def download_pdf():
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    available_characters = session.get('available_characters', [])
    selected_characters = session.get('selected_characters', {})
    username = session['username']
    
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setFont("Helvetica", 14)
    pdf.drawString(100, 750, "Japanese Characters and Meanings")
    
    y_position = 720
    for char_number, char, meaning in available_characters:
        if char in selected_characters:
            status = "Correct" if selected_characters[char] == 1 else "Incorrect"
            pdf.drawString(100, y_position, f"({int(char_number):6}) {char:<6}: {meaning:<50} - {status}")
            y_position -= 20
            if y_position < 40:
                pdf.showPage()
                y_position = 750
    
    pdf.save()
    buffer.seek(0)
    
    return send_file(buffer, as_attachment=True, download_name=f"{username}-japanese_characters.pdf", mimetype="application/pdf")

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)