# @author Joao Felipe Ribeiro Neves - 61899
# @author Manuel Maria Ledo Fernandes Garrido de Figueiredo - 68264

import socket
import threading
import pickle
import sys
import os

BUFFER_SIZE = 512
DAT = 3
ACK = 4

# ---- Auxiliary functions  ----
def send_packet(conn, packet):
    #prefixed the sizebyte to not crash the dir command(both in the first try and 2nd) 
    data = pickle.dumps(packet)
    conn.send(len(data).to_bytes(4, "big") + data)

def recv_packet(conn):
    #receives the prefixed sizebyte to not crash the dir command
    raw_size = conn.recv(4)
    if not raw_size:
        return None
    size = int.from_bytes(raw_size, "big")
    received = b""
    while len(received) < size:
        chunk = conn.recv(size - len(received))
        if not chunk:
            return None
        received += chunk
    return pickle.loads(received)



def handle_client(conn, addr):
    print(f"CONNECT TO {addr}")

    # greeting deve ser um pacote DAT
    self_IP = socket.gethostbyname(socket.gethostname())
    greeting_msg = {
        "opcode": 3,
        "block": 0,
        "size": len(f"Welcome to "+ self_IP +" file server"),
        "data": f"Welcome to "+ self_IP +" file server"
    }
    send_packet(conn, greeting_msg)

    # pdf says that it need to have those verifications
    try:
        ack = recv_packet(conn)
        if ack != "ACK":
            conn.close()
            return
    except Exception:
        conn.close()
        return

    while True:
        try:
            packet = recv_packet(conn)
            if not packet: 
                break

            # closes only this client
            if isinstance(packet, dict) and packet.get("opcode") == "END":
                conn.close()
                break
            
            elif packet.get("opcode") == "RRQ":
                if packet.get("filename") != "":
                    filename = packet.get("filename")
                    try:
                        with open(filename, "rb") as file:
                            block_num = 1
                            while True:
                                chunk = file.read(BUFFER_SIZE)
                                if not chunk:
                                    break
                                send_packet(conn, {
                                    "opcode": DAT,   # DAT
                                    "block": block_num,
                                    "size": len(chunk),
                                    "data": chunk   
                                })
                                block_num += 1
                        # bloco final vazio
                        send_packet(conn, {
                            "opcode": DAT,
                            "block": block_num,
                            "size": 0,
                            "data": b""
                        })
                        print("file transfered")
                    except FileNotFoundError:
                        send_packet(conn, {
                            "opcode": "ERR",
                            "msg": "File not found"
                        })     

                else:
                        dir_path = "."
                        if not os.path.exists(dir_path):
                            os.makedirs(dir_path)

                        res = [f for f in os.listdir(dir_path)
                            if os.path.isfile(os.path.join(dir_path, f))]
                        
                        block_num = 1
                        for fname in res: 
                            send_packet(conn, {
                                "opcode": DAT,
                                "block": block_num,
                                "size": len(fname.encode("ascii")),
                                "data": fname   # imprime string no cliente
                            })
                            reply = recv_packet(conn)
                            if reply.get("opcode") != ACK and reply.get("block")== block_num:
                                conn.close()
                                break
                            block_num += 1

                        # fim da listagem → bloco vazio
                        send_packet(conn, {
                            "opcode": DAT,
                            "block": block_num,
                            "size": 0,
                            "data": ""
                        })
                        if reply.get("opcode") != ACK and reply.get("block")== block_num:
                            conn.close()
                            break

        # client err, ver se nao eh preciso ter msg de erro
        except Exception as e:
            print(e)
            conn.close()
            break

def main():
    if len(sys.argv) != 2:
        print("python server.py <server_port>")
        return

    server_port = int(sys.argv[1])

    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(("0.0.0.0", server_port))  
        server_socket.listen(5)
        print("Server is running")
    except Exception as e:
        print("Unable to start server:", e)
        return

    while True:
        conn, addr = server_socket.accept()
        # cria uma thread para esse client
        client_thread = threading.Thread(target=handle_client, args=(conn, addr))
        client_thread.start()

if __name__ == "__main__":
    main()
