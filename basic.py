import socketserver

class EchoRequestHandler(socketserver.BaseRequestHandler):

    def handle(self):
        # Echo the back to the client
        data = self.request.recv(1024)
        self.request.send(data)
        return

if __name__ == '__main__':
    import socket
    import threading

    address = ('localhost', 0) # let the kernel give us a port
    server = socketserver.TCPServer(address, EchoRequestHandler)
    ip, port = server.server_address # find out what port we were given

    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()

    # Connect to the server
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ip, port))

    # Send the data
    message = bytes('Hello, world', 'utf-8')
    print(f'Sending : {message}')
    len_sent = s.send(message)

    # Receive a response
    response = s.recv(len_sent)
    print(f'Received: {response}')

    # Clean up
    s.close()
    server.socket.close()
    server.shutdown()
    server.server_close()