# Python program to implement client side of chat room.

import sqlite3
import socket
import bcrypt
from tkinter import *
from threading import *
import tkinter as tk
import time
import os.path



# Definition of the client class
class Client:
    # Username and password
    def __init__(self):
        self.username = ""
        self.password = ""
        self.mute = False

    # Main function of the class handle request which processes the request before sending it to server
    def sendRequest(self, username):
        # Connect to server on the designated address
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host = "127.0.0.1"
        port = 12345
        client_socket.connect((host, port))

        # User display window
        messageWindow = tk.Tk()
        messageWindow.title("Message Interface of " + username)

        messageEntry = tk.Text(messageWindow, height=10, width=40)
        messageEntry.pack(pady=10)

        responseField = tk.Text(messageWindow, height=10, width=40)
        responseField.pack(pady=10)
        responseField.config(state="disabled")

        # Function to send the message to user with designated messqage divider for the server to separate the username and the message
        def sendMessage():
            message = messageEntry.get("1.0", "end-1c")
            newmessage = username + "usersplit" + message
            client_socket.sendall(newmessage.encode("utf-8"))
            messageEntry.delete("1.0", "end")

        # Basic function for recieving server replies and messages, only broadcasting them to the user if mute == False
        def receiveMessage():
            data = client_socket.recv(1024)
            if self.mute == False:
                response = data.decode("utf-8")
                responseField.config(state="normal")
                responseField.insert("end", response + "\n")
                responseField.config(state="disabled")

        # Refreshing thread for constantly reciving responses from the server independentatly of sending
        def refresh():
            while True:
                receiveMessage()
                time.sleep(3)

        updater = Thread(target=refresh)
        updater.start()

        # Send message button
        sendButton = tk.Button(messageWindow, text="Send", command=sendMessage)
        sendButton.pack(pady=10)

        # File sending function, transfering the file in parts to the server
        def sendFile():
            fileName = fileEntry.get()
            check = fileName.split(".")
            # Prepare the message for the server to switch to file processing mode on the server side.
            serverMessage = username + "usersplit" + "/sendFileToServer"
            if (check[1] == "docx" or check[1] == "pdf" or check[1] == "jpeg") and os.path.isfile(fileName):
                client_socket.send(serverMessage.encode("utf-8"))
                client_socket.send(fileName.encode())
                with open(fileName, "rb") as file:
                    fileData = file.read()
                    client_socket.send(fileData)
                    time.sleep(1)
                    # A final snippet of data to indciate that the entrie file has been sent for the server
                    client_socket.sendall(b"Finished transfering.")

            else:
                # Bad file type error handling
                client_socket.send(serverMessage.encode("utf-8"))
                fileName = "File type not supported or file not found."
                client_socket.send(fileName.encode("utf-8"))

        # File sending buttons and labels for the display
        fileLabel = tk.Label(messageWindow, text="File Name:")
        fileLabel.pack()
        fileEntry = tk.Entry(messageWindow)
        fileEntry.pack()
        fileButton = tk.Button(messageWindow, text="Send File", command=sendFile)
        fileButton.pack(pady=10)

        # Toggles server responses being sent to user, including notifications of other users sending messages
        def toggleMute():
            self.mute = not self.mute
            if self.mute:
                muteButton.config(text="Unmute")
            else:
                muteButton.config(text="Mute")

        muteButton = tk.Button(messageWindow, text="Mute", command=toggleMute)
        muteButton.pack(pady=10)

        # Exit button for the client, allowing them to disconnect from the server and advance the server queue.
        def exitClient():
            self.mute = False
            client_socket.sendall((username + "usersplit" + "/exit").encode("utf-8"))
            client_socket.close()
            messageWindow.destroy()

        exitButton = tk.Button(messageWindow, text="Exit", command=exitClient)
        exitButton.pack(pady=10)

        messageWindow.mainloop()

    # Register method which takes the user inputs and writes them to the database after encrypting the password
    def registerUser(self, username, password):
        conn = sqlite3.connect("users.db")
        c = conn.cursor()

        c.execute(
            """CREATE TABLE IF NOT EXISTS users
                    (username text, password text)"""
        )

        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        if c.fetchone() is not None:
            print("Username already taken. Data not saved to database.")
        else:
            hashed_password = hashPass(password)
            c.execute("INSERT INTO users VALUES (?, ?)", (username, hashed_password))

            conn.commit()
            conn.close()

    # Login method which takes the user inputs and compares them to data stored on the database to verify the inputs
    def loginUser(self, username, password):
        conn = sqlite3.connect("users.db")
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


# Basic password hashing function
def hashPass(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt)


# Basic comparator function to compare input password to hashed version
def verifyPass(password, hashed_password):
    return bcrypt.checkpw(password.encode(), hashed_password)


# User login display, promoting the user to either login or register a new account
def loginDisplay():
    global new_client

    # Display and label set up
    clientDisplay = tk.Tk()
    clientDisplay.title("Client Interface")

    greetingLable = Label(
        clientDisplay, text="Welcome to your chatting application!", fg="black"
    )
    greetingLable.pack(pady=20)

    buttonFrame = Frame(clientDisplay)
    buttonFrame.pack(pady=20)

    # A secondary window using Toplevel in order for the user to input their credentials either for logging in or registering
    def userDataPrompt():
        userData = tk.Toplevel(clientDisplay)
        userData.title("Your login credentials")

        usernameLabel = Label(userData, text="Username:", fg="black")
        usernameLabel.pack()
        usernameEntry = Entry(userData)
        usernameEntry.pack()

        passwordLabel = Label(userData, text="Password:", fg="black")
        passwordLabel.pack()
        passwordEntry = Entry(userData, show="*")
        passwordEntry.pack()

        # Collect entries and destroy additional window
        def buttonPress():
            new_client.username = usernameEntry.get()
            new_client.password = passwordEntry.get()
            userData.quit()
            userData.destroy()

        enterButton = Button(userData, text="Enter Data", command=buttonPress)
        enterButton.pack()
        userData.mainloop()

    # Register and login functions, potentially will be migrated to the server, current implemintation is sloely for the proof of encryption
    # The genuine encryption of user data should be more secure but works in context of the coursework
    def registerButton():
        userDataPrompt()
        new_client.registerUser(new_client.username, new_client.password)

    # After confirming data, initialise the first request
    def loginButton():
        userDataPrompt()
        if new_client.loginUser(new_client.username, new_client.password):
            clientDisplay.destroy()
            new_client.sendRequest(new_client.username)

    # Create the login button
    login_button = Button(buttonFrame, text="Login", command=loginButton)
    login_button.pack(side=LEFT, padx=10)

    # Create the register button
    register_button = Button(buttonFrame, text="Register", command=registerButton)
    register_button.pack(side=LEFT, padx=10)

    clientDisplay.mainloop()


if __name__ == "__main__":
    new_client = Client()

    loginDisplay()
