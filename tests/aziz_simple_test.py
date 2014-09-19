# TODO: clean up the remnant datastructures like 'testConfigDict'
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
passedList = []
failedList = []
def send_request(conn, url, req, **kwargs):
    #jsontest = 0  # dataprocess fail, form2json pass
    jsontest = 1  # dataprocess pass, form2json fail
    request_headers = globals["headers"]
    if(kwargs):
      if('headers' in kwargs):
        request_headers = kwargs['headers']
        if(request_headers['Content-type'] == 'application/json'):
          jsontest = 1
        if(request_headers['Content-type'] == 'application/x-www-form-urlencoded'):
          jsontest = 0
    params = ''
    #TODO: run with json first; if fail then run with x-www-form and/or others
    if(jsontest == 1):
      print "json request params:"
      params = json.dumps(req)
      print '%s' % params
    else:
      print "   request params (human readable): %s" % json.dumps(req)
      print "x-www-form-urlencoded request params:"
      params = urllib.urlencode(req)
      print '%s' % params
      request_headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/html"}

    print("headers: " + str(request_headers))
    conn.request("POST", url, params, request_headers)
    resp = conn.getresponse()
    print "status | reason"
    print "%s | %s" % (resp.status, resp.reason)
    response = resp.read()
    print "response:\n%s\n" % response
    print "json load:"
    try:
      jsonresp = json.loads(response)
      passedList.append(url)
    except:
      jsonresp = 'testrunner_json.loads_fail'
      failedList.append(url)
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
 
######################################################
#TODO: maybe just do this as json... then I can just have a json file to specify tests
# would need to read json intelligently, i.e. add a 'defaulttest' and allow inherit etc
def get_test_dict_pattern(**kwargs):
  testPatternDict = {} # this is returned
  if(kwargs):
    params = ['request', 'service', 'headers']
    for param in params:
      if(param in kwargs):
        testPatternDict[param] = kwargs[param]
  return testPatternDict
######################################################
  
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

  # define connection
  conn = httplib.HTTPConnection(globals["server"],globals["port"])
  # TODO: define dict of services and tests in order to specify test-specific defaults
  # TODO: make that a list of dicts
  testConfigDict =  {
      'jsonreturntest':{'contenttype':'json'}, 
      'genericquery':{'contenttype':'urlencode'},
      'viewallstreams':{'contenttype':'urlencode'},
      'genericquery':{'contenttype':'urlencode'},
      #'searchallstreams':{'contenttype':'urlencode'},
      #'create':{'contenttype':'urlencode'},
      #'sign':{'contenttype':'urlencode'},
      #'manage':{'contenttype':'urlencode'},
      #'viewsinglestream':{'contenttype':'urlencode'},
      #'img_upload':{'contenttype':'urlencode'},
      'streamsubscribe': {
        'request': {
          'action': 'unsubscribe',
          'stream_name': 'testname'}
        }
      } 
  # easier
  serviceList = testConfigDict.keys()
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

  if(1):
    ## default test
    import copy
    tmpRequestDict = {}
    serviceList = [] #clear out for this example
    defaulttest = {
        'service' : '/',
        'request' : {"userId": globals["userId"]}
    }
    ## populate serviceList with testconfigs
    ## jsonreturntest
    serviceList.append(get_test_dict_pattern(
      service = 'jsonreturntest',
      request = {"userId": globals["userId"]},
      )
    )

    ## viewallstreams
    serviceList.append(get_test_dict_pattern(
      service = 'viewallstreams',
      request = {"userId": globals["userId"]},
      )
    )

    ## genericquery
    serviceList.append(get_test_dict_pattern(
      service = 'genericquery',
     # headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"},
      request =  {"redirect": 0, "search_query": "nerf|unicorn|grass"},
      )
    )


  if(1): #TMP to convert genericquery
    ## stream subscription
    ## tests-to-be-written:
    ## * sub streamA, unsub streamB, verify no change
    ## * sub streamA, unsub streamA, verify that id is same

    ## sub
    requestDict['stream_name'] = 'testname'
    requestDict['submanage'] = 'subscribe'
   #     'headers' : {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"},
    streamsubscribe = {
        'service' : 'streamsubscribe',
        'request' : copy.copy(requestDict),
    }
    # unsub
    requestDict['subscribe'] = 'unsubscribe'
    streamunsubscribe = {
        'service' : 'streamsubscribe',
        'request' : copy.copy(requestDict),
    }
    streamdonothing = copy.deepcopy(streamunsubscribe)
    del(streamdonothing['request']['submanage'])

    serviceList.append(streamdonothing)
    serviceList.append(streamsubscribe)
    serviceList.append(streamunsubscribe)

  # < override list of services to be tested>
  # test the other appengine project 'jsondemotest TODO: put the url here or change this based on cli 
  if(globals['port'] == '9080'):
    del serviceList
    serviceList = []
    ## TODO: add this as well to be complete: # jsonreturntest - the demo appspot project
    #service = 'jsonreturntest', TODO
    ## service 'dataprocess' - receives json data from form2json
    serviceList.append(get_test_dict_pattern( 
      #service = 'jsonreturntest',
      service = 'dataprocess',
      request = {"username" : "charlie", "field2": "default2", "field1": "default1", "content": "default3", "action": "dataprocess",},
      )
    )
    serviceList.append(get_test_dict_pattern( 
      service = 'form2json', #umm... FORM 2json -this needs to be a x-www-form
      request = {"username" : "charlie", "field2": "default2", "field1": "default1", "content": "default3", "action": "dataprocess",},
      #request = {"username" : "charlie", "field2": "default2", "field1": "default1", "content": "default3", "action": "dataprocess","debug":"1"},
      
      # "username": "charlie"}
      headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"},
      #'request' = {"field2": "default2", "field1": "default1", "content": "default3", "action": "dataprocess",}# "username": "charlie"}
      )
    )
    print("")
  # </override list of services to be tested>

  # RUN tests
  serviceRunList = testConfigDict.keys()
  serviceRunList = ['genericquery']
  import copy
  defaultrequest = copy.copy(request)
  # TODO: make hash where key is testname, hash is same as above with 'serviceList.append'
  # then the 'serviceRunList = testConfigDict.keys() could be used to disable a test on the fly
  #runOnlyTests = ('service',) # create a set, blah blah
  for testConfigDict in serviceList:
    service = testConfigDict['service']
    request = testConfigDict['request']
    if(0):
      #if(not service == 'streamsubscribe'):
      if(not service == 'form2json'):
        continue
      if(0 and not request['action'] == 'unsubscribe'):
        continue
    if not request:
      request = defaultrequest
    print(horizline)
    serviceUrl = '/' + service
    print("testing: %s:%s/%s\n\n" % (conn.host,conn.port,service))
    if 'headers' in testConfigDict:
      testheaders = testConfigDict["headers"]
      send_request(conn,serviceUrl,request, headers=testConfigDict["headers"])
    else:
      send_request(conn,serviceUrl,request)
    print(horizline)
    print('\n')
  #</testrun loop>

  ################################################################ 
  # print results
  print("vvvvv passed vvvvvv")
  print(passedList)
  print('#' * 64)
  print("vvvvv failed vvvvv")
  print(failedList)
