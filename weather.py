import requests
import json
import sys

location = sys.argv[1]
numDays = 4
weather = ""
location = location.replace(" ", "%20")
print"getting weather forecast for %s" % location

try:
    weatherApiKey = ""
    url = "http://api.wunderground.com/api/"+weatherApiKey+"/geolookup/q/"+location+".json"
    #url = "http://api.wunderground.com/api/"+weatherApiKey+"/forecast/q/"+location+".json"
    print url
    r = requests.get(url)
    #print r.status_code
    #print r.headers
    #print r.content
    jsonString = json.loads(r.content)
    city = jsonString['location']['city']
    state = jsonString['location']['state']
    country = jsonString['location']['country_name']
    print city, state, country
except:
    print "uh oh"
    #pass

    
