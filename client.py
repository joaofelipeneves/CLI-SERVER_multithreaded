# @author Joao Felipe Ribeiro Neves - 61899
# @author Manuel Maria Ledo Fernandes Garrido de Figueiredo - 68264

import socket
import sys
import pickle
import os

BUFFER_SIZE = 512
DAT = 3
ACK = 4


#same stuff as the server, prefixes the size of the block to not crash dir command
def send_packet(sock, packet):
    data = pickle.dumps(packet)
    sock.send(len(data).to_bytes(4, "big") + data)

def recv_packet(sock):
    raw_size = sock.recv(4)
    if not raw_size:
        return None
    size = int.from_bytes(raw_size, "big")
    received = b""
    while len(received) < size:
        chunk = sock.recv(size - len(received))
        if not chunk:
            return None
        received += chunk
    return pickle.loads(received)

def main():
    if len(sys.argv) != 3:
        print("python client.py <server_ip> <server_port>")
        return

    server_addr = sys.argv[1]

    # assure that the address port HAS to be a number 
    server_port = int(sys.argv[2])

    # stream - tcp
    # datagram - udp
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((server_addr, server_port))
    except Exception:
        #ver se aqui eh necessario
        print("Unable to connect with the server")
        return

    print("Connect to server")

    # greeting é um pacote DAT → mostrar só a mensagem
    greeting_msg = recv_packet(client_socket)
    print(greeting_msg["data"])
    send_packet(client_socket, "ACK")

    # main program has to be in here
    while True:
        try:
            user_input = input("client> ").strip()

            if user_input == "end":
                send_packet(client_socket, {"opcode": "END"})
                client_socket.close()
                print("Connection close, client ended")
                break
            
            elif user_input.startswith("get "):
                parts = user_input.split()
                if len(parts) != 3:
                     print("get <remote_filename> <local_filename>")
                     continue

                remote_filename = parts[1]
                local_filename = parts[2]

                if os.path.exists(local_filename):
                    # print("File alr exists")
                    continue

                send_packet(client_socket, {
                    "opcode": "RRQ",
                    "filename": remote_filename
                })

                with open(local_filename, "wb") as file:
                    while True:
                        packet = recv_packet(client_socket)
                        if not packet:
                            break

                        if packet.get("opcode") == DAT:  
                            if packet["size"] == 0:
                                print("File transfer completed")
                                break
                            else:
                                file.write(packet["data"]) 
                        elif packet.get("opcode") == "ERR":
                            print(packet["msg"])
                            file.close()
                            os.remove(local_filename)
                            break
                        else:
                            break

            elif user_input == "dir":
                send_packet(client_socket, {"opcode": "RRQ", "filename": "" })
                while True:
                        packet = recv_packet(client_socket)
                        if not packet: 

                            break
                        
                        if packet["opcode"] == DAT:
                            #dir acabou
                            if packet["size"] == 0:
                                break
                            else:
                                print(packet["data"])   # imprime string
                                send_packet(client_socket, {"opcode": ACK, "block":  packet["block"]})
                        elif packet.get("opcode") == "ERR":
                                print(packet["msg"])
                                break
                        else:    
                                break
                           
                        
            else:
                print("Unknown command")  

        except KeyboardInterrupt:
            print("\nExiting by keyboard interrupt...")
            client_socket.close()
            break

if __name__ == "__main__":
    main()
