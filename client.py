# Python program to implement client side of chat room. 

from cryptography.fernet import Fernet
import threading
import socket 
import bcrypt
 
def sendRequest():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = '127.0.0.1'
    port = 12344
    client_socket.connect((host, port))

    while True:
        message = input("Enter your message: ")
        client_socket.sendall(message.encode('utf-8'))
        data = client_socket.recv(1024)
        response = data.decode('utf-8')
        print(f"Server response: {response}")

def makeKey():
    return Fernet.generate_key()

def encryptData(key, message):
    encoding = Fernet(key)
    return encoding.encrypt(message.encode())

def decodeData(key, message):
    encoding = Fernet(key)
    return encoding.decrypt(message).decode()

def hashPass(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt)

def verifyPass(password, hashed_password):
    return bcrypt.checkpw(password.encode(), hashed_password)

def registerNewUser():
    username = input("Enter your username: ")
    password = input("Enter your password: ")
    key = makeKey()

    secureName = encryptData(key, username)
    securePass = hashPass(password)
    return secureName, securePass, key

def loginUser(username, password, key):
    if username == decodeData(key, username):
        if verifyPass(password, password):
            ...

if __name__ == "__main__":
    sendRequest()
