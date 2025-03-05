import os
import tftpy

def main():
    # Directory where files will be served from
    serve_directory = './configs'
    
    # Create the serve directory if it doesn't exist
    if not os.path.exists(serve_directory):
        os.makedirs(serve_directory)
    
    try:
        # Create TFTP server
        server = tftpy.TftpServer(serve_directory)
        
        # Configuration parameters
        host = '192.168.100.1'  # Listen on all available interfaces
        port = 69  # Standard TFTP port
        
        print(f"Starting TFTP server on {host}:{port}")
        print(f"Serving files from: {os.path.abspath(serve_directory)}")
        
        # Start the server (blocking call)
        server.listen(host, port)
    
    except PermissionError:
        print("Error: Need root/admin privileges to bind to port 69")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    main()