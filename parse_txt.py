import csv
import re

# Define the output CSV columns
columns = ["meaning", "translation", "character", "Lesson number", "Frame number", "Stroke number", "Grade number", 
           "JLPT", "Constituents", "Example sentence 1", "Example sentence 2", "On-Yomi", "Kun-Yomi", "Example words"]

# Function to parse each line and extract fields safely
def parse_line(line):
    # Split the sections by multiple spaces or tabs
    sections = re.split(r'\s{2,}', line.strip())

    # Validate that we have enough basic fields to extract
    if len(sections) < 3:  # minimum: meaning, translation, character
        return None

    # Basic fields
    meaning = sections[0].split()[0] if len(sections) > 0 else ''
    translation = sections[0].split()[1] if len(sections) > 1 else ''
    character = sections[1].strip() if len(sections) > 2 else ''
  
    # Search for lesson info
    lesson_info = re.search(r"Lesson: (\d+)", line)
    lesson_number = lesson_info.group(1) if lesson_info else ''
  
    # Search for other fields like frame, strokes, etc.
    frame_info = re.search(r"Frame: (\d+)", line)
    stroke_info = re.search(r"Strokes: (\d+)", line)
    grade_info = re.search(r"Jouyou Grade: (\d+)", line)
    jlpt_info = re.search(r"JLPT: (\d+)", line)

    # Constituents, On-Yomi, Kun-Yomi, and Example words
    constituents = next((s for s in sections if "Constituents" in s), '').strip().replace("Constituents: ", "")
    
    # Extract the part between "On-Yomi:" and "Kun-Yomi:"
    on_yomi = re.search(r"On-Yomi:\s*(.*?)\s*Kun-Yomi:", line)
    
    # Extract Kun-Yomi part (after "Kun-Yomi:")
    kun_yomi = re.search(r"Kun-Yomi:\s*(.*?)\s*Examples:", line)
   
    # Extract the part after "Examples:"
    example_words = re.search(r"Examples:\s*(.+)", line)
    example_words = example_words.group(1) if example_words else ''
    
    # Extract Example sentence 1 (after "Constituents:" but before "On-Yomi:")
    example_sentence_1_match = re.search(r"Constituents:.+?\s*(.+?)\s*On-Yomi:", line)
    example_sentence_1 = example_sentence_1_match.group(1).strip() if example_sentence_1_match else ''
    example_sentence_section = re.split(r'\s{2,}', example_sentence_1.strip())

    if len(example_sentence_section) == 3:
       example_sentence_1 = example_sentence_section[1]
       example_sentence_2 = example_sentence_section[2]
    elif len(example_sentence_section) == 4:
        example_sentence_1 = example_sentence_section[1] + example_sentence_section[2]
        example_sentence_2 = example_sentence_section[3]
    elif len(example_sentence_section) == 5:
        example_sentence_1 = example_sentence_section[1] + example_sentence_section[2]
        example_sentence_2 = example_sentence_section[3] + example_sentence_section[4]
    else:
        example_sentence_1 = ""
        example_sentence_2 = ""

    # Return a dictionary for CSV with quotes around meaning, translation, and character
    return {
        "meaning": meaning,
        "translation": translation,
        "character": character,
        "Lesson number": lesson_number,
        "Frame number": frame_info.group(1) if frame_info else '',
        "Stroke number": stroke_info.group(1) if stroke_info else '',
        "Grade number": grade_info.group(1) if grade_info else '',
        "JLPT": jlpt_info.group(1) if jlpt_info else '',
        "Constituents": constituents,
        "Example sentence 1": example_sentence_1,
        "Example sentence 2": example_sentence_2,
        "On-Yomi": on_yomi.group(1) if on_yomi else '',
        "Kun-Yomi": kun_yomi.group(1) if kun_yomi else '',
        "Example words": example_words
    }

# Read the text file and create the CSV
with open('japanese_characters.txt', 'r', encoding='utf-8') as infile, \
        open('output.csv', 'w', newline='', encoding='utf-8') as outfile:
    
    writer = csv.DictWriter(outfile, fieldnames=columns)
    writer.writeheader()
    
    for line in infile:
        parsed_data = parse_line(line)
        if parsed_data:  # Only write valid rows
            writer.writerow(parsed_data)

print("CSV file created successfully.")
