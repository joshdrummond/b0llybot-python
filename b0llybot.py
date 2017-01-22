from irc import *
import random

IRC_SERVER_HOSTNAME = "irc.colosolutions.net"
IRC_NICK = "pybolly"
IRC_CHANNEL = "#garbage"

MAGIC_8BALL_ANSWERS = [
                "It is certain",
                "It is decidedly so",
                "Without a doubt",
                "Yes definitely",
                "You may rely on it",
                "As I see it, yes",
                "Most likely",
                "Outlook good",
                "Yes",
                "Signs point to yes",
                "Reply hazy try again",
                "Ask again later",
                "Better not tell you now",
                "Cannot predict now",
                "Concentrate and ask again",
                "Don't count on it",
                "My reply is no",
                "My sources say no",
                "Outlook not so good",
                "Very doubtful"
    ];

##################################################

def get8ball():
	randnum = random.randint(1,len(MAGIC_8BALL_ANSWERS))-1
	return MAGIC_8BALL_ANSWERS[randnum]

def getRandomReply():
	return ""


##################################################

irc = IRC()
irc.connect(IRC_SERVER_HOSTNAME, IRC_CHANNEL, IRC_NICK)

while 1:
	text = irc.get_text()
	print text
	if "PRIVMSG" in text and IRC_CHANNEL in text:
		message = text.split("^PRIVMSG "+IRC_CHANNEL+" :")[0]
		if "hello" in message:
			irc.send(IRC_CHANNEL, "Hello!")
		elif ".8 " in message:
			irc.send(IRC_CHANNEL, get8ball())
		else:
			irc.send(IRC_CHANNEL, getRandomReply())

