import socket


class IRC:

    irc = socket.socket()

    def __init__(self):
        self.irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def send(self, chan, msg):
        #print msg
        if msg != "":
            try:
                self.irc.send("PRIVMSG " + chan + " :" + msg + "\n")
            except:
                pass

    def command(self, command):
        if command != "":
            #print command
            try:
                self.irc.send(command+"\n")
            except:
                pass

    def connect(self, server, channel, botnick):
        #defines the socket
        print "connecting to: "+server
        self.irc.connect((server, 6667)) #connects to the server
        self.command("USER " + botnick + " " + botnick +" " + botnick + " :"+botnick+" in the house!") #user authentication
        self.command("NICK " + botnick)
        self.command("JOIN " + channel)        #join the chan

    def get_text(self):
        text = self.irc.recv(2040)  #receive the text
        if text.find('PING') != -1:
            self.irc.send('PONG ' + text.split() [1] + '\r\n')
        return text
