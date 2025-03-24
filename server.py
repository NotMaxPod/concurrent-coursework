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

# Que and Connected, storing the connections of all user who log into the server. After connections >= 3, all further connections are added to queue.
que = {}
connected = {}


# The server class
class Server:
    def __init__(self):
        # Key generated with Fernet.generate_key()
        self.key = b"qcF8OL2wPTO7Ic7Wr3pUhwjRfdVf4YDJmgzf57IGRWs="

    # Main functions of the server class for processing client requests sent by the user
    def handleRequest(self, client_socket, client_address):
        # Main server loop for constantly recieving data from the user, break if empty
        while True:
            data = client_socket.recv(1024)
            if not data:
                break

            # Decode the message and separate username from user input
            message = data.decode("utf-8")
            username, message = message.split("usersplit")

            # If message sent by the server is of the /send type, intiate file transfering
            if message == "/sendFileToServer":
                # Flag for data reception and file name
                doneSending = False
                fileName = client_socket.recv(1024)
                if fileName.decode("utf-8") == "File type not supported or file not found.":
                    client_socket.sendall(fileName)
                    continue
                # Create new unique file name with the user's name to clearly indicate who sent it
                fileName = username.encode("utf-8") + fileName
                file = open(fileName, "wb")
                newFileBytes = b""
                # Loop for larger files being transfered, when the tag "Finished transfering." or empty bytes are sent, change flag and break loop
                while not doneSending:
                    fileData = client_socket.recv(1024)
                    if fileData == b"Finished transfering." or fileData == b"":
                        doneSending = True
                        break
                    else:
                        newFileBytes += fileData
                # Encrypt the data of the file to database before writing it on the server
                self.encryptToDb(username, fileData.decode(), "File.")
                file.write(newFileBytes)
                file.close()
                # Some background server terminal outputs for debug purposes
                print(username, "has sent a file to the server.")
                # Send response to client
                client_socket.send("File sent to server.".encode("utf-8"))
                continue

            # Call user managing function to refresh queue
            response = self.manageUsers(client_socket, username, message)

            # Client is not in queue, process message

            # Exit message to terminate connection and update currenly connected users
            if message == "/exit":
                # Remove client from connected clients
                del connected[client_socket]
                break

            # The main message processing for basic texts sent in the chat
            elif client_socket in connected.keys():
                # Store message history to database
                self.encryptToDb(username, message, "Chat Message.")

                # Organise current time to print to server.
                current_time = datetime.datetime.now()
                hour = current_time.hour
                if hour < 10:
                    hour = "0" + str(hour)
                minute = current_time.minute
                if minute < 10:
                    minute = "0" + str(minute)

                # Main message print statement
                message = f"{username} {current_time.year}/{current_time.month}/{current_time.day} {hour}:{minute}: {message}"
                print(message)
                response = "Message sent to server."

                # Send notification to all other users from the server that current client sent a message
                for x in connected.keys():
                    if x != client_socket:
                        clients = f"{username} sent a message!"
                        x.send(clients.encode())

                # Update chat
                self.chatText.insert(tk.END, message + "\n")
                self.chatText.see(tk.END)

            # Send response from server to client
            client_socket.sendall(response.encode("utf-8"))

        client_socket.close()

    # User managment method
    def manageUsers(self, client_socket, username, message):
        # Set default response to empty, meaning the server returns no response
        response = "Empty"
        # If connection is free and the current user isn't connected, add them to connection
        if (len(connected) < 3) and (client_socket not in connected.keys()):
            connected[client_socket] = username
            # print("Added to connected")

        # The server is too full, add current client to queue and store their connection time. If already in queue, return waiting time as server response
        elif len(connected) > 2:
            if (client_socket not in que.keys()) and (
                client_socket not in connected.keys()
            ):
                que[client_socket] = time.time()
                response = "The server is current at maximum capcity, you have been added to the queue."
                # print("Added to queue.")

            elif client_socket in que.keys():
                waitingTime = round((time.time() - que[client_socket]), 2)
                response = f"Waiting in queue for {waitingTime} seconds."
                # print("in queue")
        # Connection has decreased and the user is in queue, move user to connected
        elif len(connected) < 3 and client_socket in que.keys():
            del que[client_socket]
            connected[client_socket] = username
            response = message
            # print("removed from queue")

        return response

    # Encryption of files and message history to a designated database
    def encryptToDb(self, username, message, message_type):
        # Retrive encryption key used by the server and apply to message
        fer = Fernet(self.key)
        encrypted = fer.encrypt(message.encode("utf-8"))

        # Open the database and add current message/file to it
        conn = sqlite3.connect("messages.db")
        c = conn.cursor()

        c.execute(
            """CREATE TABLE IF NOT EXISTS messages
                 (username text, message text, message_type)"""
        )

        c.execute(
            "INSERT INTO messages VALUES (?, ?, ?)",
            (
                username,
                encrypted,
                message_type,
            ),
        )

        conn.commit()
        conn.close()

    # Server chat window initalisation
    def serverDisplay(self):
        self.chatWindow = tk.Tk()
        self.chatWindow.title("Server Chat")
        self.chatText = scrolledtext.ScrolledText(self.chatWindow, width=100, height=50)
        self.chatText.pack(padx=10, pady=10)

        self.chatText.mainloop()

    # Boot method to intialise a client thread
    def boot(self, server_socket):
        while True:
            client_socket, client_address = server_socket.accept()
            print(f"Accepted connection from {client_address}")
            client_handler = threading.Thread(
                target=self.handleRequest,
                args=(
                    client_socket,
                    client_address,
                ),
            )
            client_handler.start()


def main():
    # Server initialisation in the main method
    theServer = Server()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = "127.0.0.1"
    port = 12345

    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Server listening on {host}:{port}")

    # Seaparate server booting method due to tkinter not being able to run on non main threads.
    serverThread = threading.Thread(target=theServer.boot, args=(server_socket,))
    serverThread.start()

    theServer.serverDisplay()


if __name__ == "__main__":
    main()
