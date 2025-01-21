from flask import Flask, redirect, url_for, request, session
from models import User

app = Flask(__name__)
app.secret_key = "secret_key"

@app.route('/')
def landing_page():
    if 'user' not in session:
        return redirect(url_for('login'))
    return "hi CALPIRG"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.authenticate(username, password):
            session['user'] = username
            return redirect(url_for('landing_page'))
        return "Invalid credentials. Please try again."
    return '''
        <form method="post">
            Username: <input type="text" name="username"><br>
            Password: <input type="password" name="password"><br>
            <input type="submit" value="Login">
        </form>
    '''

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.create(username, password):
            return redirect(url_for('login'))
        return "User already exists. Please try again."
    return '''
        <form method="post">
            Username: <input type="text" name="username"><br>
            Password: <input type="password" name="password"><br>
            <input type="submit" value="Sign Up">
        </form>
    '''

if __name__ == "__main__":
    app.run(debug=True)