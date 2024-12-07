import socket
import ssl
import sys
import os

def send_file(server_ip, server_port, file_path):
    """Send a file to the server over TLS.
    
    Args:
        server_ip (str): IP address of the server.
        server_port (int): Port number of the server.
        file_path (str): Path of the file to be sent.
    """

    # Ensure that the given file exists
    assert os.path.exists(file_path), "File not found."
    
    # Create a TCP/IP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.settimeout(30)  # 30 seconds timeout
    
    try:
        # Create SSL context with strong security settings
        context = ssl.create_default_context()
        context.check_hostname = False  # For self-signed certificates
        context.verify_mode = ssl.CERT_NONE  # For self-signed certificates
        
        # For production, verify certificates:
        # context.verify_mode = ssl.CERT_REQUIRED
        # context.load_verify_locations("path_to_ca_cert.pem")
        
        # Wrap the socket with TLS
        secure_socket = context.wrap_socket(client_socket, server_hostname=server_ip)
        
        # Connect to the server
        secure_socket.connect((server_ip, server_port))
        print(f"Connected to server at {server_ip}:{server_port}")
        print(f"Using cipher: {secure_socket.cipher()}")
        print(f"TLS version: {secure_socket.version()}")

        # Extract file name from path
        file_name = file_path.split('/')[-1]
        
        # Get file size for progress reporting
        file_size = os.path.getsize(file_path)
        bytes_sent = 0
        
        # Send the length of the file name to the server
        name_length = len(file_name.encode())
        secure_socket.sendall(name_length.to_bytes(4, byteorder='big'))
        
        # Send the actual file name
        secure_socket.sendall(file_name.encode())
        
        # Open and send file
        with open(file_path, 'rb') as file:
            while True:
                data = file.read(1024)
                if not data:
                    break
                secure_socket.sendall(data)
                bytes_sent += len(data)
                # Print progress
                progress = (bytes_sent / file_size) * 100
                print(f"\rProgress: {progress:.1f}% ({bytes_sent}/{file_size} bytes)", end='')
            print()  # New line after progress

        print("File sent successfully.")

    except ssl.SSLError as e:
        print(f"SSL Error: {e}")
    except ConnectionError as e:
        print(f"Connection error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'secure_socket' in locals():
            try:
                secure_socket.shutdown(socket.SHUT_RDWR)
            except:
                pass
            secure_socket.close()
        print(f"Connection to {server_ip}:{server_port} closed.")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: SecureNetFileXferClient.py <SERVER_IP> <SERVER_PORT> <FILE_PATH>")
        sys.exit(1)

    server_ip = sys.argv[1]
    
    try:
        server_port = int(sys.argv[2])
        assert 1024 <= server_port <= 65535, "Port number should be between 1024 and 65535."

        file_path = sys.argv[3]
        send_file(server_ip, server_port, file_path)
    except ValueError:
        print("Port should be a number.") 