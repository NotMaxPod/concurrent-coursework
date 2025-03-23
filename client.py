# Python program to implement client side of chat room. 

import sqlite3
import socket 
import bcrypt
from tkinter import*
from threading import *
import tkinter as tk
import time

class Client():

    def __init__(self):
        self.username = ""
        self.password = ""
    
    
    
    def sendRequest(self, username):
            
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host = '127.0.0.1'
        port = 12345
        client_socket.connect((host, port))
        
        messageWindow = tk.Tk()
        messageWindow.title("Message Interface of " + username)

        messageEntry = tk.Text(messageWindow, height=10, width=40)
        messageEntry.pack(pady=10)

        responseField = tk.Text(messageWindow, height=10, width=40)
        responseField.pack(pady=10)
        responseField.config(state="disabled")

        
        
        def sendMessage():
            message = messageEntry.get("1.0", "end-1c")
            newmessage = username + "usersplit" + message
            client_socket.sendall(newmessage.encode('utf-8'))
            messageEntry.delete("1.0", "end")

        def receiveMessage():
            data = client_socket.recv(1024)
            response = data.decode('utf-8')
            responseField.config(state="normal")
            responseField.insert("end", response + "\n")
            responseField.config(state="disabled")

        def refresh():
            while True:
                receiveMessage()
                time.sleep(1)

        updater = Thread(target=refresh)
        updater.start()
        
        sendButton = tk.Button(messageWindow, text="Send", command=sendMessage)
        sendButton.pack(pady=10)

        # Create a file send button
        def sendFile():
            fileName = fileEntry.get()
            check = fileName.split(".")
            serverMessage = username + "usersplit" + "/send"
            if check[1] == "docx" or check[1] == "pdf" or check[1] == "jpeg":
                client_socket.send(serverMessage.encode('utf-8'))
                client_socket.send(fileName.encode())
                with open(fileName, "rb") as file:
                    fileData = file.read()
                    client_socket.send(fileData)
                    time.sleep(1)
                    client_socket.sendall(b"Finished transfering.")
            

            else:
                client_socket.send(serverMessage.encode('utf-8'))
                fileName = "File type not supported."
                client_socket.send(fileName.encode('utf-8'))
                #print("File type not supported.")

        fileLabel = tk.Label(messageWindow, text="File Name:")
        fileLabel.pack()
        fileEntry = tk.Entry(messageWindow)
        fileEntry.pack()
        fileButton = tk.Button(messageWindow, text="Send File", command=sendFile)
        fileButton.pack(pady=10)

        # Create an exit button
        def exitClient():
            client_socket.sendall((username + "usersplit" + "/exit").encode('utf-8'))
            client_socket.close()
            messageWindow.destroy()

        exitButton = tk.Button(messageWindow, text="Exit", command=exitClient)
        exitButton.pack(pady=10)

        

        messageWindow.mainloop()
        '''while True:
            message = input("Enter your message: ")
            newmessage = username + "usersplit" + message
            if message == "/send":
                client_socket.send(newmessage.encode('utf-8'))
                fileName = input("Please enter the file name: ")
                check = fileName.split(".")
                if check[1] == "docx" or check[1] == "pdf" or check[1] == "jpeg":
                    client_socket.send(fileName.encode())
                    with open(fileName, "rb") as file:
                        fileData = file.read()
                        #print(fileData)
                        client_socket.send(fileData)
                        time.sleep(1)
                        client_socket.sendall(b"Finished transfering.")
                        continue
                else:
                    print("File type not supported.")
                    continue
                print("File sent")
                continue
            client_socket.sendall(newmessage.encode('utf-8'))

            # Client termination if termibation command entered
            if message == "/exit":
                client_socket.close()
                break
            data = client_socket.recv(1024)
            response = data.decode('utf-8')
            if response == "Muted." or response == "Empty":
                continue
            print(f"Sent to server: {response}")'''

    def registerUser(self, username,password):
        conn = sqlite3.connect('users.db')
        c = conn.cursor()

        c.execute('''CREATE TABLE IF NOT EXISTS users
                    (username text, password text)''')
        
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        if c.fetchone() is not None:
            print("Username already taken. Data not saved to database.")
        else:
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

def loginDisplay():
    global new_client
    clientDisplay = tk.Tk()
    clientDisplay.title("Client Interface")
    
    greetingLable = Label(clientDisplay, text="Welcome to your chatting application!", fg="black")
    greetingLable.pack(pady=20)

    buttonFrame = Frame(clientDisplay)
    buttonFrame.pack(pady=20)

    def userDataPrompt():
        userData = tk.Toplevel(clientDisplay)
        userData.title("Your login credentials")

        usernameLabel = Label(userData, text="Username:")
        usernameLabel.pack()
        usernameEntry = Entry(userData)
        usernameEntry.pack()

        passwordLabel = Label(userData, text="Password:")
        passwordLabel.pack()
        passwordEntry = Entry(userData, show="*")
        passwordEntry.pack()

        def buttonPress():
            new_client.username = usernameEntry.get()
            new_client.password = passwordEntry.get()
            userData.quit()
            userData.destroy()
            

        
        enterButton = Button(userData, text="Enter Data", command=buttonPress)
        enterButton.pack()
        userData.mainloop()


    def registerButton():
        userDataPrompt()
        new_client.registerUser(new_client.username, new_client.password)

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


