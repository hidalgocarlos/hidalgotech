#!/usr/bin/env python3
"""
Create or reset admin user.
Usage: python setup_admin.py <username> <password>
       python setup_admin.py <username> <password> --reset   # cambia contraseña si ya existe
Or from Docker: docker exec portal python setup_admin.py admin TuPasswordSeguro123!
               docker exec portal python setup_admin.py admin NuevaClave --reset
"""
import sys
import os

# Ensure app is on path when run from project root or from /app in container
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.auth import hash_password
from app.dao.user_dao import UserDAO


def main():
    if len(sys.argv) < 3:
        print("Usage: python setup_admin.py <username> <password> [--reset]")
        sys.exit(1)
    username = sys.argv[1]
    password = sys.argv[2]
    reset = len(sys.argv) > 3 and sys.argv[3] == "--reset"
    dao = UserDAO()
    user = dao.get_by_username(username)
    if user:
        if reset:
            dao.update_password(username, hash_password(password))
            print(f"Contraseña de '{username}' actualizada.")
        else:
            print(f"El usuario '{username}' ya existe. Usa --reset para cambiar la contraseña.")
        sys.exit(0)
    dao.create_user(username, hash_password(password))
    print(f"Usuario '{username}' creado correctamente.")


if __name__ == "__main__":
    main()
