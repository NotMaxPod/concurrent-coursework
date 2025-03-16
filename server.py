import socket
import threading

MAX_DATA_RECV = 65535


# Code to set up the client and server structure, 
# https://pandeyshikha075.medium.com/building-a-chat-server-and-client-in-python-with-socket-programming-c76de52cc1d5
# The following website was used to explain and set up the basic structure

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = '127.0.0.1'
    port = 12345
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Server listening on {host}:{port}")

    while True:
        client_socket, client_address = server_socket.accept()
        print(f"Accepted connection from {client_address}")
        client_handler = threading.Thread(target=handleRequest, args=(client_socket,))
        client_handler.start()

if __name__ == "__main__":
    main()

    def handleRequest(clientsoc):
        while True:
            client_data = clientsoc.recieve(1024)
            if not client_data:
                break
            client_message = client_data.deocde("utf-8")
            print("Recieved Message: ", client_message)
            response = "Server received your message: " + client_message
            clientsoc.sendall(response.encode('utf-8'))
        clientsoc.close()