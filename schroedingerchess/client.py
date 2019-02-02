from twisted.internet.protocol import Protocol

import json

class ChessClientProtocol(Protocol):

    """ Class which handles the communication protocol between the game client and the game server."""

    def __init__(self, client):
        """
        Constructor.
        :param client: Client to bind to the protocol
        """
        self.client = client # reference to the client (a GameEngine object)
        self.state = "INITIALIZATION"

    def connectionMade(self):
        self.sendMessage({"type" : "player-info", "player-name" : self.client.name, "color": self.client.color})

    def dataReceived(self, data):

        """
        Handles the reception of data from the server.
        :param data: A byte representing a JSON-encoded object (default encoding UTF-8)
        """
        messages = self.split_messages(data)

        for msg_json in messages:
            msg = json.loads(msg_json)
            
            if self.state == "INITIALIZATION":
                if msg["type"] == "greetings":
                    self.client.handleInit()
                self.state = "PLAYING"
            elif self.state == "PLAYING":
                if msg["type"] == "chat":
                    self.client.display.addMessage(msg["content"])
                if msg["type"] == "move":
                    self.client.handleMove(msg["description"])
                elif msg["type"] == "illegal-move":
                    self.client.handleIllegalMove(msg["description"])
                elif msg["type"] == "status":
                    if msg["status"] == "ready":
                        self.client.handleReady()
                elif msg["type"] == "lightboard":
                    self.client.handleUpdateBoard(msg["description"])
                elif msg["type"] == "checks":
                    self.client.handleChecks(msg["description"])
                elif msg["type"] == "checkmates":
                    self.client.CheckMates(msg["description"])
                elif msg["type"] == "disconnection":
                    self.client.handleDisconnection(msg["description"])
                else:
                    pass

    def connectionLost(self, reason):
        """
        Handles the connection lost with the server.
        :param reason: Reason of the disconnection
        """
        self.client.handleDisconnection(reason)

    def sendMessage(self, msg):
        """
        Sends a message to the server using the protocol.
        :param msg: A dictionary representing a message.
        """
        self.transport.write(json.dumps(msg).encode())

    def split_messages(self, data):
        messages = []
        split = data.decode().split("}{")
        if len(split) == 1:
            return split
        for i, sp in enumerate(split):
            m = sp
            if i > 0:
                m = "{" + m
            if i < len(split)-1:
                m = m + "}"
            messages.append(m)
        return messages
