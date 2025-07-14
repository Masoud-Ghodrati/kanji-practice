import csv
import re

def parse_kanji_file(input_file, output_file):
    """Parse the japanese_characters.txt file and convert to CSV format"""
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by lines and process each entry
    lines = content.strip().split('\n')
    
    kanji_data = []
    
    for i, line in enumerate(lines):
        if not line.strip():
            continue
            
        # Split by tabs first
        parts = line.split('\t')
        if len(parts) < 2:
            continue
            
        meaning = parts[0].strip()
        full_description = parts[1].strip() if len(parts) > 1 else ""
        
        # Extract character and lesson from the description
        char_match = re.search(r'([\u4e00-\u9faf]+)\s+.*?Lesson:\s*(\d+)', full_description)
        if not char_match:
            continue
            
        character = char_match.group(1).strip()
        lesson = char_match.group(2).strip()
        
        # Extract description (text between first quotes)
        desc_match = re.search(r'"([^"]*?)"', full_description)
        description = desc_match.group(1).strip() if desc_match else ""
        
        # Extract stories - there are usually 2 stories separated by \t \t
        # Pattern: after description, before On-Yomi
        story_section = ""
        story_match = re.search(r'"[^"]*"\s+(.+?)\s+On-Yomi:', full_description, re.DOTALL)
        if story_match:
            story_section = story_match.group(1).strip()
        
        # Split stories by double tab or multiple spaces/tabs
        story_parts = re.split(r'\t\s*\t|\s{4,}', story_section)
        story_parts = [s.strip() for s in story_parts if s.strip()]
        
        # Assign stories
        story1 = story_parts[0] if len(story_parts) > 0 else ""
        story2 = story_parts[1] if len(story_parts) > 1 else ""
        
        # If we have more than 2 parts, combine the rest into story2
        if len(story_parts) > 2:
            story2 = " ".join(story_parts[1:])
        
        # Extract readings
        on_yomi = ""
        kun_yomi = ""
        examples = ""
        
        on_match = re.search(r'On-Yomi:\s*([^\t]+?)(?:\s+Kun-Yomi:|\s+Examples:|$)', full_description)
        if on_match:
            on_yomi = on_match.group(1).strip()
            
        kun_match = re.search(r'Kun-Yomi:\s*([^\t]+?)(?:\s+Examples:|$)', full_description)
        if kun_match:
            kun_yomi = kun_match.group(1).strip()
        
        # Extract examples
        examples_match = re.search(r'Examples:\s*(.+?)(?:"|$)', full_description)
        if examples_match:
            examples = examples_match.group(1).strip()
        
        kanji_data.append({
            'number': i + 1,
            'character': character,
            'meaning': meaning,
            'lesson': lesson,
            'description': description,
            'story1': story1,
            'story2': story2,
            'on_yomi': on_yomi,
            'kun_yomi': kun_yomi,
            'examples': examples
        })
    
    # Write to CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['number', 'character', 'meaning', 'lesson', 'description', 'story1', 'story2', 'on_yomi', 'kun_yomi', 'examples']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for row in kanji_data:
            writer.writerow(row)
    
    print(f"Parsed {len(kanji_data)} kanji entries and saved to {output_file}")
    return len(kanji_data)

if __name__ == "__main__":
    parse_kanji_file("japanese_characters.txt", "kanji_data.csv")