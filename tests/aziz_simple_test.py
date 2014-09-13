import json
import httplib
import urllib

#  disable proxy settings if using urllib2
#import urllib2
#proxy_support = urllib2.ProxyHandler({})
#opener = urllib2.build_opener(proxy_support)
#print opener.open("http://localhost:8080/").read()
#

 
globals = {
           "server": "localhost",
           "port"  : "8080",
           # prepare request header
           "headers": {"Content-type": "application/json", "Accept": "text/plain"},
           "userId": "yoinkboid"
          }
 
conn = httplib.HTTPConnection(globals["server"],globals["port"])
 
def send_request(conn, url, req):
    print "json request:"
    print '%s' % json.dumps(req)
    conn.request("POST", url, json.dumps(req), globals["headers"])
    resp = conn.getresponse()
    print "status reason"
    print resp.status, resp.reason
    jsonresp = json.loads(resp.read())
    print '  %s' % jsonresp
    return jsonresp
 
def place_create_request(conn):
    # prepare create user request
    req = {"userId": globals["userId"]}
    # send request to server
    res = send_request(conn, "/api/user/create", req)
    return res
 
# many more functions like the above

if __name__ == '__main__':
  
  service = 'jsonreturntest'
  serviceUrl = '/' + service
  import random;
  tmpRequest = str(random.random()) # send any request for now
  send_request(conn,serviceUrl,tmpRequest)
