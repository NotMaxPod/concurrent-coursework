# Basic implemintation of web server and client as show o nhttps://pandeyshikha075.medium.com/building-a-chat-server-and-client-in-python-with-socket-programming-c76de52cc1d5
# This structure was closely followed and will be modified to fit the coursework
import socket 
import sqlite3
import threading
import datetime
import time
from cryptography.fernet import Fernet

#lim = threading.Semaphore(3)
sem_counter = 0
que = {}
connected = {}

class Server():
    def __init__(self):
        # Key generate with Fernet.generate_key()
        self.key = b'qcF8OL2wPTO7Ic7Wr3pUhwjRfdVf4YDJmgzf57IGRWs='
        self.mute = False

    # Handle the request sent to by the client to the server
    def handleRequest(self, client_socket, client_address):
        global sem_counter

        while True:

            data = client_socket.recv(1024)
            if not data:
                break
            message = data.decode('utf-8')
            username, message = message.split('usersplit')
            response = "Empty"

            if (len(connected) < 3) and (client_socket not in connected.values()):
                connected[client_address] = client_socket
                sem_counter+=1
                print("Added to connected")
            
            elif len(connected) > 2:
                if (client_socket not in que.keys()) and (client_socket not in connected.values()):
                    que[client_socket] = time.time()
                    print("Added to que.")
                elif client_socket in que.keys():
                    waitingTime = time.time() - que[client_socket]
                    response = f"Waiting in queue for {waitingTime} seconds."
            
            elif len(connected) < 3 and client_socket in que.keys():
                del que[client_socket]
                connected[client_address] = client_socket
                response = message
                print("removed from que")
            
            # Client is not in queue, process message
            if message == "/exit":
                # Remove client from connected clients
                del connected[client_address]
                break
            elif message == "/mute":
                if self.mute:
                    self.mute = False
                else:
                    self.mute = True
            elif self.mute:
                response = "Muted."
            elif client_socket in connected.values():
                self.encryptToDb(username, message)
                current_time = datetime.datetime.now()
                hour = current_time.hour
                if hour < 10:
                    hour = '0' + str(hour)
                minute = current_time.minute
                if minute < 10:
                    minute = '0' + str(minute)
                print(f"{username} {current_time.year}/{current_time.month}/{current_time.day} {hour}:{minute}: {message}")
                response = message

            # Send response back to client only if not muted

            client_socket.sendall(response.encode('utf-8'))

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
    global sem_counter

    theServer = Server()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = '127.0.0.1'
    port = 12345
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Server listening on {host}:{port}")

    while True:
        
        client_socket, client_address = server_socket.accept()
        print(que)
                
        print(f"Accepted connection from {client_address}")
        client_handler = threading.Thread(target=theServer.handleRequest, args=(client_socket,client_address,))
        #lim.acquire()
        client_handler.start()

if __name__ == "__main__":
    main()