import streamlit as st
import random
import json
import os
import re
import pandas as pd  # For CSV export
from io import BytesIO  # For PDF export
from reportlab.lib.pagesizes import letter  # PDF page size
from reportlab.pdfgen import canvas  # For generating PDFs
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
txt_file_path = "japanese_characters.txt"  # Path to your text file

# Define the file paths
json_file_path_english_to_japanese = "selected_characters_english_to_japanese.json"
json_file_path_japanese_to_english = "selected_characters_japanese_to_english.json"

# Load the list of Japanese characters and their meanings from the text file
def load_numbers_from_file(file_path, num_rows):
    characters = []
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            for i, line in enumerate(file):
                if i >= num_rows:  # Stop after reading num_rows characters
                    break
                # Extract the meaning (before the first double quote) and the Japanese character (before "Lesson:")
                match = re.search(r'^(.+?)\s+"[^"]*\s+([^\s]+)\s+Lesson:', line)
                if match:
                    meaning = match.group(1).strip()  # Extract meaning
                    character = match.group(2).strip()  # Extract character
                    # Append (character_number, character, meaning)
                    characters.append((i + 1, character, meaning))  # i+1 to make character number start from 1
    except Exception as e:
        st.error(f"An error occurred while reading the file: {e}")
    return characters

# Load previously selected numbers and their scores from the file (as a dictionary)
def load_selected_characters(direction):
    file_name = json_file_path_english_to_japanese if direction == "English → Japanese" else json_file_path_japanese_to_english
    if os.path.exists(file_name):
        with open(file_name, "r") as file:
            selected_characters = json.load(file)
    else:
        selected_characters = {}
    return selected_characters

# Save the selected numbers and their scores back to the file
def save_selected_characters(direction, selected_characters):
    file_name = json_file_path_english_to_japanese if direction == "English → Japanese" else json_file_path_japanese_to_english
    print(selected_characters)
    with open(file_name, "w") as file:
        json.dump(selected_characters, file)

# Get a random character without selecting previously chosen ones
def select_random_character(available_characters, selected_characters):
    remaining_characters = [char for _, char, _ in available_characters if char not in selected_characters]
    if not remaining_characters:
        st.warning("No remaining characters to select!")
        return None
    return random.choice(remaining_characters)

# Calculate the percentage of correct answers
def calculate_score(selected_characters):
    if not selected_characters:
        return 0
    total = len(selected_characters)
    correct = sum(selected_characters.values())  # Count all correct answers (1's)
    return round((correct / total) * 100, 2)

# Function to update the selected character
def update_character():
    available_characters = st.session_state.available_characters
    selected_characters = st.session_state.selected_characters
    selected = select_random_character(available_characters, selected_characters)
    if selected:
        char_number, char, meaning = next((n, c, m) for n, c, m in available_characters if c == selected)
        st.session_state.selected = (char_number, char)
        st.session_state.meaning = meaning

# Reset the app's progress and clear the history
def reset_progress():
    st.session_state.selected_characters = {}
    st.session_state.show_character_input = True  # Show character input after reset
    st.session_state.available_characters = []  # Clear available characters
    save_selected_characters(st.session_state.quiz_direction, st.session_state.selected_characters)

# Generate CSV for download
def generate_csv():
    data = []
    for char_number, char, meaning in st.session_state.available_characters:
        if char in st.session_state.selected_characters:
            status = "Correct" if st.session_state.selected_characters[char] == 1 else "Incorrect"
            data.append([char_number, char, meaning, status])
    df = pd.DataFrame(data, columns=["Character Number", "Character", "Meaning", "Status"])
    return df.to_csv(index=False).encode('utf-8')

# Generate PDF for download
def generate_pdf():
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdfmetrics.registerFont(TTFont("Noto Sans JP Thin", "NOTOSANSJP-THIN.TTF"))
    pdf.setFont("Noto Sans JP Thin", 14)
    pdf.drawString(100, 750, "Japanese Characters and Meanings")
    
    y_position = 720
    for char_number, char, meaning in st.session_state.available_characters:
        if char in st.session_state.selected_characters:
            status = "Correct" if st.session_state.selected_characters[char] == 1 else "Incorrect"
            pdf.drawString(100, y_position, f"({int(char_number):6}) {char:<6}: {meaning:<50} - {status}")
            y_position -= 20
            if y_position < 40:  # Create a new page if space runs out
                pdf.showPage()
                y_position = 750

    pdf.save()
    buffer.seek(0)
    return buffer

# Streamlit app
def main():
    # Initialize session state variables if not already initialized
    if 'available_characters' not in st.session_state:
        st.session_state.available_characters = []
    if 'selected_characters' not in st.session_state:
        st.session_state.selected_characters = {}
    if 'show_character_input' not in st.session_state:
        st.session_state.show_character_input = True
    if 'selected' not in st.session_state:
        st.session_state.selected = None
    if 'meaning' not in st.session_state:
        st.session_state.meaning = None
    if 'quiz_direction' not in st.session_state:
        st.session_state.quiz_direction = "Japanese → English"

    st.title("Japanese Character Quiz")

    # Language selection option
    st.session_state.quiz_direction = st.radio(
        "Select Quiz Direction:",
        ("Japanese → English", "English → Japanese"),
        index=0  # Default to Japanese → English
    )

    # Reset button at the top
    if st.button("Reset Progress"):
        reset_progress()
        st.success("Progress has been reset!")

    # Show the character input only after reset
    if st.session_state.show_character_input:
       
        num_chars = st.number_input("Select number of characters", min_value=1, max_value=2200, value=2200)
        st.session_state.available_characters = load_numbers_from_file(txt_file_path, num_chars)
        st.session_state.selected_characters = load_selected_characters(st.session_state.quiz_direction)
        update_character()  # Initialize the first character
        st.session_state.show_character_input = True  # Hide the input once it's used

    # Show the selected character or meaning based on the quiz direction
    if st.session_state.selected:
        char_number, char = st.session_state.selected
        print(char)
        meaning = st.session_state.meaning

        if st.session_state.quiz_direction == "Japanese → English":
            st.subheader(f"Character ({char_number}): {char}")
        else:
            st.subheader(f"Meaning ({char_number}): {meaning}")

        # Buttons for correct and incorrect
        col1, col2 = st.columns(2)
        with col1:
            correct_clicked = st.button("Correct")

        with col2:
            incorrect_clicked = st.button("Incorrect")
     
        # Handle button clicks
        if correct_clicked:
            st.session_state.selected_characters[char] = 1  # Mark as correct (1)
            save_selected_characters(st.session_state.quiz_direction, st.session_state.selected_characters)
            update_character()  # Update the character immediately
        
        if incorrect_clicked:
            st.session_state.selected_characters[char] = 0  # Mark as incorrect (0)
            save_selected_characters(st.session_state.quiz_direction, st.session_state.selected_characters)
            update_character()  # Update the character immediately
        
        # Show the meaning after user interaction
        if st.session_state.quiz_direction == "Japanese → English":
            with st.expander("Show Meaning"):
                st.write(meaning)
        else:
            with st.expander("Show Character"):
                st.write(char)
    # Sidebar for progress and score tracking
    st.sidebar.header("Progress")
    total_characters = len(st.session_state.available_characters)
    shown_characters = len(st.session_state.selected_characters)

    # Fix the division by zero issue
    if total_characters > 0:
        progress_percentage = min(shown_characters / total_characters, 1.0)
    else:
        progress_percentage = 0  # Avoid division by zero

    # Display the progress with character counter
    st.sidebar.progress(progress_percentage)
    st.sidebar.write(f"Progress: {shown_characters} / {total_characters} ({round(progress_percentage * 100, 2)}%)")

    score_percentage = calculate_score(st.session_state.selected_characters)
    st.sidebar.write(f"Score: {score_percentage}% correct")
    
    # Display incorrect characters and their meanings
    incorrect_characters = [char for char, score in st.session_state.selected_characters.items() if score == 0]
    if incorrect_characters:
        st.sidebar.write("Incorrect Characters:")
        for char in incorrect_characters:
            meaning = next((m for _, c, m in st.session_state.available_characters if c == char), "No meaning found")
            st.sidebar.write(f"{char}: {meaning}")



    # Download buttons for CSV and PDF exports
    col1, col2 = st.columns(2)
    with col1:
        csv_data = generate_csv()
        st.download_button(
            label="Download as CSV",
            data=csv_data,
            file_name="japanese_characters.csv",
            mime='text/csv'
        )
    with col2:
        pdf_data = generate_pdf()
        st.download_button(
            label="Download as PDF",
            data=pdf_data,
            file_name="japanese_characters.pdf",
            mime="application/pdf"
        )

if __name__ == "__main__":
    main()
