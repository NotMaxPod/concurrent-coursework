# Basic implemintation of web server and client as show o nhttps://pandeyshikha075.medium.com/building-a-chat-server-and-client-in-python-with-socket-programming-c76de52cc1d5
# This structure was closely followed and will be modified to fit the coursework
import socket 
import sqlite3
import threading
import datetime
import time
import tkinter as tk
from tkinter import scrolledtext
from tkinter import *
from cryptography.fernet import Fernet
import sys

que = {}
connected = {}

class Server():
    def __init__(self):
        # Key generate with Fernet.generate_key()
        self.key = b'qcF8OL2wPTO7Ic7Wr3pUhwjRfdVf4YDJmgzf57IGRWs='
        self.mute = False

    # Handle the request sent to by the client to the server
    def handleRequest(self, client_socket, client_address):

        while True:
            #print(connected)
            data = client_socket.recv(1024)
            if not data:
                break
            message = data.decode('utf-8')
            username, message = message.split('usersplit')

            if message == "/send":
                doneSending = False
                fileName = client_socket.recv(1024)
                if fileName.decode('utf-8') == "File type not supported.":
                    client_socket.sendall(fileName)
                    continue
                fileName = username.encode('utf-8') + fileName
                file = open(fileName, "wb")
                newFileBytes = b""
                while not doneSending:
                    fileData = client_socket.recv(1024)
                    if fileData == b"Finished transfering." or fileData == b'':
                        doneSending = True
                        break
                    else:
                        newFileBytes += fileData
                self.encryptToDb(username, fileData.decode(), "File.")
                file.write(newFileBytes)
                file.close()
                print(username, "has sent a file to the server.")
                client_socket.send("File sent to server.".encode('utf-8'))
                continue

            response = self.manageUsers(client_socket, username, message)
            
            # Client is not in queue, process message
            if message == "/exit":
                # Remove client from connected clients
                del connected[client_socket]
                break

            #Update current status of mute flag
            elif message == "/mute":
                if self.mute:
                    self.mute = False
                else:
                    self.mute = True
            if self.mute:
                response = "Muted."
            elif client_socket in connected.keys():
                self.encryptToDb(username, message, "Chat Message.")
                current_time = datetime.datetime.now()
                hour = current_time.hour
                if hour < 10:
                    hour = '0' + str(hour)
                minute = current_time.minute
                if minute < 10:
                    minute = '0' + str(minute)
                message = f"{username} {current_time.year}/{current_time.month}/{current_time.day} {hour}:{minute}: {message}"
                print(message)
                response = "Message sent to server."

                for x in connected.keys():
                    #print(client_socket)
                    if x != client_socket:
                        #print(x)
                        clients = f"{username} sent a message!"
                        x.send(clients.encode())

                self.chatText.insert(tk.END, message + "\n")
                self.chatText.see(tk.END)

    

            client_socket.sendall(response.encode('utf-8'))

        client_socket.close()

    def manageUsers(self, client_socket, username, message):
        response = "Empty"
        if (len(connected) < 3) and (client_socket not in connected.keys()):
                connected[client_socket] = username
                #print("Added to connected")
            
        elif len(connected) > 2:
            if (client_socket not in que.keys()) and (client_socket not in connected.keys()):
                que[client_socket] = time.time()
                response = "The server is current at maximum capcity, you have been added to the que."
                #print("Added to que.")

            elif client_socket in que.keys():
                waitingTime = time.time() - que[client_socket]
                response = f"Waiting in queue for {waitingTime} seconds."
                #print("in que")
            
        elif len(connected) < 3 and client_socket in que.keys():
                del que[client_socket]
                connected[client_socket] = username
                response = message
                #print("removed from que")

        return response
    def encryptToDb(self, username, message, message_type):

        fer = Fernet(self.key)

        encrypted = fer.encrypt(message.encode('utf-8'))

        conn = sqlite3.connect('messages.db')
        c = conn.cursor()

        c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (username text, message text, message_type)''')
        
        c.execute("INSERT INTO messages VALUES (?, ?, ?)", (username, encrypted, message_type,))

        conn.commit()
        conn.close()

    def serverDisplay(self):
        self.chatWindow = tk.Tk()
        self.chatWindow.title("Server Chat")
        self.chatText = scrolledtext.ScrolledText(self.chatWindow, width=100, height=50)
        self.chatText.pack(padx=10, pady=10)

        self.chatText.mainloop()


    def boot(self, server_socket):
        while True:
            client_socket, client_address = server_socket.accept()
            print(f"Accepted connection from {client_address}")
            client_handler = threading.Thread(target=self.handleRequest, args=(client_socket,client_address,))
            client_handler.start()


def main():

    theServer = Server()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = '127.0.0.1'
    port = 12345

    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Server listening on {host}:{port}")

    serverThread = threading.Thread(target=theServer.boot, args=(server_socket,))
    serverThread.start()

    theServer.serverDisplay()

    while True:
        
        client_socket, client_address = server_socket.accept() 
        print(f"Accepted connection from {client_address}")
        clientThread = threading.Thread(target=theServer.handleRequest, args=(client_socket,client_address,))
        clientThread.start()


if __name__ == "__main__":
    main()

