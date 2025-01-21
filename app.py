from flask import Flask, redirect, url_for, session, request
from flask import render_template
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "default_secret_key")  # Use environment variable for security

# Decorator to require login

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@login_required
def landing_page():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Process login form submission
        username = request.form.get('username')
        password = request.form.get('password')

        # Authenticate user (add your own logic here)
        if username == 'admin' and password == 'password':  # Replace with actual authentication
            session['logged_in'] = True
            return redirect(url_for('landing_page'))
        else:
            return render_template('login.html', error='Invalid credentials')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
