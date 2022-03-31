import socket
import threading
from settings import AsyncChatSettings

# make one instance of the settings variable.
serverSettings = AsyncChatSettings()

clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
clientSocket.connect((serverSettings.serverIp, serverSettings.serverPort))
clientSocket.setblocking(0)

inp_msg     = ""
inp_flag    = False
connected   = True

# Thread for reading messages from socket, and writing back.
# also this responds for the PING - PONG
def chat_function():
    global clientSocket
    global inp_msg
    global inp_flag
    global connected
    while connected:
        try:
            # Maximum length of inp_msg is 4MB
            data = clientSocket.recv(4096)
            if data == b'':
                print("Connection lost")
                break
            # If this is a PING we send back a PONG (same value 0x01)
            if data == b'\x01':
                clientSocket.send(b'\x01')
            # We received a valid message, just print out on console
            else:
                print(data.decode('utf-8'))
        except:
            # If a new input was typed send it
            if inp_flag:
                inp_flag = False
                clientSocket.sendall(inp_msg.encode("utf-8"))
    
    connected = False
    clientSocket.close()
    print("chat_function closed")

# Thread for getting the input messages
def input_function():
    global inp_msg
    global inp_flag
    global connected
    while connected:
        inp_msg = input("")
        inp_msg += '\n'
        inp_flag = True
        if inp_msg == "\exit\n":
            break
    print("input_function closed")


def main()->None:
    # Create threads
    chatThread = threading.Thread(target=chat_function)
    inputThread = threading.Thread(target=input_function)
    # Start threads
    chatThread.start()
    inputThread.start()

if __name__ == "__main__":
    main()