import socket
import ssl
import sys
import select

def receive_data(secure_client, length):
    """Receive exact amount of data from the client.
    
    Args:
        secure_client: The secure socket connection
        length: Number of bytes to receive
        
    Returns:
        The received data
    """
    data = b''
    while len(data) < length:
        try:
            chunk = secure_client.recv(min(length - len(data), 1024))
            if not chunk:  # Connection closed by client
                raise ConnectionError("Connection closed by client")
            data += chunk
        except ssl.SSLWantReadError:
            continue
    return data

def start_server(port):
    """Start the secure file transfer server using TLS.
    
    Args:
        port (int): Port on which the server should listen.
    """

    # Assert port is a valid value
    assert 1024 <= port <= 65535, "Port number should be between 1024 and 65535."

    # Create the server socket using IPv4 and TCP
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('localhost', port))
    server_socket.listen(5)  # Listen with a backlog of 5 connections
    
    # Set up SSL context with strong security settings
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile='cert.pem', keyfile='key.pem')
    
    # Configure TLS settings for better security
    context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1  # Disable older TLS versions
    context.set_ciphers('ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384')
    
    print(f"Secure server listening on port {port}...")

    while True:
        try:
            client_socket, client_address = server_socket.accept()
            print(f"Accepted connection from {client_address}")
            
            # Set socket timeout
            client_socket.settimeout(30)  # 30 seconds timeout
            
            # Wrap the socket with TLS
            secure_client = context.wrap_socket(client_socket, server_side=True)
            print(f"TLS connection established with {client_address}")
            print(f"Using cipher: {secure_client.cipher()}")
            print(f"TLS version: {secure_client.version()}")

            try:
                # First, receive the 4-byte file name length
                name_length_data = receive_data(secure_client, 4)
                file_name_length = int.from_bytes(name_length_data, byteorder='big')

                # Now, receive the actual file name
                file_name = receive_data(secure_client, file_name_length).decode()
                print(f"Receiving file named: {file_name}\n" + "*" * 80)

                # Receive the file content and save it
                with open(file_name, 'wb') as file:
                    while True:
                        # Use select to check for data availability
                        ready = select.select([secure_client], [], [], 5.0)  # 5 seconds timeout
                        if not ready[0]:  # Timeout
                            continue
                            
                        try:
                            data = secure_client.recv(1024)
                            if not data:  # EOF received
                                break
                            file.write(data)
                        except ssl.SSLWantReadError:
                            continue
                        except ssl.SSLError as e:
                            if 'UNEXPECTED_EOF_WHILE_READING' in str(e):
                                break
                            raise
                        
                print(f"Received file {file_name} successfully")

            except ConnectionError as e:
                print(f"Connection error: {e}")
            except Exception as e:
                print(f"Error while receiving file: {e}")
            finally:
                try:
                    secure_client.shutdown(socket.SHUT_RDWR)
                except:
                    pass
                secure_client.close()
                print(f"Connection with {client_address} closed.")

        except ssl.SSLError as e:
            print(f"SSL Error: {e}")
            if 'client_socket' in locals():
                try:
                    client_socket.shutdown(socket.SHUT_RDWR)
                except:
                    pass
                client_socket.close()
        except Exception as e:
            print(f"Error: {e}")
            if 'client_socket' in locals():
                try:
                    client_socket.shutdown(socket.SHUT_RDWR)
                except:
                    pass
                client_socket.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: SecureNetFileXferServer.py <PORT>")
        sys.exit(1)

    try:
        port = int(sys.argv[1])
        start_server(port)
    except ValueError:
        print("Port should be a number.") 