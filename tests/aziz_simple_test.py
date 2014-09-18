import json
import httplib
import urllib

#  disable proxy settings if using urllib2
#import urllib2
#proxy_support = urllib2.ProxyHandler({})
#opener = urllib2.build_opener(proxy_support)
#print opener.open("http://localhost:8080/").read()
#

# documentation
# https://docs.python.org/release/2.6/library/httplib.html

# https://developers.google.com/appengine/docs/python/tools/localunittesting
# https://developers.google.com/appengine/docs/python/tools/handlertesting

# information
# https://webapp-improved.appspot.com/guide/request.html#registry
# https://appengine.cloudbees.com/index.html
# http://googleappengine.blogspot.com/2012/10/jenkins-meet-google-app-engine.html
 
globals = {
           "server": "localhost",
           "port"  : "8080",
           # prepare request header
           "headers": {"Content-type": "application/json", "Accept": "text/plain"},
           "userId": "honey_badger"
          }
 
horizline = ('#' * 32)

def send_request(conn, url, req):
    jsontest = 0
    params = ''
    if(jsontest == 1):
      print "json request params:"
      params = json.dumps(req)
      print '%s' % params
    else:
      print "   request params (human readable): %s" % json.dumps(req)
      print "x-www-form-urlencoded request params:"
      params = urllib.urlencode(req)
      print '%s' % params
      globals["headers"] = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}

    conn.request("POST", url, params, globals["headers"])
    resp = conn.getresponse()
    print "status | reason"
    print "%s | %s" % (resp.status, resp.reason)
    response = resp.read()
    print "response:\n%s\n" % response
    print "json load:"
    try:
      jsonresp = json.loads(response)
    except:
      jsonresp = 'fail'
    print '  %s' % jsonresp
    print "easy to read:"
    print '  %s' % json.dumps(jsonresp, indent=4)
    return jsonresp
 
def place_create_request(conn):
    # prepare create user request
    req = {"userId": globals["userId"]}
    # send request to server
    res = send_request(conn, "/api/user/create", req)
    return res
 
# many more functions like the above

if __name__ == '__main__':
  # < read args>
  # https://docs.python.org/2/library/optparse.html
  import optparse
  parser = optparse.OptionParser()
  options, args = parser.parse_args()
  # </read args>
  # < read from args>
  # path is first arg, port is second
  if len(args) >= 1:
    globals['server'] = args[0]
    if len(args) >= 2:
      globals['port'] = args[1]
    # don't check for 3, just assume away
    else:
      del(globals['port'])
  # </read from args>


  # < define server>
  # localhost
  if('port' in globals):
    conn = httplib.HTTPConnection(globals["server"],globals["port"])
  else:
    conn = httplib.HTTPConnection(globals["server"])
  # < external>
  if(0):
    serverpath = 'jsontestsimple.appspot.com'
    conn = httplib.HTTPConnection(serverpath)
  # </external>
  # </define server>

  
  conn = httplib.HTTPConnection(globals["server"],globals["port"])
  # TODO: define dict of services and tests in order to specify test-specific defaults
  # e.g.: testConfigDict =  {'jsonreturntest':{'contenttype':'json'}, 'genericquery':{'contenttype':'urlencode'},}
  # vvv uncomment as the services are added vvv
  serviceList = [
      #'create',
      #'sign',
      #'manage',
      #'viewsinglestream',
      'viewallstreams',
      #'searchallstreams',
      'genericquery',
      #'img_upload',
      'jsonreturntest',
      'streamsubscribe'
      ]
  #< define request data>
  request = {"userId": globals["userId"]}
  request['redirect'] = 0 # HACK for the query page
  request['search_query'] = 'nerf|unicorn|grass'
  #< define request data>

  # < override list of services to be tested>
  # TODO: vvvv this is temporary vvvv
  if(1):
    serviceList = ['streamsubscribe'] # only working on one service right now
    requestDict = {}
    # ideally everything is in 'jsonstr'
    #request['jsonstr'] = json.dumps(requestDict)
    #  something may needs this in the future
    #request['jsonstr'] = urllib.quote_plus({'streamid':'testname'})
    #request['jsonstr'] = json.dumps(requestDict)
    requestDict['stream_name'] = 'testname'
    request = requestDict

  # </override list of services to be tested>
  jsondemotest = 0 # test the other appengine project 'jsondemotest TODO: put the url here or change this based on cli 
  if(jsondemotest): # test the 'jsondemo'
    serviceList = ['jsonreturntest','form2json']# ,'dataprocess'] #'formtest'] #TODO: would be good to test form submission
    #{"greeting": "sorry charlie!", "field2": "default2", "field1": "default1", "action": "dataprocess", "content": "default3", "username": "charlie"}
    # 'username: charlie should cause a return data of 'message:sorry charlie!'
    request = {"field2": "default2", "field1": "default1", "content": "default3", "action": "dataprocess",}# "username": "charlie"}
    #request['debug'] = 1 - turns on html
  for service in serviceList:
    print(horizline)
    serviceUrl = '/' + service
    print("testing: %s:%s/%s\n\n" % (conn.host,conn.port,service))
    send_request(conn,serviceUrl,request)
    print(horizline)
    print('\n')
