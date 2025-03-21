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
            
            # Check if client is in queue
            if client_address in que.keys() and sem_counter > 2:
                # Send waiting time to client as response
                waiting_time = time.time() - que[client_address]
                response = f"Waiting in queue for {waiting_time} seconds."
                client_socket.sendall(response.encode('utf-8'))
                # Continue to next iteration, blocking message from being sent to server
                continue
            elif client_address in que.keys() and sem_counter<3:
                del que[client_address]
                connected[client_address] = client_socket
            elif client_address not in que.keys() and (client_address not in connected.keys()):
                    connected[client_address] = client_socket
                    sem_counter+=1
            
            # Client is not in queue, process message
            if message == "/exit":
                break
            elif message == "/mute":
                if self.mute:
                    self.mute = False
                else:
                    self.mute = True
            else:
                self.encryptToDb(username, message)
                current_time = datetime.datetime.now()
                hour = current_time.hour
                if hour < 10:
                    hour = '0' + str(hour)
                minute = current_time.minute
                if minute < 10:
                    minute = '0' + str(minute)
                print(f"{username} {current_time.year}/{current_time.month}/{current_time.day} {hour}:{minute}: {message}")

            # Send response back to client only if not muted
            if self.mute == False:
                response = f"{username} {current_time.year}/{current_time.month}/{current_time.day} {hour}:{minute}: {message}"
            else:
                response = "Muted."
            client_socket.sendall(response.encode('utf-8'))


        sem_counter -= 1
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
        if client_address not in que.keys() and sem_counter > 2:
                que[client_address] = time.time()
        print(que)
                
        print(f"Accepted connection from {client_address}")
        client_handler = threading.Thread(target=theServer.handleRequest, args=(client_socket,client_address,))
        #lim.acquire()
        client_handler.start()

if __name__ == "__main__":
    main()