# login.py
import streamlit as st
import hashlib
import json
import os

USER_FILE = "users.json"

class LoginManager:
    def __init__(self):
        self.users = self.load_users()

    def load_users(self):
        if os.path.exists(USER_FILE):
            with open(USER_FILE, "r") as f:
                return json.load(f)
        return {}

    def save_users(self):
        with open(USER_FILE, "w") as f:
            json.dump(self.users, f, indent=4)

    def hash_text(self, text):
        return hashlib.sha256(text.encode()).hexdigest()

    def check_login(self, username, password):
        return username in self.users and self.users[username]["password"] == self.hash_text(password)

    def sign_up(self, username, password, security_question, security_answer):
        if username in self.users:
            return False
        self.users[username] = {
            "password": self.hash_text(password),
            "security_question": security_question,
            "security_answer": self.hash_text(security_answer)
        }
        self.save_users()
        return True

    def reset_password(self, username, security_question, security_answer, new_password):
        if (
            username in self.users and
            self.users[username]["security_question"] == security_question and
            self.users[username]["security_answer"] == self.hash_text(security_answer)
        ):
            self.users[username]["password"] = self.hash_text(new_password)
            self.save_users()
            return True
        return False

def login_page(login_manager):
    st.title("Login / Sign Up / Forgot Password")
    choice = st.radio("Choose an option:", ["Login", "Sign Up", "Forgot Password"])

    username = st.text_input("Username")

    if choice == "Login":
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if login_manager.check_login(username, password):
                st.session_state.username = username
                st.session_state.authenticated = True
                st.session_state.data = []
                st.success("Logged in successfully!")
            else:
                st.error("Invalid username or password.")

    elif choice == "Sign Up":
        password = st.text_input("Password", type="password")
        security_question = st.selectbox(
            "Select a security question:",
            [
                "What is your mother's maiden name?",
                "What was the name of your first pet?",
                "What was the name of your elementary school?",
                "What is the name of the town where you were born?",
                "What was your childhood nickname?"
            ]
        )
        security_answer = st.text_input("Answer to security question")
        if st.button("Sign Up"):
            if login_manager.sign_up(username, password, security_question, security_answer):
                st.success("Account created successfully! Please log in.")
            else:
                st.error("Username already exists. Please choose a different one.")

    elif choice == "Forgot Password":
        security_question = st.selectbox(
            "Select your security question:",
            [
                "What is your mother's maiden name?",
                "What was the name of your first pet?",
                "What was the name of your elementary school?",
                "What is the name of the town where you were born?",
                "What was your childhood nickname?"
            ]
        )
        security_answer = st.text_input("Answer to your security question")
        new_password = st.text_input("New Password", type="password")
        if st.button("Reset Password"):
            if login_manager.reset_password(username, security_question, security_answer, new_password):
                st.success("Password reset successfully! Please log in with your new password.")
            else:
                st.error("Invalid username, security question, or answer.")
