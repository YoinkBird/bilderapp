import httplib
import urllib
 
globals = {    
           "server": "localhost",
           # prepare request header
           "headers": {"Content-type": "application/json", "Accept": "text/plain"},
           "userId": "Adnan Aziz"
          }
 
conn = httplib.HTTPConnection(globals["server"])
 
def send_request(conn, url, req):
    print '%s' % json.dumps(req)
    conn.request("POST", url, json.dumps(req), globals["headers"])
    resp = conn.getresponse()
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
