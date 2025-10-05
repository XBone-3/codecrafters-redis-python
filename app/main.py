import socket  # noqa: F401
import threading

def handle_connection(connection):
    try:
        while True:
            data = connection.recv(4096)
            if not data:
                break
            connection.sendall(b"+PONG\r\n")
    except ConnectionResetError:
        print("Connection was reset by the client.")
    finally:
        connection.close()


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    # Uncomment this to pass the first stage
    #
    # server_socket = socket.create_server(("localhost", 6379), reuse_port=True)
    server_socket = socket.create_server(("localhost", 6379))
    try:
        while True:
            connection, _ = server_socket.accept() # wait for client

            # implementing threading to handle multiple clients simultaneously
            thread = threading.Thread(target=handle_connection, args=(connection))
            thread.daemon = True
            thread.start()
    except KeyboardInterrupt:
        print("Shutting down server.")
    finally:
        server_socket.close()
        

if __name__ == "__main__":
    main()
