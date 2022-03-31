# PythonChatAPI
Small chat application writen in python 3.10  

## Server  
The server based on asyncio library.  
It can handle multiple connections.  
Settings of the server can be done in settings.json  
There you can set the IP, PORT, PingTime, Max allowed length of the username.  
Every Client is pinged with the given interval, if it does not respond than breaks the connection.

### Commands  
\exit - Quits from the chat and disconnects from the server.  
\time - Gives back the current server time  
\priv "name" "Message" - Sends a private message to the user with "name"  
\users - Gives a list of the current users names.  
\help  - Prints out this small helping text.  


## Client
Also uses the same settings what the server uses.  
It just connects to the server, and waits for inputs.  
Also it responds to the pinging from the server.
