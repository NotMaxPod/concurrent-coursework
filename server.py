# Basic implemintation of web server and client as show o nhttps://pandeyshikha075.medium.com/building-a-chat-server-and-client-in-python-with-socket-programming-c76de52cc1d5
# This structure was closely followed and will be modified to fit the coursework
import socket 
import sqlite3
import threading
import datetime
from cryptography.fernet import Fernet

lim = threading.Semaphore(3)

class Server():
    def __init__(self):
        # Key generate with Fernet.generate_key()
        self.key = b'qcF8OL2wPTO7Ic7Wr3pUhwjRfdVf4YDJmgzf57IGRWs='
    # Handle the request sent to by the client to the server
    def handleRequest(self, client_socket):
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            message = data.decode('utf-8')
            username, message = message.split('usersplit')
            if message == "/exit":
                break
            self.encryptToDb(username, message)
            current_time = datetime.datetime.now()
            hour = current_time.hour
            if hour < 10:
                hour = '0' + str(hour)
            minute = current_time.minute
            if minute < 10:
                minute = '0' + str(minute)
            print(f"{username} {current_time.year}/{current_time.month}/{current_time.day} {hour}:{minute}: {message}")
            response = "Server received your message: " + message
            client_socket.sendall(response.encode('utf-8'))
        lim.release()
        client_socket.close()

    def encryptToDb(self, username, message):

        fer = Fernet(self.key)

        encrypted = fer.encrypt(message.encode('utf-8'))

        conn = sqlite3.connect('messages.db')
        c = conn.cursor()

        c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (username text, message text)''')
        
        c.execute("INSERT INTO messages VALUES (?, ?)", (username, encrypted))

        conn.commit()
        conn.close()


def main():
    theServer = Server()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = '127.0.0.1'
    port = 12345
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Server listening on {host}:{port}")

    while True:
        client_socket, client_address = server_socket.accept()
        print(f"Accepted connection from {client_address}")
        client_handler = threading.Thread(target=theServer.handleRequest, args=(client_socket,))
        lim.acquire()
        client_handler.start()

if __name__ == "__main__":
    main()