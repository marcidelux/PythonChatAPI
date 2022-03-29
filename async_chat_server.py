import asyncio
import re
from settings import AsyncChatSettings
import logging

# Create only one instance of the Settings class. (I should make this singleton.)
mSettings = AsyncChatSettings()

# Setup logging
logging.basicConfig(filename='async_chat_server.log', encoding='utf-8', level=logging.DEBUG)

class Client():
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
        if str == "":
            return "Error: Empty name is not allowed.", False
        
        # Cut the string by spaces and take the first one, than if its longer than 32 cut the remaining characters.
        firstPart = name.split(" ")[0]
        if len(firstPart) > mSettings.clientNameLen:
            firstPart = firstPart[:mSettings.clientNameLen]
        
        # Now check if only the allowed characters are in the name.
        if re.match("^[A-Za-z0-9_-]*$", firstPart):
            print("Valid name: " + firstPart)
            return firstPart, True
        else:
            return "Error: Invalid characters at name. Only numbers letters and underscore allowed.", False

    async def broadcast(self, message:str) -> None:
        for name, client in Client.clients.items():
            if name != self.name:
                print("Send message to: " + name)
                client.writer.write((self.name + ": " + message).encode("utf-8"))
                await client.writer.drain()
    
    async def ping_client(self):
        await asyncio.sleep(mSettings.pingTime)
        Client.clients[self.name].writer.write("ping".encode())
        await self.ping_client()

    async def start_name_setting(self):
        logging.info("Name setting called")
        while True:
            if self.connected == False:
                break
            
            #Atempt of setting the name
            name = await self.reader.readline()
            name = name.decode("utf-8").replace('\n', '').replace('\r', '')
            retStr, retEx = Client.check_name(name)
            # If the name was illegal:
            if retEx == False:
                self.writer.write(retStr.encode('utf-8'))
                self.writer.write("Send a new name:".encode())
                await self.writer.drain()
            # Name has valid syntax
            else:
                #Name already exists or not.
                if retStr in Client.clients:
                    print(f"{retStr} already in chat")
                    self.writer.write("Error: Name already exists.".encode())
                    self.writer.write("Send a new name:".encode())
                    await self.writer.drain()
                # Name is valid and unique, add it to the dict and break the loop.
                else :
                    print(f"Add {retStr} to the chat")
                    self.name = retStr
                    Client.clients[self.name] = self
                    self.writer.write("You have joined the chat".encode())
                    await self.writer.drain()
                    await self.broadcast("Server: " + self.name + " has joined the chat")
                    break
                

    async def start_chatting(self):
        logging.info("Chatting called")
        print(f"{self.name} - start listening")
        while True:
            data = await self.reader.readline()
            msg = data.decode('utf-8').strip()
            if msg == "\exit":
                print("End connection")
                break
            #Send private message
            elif msg.split(" ")[0] == "\p":
                if msg.split(" ")[1] in Client.clients:
                    Client.clients[msg.split(" ")[1]].writer.write(("priv msg from: "+ self.name + " : " + (" ".join(msg.split(" ")[2:]))).encode())
            else:
                print("Broadcast message")
                await self.broadcast(msg)

        self.writer.close()
        await self.writer.wait_closed()
        del Client.clients[self.name]

async def handle_client_request(reader:asyncio.StreamReader, writer:asyncio.StreamWriter):
    tempClient = Client("temp", reader, writer)
    #await tempClient.ping_client()
    await tempClient.start_name_setting()
    await tempClient.start_chatting()
    print("Client exited")

    """   
    if not name in Client.clients:
        Client.clients[name] = Client(name, reader, writer)
        print(f"Client {name} added to chat")
        print(Client.clients)
        await Client.clients[name].start_chatting()
        print("Client exited")
    else:
        writer.write("Username already exists")
        print(f"Client {name} already exists")
    """

async def main():
    server = await asyncio.start_server(handle_client_request, "192.168.0.30", 8888)
    addr = server.sockets[0].getsockname()
    print(f"Serviong on: {addr}")
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())