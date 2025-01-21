import os

class User:
    FILE_PATH = "users.txt"

    @staticmethod
    def authenticate(username, password):
        if not os.path.exists(User.FILE_PATH):
            return False
        with open(User.FILE_PATH, "r") as file:
            for line in file:
                stored_username, stored_password = line.strip().split(":")
                if username == stored_username and password == stored_password:
                    return True
        return False

    @staticmethod
    def create(username, password):
        if os.path.exists(User.FILE_PATH):
            with open(User.FILE_PATH, "r") as file:
                for line in file:
                    stored_username, _ = line.strip().split(":")
                    if username == stored_username:
                        return False
        with open(User.FILE_PATH, "a") as file:
            file.write(f"{username}:{password}\n")
        return True
