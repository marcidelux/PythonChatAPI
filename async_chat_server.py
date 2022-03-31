import asyncio
from csv import reader
import re
from settings import AsyncChatSettings
import logging
from datetime import datetime
import time

# Create only one instance of the Settings class. (I should make this singleton.)
mSettings = AsyncChatSettings()

# Setup logging
logging.basicConfig(filename='async_chat_server.log', encoding='utf-8', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S', format='%(asctime)s %(levelname)-8s %(message)s')

ErrMsg = {
    "EMPTY_NAME"            : "Server: Error- Empty name is not allowed.",
    "INVALID_NAME_SYNTAX"   : "Server: Error - Invalid characters at name. Only numbers letters and underscore allowed.",
    "NAME_EXIST"            : "Server: Error - Name already exists. Please give a new one.",
    "INVALID_COMMAND_SYNTAX": "Server: Error - The given command syntax is invalid. Please write \\help for get info.",
}

HelpStr =   """
Async Chat Help:
- First give your name, it can consist only letters and numbers and underscore.
- All messages are broadcasted to all users.
- You can send commands to the server, each command start with an \\ character.
            
Commands:
\\exit - Quits from the chat and disconnects from the server.
\\time - Gives back the current server time
\\priv "name" "Message" - Sends a private message to the user with "name"
\\users - Gives a list of the current users names.
\\help  - Prints out this small helping text.
""".encode('utf-8')

class ClientsHandler():
    # This is a class variable holding all the active clients.
    clients = {}

    def __init__(self, name:str, reader:asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        self.name       = name
        self.writer     = writer
        self.reader     = reader
        self.connected  = True

    # Class function for detecting name validity.
    def check_name(name:str)->tuple[str, bool]:
        #Check if the string is empty
        if name == "":
            return ErrMsg["EMPTY_NAME"], False
        
        # Cut the string by spaces and take the first one, than if its longer than 32 cut the remaining characters.
        firstPart = name.split(" ")[0]
        if len(firstPart) > mSettings.clientNameLen:
            firstPart = firstPart[:mSettings.clientNameLen]
        
        # Now check if only the allowed characters are in the name.
        if re.match("^[A-Za-z0-9_-]*$", firstPart):
            return firstPart, True
        else:
            return ErrMsg["INVALID_NAME_SYNTAX"], False

    async def sendServerTime(self)->None:
        # datetime object containing current date and time
        now = datetime.now()
        dt_string = "Server Time: "+ now.strftime("%Y/%m/%d %H:%M:%S")
        self.writer.write(dt_string.encode())
        await self.writer.drain()

    async def broadcast(self, message:str) -> None:
        for name, client in ClientsHandler.clients.items():
            if name != self.name:
                client.writer.write((self.name + ": " + message).encode("utf-8"))
                await client.writer.drain()

    async def ping(self)->bool:
        self.writer.write(b'\x01')
        await self.writer.drain()
        try:
            rec = await asyncio.wait_for(self.reader.read(1), 1)
            return True
        except asyncio.TimeoutError:
            logging.info(f"Timeout on client: {self.name}")
            return False

    async def start_name_setting(self):
        self.writer.write(HelpStr)
        self.writer.write("\nServer: Please enter your name for joining the chat".encode())
        await self.writer.drain()

        name = ""
        # this is important to detect client disconnect, it seems like than empty messages will arive on stream reader.
        prev = time.time() 

        while self.connected:
            # Get name 
            try:
                name = await asyncio.wait_for(self.reader.readline(), mSettings.pingTime)
            # If no message cam in the past mSettings.pingTime seconds than pings the client.
            except asyncio.TimeoutError:
                self.connected = await self.ping()
                continue

            # If Client disconnected, empty messages are arriving in a loop, its kinda a bug.
            now = time.time()
            if now - prev < 0.01:
                logging.info(f"Client {self.name} disconnected")
                self.connected = False
                continue
            prev = now

            name = name.decode("utf-8").replace('\n', '').replace('\r', '')
            retStr, retEx = ClientsHandler.check_name(name)            
            # If the name was illegal:
            if retEx == False:
                self.writer.write(retStr.encode('utf-8'))
                self.writer.write("Send a new name:".encode())
                await self.writer.drain()
            # Name has valid syntax
            else:
                #Name already exists or not.
                if retStr in ClientsHandler.clients:
                    logging.info(f"{retStr} already in chat")
                    self.writer.write(ErrMsg["NAME_EXIST"].encode())
                    await self.writer.drain()
                # Name is valid and unique, add it to the dict and break the loop.
                else :
                    logging.info(f"Add {retStr} to the chat")
                    self.name = retStr
                    ClientsHandler.clients[self.name] = self
                    self.writer.write("You have joined the chat".encode())
                    await self.writer.drain()
                    await self.broadcast("has joined the chat")
                    break

    async def start_chatting(self):
        if not self.connected:
            return

        logging.info(f"{self.name} - start chatting")

        msg = ""
        
        # this is important to detect client disconnect, it seems like than empty messages will arive on stream reader.
        prev = time.time() 

        while self.connected:
            try:
                msg = await asyncio.wait_for(self.reader.readline(), mSettings.pingTime)
            # If no message cam in the past mSettings.pingTime seconds than pings the client.
            except asyncio.TimeoutError:
                self.connected = await self.ping()
                continue    
            
            # If Client disconnected, empty messages are arriving in a loop, its kinda a bug.
            now = time.time()
            if now - prev < 0.01: 
                logging.info(f"Client {self.name} disconnected")
                self.connected = False
                continue
            prev = now

            msg = msg.decode('utf-8').strip()
            await self.command_parser(msg)
    
    async def command_parser(self, msg:str)->None:
        if len(msg):
            ## If this is a command than swithc by parameter
            if msg[0] == '\\' :
                if msg == "\\exit":
                    self.connected = False
                elif msg == "\\time":
                    await self.sendServerTime()
                elif msg == "\\help":
                    self.writer.write(HelpStr)
                    await self.writer.drain()
                elif msg == "\\users":
                    users = ", ".join(list(ClientsHandler.clients.keys()))
                    self.writer.write(("Server: List of active users: " + users).encode())
                    pass
                elif len(msg) > 5 and msg[1:5] == "priv":
                    splittedMsg = msg.split(" ")
                    if len(splittedMsg) < 3 :
                        self.writer.write(ErrMsg["INVALID_COMMAND_SYNTAX"].encode())
                        await self.writer.drain()
                    else:
                        if splittedMsg[1] in ClientsHandler.clients:
                            ClientsHandler.clients[splittedMsg[1]].writer.write(("Private message from \"" + self.name + "\" : " + " ".join(splittedMsg[2:])).encode())
                else:
                    self.writer.write(ErrMsg["INVALID_COMMAND_SYNTAX"].encode())
                    await self.writer.drain()
            ## Else it is just a simple message --> Broadcast it.
            else:
                await self.broadcast(msg)

    async def close(self):
        logging.info(f"Closing client: {self.name}")
        self.writer.close()
        # Delete Client from Clients if it was added.
        if self.name in ClientsHandler.clients:
            del ClientsHandler.clients[self.name]

async def handle_client_request(reader:asyncio.StreamReader, writer:asyncio.StreamWriter):
    logging.info("New client requested to join the chat")
    tempClient = ClientsHandler("temp", reader, writer)
    # Start the name setting part
    await tempClient.start_name_setting()
    # After name is done start chatting
    await tempClient.start_chatting()
    # Close the connection, delete the Client from dict.
    await tempClient.close()

async def main():
    server = await asyncio.start_server(handle_client_request, mSettings.serverIp, mSettings.serverPort)
    addr = server.sockets[0].getsockname()
    print(f"Listening on IP: {mSettings.serverIp} port: {mSettings.serverPort}")
    logging.info(f"Listening on IP: {mSettings.serverIp} port: {mSettings.serverPort}")
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())