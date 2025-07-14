
# Japanese Character Quiz App

This is a **Streamlit** web application designed to help users practice Japanese characters and their meanings. The app allows users to quiz themselves on randomly selected characters, track their progress, and download the results in both CSV and PDF formats.

## Features

- **Character Quiz**: Randomly select characters and test your knowledge of their meanings.
- **Progress Tracking**: Displays the number of characters answered correctly and the overall score in the sidebar.
- **Export Results**: Download your quiz results in CSV or PDF format.
- **Character Reset**: Option to reset the quiz and start again.
- **Custom Character Set**: Choose the number of characters to practice from a provided list.

## Requirements

To run this application, ensure you have the following installed:

- Python 3.7 or higher
- Required Python libraries (can be installed via `requirements.txt`):

  ```
  streamlit
  pandas
  reportlab
  ```

## Installation

1. **Clone the repository**:
   
   ```bash
   git clone https://github.com/your-username/japanese-character-quiz.git
   cd japanese-character-quiz
   ```

2. **Install the required dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Prepare the Text File**: 
   
   Ensure that your character list is available as a `.txt` file in the following format:

   ```
   Meaning   "Description"  Character   Lesson: x
   ```

   Modify the file path `numbers.txt` to point to your text file in the code.

4. **Run the app**:

   ```bash
   streamlit run app.py
   ```

   The app will open in your browser automatically.

## Usage

1. **Launch the App**: Once the app is running, you will see a simple interface with a few options to customize your quiz.
   
2. **Choose the Quiz Direction**:
   - **Japanese → English**: Test yourself by seeing the Japanese characters and providing their English meanings.
   - **English → Japanese**: Test yourself by seeing the meanings and providing the Japanese characters.

3. **Select the Number of Characters**: Input the number of characters you want to include in your quiz session (default is 2200).

4. **Answer Questions**: For each character, click **Correct** or **Incorrect** based on your knowledge.

5. **Track Your Progress**: The sidebar shows how many characters you have attempted, your percentage of correct answers, and lists any incorrect characters along with their meanings.

6. **Download Results**: After finishing the quiz or at any time, download your results as:
   - **CSV File**: A table with character number, character, meaning, and status (correct/incorrect).
   - **PDF File**: A formatted PDF document with the same data.

7. **Reset Progress**: To start a new session, click the **Reset Progress** button.

## File Descriptions

- **numbers.txt**: A text file containing Japanese characters and their meanings in the format described above.
- **selected_numbers.json**: A JSON file where the app stores previously selected characters and their scores (correct or incorrect). This file is updated every time a user selects "Correct" or "Incorrect".
  
## Example Text File Format

Ensure the text file (`numbers.txt`) follows the format below:

```
Character Meaning   "Explanation"  Character   Lesson: X
Example Meaning   "This is an example"  日  Lesson: 1
```

The regular expression extracts the meaning and character from this format.

## How It Works

- **Random Character Selection**: The app selects a random character that hasn't been used previously. Once all characters have been used, a warning will appear.
- **Scoring**: Each character is marked as either "Correct" (1) or "Incorrect" (0), and the score percentage is calculated and displayed in the sidebar.
- **Exporting Results**: Users can export their progress and character list at any time by downloading a CSV or PDF file.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.