import json
################################################################
# < def_sendJson>
# TODO: split into two functions:
#     - one purely for setting up url, args, etc
#     - one purely for sending json/retrieving result
def sendJson(self,**kwargs):
  from google.appengine.api import urlfetch
  urlfetch.set_default_fetch_deadline(60)
  #TODO: for loop, defaults, error checkign
  formDict = kwargs
  jsondata = formDict['jsondata']

  # check if input data is json
  # if not, convert to json - this makes calling the function much simpler
  try:
    json.loads(jsondata)
  except:
    jsondata = json.dumps(jsondata)
  # define URL as current host
  url = self.request.host_url + '/'

  # get "service name", i.e. the url sub-path
  if('service_name' in formDict):
    url += formDict['service_name']
  # src: https://developers.google.com/appengine/docs/python/appidentity/#Python_Asserting_identity_to_Google_APIs
  result = urlfetch.fetch(
      url,
      payload = jsondata,
      method=urlfetch.POST,
      headers = {'Content-Type' : "application/json"},
      )
  # store return string
  jsonRetStr = 'the_if_else_broke_in_def_sendjson'
  if(result.status_code == 200):
    jsonRetStr = result.content
  else:
    jsonRetStr = ("Call failed. Status code %s. Body %s" % (result.status_code, result.content))
    # Note on error-handling from above google page: # raise Exception(jsonRetStr)
    jsonRetStr = json.dumps({'error':jsonRetStr})
  #TODO: validate response with "try: ... except: ..." etc #jsonRetStr = json.loads(result.content)
  return jsonRetStr
# </def_sendJson>
################################################################


