import socket  # noqa: F401
import threading

def parse_command(data: bytes):
    """
    Parse a RESP array like:
    *2\r\n$4\r\nECHO\r\n$3\r\nhey\r\n
    -> ["ECHO", "hey"]
    """
    lines = data.split(b'\r\n')
    if not lines or not lines[0].startswith(b'*'):
        return []
    try:
        num_elements = int(lines[0][1:])
        elements = []
        idx = 1
        for _ in range(num_elements):
            if lines[idx].startswith(b'$'):
                length = int(lines[idx][1:])
                idx += 1
                elements.append((lines[idx][:length]).decode('utf-8'))
            idx += 1
        return elements
    except ValueError:
        return []        
    
def handle_command(parts):
    if not parts:
        return b""
    
    command = parts[0].upper()
    if command == "PING":
        return b"+PONG\r\n"
    elif command == "ECHO" and len(parts) > 1:
        arg = parts[1]
        return f"${len(arg)}\r\n{arg}\r\n".encode()
    else:
        return b"-ERR unknown command\r\n"

def handle_connection(connection):
    try:
        while True:
            data = connection.recv(4096)
            if not data:
                break

            parts = parse_command(data)
            response = handle_command(parts)
            if response:
                connection.sendall(response)
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
            thread = threading.Thread(target=handle_connection, args=(connection,))
            thread.daemon = True
            thread.start()
    except KeyboardInterrupt:
        print("Shutting down server.")
    finally:
        server_socket.close()
        

if __name__ == "__main__":
    main()
