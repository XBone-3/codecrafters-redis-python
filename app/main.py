import socket  # noqa: F401
import threading
import time

GLOBAL_STORE = {}
GLOBAL_STORE_EXPIRY = {}

lock = threading.Lock()

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

def clean_expired_keys():
    now = time.time() * 1000  # current time in milliseconds
    expired_keys = [key for key, expiry in GLOBAL_STORE_EXPIRY.items() if expiry <= now]
    for key in expired_keys:
        with lock:
            GLOBAL_STORE.pop(key, None)
            GLOBAL_STORE_EXPIRY.pop(key, None)     
    
def handle_command(parts):
    global GLOBAL_STORE
    if not parts:
        return b""
    
    command = parts[0].upper()
    if command == "PING":
        return b"+PONG\r\n"
    elif command == "ECHO" and len(parts) > 1:
        arg = parts[1]
        return f"${len(arg)}\r\n{arg}\r\n".encode()
    elif command == "SET" and len(parts) >= 3:
        key, value = parts[1], parts[2]
        expiry_time = None
        if len(parts) == 5:
            if parts[3].upper() == "PX":
                try:
                    time_in_ms = int(parts[4])
                    expiry_time = time.time() * 1000 + time_in_ms  # current time in ms + expiry
                except ValueError:
                    pass
            elif parts[3].upper() == "EX":
                try:
                    time_in_s = int(parts[4])
                    expiry_time = time.time() * 1000 + (time_in_s * 1000)  # current time in ms + expiry
                except ValueError:
                    pass
        with lock:
            GLOBAL_STORE[key] = value
            if expiry_time:
                GLOBAL_STORE_EXPIRY[key] = expiry_time
            elif key in GLOBAL_STORE_EXPIRY:
                GLOBAL_STORE_EXPIRY.pop(key, None)
        return b"+OK\r\n"
    elif command == "GET" and len(parts) > 1:
        key = parts[1]
        with lock:
            clean_expired_keys()
            value = GLOBAL_STORE.get(key)
        if value is None:
            return b"$-1\r\n"
        else:
            return f"${len(value)}\r\n{value}\r\n".encode()
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
