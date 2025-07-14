class KanjiQuiz {
    constructor() {
        this.currentCharacter = null;
        this.gameStarted = false;
        this.init();
    }

    init() {
        this.bindEvents();
        this.updateProgress();
    }

    bindEvents() {
        document.getElementById('startGame').addEventListener('click', () => this.startGame());
        document.getElementById('correctBtn').addEventListener('click', () => this.answerQuestion(true));
        document.getElementById('incorrectBtn').addEventListener('click', () => this.answerQuestion(false));
        document.getElementById('resetBtn').addEventListener('click', () => this.resetProgress());
    }

    async startGame() {
        const numChars = document.getElementById('numChars').value;
        const direction = document.querySelector('input[name="direction"]:checked').value;
        
        const startBtn = document.getElementById('startGame');
        setLoading(startBtn, true);

        try {
            const response = await fetch('/start_game', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({num_chars: parseInt(numChars), direction})
            });

            if (response.ok) {
                const data = await response.json();
                if (data.no_more_characters) {
                    this.showNoMoreCharacters();
                } else {
                    this.showCharacter(data);
                    this.gameStarted = true;
                    document.getElementById('gameSetup').style.display = 'none';
                    document.getElementById('quizInterface').style.display = 'block';
                    this.updateProgress();
                }
            }
        } catch (error) {
            showAlert('Error starting game', 'danger');
        } finally {
            startBtn.disabled = false;
            startBtn.innerHTML = '<i class="fas fa-play"></i> Start Quiz';
        }
    }

    async getNextCharacter() {
        try {
            const response = await fetch('/get_character');
            const data = await response.json();
            
            if (data.no_more_characters) {
                this.showNoMoreCharacters();
            } else {
                this.showCharacter(data);
            }
        } catch (error) {
            showAlert('Error getting next character', 'danger');
        }
    }

    showCharacter(data) {
        this.currentCharacter = data;
        const displayElement = document.getElementById('characterDisplay');
        const answerElement = document.getElementById('answerDisplay');
        
        if (data.direction === 'Japanese → English') {
            displayElement.innerHTML = `<div class="character-jp">${data.character}</div><small class="text-muted">(#${data.char_number})</small>`;
            answerElement.textContent = data.meaning;
        } else {
            displayElement.innerHTML = `<div>${data.meaning}</div><small class="text-muted">(#${data.char_number})</small>`;
            answerElement.innerHTML = `<span class="character-jp">${data.character}</span>`;
        }
        
        // Collapse the answer if it's open
        const answerCollapse = document.getElementById('answerReveal');
        if (answerCollapse.classList.contains('show')) {
            bootstrap.Collapse.getInstance(answerCollapse).hide();
        }
    }

    async answerQuestion(isCorrect) {
        if (!this.currentCharacter) return;

        const correctBtn = document.getElementById('correctBtn');
        const incorrectBtn = document.getElementById('incorrectBtn');
        
        correctBtn.disabled = true;
        incorrectBtn.disabled = true;

        try {
            const response = await fetch('/answer', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    character: this.currentCharacter.character,
                    is_correct: isCorrect
                })
            });

            if (response.ok) {
                this.updateProgress();
                setTimeout(() => {
                    this.getNextCharacter();
                    correctBtn.disabled = false;
                    incorrectBtn.disabled = false;
                }, 500);
            }
        } catch (error) {
            showAlert('Error submitting answer', 'danger');
            correctBtn.disabled = false;
            incorrectBtn.disabled = false;
        }
    }

    async updateProgress() {
        try {
            const response = await fetch('/get_progress');
            const data = await response.json();
            
            const progressBar = document.getElementById('progressBar');
            const progressText = document.getElementById('progressText');
            const scoreText = document.getElementById('scoreText');
            const incorrectList = document.getElementById('incorrectList');
            
            progressBar.style.width = `${data.progress_percentage}%`;
            progressBar.setAttribute('aria-valuenow', data.progress_percentage);
            progressText.textContent = `${data.shown_characters} / ${data.total_characters} (${data.progress_percentage}%)`;
            scoreText.textContent = `${data.score_percentage}%`;
            
            if (data.incorrect_characters.length > 0) {
                incorrectList.innerHTML = data.incorrect_characters.map(item => 
                    `<div class="incorrect-item">
                        <span class="character-jp">${item.character}</span>: ${item.meaning}
                    </div>`
                ).join('');
            } else {
                incorrectList.innerHTML = '<em class="text-muted">No incorrect answers yet</em>';
            }
        } catch (error) {
            console.error('Error updating progress:', error);
        }
    }

    async resetProgress() {
        if (!confirm('Are you sure you want to reset your progress? This will clear all your answers.')) {
            return;
        }

        const resetBtn = document.getElementById('resetBtn');
        setLoading(resetBtn, true);

        try {
            const response = await fetch('/reset_progress', {method: 'POST'});
            
            if (response.ok) {
                showAlert('Progress has been reset!', 'success');
                this.gameStarted = false;
                document.getElementById('gameSetup').style.display = 'block';
                document.getElementById('quizInterface').style.display = 'none';
                document.getElementById('noMoreChars').style.display = 'none';
                this.updateProgress();
            }
        } catch (error) {
            showAlert('Error resetting progress', 'danger');
        } finally {
            resetBtn.disabled = false;
            resetBtn.innerHTML = '<i class="fas fa-redo"></i> Reset Progress';
        }
    }

    showNoMoreCharacters() {
        document.getElementById('quizInterface').style.display = 'none';
        document.getElementById('noMoreChars').style.display = 'block';
    }
}

// Initialize the quiz when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new KanjiQuiz();
});