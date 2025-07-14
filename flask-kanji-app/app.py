from flask import Flask, render_template, request, jsonify, session, send_file, redirect, url_for
import random
import json
import os
import re
import csv
from io import BytesIO, StringIO
# PDF functionality temporarily disabled
import warnings
from database import init_db, create_user, authenticate_user, get_user_settings, save_user_settings, get_progress, save_progress, delete_progress_item, reset_progress, get_user_stats

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'fallback-secret-key-change-in-production')

warnings.filterwarnings("ignore", category=DeprecationWarning)

# Initialize database
init_db()

# Configuration
TXT_FILE_PATH = "japanese_characters.txt"

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
        
        if authenticate_user(username, password):
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
        
        if create_user(username, password):
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Username already exists'})
    
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
    username = session['username']
    
    # Load saved num_chars or use provided/default
    saved_num_chars = get_user_settings(username)
    num_chars = data.get('num_chars', saved_num_chars)
    direction = data.get('direction', 'Japanese → English')
    
    save_user_settings(username, num_chars)
    
    available_characters = load_numbers_from_file(TXT_FILE_PATH, num_chars)
    selected_characters = get_progress(username, direction)
    
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
    direction = session.get('quiz_direction')
    selected_characters = session.get('selected_characters', {})
    selected_characters[character] = 1 if is_correct else 0
    session['selected_characters'] = selected_characters
    
    save_progress(username, character, direction, 1 if is_correct else 0)
    
    return jsonify({'success': True, 'character': character})

@app.route('/get_progress')
def get_progress_route():
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

@app.route('/undo_answer', methods=['POST'])
def undo_answer():
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    character = data.get('character')
    
    username = session['username']
    direction = session.get('quiz_direction')
    selected_characters = session.get('selected_characters', {})
    
    if character in selected_characters:
        del selected_characters[character]
        session['selected_characters'] = selected_characters
        delete_progress_item(username, character, direction)
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'message': 'Character not found'})

@app.route('/get_user_settings')
def get_user_settings_route():
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    username = session['username']
    from database import get_user_settings as db_get_user_settings
    saved_num_chars = db_get_user_settings(username)
    
    return jsonify({
        'username': username,
        'saved_num_chars': saved_num_chars or 2200
    })

@app.route('/reset_progress', methods=['POST'])
def reset_progress_route():
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    username = session['username']
    direction = session.get('quiz_direction', 'Japanese → English')
    
    session['selected_characters'] = {}
    from database import reset_progress as db_reset_progress
    db_reset_progress(username, direction)
    
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
    return jsonify({'error': 'PDF download temporarily disabled'}), 503

@app.route('/stats')
def stats():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('stats.html')

@app.route('/api/stats')
def api_stats():
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    username = session['username']
    stats = get_user_stats(username)
    return jsonify(stats)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)