import asyncio
from dataclasses import dataclass

class Client():
    clients = {}
    
    def __init__(self, name:str, reader:asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        self.name   = name
        self.writer = writer
        self.reader = reader
        #append the class variable if this name didnt existed


    async def broadcast(self, message:str) -> None:
        for name, client in Client.clients.items():
            if name != self.name:
                client.writer.write((self.name + ": " + message).encode())
                await client.writer.drain()
    
    async def start_listening(self):
        print(f"{self.name} - start listening")
        while True:
            data = await self.reader.readline()
            msg = data.decode().strip()
            if msg == "exit":
                print("End connection")
                break
            else:
                await self.broadcast(msg)

        self.writer.close()
        await self.writer.wait_closed()
        del Client.clients[self.name]

async def handle_client_request(reader:asyncio.StreamReader, writer:asyncio.StreamWriter):
    name = await reader.readline()
    name = name.decode().strip()
    if not name in Client.clients:
        Client.clients[name] = Client(name, reader, writer)
        print(f"Client {name} added to chat")
        print(Client.clients)
        await Client.clients[name].start_listening()
        print("Client exited")
    else:
        print(f"Client {name} already exists")

async def main():
    server = await asyncio.start_server(handle_client_request, "192.168.0.30", 8888)
    addr = server.sockets[0].getsockname()
    print(f"Serviong on: {addr}")
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())