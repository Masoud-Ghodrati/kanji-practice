# Flask Kanji Practice App

A modern, responsive web application for practicing Japanese Kanji characters built with Flask and Bootstrap.

## Features

- **User Authentication**: Login/Register system with session management
- **Interactive Quiz**: Practice Kanji in both directions (Japanese → English, English → Japanese)
- **Progress Tracking**: Real-time progress bar and score tracking
- **Mistake Review**: View incorrect answers with meanings
- **Export Options**: Download results as CSV or PDF
- **Responsive Design**: Modern Bootstrap UI that works on all devices
- **Session Persistence**: Your progress is saved between sessions

## Installation

1. **Navigate to the Flask app directory**:
   ```bash
   cd flask-kanji-app
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python app.py
   ```

4. **Open your browser** and go to `http://localhost:5000`

## Usage

1. **Register/Login**: Create an account or login with existing credentials
2. **Setup Quiz**: Choose direction (Japanese → English or English → Japanese) and number of characters
3. **Practice**: Click "Correct" or "Incorrect" for each character
4. **Track Progress**: Monitor your progress and review mistakes in the sidebar
5. **Export Results**: Download your progress as CSV or PDF files
6. **Reset**: Start over anytime with the reset button

## File Structure

```
flask-kanji-app/
├── app.py                 # Main Flask application
├── templates/
│   ├── base.html         # Base template
│   ├── login.html        # Login/Register page
│   └── index.html        # Main quiz interface
├── static/
│   ├── css/
│   │   └── style.css     # Custom styles
│   └── js/
│       ├── app.js        # Common utilities
│       └── quiz.js       # Quiz functionality
├── japanese_characters.txt # Character data
└── requirements.txt      # Python dependencies
```

## Key Improvements over Streamlit Version

- **Better UX**: Modern, responsive interface with smooth interactions
- **User Management**: Multi-user support with individual progress tracking
- **Performance**: Faster loading and better resource management
- **Customization**: Easy to modify and extend functionality
- **Mobile Friendly**: Works seamlessly on mobile devices

## Configuration

- Change the `secret_key` in `app.py` for production use
- Modify character file path in `TXT_FILE_PATH` if needed
- Adjust styling in `static/css/style.css`

## License

MIT License - Feel free to modify and distribute.