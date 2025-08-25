import socket
from MMSI.modules.symbolic_bridge import handle_symbolic_input

HOST = '0.0.0.0'  # Listen on all interfaces
PORT = 65432      # Port to listen on

print("🔌 Listening for symbolic phrases from Aletheia...")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    conn, addr = s.accept()
    with conn:
        print(f"📡 Connection from {addr}")
        data = conn.recv(1024).decode('utf-8').strip()
        if data:
            print(f"📥 Received symbolic phrase: {data}")
            handle_symbolic_input(data)
