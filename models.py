import os
import sqlite3

class User:
    DB_PATH = "database.db"

    @staticmethod
    def initialize_db():
        conn = sqlite3.connect(User.DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                roles TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS roles (
                role_name TEXT PRIMARY KEY,
                can_delete_user BOOLEAN NOT NULL,
                can_assign_admin BOOLEAN NOT NULL,
                can_assign_organizer BOOLEAN NOT NULL,
                can_assign_gen_roles BOOLEAN NOT NULL,
                can_access_admin_page BOOLEAN NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

    @staticmethod
    def authenticate(email, password):
        conn = sqlite3.connect(User.DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password))
        user = cursor.fetchone()
        conn.close()
        return user is not None

    @staticmethod
    def create(email, password, first_name, last_name):
        roles = "member"
        if email == "phillipmlavrador@gmail.com":
            roles = "Organizer"
        conn = sqlite3.connect(User.DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (email, password, first_name, last_name, roles) VALUES (?, ?, ?, ?, ?)',
                           (email, password, first_name, last_name, roles))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    @staticmethod
    def update_role(email, add_admin):
        conn = sqlite3.connect(User.DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT roles FROM users WHERE email = ?', (email,))
        result = cursor.fetchone()
        roles = result[0] if result else ''
        roles_list = roles.split(',')
        if add_admin:
            if 'Admin' not in roles_list:
                roles_list.append('Admin')
        else:
            if 'Admin' in roles_list:
                roles_list.remove('Admin')
        new_roles = ','.join(roles_list)
        cursor.execute('UPDATE users SET roles = ? WHERE email = ?', (new_roles, email))
        conn.commit()
        conn.close()

    @staticmethod
    def update_roles(email, roles):
        new_roles = ','.join(roles)
        conn = sqlite3.connect(User.DB_PATH)
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET roles = ? WHERE email = ?', (new_roles, email))
        conn.commit()
        conn.close()

    @staticmethod
    def delete_user(email):
        conn = sqlite3.connect(User.DB_PATH)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE email = ?', (email,))
        conn.commit()
        conn.close()

class Role:
    DB_PATH = "database.db"

    @staticmethod
    def add_role(role_name, can_delete_user, can_assign_admin, can_assign_organizer, can_assign_gen_roles, can_access_admin_page):
        conn = sqlite3.connect(Role.DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT role_name FROM roles WHERE role_name = ?', (role_name,))
        if cursor.fetchone() is None:
            cursor.execute('''
                INSERT INTO roles (role_name, can_delete_user, can_assign_admin, can_assign_organizer, can_assign_gen_roles, can_access_admin_page)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (role_name, can_delete_user, can_assign_admin, can_assign_organizer, can_assign_gen_roles, can_access_admin_page))
            conn.commit()
        conn.close()

class DocumentModel:
    DB_PATH = "database.db"

    @staticmethod
    def add_document(title, content):
        conn = sqlite3.connect(DocumentModel.DB_PATH)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO documents (title, content) VALUES (?, ?)', (title, content))
        conn.commit()
        conn.close()

    @staticmethod
    def get_all_documents():
        conn = sqlite3.connect(DocumentModel.DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT title, content FROM documents')
        documents = cursor.fetchall()
        conn.close()
        return documents

# Initialize the database and add default roles
User.initialize_db()
Role.add_role("Organizer", True, True, True, True, True)
Role.add_role("Admin", True, False, False, True, True)
Role.add_role("Campaign Coordinator", False, False, False, True, True)
Role.add_role("Member", False, False, False, False, False)

# Delete old databases
if os.path.exists("users.db"):
    os.remove("users.db")
if os.path.exists("roles.db"):
    os.remove("roles.db")