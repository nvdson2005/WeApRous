"""
daemon.database
~~~~~~~~~~~~~~~~~
This is a customized module for easily managing user credentials
"""
import csv

DATABASE_FILE = '../db/database.csv'
def register_user(username, password):
    if check_user_exists(username):
        print("[ABORT]: User already exists.")
        return
    with open(DATABASE_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([username, password])

def check_user_exists(username):
    with open(DATABASE_FILE, mode='r') as file:
        reader = csv.reader(file)
        for row in reader:
            if row[0] == username:
                return True
    return False

def login_user(username, password):
    with open(DATABASE_FILE, mode='r') as file:
        reader = csv.reader(file)
        for row in reader:
            if row[0] == username and row[1] == password:
                return True
    return False