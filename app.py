"""
M-Store Admin - E-commerce Backend
-----------------------------------
Pure Python (Tkinter only, no external chart libraries).

Flow:
    1. App starts at the Auth window (Login / Create Account toggle).
    2. On successful login, the Auth window closes and the Dashboard
       (main admin window) opens.
    3. Logging out from the Dashboard returns to the Auth window.

Accounts are stored locally in admin_users.json (username, salted
password hash, email, created date). No external DB/network needed.
"""
from flask import Flask, render_template, request, redirect, url_for, session
app = Flask(__name__)

@app.route("/")
def home():
    return "Hello, Render!"
#if __name__ == '__main__':
    #appBcd.run(debug=True)
