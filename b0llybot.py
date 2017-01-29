from irc import *
import requests
import json
import sys
import traceback
import xml.etree.ElementTree as ET
import random
import ConfigParser
import re
import socket


IRC_SERVER_HOSTNAME = ""
IRC_NICK = ""
IRC_CHANNEL = ""
WEATHER_API_KEY = ""
PROPERTIES_FILE = "b0llybot.properties"
FILE_REPLIES = "replies.dat"
FILE_QUOTES = "quotes.dat"
FILE_OPIPS = "opips.dat"
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
    ]
replies = {}
quotes = []
tells = {}


##################################################

def get8ball():
    randnum = random.randint(1,len(MAGIC_8BALL_ANSWERS)) - 1
    return MAGIC_8BALL_ANSWERS[randnum]

def doRandomReply(irc, message):
    for key in replies.keys():
        if key in "*" or key in message:
            chance = replies[key][0]
            answers = replies[key][1]
            randnum = random.randint(1,100)
            if (randnum <= chance):
                randmsg = random.randint(1,len(answers))
                irc.send(IRC_CHANNEL, answers[randmsg-1])
                break

def getWeatherLocation(location):
    weather = ""
    location = location.replace(" ", "%20")
    #print "getting location for %s" % location
    url = "http://api.wunderground.com/api/"+WEATHER_API_KEY+"/geolookup/q/"+location+".json"
    #print url
    try:
        req = requests.get(url)
        jsonString = json.loads(req.content)
        city = jsonString['location']['city']
        state = jsonString['location']['state']
        country = jsonString['location']['country_name']
        weather = city + ", " + state + ", " + country
    except:
        pass
    return weather

def getCurrentWeather(location):
    weather = ""
    location = location.replace(" ", "%20")
    url = "http://api.wunderground.com/api/"+WEATHER_API_KEY+"/conditions/q/"+location+".json"
    try:
        req = requests.get(url)
        jsonString = json.loads(req.content)
        city = jsonString['current_observation']['display_location']['full']
        country = jsonString['current_observation']['display_location']['country_iso3166']
        temp = jsonString['current_observation']['temperature_string']
        condition = jsonString['current_observation']['weather']
        humidity = jsonString['current_observation']['relative_humidity']
        wind = jsonString['current_observation']['wind_string']
        station = jsonString['current_observation']['station_id']
        weather = "Current conditions for " + city + ", " + country + " (" + station + ") --- " + temp + " / " + condition + " / Humidity: " + humidity + " / Wind: " + wind
    except Exception as e:
        #traceback.print_exc()
        pass
    return weather

def getWeatherForecast(location):
    numDays = 4
    weather = ""
    location = location.replace(" ", "%20")
    #print "getting weather forecast for %s" % location
    url = "http://api.wunderground.com/api/" + WEATHER_API_KEY + "/forecast/q/" + location + ".json"
    try:
        req = requests.get(url)
        jsonString = json.loads(req.content)
        weather = "Forecast conditions for " + getWeatherLocation(location) + " --- "
        for i in range(numDays):
            if (i > 0):
                weather += "; "
            day = jsonString['forecast']['simpleforecast']['forecastday'][i]['date']['weekday_short']
            weather += day + " - "
            high = jsonString['forecast']['simpleforecast']['forecastday'][i]['high']['fahrenheit'] + "F(" + jsonString['forecast']['simpleforecast']['forecastday'][i]['high']['celsius'] + "C)"
            low = jsonString['forecast']['simpleforecast']['forecastday'][i]['low']['fahrenheit'] + "F(" + jsonString['forecast']['simpleforecast']['forecastday'][i]['low']['celsius'] + "C)"
            weather += "High: " + high + ", Low: " + low
    except Exception as e:
        #traceback.print_exc()
        pass
    return weather

def getWeatherForecastDetail(location):
    numDays = 8
    weather = []
    location = location.replace(" ", "%20")
    url = "http://api.wunderground.com/api/"+WEATHER_API_KEY+"/forecast/q/"+location+".json"
    try:
        req = requests.get(url)
        jsonString = json.loads(req.content)
        weather.append("Detailed Forecast conditions for "+getWeatherLocation(location)+" --- ")
        for i in range(numDays):
            day = jsonString['forecast']['txt_forecast']['forecastday'][i]['title']
            conditions = jsonString['forecast']['txt_forecast']['forecastday'][i]['fcttext']
            weather.append(day+" - "+conditions)
    except Exception as e:
        #traceback.print_exc()
        pass
    return weather

def getRainForecast(location):
    numDays = 4
    weather = ""
    location = location.replace(" ", "%20")
    #print "getting weather forecast for %s" % location
    url = "http://api.wunderground.com/api/"+WEATHER_API_KEY+"/forecast/q/"+location+".json"
    #print url
    try:
        req = requests.get(url)
        jsonString = json.loads(req.content)
        weather = "Rain Forecast for " + getWeatherLocation(location) + " --- "
        for i in range(numDays):
            if (i > 0): weather += "; "
            day = jsonString['forecast']['simpleforecast']['forecastday'][i]['date']['weekday_short']
            weather += day + " - "
            rain = jsonString['forecast']['simpleforecast']['forecastday'][i]['pop']
            weather += str(rain)+"%"
    except Exception as e:
        #traceback.print_exc()
        pass
    return weather

def doWZFD(irc, message):
    s = message.strip().split("wzfd")
    if len(s) > 1:
        for weather in getWeatherForecastDetail(s[1].strip()):
            irc.send(IRC_CHANNEL, weather)

def doWZF(irc, message):
    s = message.strip().split("wzf")
    if len(s) > 1:
        irc.send(IRC_CHANNEL, getWeatherForecast(s[1].strip()))

def doWZ(irc, message):
    s = message.strip().split("wz")
    if len(s) > 1:
        irc.send(IRC_CHANNEL, getCurrentWeather(s[1].strip()))

def doRain(irc, message):
    s = message.strip().split("rain")
    if len(s) > 1:
        irc.send(IRC_CHANNEL, getRainForecast(s[1].strip()))

def getNews(query, count):
    news = []
    url = "https://news.google.com/?q="+query+"&output=rss"
    try:
        req = requests.get(url)
        root = ET.fromstring(req.content)
        for i, item in enumerate(root.findall('.//item')):
            if i >= count:
                break
            title = item.find('title').text
            link = item.find('link').text
            link = link[link.rindex("url=")+4:]
            news.append(title + " ("+link+")")
    except Exception as e:
        traceback.print_exc()
        #pass
    return news

def doNews(irc, message, search):
    s = message.strip().split(" ")
    numNews = 1
    if len(s) > 1:
        numNews = int(s[1].strip())
    for news in getNews(search, numNews):
        irc.send(IRC_CHANNEL, news)

def getReddit(category, count):
    articles = []
    url = "https://www.reddit.com/"+category+"/.json"
    try:
        req = requests.get(url)
        jsonString = json.loads(req.content)
        #print jsonString
        for i in range(count):
            articles.append(("["+jsonString['data']['children'][i]['data']['subreddit'] + "] " + jsonString['data']['children'][i]['data']['title'] + " - " + jsonString['data']['children'][i]['data']['url']).replace("&amp;", "&"))
    except Exception as e:
        #traceback.print_exc()
        pass
    return articles

def doReddit(irc, message):
    s = message.strip().split(" ")
    category = "hot"
    numNews = 1
    if len(s) > 1:
        try:
            numNews = int(s[1].strip())
        except:
            numNews = 1
            category = s[1].strip()
    if len(s) > 2:
        if category != "hot":
            try:
                numNews = int(s[2].strip())
            except:
                pass
        else:
            category = s[2].strip()
    if category not in ['new', 'hot', 'rising', 'controversial', 'top', 'gilded']:
        category = "r/"+category
    for news in getReddit(category, numNews):
        irc.send(IRC_CHANNEL, news)

def getDefine(search):
    result = ""
    search = search.replace(" ","%20")
    url = "http://api.urbandictionary.com/v0/define?term="+search
    try:
        req = requests.get(url)
        jsonString = json.loads(req.content)
        index = random.randint(1,len(jsonString['list'])) - 1
        result = jsonString['list'][index]['definition']
    except Exception as e:
        #traceback.print_exc()
        pass
    return result

def doDefine(irc, message):
    s = message.split("define")
    if len(s) > 1:
        irc.send(IRC_CHANNEL, getDefine(s[1].strip()))

def getWiki(search):
    result = ""
    search = search.replace(" ","%20")
    url = "http://en.wikipedia.org/w/api.php?format=json&action=query&prop=extracts&titles="+search+"&exintro=&redirects=true"
    try:
        req = requests.get(url)
        jsonString = json.loads(req.content)
        key = jsonString['query']['pages'].keys()[0]
        result = jsonString['query']['pages'][key]['extract']
        result = result.replace("<b>", "")
        result = result.replace("</b>", "")
        result = result.replace("<i>", "")
        result = result.replace("</i>", "")
        result = result.replace("<p>", "")
        result = result.replace("</p>", "")
        result = result.replace("<small>", "")
        result = result.replace("</small>", "")
    except Exception as e:
        #traceback.print_exc()
        pass
    return result

def doWiki(irc, message):
    s = message.split("wiki")
    if len(s) > 1:
        irc.send(IRC_CHANNEL, getWiki(s[1].strip()))

def doQuote(irc, message):
    num = 0
    try:
        s = message.split("quote")
        if len(s) > 1:
            num = int(s[1])
            if num < 1 or num > len(quotes):
                num = 0
    except:
        pass
    if num == 0:
        num = random.randint(1,len(quotes))
    irc.send(IRC_CHANNEL, "Quote #"+str(num)+": "+quotes[num-1])

def doRoulette(irc, sender):
    randnum = random.randint(1,6) - 1
    if randnum == 0:
        irc.command("KICK " + IRC_CHANNEL + " " + sender + " BANG!")
    else:
        irc.send(IRC_CHANNEL, "*click*")

def getLinkTitle(url):
    print "getting link title for "+url
    title = ""
    pattern = re.compile("<title.*?>(.+?)</title>")
    try:
        req = requests.get(url)
        titles = re.findall(pattern, req.content)
        if len(titles) > 0:
            title = titles[0]
    except:
        pass
    return title

def doLinkTitle(irc, message):
    s = message.strip().split(" ")
    for word in s:
        if word.startswith("http://") or word.startswith("https://"):
            irc.send(IRC_CHANNEL, getLinkTitle(word))

def loadProperties():
    config = ConfigParser.RawConfigParser()
    config.read(PROPERTIES_FILE)
    global IRC_SERVER_HOSTNAME
    IRC_SERVER_HOSTNAME = config.get("main", "hostname")
    global IRC_NICK
    IRC_NICK = config.get("main", "nick")
    global IRC_CHANNEL
    IRC_CHANNEL = config.get("main", "channel")
    global WEATHER_API_KEY
    WEATHER_API_KEY = config.get("main", "weather_api_key")

def loadReplies():
    f = open(FILE_REPLIES)
    global replies
    replies.clear()
    for line in f.readlines():
        parts = line.split("|")
        replies[parts[0]] = (int(parts[1]), parts[2:])
    f.close()

def loadQuotes():
    f = open(FILE_QUOTES)
    global quotes
    quotes = []
    for line in f.readlines():
        quotes.append(line.strip())
    f.close()

def loadOpIps():
    f = open(FILE_OPIPS)
    global opips
    opips = []
    for line in f.readlines():
        opips.append(line.strip())
    f.close()

def loadFiles():
    loadReplies()
    loadQuotes()
    loadOpIps()

def getSender(text):
    sender = text[1:text.index('!')]
    return sender

def getHostname(text):
    hostname = ""
    pattern = re.compile("^:\w+!~\w+\@(\S+)\s")
    hostnames = re.findall(pattern, text)
    if len(hostnames) > 0:
        hostname = hostnames[0]
    return hostname

def isOpIP(hostname):
    try:
        ipaddress = socket.gethostbyname(hostname)
        #print "ip address="+ipaddress
        if ipaddress in opips:
            return True
    except:
        pass
    return False

def doTell(irc, message, sender):
    global tells
    s = message.strip().split("tell")
    if len(s) > 1:
        content = s[1].strip()
        i = content.find(" ")
        if i > 0:
            receiver = content[0:i].lower()
            message = content[i+1:]
            messageList = []
            if receiver in tells.keys():
                messageList = tells[receiver]
            messageList.append(" <"+sender+"> tell "+receiver+" "+message)
            tells[receiver] = messageList
            irc.send(IRC_CHANNEL, sender+": I'll pass that on when "+receiver+" is around.")
        else:
            irc.send(IRC_CHANNEL, "tell "+content+" what?")
    else:
        irc.send(IRC_CHANNEL, "tell who?")

def checkOp(irc, sender, hostname):
    if isOpIP(hostname):
        irc.command("MODE " + IRC_CHANNEL + " +o " + sender)

def checkTells(irc, sender):
    global tells
    sender = sender.lower()
    if sender in tells.keys():
        messageList = tells[sender]
        for message in messageList:
            irc.send(IRC_CHANNEL, message)
        del tells[sender]

def runIRC():
    irc = IRC()
    irc.connect(IRC_SERVER_HOSTNAME, IRC_CHANNEL, IRC_NICK)
    while True:
        text = irc.get_text()
        print "IRC got: "+text
        onJoin = "JOIN :" + IRC_CHANNEL
        if onJoin in text:
            sender = getSender(text)
            hostname = getHostname(text)
            checkOp(irc, sender, hostname)
            checkTells(irc, sender)
            continue
        onMessage = "PRIVMSG " + IRC_CHANNEL + " :"
        if onMessage in text:
            message = text.split(onMessage)[1]
            sender = getSender(text)
            checkTells(irc, sender)
            if message.startswith(".reload"):
                loadFiles()
            elif message.startswith(".tell"):
                doTell(irc, message, sender)
            elif message.startswith(".define"):
                doDefine(irc, message)
            elif message.startswith(".wiki"):
                doWiki(irc, message)
            elif message.startswith(".news"):
                doNews(irc, message, "")
            elif message.startswith(".spnews"):
                doNews(irc, message, "smashing pumpkins")
            elif message.startswith(".reddit"):
                doReddit(irc, message)
            elif message.startswith(".8"):
                irc.send(IRC_CHANNEL, get8ball())
            elif message.startswith(".roulette"):
                doRoulette(irc, sender)
            elif message.startswith(".wzfd"):
                doWZFD(irc, message)
            elif message.startswith(".wzf"):
                doWZF(irc, message)
            elif message.startswith(".wz"):
                doWZ(irc, message)
            elif message.startswith(".rain"):
                doRain(irc, message)
            elif message.startswith(".quote"):
                doQuote(irc, message)
            elif "http://" in message or "https://" in message:
                doLinkTitle(irc, message)
            else:
                doRandomReply(irc, message)


##################################################

loadProperties()
loadFiles()
runIRC()
#print getLinkTitle(sys.argv[1])
#location = " ".join(sys.argv[1:])
#print getDefine(location)
#print getCurrentWeather(location, weatherApiKey)
#for s in getWeatherForecastDetail(location, weatherApiKey):
#    print s
#print getRainForecast(location,weatherApiKey)
#for n in getRedditTop(5):
#for n in getNews("", 5):
#    print n
