import json

class AsyncChatSettings():
    def __init__(self) -> None:
        f = open("settings.json")
        configData          = json.load(f)
        f.close()
        self.serverIp       = configData["serverIp"]
        self.serverPort     = configData["serverPort"]
        self.pingTime       = configData["pingTime"]
        self.clientNameLen  = configData["clientNameLen"]
    
    def __str__(self) -> str:
        ret = ""
        ret += "Configuration:\n"
        ret += f"Server ip address: {self.serverIp}\n"
        ret += f"Server port: {self.serverPort}\n"
        ret += f"Ping time: {self.pingTime}\n"
        ret += f"Client name max len: {self.clientNameLen}\n"
        return ret        


def test():
    testSettings = AsyncChatSettings()
    print(testSettings)
    
if __name__ == "__main__":
    test()
