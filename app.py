from flask import Flask, redirect, url_for, request, session, render_template, flash, send_file, jsonify
from models import User, DocumentModel
from drive_search import search_files
from google_drive import google_drive_auth, google_drive_callback, picker_route, sync_google_drive, sync_folder_route  # Update this import
import os
from docx import Document
import pandas as pd
import sqlite3  # Add this import
from flask_wtf.csrf import CSRFProtect  # Add this import

# Allow insecure transport for development
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = Flask(__name__)
app.secret_key = "secret_key"
csrf = CSRFProtect(app)

User.initialize_db()

# Ensure the email "phillipmlavrador@gmail.com" always has the "Organizer" role
User.update_role('phillipmlavrador@gmail.com', 'Organizer')

def has_permission(email, permission):
    conn = sqlite3.connect(User.DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT roles FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    if user:
        roles = user[0].split(',')
        for role in roles:
            cursor.execute(f'SELECT {permission} FROM roles WHERE role_name = ?', (role,))
            role_info = cursor.fetchone()
            if role_info and role_info[0]:
                return True
    conn.close()
    return False

@app.route('/')
def home():
    if 'user' in session and has_permission(session['user'], 'can_access_admin_page'):
        can_access_admin_page = True
    else:
        can_access_admin_page = False
    return render_template('home.html', can_access_admin_page=can_access_admin_page)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if User.authenticate(email, password):
            session['user'] = email
            conn = sqlite3.connect(User.DB_PATH)
            cursor = conn.cursor()
            cursor.execute('SELECT first_name FROM users WHERE email = ?', (email,))
            session['first_name'] = cursor.fetchone()[0]
            conn.close()
            next_page = request.args.get('next')
            return redirect(next_page or url_for('home'))
        else:
            flash('Incorrect email or password', 'error')
    return render_template('login/login.html', next=request.args.get('next'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        if not email or not password or not confirm_password or not first_name or not last_name:
            flash('All fields are required', 'error')
        elif password != confirm_password:
            flash('Passwords do not match', 'error')
        elif User.create(email, password, first_name, last_name):
            session['user'] = email
            session['first_name'] = first_name
            return redirect(url_for('home'))
        else:
            flash('User creation failed', 'error')
    return render_template('login/signup.html')

@app.route('/files', methods=['GET', 'POST'])
def files():
    if 'user' not in session:
        flash('You must be logged in to access this page', 'error')
        return redirect(url_for('login', next=request.url))
    results = None
    if request.method == 'POST':
        query = request.form['query']
        results = search_files('./documents', query)  # Update the path as needed
    is_admin = 'user' in session and has_permission(session['user'], 'can_access_admin_page')
    is_organizer = 'user' in session and has_permission(session['user'], 'can_assign_admin')
    return render_template('doc_search/files.html', results=results, is_admin=is_admin, is_organizer=is_organizer)

@app.route('/open_file')
def open_file():
    file_path = request.args.get('file_path')
    if file_path and os.path.exists(file_path):
        if file_path.lower().endswith('.docx'):
            doc = Document(file_path)
            content = ''.join([f'<p>{para.text}</p>' for para in doc.paragraphs])
        elif file_path.lower().endswith('.xlsx'):
            df = pd.read_excel(file_path)
            content = df.to_html(classes='dataframe')
        else:
            with open(file_path, 'r', errors='ignore') as file:
                content = file.read()
        is_admin = 'user' in session and has_permission(session['user'], 'can_access_admin_page')
        is_organizer = 'user' in session and has_permission(session['user'], 'can_assign_admin')
        return render_template('doc_search/file_content.html', content=content, is_admin=is_admin, is_organizer=is_organizer)
    else:
        flash('File not found', 'error')
        return redirect(url_for('files'))

@app.route('/admin')
def admin():
    if 'user' not in session:
        flash('You must be logged in to access this page', 'error')
        return redirect(url_for('login', next=request.url))
    email = session['user']
    if has_permission(email, 'can_access_admin_page'):
        return render_template('admin_pages/admin.html')
    flash('You do not have permission to access this page', 'error')
    return redirect(url_for('home'))

@app.route('/admin_pages/members')
def members():
    if 'user' not in session or not has_permission(session['user'], 'can_access_admin_page'):
        flash('You do not have permission to access this page', 'error')
        return redirect(url_for('home'))
    conn = sqlite3.connect(User.DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT email, first_name, last_name, roles FROM users')
    members = cursor.fetchall()
    conn.close()
    perms = {
        'can_assign_organizer': 'user' in session and has_permission(session['user'], 'can_assign_organizer'),
        'can_assign_admin': 'user' in session and has_permission(session['user'], 'can_assign_admin'),
        'can_assign_gen_roles': 'user' in session and has_permission(session['user'], 'can_assign_gen_roles'),
                   }
    return render_template('admin_pages/members.html', members=members, perms=perms)

@app.route('/doc_db')
def doc_db():
    if 'user' not in session or not has_permission(session['user'], 'can_access_admin_page'):
        flash('You do not have permission to access this page', 'error')
        return redirect(url_for('home'))
    documents = DocumentModel.get_all_documents()
    return render_template('admin_pages/doc_db.html', documents=documents)

@app.route('/toggle_admin', methods=['POST'])
@csrf.exempt
def toggle_admin():
    if 'user' not in session or not has_permission(session['user'], 'can_assign_admin'):
        return 'Unauthorized', 403
    data = request.get_json()
    email = data['email']
    is_admin = data['is_admin']
    User.update_role(email, is_admin)
    return 'Success', 200

@app.route('/update_roles', methods=['POST'])
@csrf.exempt
def update_roles():
    if 'user' not in session or not has_permission(session['user'], 'can_assign_admin'):
        return 'Unauthorized', 403
    data = request.get_json()
    email = data.get('email')
    role = data.get('role')
    is_checked = data.get('is_checked')
    
    conn = sqlite3.connect(User.DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT roles FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        return jsonify({'error': 'User not found'}), 404
    
    roles = user[0].split(',') if user[0] else []
    if is_checked:
        if role not in roles:
            roles.append(role)
    else:
        if role in roles:
            roles.remove(role)
    
    new_roles = ','.join(roles)
    cursor.execute('UPDATE users SET roles = ? WHERE email = ?', (new_roles, email))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/delete_user', methods=['POST'])
@csrf.exempt
def delete_user():
    if 'user' not in session or not has_permission(session['user'], 'can_delete_user'):
        return 'Unauthorized', 403
    data = request.get_json()
    email = data['email']
    if has_permission(email, 'can_access_admin_page') and not has_permission(session['user'], 'can_assign_admin'):
        return 'Unauthorized', 403
    User.delete_user(email)
    return 'Success', 200

@app.route('/sync_files', methods=['POST'])
@csrf.exempt
def sync_files():
    if 'user' not in session or not has_permission(session['user'], 'can_access_admin_page'):
        return 'Unauthorized', 403
    sync_google_drive()
    return 'Success', 200

@app.route('/sync_folder', methods=['POST'])
@csrf.exempt
def sync_folder_route():
    return sync_folder_route()

@app.route('/google_drive_auth')
def google_drive_auth_route():
    return google_drive_auth()

@app.route('/google_drive_callback')
def google_drive_callback_route():
    return google_drive_callback()

@app.route('/picker')
def picker():
    return picker_route()

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True, host='localhost', port=5000)