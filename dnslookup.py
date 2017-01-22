import socket
import sys

content = []
try:
    with open(sys.argv[1]) as f:
        content = f.readlines()
except:
    pass

content = [x.strip() for x in content]

for line in content:
    try:
        print socket.gethostbyaddr(line)[0]
    except:
        print line

