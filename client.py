# Python program to implement client side of chat room. 

import sqlite3
import threading
import socket 
import bcrypt
import tkinter as tk

class Client():
 
    def sendRequest(self, username):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host = '127.0.0.1'
        port = 12345
        client_socket.connect((host, port))

        while True:
            message = input("Enter your message: ")
            newmessage = username + "usersplit" + message
            client_socket.sendall(newmessage.encode('utf-8'))
            if message == "/exit":
                client_socket.close()
                break
            data = client_socket.recv(1024)
            response = data.decode('utf-8')
            print(f"Server response: {response}")

    def registerUser(self, username,password):
        conn = sqlite3.connect('users.db')
        c = conn.cursor()

        c.execute('''CREATE TABLE IF NOT EXISTS users
                    (username text, password text)''')
        
        hashed_password = hashPass(password)

        c.execute("INSERT INTO users VALUES (?, ?)", (username, hashed_password))

        conn.commit()
        conn.close()

    def loginUser(self, username, password):
        conn = sqlite3.connect('users.db')
        c = conn.cursor()

        c.execute("SELECT password FROM users WHERE username = ?", (username,))
        hashed_password = c.fetchone()

        logged_in = False
        if hashed_password is None:
            conn.close()
            return logged_in
        if verifyPass(password, hashed_password[0]):
            logged_in = True
        
        conn.close()
        return logged_in

def hashPass(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt)

def verifyPass(password, hashed_password):
    return bcrypt.checkpw(password.encode(), hashed_password)

if __name__ == "__main__":
    new_client = Client()

    while True:
        userinput = input("Would you like to register (r) or login (l): ")
        if userinput == "r":
            username = input("Enter your username: ")
            password = input("Enter your password: ")
            new_client.registerUser(username, password)

        elif userinput == "l":
            username = input("Enter your username: ")
            password = input("Enter your password: ")

            if new_client.loginUser(username, password):
                break
    new_client.sendRequest(username)
