import json
import cgi
import os
import urllib
import urlparse

from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.api import urlfetch
urlfetch.set_default_fetch_deadline(60)

from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers

import webapp2
import jinja2

########## 
'''
DOCUMENTATION

view:
http://localhost:8080/viewallstreams

admin:
http://localhost:8008/datastore?kind=Greeting

test:
python tests/aziz_simple_test.py

information about the env
https://webapp-improved.appspot.com/guide/request.html#registry


some good clarification on keys
http://stackoverflow.com/questions/16020686/understanding-ndb-key-class-vs-keyproperty


Routing
http://blog.notdot.net/2010/01/Webapps-on-App-Engine-part-1-Routing

webapp2
http://docs.webob.org/en/latest/do-it-yourself.html#routing
https://webapp-improved.appspot.com/guide/app.html#router

https://webapp-improved.appspot.com/guide/handlers.html


'''
########## 
'''
TODO: CLEANUP ORDER
* viewsinglestream must be converted to service - many things rely on the viewcount being increased and 'viewsinglestream' is called from a few places
'''

import bilder_templates


################################################################
# < def_sendJson>
# TODO: split into two functions:
#     - one purely for setting up url, args, etc
#     - one purely for sending json/retrieving result
def sendJson(self,**kwargs):
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


###############################################################################
# < def_get_user_data>
# return a fake user if not logged in
def get_user_data():
  user = ''
  if users.get_current_user():
      user = users.get_current_user()
  else:
    #  stream.author = 'anonymous' - nono! it's a usertype, can't simply asign
    # < mock user>
    # mock user: # src: http://stackoverflow.com/a/6230083
    import os
    #os.environ['USER_EMAIL'] = 'poland.barker@swedishcomedy.com'
    os.environ['USER_EMAIL'] = 'leewatson1@gmail.com'
    os.environ['USER_ID'] = 'pbarker'
    #   < more mock user values>
    #os.environ['AUTH_DOMAIN'] = 'testbed' # To avoid  /google/appengine/api/users.py:115 - AssertionError: assert _auth_domain
    #os.environ['USER_IS_ADMIN'] = '1'     #  for an administrative user
    #   </more mock user values>
    # </mock user>
    user = users.get_current_user()
  return user
# </def_get_user_data>
###############################################################################

def genNav():
  #TODO: match link targets with the mockups, tie-in to 'application = webapp2.WSGIApplication'
  #TODO: autogenerate from dict with linktext->target
  #TODO: use bullet list
  #raw data: Manage Create View Search Trending Social 
  navDict = {
      'Home'   : '/',
      'Manage'   : 'manage',
      'Create'   : 'create',
      'View'     : 'viewallstreams',
      'GeoView'  : 'geoview',
      'Search'   : 'searchallstreams',
      'Trending'   : 'trending',
      'Social'   : 'social',
      }
  #TODO: convert to 2d list or object or whatever, try to autogenerate initial link->target
  navList = [ "Home", "Manage", "Create", "View", "GeoView", "Search", "Trending", "Social", ]
  navTr = ''
  for param in navList:
    tmplink = '<a href=%s>%s</a>' % (navDict[param], param)
    tmptd   = '<td>%s</td>' % tmplink
    navTr += tmptd
    del tmplink
    del tmptd
    colspan = len(navList)
    TEMPLATE_NAVIGATION = """\
    <table border=1 cellpadding=5>
      <tr>
        <td colspan=%s>
      <tr>
        %s
      </tr>
    </table>
    """
  navTable = TEMPLATE_NAVIGATION % (colspan,navTr)
  return navTable
#</genNav>


################################################################
# < def_load_template>
# returns valid html, sample usage: self.response.write(load_template(<filepath>))
def load_template(self, **kwargs):
  paramDict = kwargs
  templateStr = ''
  # jinja setup
  jinja_loader_instance = jinja2.Environment(
      loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
      extensions=['jinja2.ext.autoescape'],
      autoescape=True)
  if('file' in paramDict):
    # default case if 'type' not specified
    if(not 'type' in paramDict):
      paramDict['type'] = 'html'
    if('type' in paramDict):
      # load file as jinja template
      if(paramDict['type'] == 'jinja'):
        templateInst = jinja_loader_instance.get_template(paramDict['file'])
        valuesDict = {}
        #TODO: add param for 'template_values'
        if('values' in paramDict):
          valuesDict = paramDict['values']
        templateStr = templateInst.render(valuesDict)
      # load file as plain-text, no parsing 
      elif(paramDict['type'] == 'html'):
        # normal open file
        indexTemplateHandler = open(paramDict['file'], 'r')
        templateStr = indexTemplateHandler.read()
        indexTemplateHandler.close()
  return templateStr
# < def_load_template>
################################################################

    
TEMPLATE_NAVIGATION = genNav()
 

#TODO: rename to 'DEFAULT_USER_NAME'
#TODO: read username from user API
DEFAULT_GUESTBOOK_NAME = 'default_guestbook'

#NOTE: keep it simple:
# Guestbook equ User (has a db key)
# `- Greeting equ Stream
#   `- photoList (simple list of urls to blobstore)

# We set a parent key on the 'Greetings' to ensure that they are all in the same
# entity group. Queries across the single entity group will be consistent.
# However, the write rate should be limited to ~1/second.

# TODO: rename
# NOTE: ancestor/parent entity need not actually exist, just needs to be able to create a key
#   that is why clicking on 'Guestbook: name=default_guestbook' in the 'datastore viewer' is not found
#   same for GuestbookNDB - neither are instantiated
#   src: https://developers.google.com/appengine/docs/python/datastore/entities#Python_Ancestor_paths
# user_key
def guestbook_key(guestbook_name=DEFAULT_GUESTBOOK_NAME):
    """Constructs a Datastore key for a Guestbook entity with guestbook_name."""
    return ndb.Key('GuestbookNDB', guestbook_name)
    # syntax: class Key(kind1, id1) # https://developers.google.com/appengine/docs/python/ndb/keyclass
    # kind: usually the name of the class # https://developers.google.com/appengine/docs/python/datastore/entities#Python_Kinds_and_identifiers
    # id: numberic or string
    # Key: unique identifer associated with each entity in Datastore
    #  The key consists of the following components:
    #  * The namespace of the entity ( allows for multitenancy )
    #  * The kind of the entity ( categorizes it for Datastore queries )
    #  * An identifier for the individual entity, either 'key name string' or 'integer numeric ID'
    #  * An optional ancestor path locating the entity within the Datastore hierarchy

###############################################################################
#< class_Stream>
# class Stream aka Greeting
# doc on internal properties: https://developers.google.com/appengine/docs/python/ndb/properties
# TODO: implement custom to_dict to avoid the 'blah is not JSON serializable' errors
class Greeting(ndb.Model):
#class Stream(ndb.Model):
    #TODO: implement all the internal methods
    """Models an individual Guestbook entry."""
    author = ndb.UserProperty()
    content = ndb.StringProperty() # TODO: convert to 'streamid'
    #streamid = content              # TODOno: created a stream and then double-check in the console - only 'streamid' gets updated for some reason
    streamid = ndb.StringProperty(required=True) # TODO:  make this match StreamSubscription, which uses 'stream_id' with an undescore
    date = ndb.DateTimeProperty(auto_now_add=True)
    coverurl = ndb.StringProperty()
    tags        = ndb.StringProperty(repeated=True)
    subscribers = ndb.StringProperty(repeated=True)

    #TODO: no duplicate streams allowed - find a way to detect and error for collisions 
    # https://developers.google.com/appengine/docs/python/ndb/properties#repeated
    # repeated-True: Property value is a Python list containing values of the underlying type
    # make sure to run str() for in-place editing, or overwrite list each time: 
    #     "When you assign a new list, the types of the list items are validated immediately."
    imgurls = ndb.StringProperty(indexed=False, repeated=True)

    #TODO: store image name and comments as well; either requires a new ndb class or could possibly also be handled by blobstore
    # see https://developers.google.com/appengine/docs/python/ndb/properties#structured

    # DOC: on counters: https://developers.google.com/appengine/articles/sharding_counters
    #TODO: implement these mocks
    img_amount = ndb.IntegerProperty(default = 0)
    views      = ndb.IntegerProperty(default = 0)
    # ValueError: DateTimeProperty None could use auto_now and be repeated, but there would be no point.
    # Set property to current date/time when entity is created and whenever it is updated
    viewtimes  = ndb.DateTimeProperty(repeated = True)#, auto_now = True)

    def getKeyWords(self):
      jsonRetDict = {}
      keyWordArr = [];
      keyWordArr.append(self.streamid)
      keyWordArr.extend(self.tags)
      # < uniqify_list>
      # remove duplicate keywords
      if(1):
        tmpSet   = set(keyWordArr)
        tmpList  = list(tmpSet)
        keyWordArr = list(tmpSet)
      # </uniqify_list>
      jsonRetDict['keywords'] = keyWordArr
      jsonRetDict = keyWordArr
      return jsonRetDict

    def getKeyWordsDict(self):
    # e.g.
    # [{"id":"Dromas ardeola","label":"Crab-Plover","value":"Crab-Plover"},{"id":"Larus sabini","label":"Sabine`s Gull","value":"Sabine`s Gull"},{"id":"Vanellus gregarius","label":"Sociable Lapwing","value":"Sociable Lapwing"},{"id":"Oenanthe isabellina","label":"Isabelline Wheatear","value":"Isabelline Wheatear"}]
      # < uniqify_list>
      # remove duplicate keywords
      if(1):
        tmpSet   = set(self.tags)
        tmpList  = list(tmpSet)
        keyWordArr = list(tmpSet)
      # </uniqify_list>

      jsonRetDict = {}
      jsonRetDict['id']    = self.streamid
      jsonRetDict['label'] = self.streamid + ' ' + ' '.join(keyWordArr)
      jsonRetDict['value'] = self.streamid + ' ' + ' '.join(keyWordArr)


      return jsonRetDict



#</class_Stream>
###############################################################################


###############################################################################
#<>
# NOTE: 'cls' is equ to 'self', bit confusing at first
# store a stream_id and a user_id
# goal: track subscriptions for users
# http://stackoverflow.com/questions/11711077/how-to-structure-movies-database-and-user-choices
# TODO: implement custom to_dict to avoid the 'blah is not JSON serializable' errors
class StreamSubscription(ndb.Model):
  #stream_id  = ndb.KeyProperty(kind = Greeting, required = True)
  # keyproperty - like a reference to the object. generate based on 'Greeting' to tie together, i think
  stream_id  = ndb.KeyProperty(kind = Greeting, required = True)
  user_id    = ndb.UserProperty( required = True )  # keep track of users
  subscribed = ndb.BooleanProperty( required = True ) # subscription is prereqruisite..
  date       = ndb.DateTimeProperty(auto_now_add=True, indexed = False) # date is purely for viewing in datastore :-)
  streamname = ndb.StringProperty( required = False, indexed = False)   # debug only

  @classmethod
  def get_subscribed_streams(cls, user_id):
    return cls.query(cls.user_id == user_id, cls.subscribed == True).fetch()

  @classmethod
  def get_by(cls, user_id, stream_id_key):
     return cls.query(cls.user_id == user_id, cls.stream_id == stream_id_key).get()
#</>
###############################################################################


###############################################################################
# < class_TrendingStream>
class TrendingStream(ndb.Model):
  streamsList = ndb.KeyProperty(kind = Greeting, repeated = True)
# < class_TrendingStream>
###############################################################################


###############################################################################
# < class_DigestInformation>
# store user email frequency preferences ("digest")
class DigestInformation(ndb.Model):
  useraccount = ndb.UserProperty(required = True)
  frequency   = ndb.IntegerProperty(required = True)
# < class_DigestInformation>
###############################################################################


###############################################################################
#< class_UserInfo>
# create a user model to hold data , store it in the Guestbook/User key
# user class will store subscribed streams
# TODO: implement this as the 'Guestbook' and it will inheirit streams, subscriptions
#       because these classes claim 'Guestbook' as acnestor
class UserInfo(ndb.Model):
  author = ndb.UserProperty()
  content = ndb.StringProperty() # TODO: convert to 'streamid'
  streamid = content              # TODO: I hope this works ; create a stream and then double-check in the console
  date = ndb.DateTimeProperty(auto_now_add=True)

  img_subscribed = ndb.StringProperty(indexed=False, repeated=True)

#</class_UserInfo>
###############################################################################

###############################################################################
#< class MainPage>
# good for 'add stream'
# balsamiq1: return to 'manage' page on form submit
class MainPage(webapp2.RequestHandler):
    def get(self):
        #TODO: convert multiple self.response.write calls into multiple string concats and one call 
        # look up guestbook
        guestbook_name = self.request.get('guestbook_name',
                                          DEFAULT_GUESTBOOK_NAME)

        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        response = TEMPLATE_NAVIGATION
        response = bilder_templates.generateContainerDiv('<h1>Handler: MainPage<br/>(frmly Create Stream)</h1>' + response,'#C0C0C0')
        response = '<html>\n  <body>\n' + response + '\n  </body>\n</html>'

        self.response.write(response)
#</class MainPage>
###############################################################################


###############################################################################
#< class Manage>
# * management (in which you take a user id and return two lists of streams)
#TODO:
# balsamiq1: stream hyperlink goes to 'view a single stream' page, increases viewcount
#TODO:
# balsamiq2: return to management page on submission 
# -> go to handler for deleting and then return to 'Manage'
class Manage(webapp2.RequestHandler):
  def post(self):
    postVarDict = {}
    # < read in options>
    try: # json input
      postVarDict = json.loads(self.request.body)
      # TODO: move after try/catch
      if(not 'user_name' in postVarDict):
        postVarDict['user_name'] = get_user_data()
    except: # x-www-form
      #redirect = self.request.get('redirect',1) # for now, simply check if true is defined
      for param in ['delete',]:
        postVarDict[param] = self.request.get(param)
    #</read in options>

    # get both stream and sub deletes, since removing stream requires removing sub
    #(TODO: delete sub should delete stream :-) )
    self.response.write(json.dumps(postVarDict))

    if('delete' in postVarDict):
      if(postVarDict['delete'] == 'stream'):
        # get all stream items
        itemDeleteList = self.request.get_all('stream_delete')
        if(1):
          self.response.write(json.dumps(itemDeleteList))
        self.delete_streams(itemDeleteList)
        #delete subscription and stream
        print('')
      if(postVarDict['delete'] == 'subscription'):
        #delete subscription
        # get all stream items
        itemDeleteList = self.request.get_all('stream_unsub')
        if(0): # DEBUG
          self.response.write(json.dumps(itemDeleteList))
        #delete subscription
        self.delete_subscriptions(itemDeleteList)
        print('')
      if(postVarDict['delete'] == 'subscription'):
        #delete subscription
        print('')
    self.redirect('/manage') #TODO: don't do this
  def delete_subscriptions(self,stream_idList):
    print('')
    for streamid in stream_idList:
      jsonStr = sendJson(self, jsondata={"stream_name": streamid, "submanage": "unsubscribe"}, service_name = 'streamsubscribe')
    return
  def delete_streams(self,stream_idList):
    print('')
    for streamid in stream_idList:
      jsonStr = sendJson(self, jsondata={"streamid": streamid, "manage_action": "delete"}, service_name = 'managestream')
    return


  def get(self):
    if users.get_current_user():
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'
    else:
        url = users.create_login_url(self.request.uri)
        url_linktext = 'Login'
    
    # look up guestbook
    #TODO: phasing in 'user_name' instead of 'guestbook_name'; don't want to have to do a global find/replace and then test any ensuing messes
    user_name = self.request.get('guestbook_name', DEFAULT_GUESTBOOK_NAME)
    user_name = self.request.get('user_name', DEFAULT_GUESTBOOK_NAME)
    # < debug query subscriptions>
    subscription_query = StreamSubscription.query(
        ancestor=guestbook_key(user_name))#.order(-Greeting.date)
    #TODO: debug this, from http://stackoverflow.com/a/11724844 # subscription_query = StreamSubscription.get_subscribed_streams(user_name)
    # vvv doesn't work: BadValueError: Expected User, got 'default_guestbook'  vvvvv
    #subscription_query = StreamSubscription.get_subscribed_streams(user_name)
    # mock user: # src: http://stackoverflow.com/a/6230083
    import os
    os.environ['USER_EMAIL'] = 'poland.barker@swedishcomedy.com'
    os.environ['USER_ID'] = 'pbarker'
    #os.environ['AUTH_DOMAIN'] = 'testbed' # To avoid  /google/appengine/api/users.py:115 - AssertionError: assert _auth_domain
    #os.environ['USER_IS_ADMIN'] = '1'     #  for an administrative user
    #user_name = 'poland_barker'
    if users.get_current_user():
        user_name = users.get_current_user()
    #user_name = 'pbarker'
    subscription_query = StreamSubscription.get_subscribed_streams(user_name)
    # reset username - remaining examples need DEFAULT_GUESTBOOK_NAME
    user_name = self.request.get('user_name', DEFAULT_GUESTBOOK_NAME)
    # < debug query subscriptions>

    #< retrieve greetings>
    # TODO: this part is good for 'manage'
    # Ancestor Queries, as shown here, are strongly consistent with the High Replication Datastore. 
    # Queries that span entity groups are eventually consistent.
    # If we omitted the ancestor from this query there would be a slight chance 
    #  that 'Greeting' that had just been written would not show up in a query.

    greetings_query = Greeting.query(
        ancestor=guestbook_key(user_name)).order(-Greeting.date)
    greetings = greetings_query.fetch(10)
    #DEBUG
    if(0):
      debugStr = str(greetings_query)
      debugStr += '<br/>\n'
      debugStr += '<br/>\n'
      debugStr += '<br/>\n'
      debugStr += '<br/>\n'
      debugStr = str(greetings)
      debugStr += '<br/>\n'

      self.response.write(debugStr)
      return

    #TODO: stop calling it a greeting:

    # calling it 'greetingsOwnList' for better conversion to 'streams i own' and 'streams i subscribe to'
    #TODO: get the stream that 'subscription' points to
    greetingsOwnList = []
    for greeting in greetings:
      greetingDict = {}
      if greeting.author:
        author = greeting.author.nickname()
      else:
        author = 'Anonymous'
      greetingDict['author'] = author
      greetingDict['content'] = cgi.escape(greeting.content)
      #TODO: remove HACK, implement nicely
      contentHref = '<a href=/viewsinglestream?streamid=%s>%s</a>' % \
          (urllib.quote_plus(greetingDict['content']) , greetingDict['content'])
      greetingDict['contenthref'] = contentHref
      #</HACK>
      greetingDict['date'] = str(greeting.date)
      greetingDict['img_amount'] = str(greeting.img_amount)
      greetingDict['views'] = str(greeting.views)
      greetingsOwnList.append(greetingDict)
    #</retrieve greetings>
    # < query subscriptions>
    #subscription_query = StreamSubscription.query(
    #    ancestor=guestbook_key(user_name))#.order(-Greeting.date)
    #TODO: debug this, from http://stackoverflow.com/a/11724844 # subscription_query = StreamSubscription.get_subscribed_streams(user_name)
    subsMatchList = subscription_query#.fetch()
    # store data from all matches
    userSubsList = []
    for sub in subsMatchList:
      subParamDict = sub.to_dict(exclude=['date'])
      #userSubsList.append(subParamDict) # this is the StreamSubscription object, no point in that now is there, love?
      # WARNING: DO NOT LET GO OF THIS! vvvv
      #userSubsList.append(subParamDict['stream_id'].get()) # that's more like it, I hope
      #TODO: sub.stream_id.get().to_dict()
      userSubsList.append(subParamDict['stream_id'].get().to_dict()) # that's more like it, I hope
      # WARNING: DO NOT LET GO OF THIS! ^^^^
    # </query subscriptions>
    greetSubTr = ''
    greetOwnTr = ''

    html_form_checkbox = lambda name,value: '<input type="checkbox" name="%s" value="%s">' % (name,value)
    # own
    # loop through all greetings
    for greetDict in greetingsOwnList:
      valueList = [] 
      #TODO: make a list with common elements to 'own' and 'sub' and then just add on for 'sub'
      attribOrderList = ['contenthref','date','img_amount']
      for attrib in attribOrderList:
        valueList.append(greetDict[attrib])
      # add the checkbox
      # table 'delete' template
      #TODO: add insert row function?
      valueList.append(html_form_checkbox('stream_delete',greetDict['content']))
      # build the row
      greetOwnTr += bilder_templates.generateTableRow(valueList)


    # < subscribed table>
    # loop through all subscriptions
    for subDict in userSubsList:
      valueList = [] 
      #valueList.append(subDict.to_dict())
      attribOrderList = ['content','date','img_amount','views']
      for attrib in attribOrderList:
      #solved: for attrib in subDict:
        valueList.append(subDict[attrib])
        #solved: valueList.append(attrib + ' = ' + str(subDict[attrib]) + ' is ' + type(subDict[attrib]).__name__)

      # add the checkbox
      valueList.append(html_form_checkbox('stream_unsub',subDict['content']))
      # build the row
      greetSubTr += bilder_templates.generateTableRow(valueList)
    # < /subscribed table>

    ####################################
    # Table Generation
    ## generate table headers
    # table: own streams
    headerOwn = bilder_templates.generateTableRow(['Name','Last New Picture','Number of Pictures','Delete'])
    headerOwn += greetOwnTr

    # table: own streams
    headerSub = bilder_templates.generateTableRow(['Name','Last New Picture','Number of Pictures','Views','Unsubscribe'])
    headerSub += greetSubTr

    ## generate tables
    table_streams_own = bilder_templates.get_html_template_table(headerOwn)
    table_streams_sub = bilder_templates.get_html_template_table(headerSub)

    ## generate form for delete/unsub stream
    # define table layout: 
    gen_html_form = lambda action,method,submit_value,contents: '<form action="%s" method="post">\n  %s\n<input type="submit" value="%s">\n</form>' % (action, contents,submit_value)

    # form: own streams
    #TODO: make a fancy button with the (X) on it
    form_streams_own = gen_html_form('manage?delete=stream',      'post','(X) Delete Checked Streams',      table_streams_own)
    form_streams_sub = gen_html_form('manage?delete=subscription','post','(X) Unsubscribed Checked Streams',table_streams_sub)


    contentList = []
    #TODO: add form to table to delete selected streams - just have a checkbox with the stream id
    # https://apt.mybalsamiq.com/mockups/1083489.png?key=c6286db5bf27f95012252833d5214a336f17922c
    response = TEMPLATE_NAVIGATION
    #response += greetTable
    contentList.append('<h3>Streams I Own</h3>')
    contentList.append('<p>Total Streams:%s<p>' % str(len(greetings)))
    contentList.append(form_streams_own)
    contentList.append('<h3>Streams I Subscribe to</h3>')
    contentList.append('<h4>TODO: currently subscriptions are automatic</h4>')
    contentList.append('<p>Total Streams:%s<p>' % str(len(subsMatchList)))
    contentList.append(form_streams_sub)
    for content in contentList:
      response += content + '\n'
    #response += bilder_templates.get_html_template_table()
    # wrap in grey div
    response = bilder_templates.generateContainerDiv('<h1>Handler: Manage</h1>' + response,'#C0C0C0')
    response = '<html>\n  <body>\n' + response + '\n  </body>\n</html>'
    self.response.write(response)
    #self.response.write('{"stream1": "name1", "payload": "some var"}')
#</class Manage>
###############################################################################


###############################################################################
#< class ViewSingleStream>
#TODO: abstract the query into a separate 'post' service in order to satisfy this requirement:
# * view a stream (which takes a stream id and a page range and returns a list of URLs to images and a page range)
# doc: different kinds of request handlers
# https://developers.google.com/appengine/docs/python/tools/webapp/requesthandlers
#TODO: 'more pictures' https://piazza.com/class/hz1r799mk0ah?cid=56
#TODO: todo: viewsinglestream does not display image immediately, waits until page reload -> convert to service-based 
#TODO TODAY 20140919
#TODO: make 'get self' call 'post self' to get the images to display
#TODO: range - "pagination" through DB of images, i.e return <range_lower>:<range_upper> images at a time
class ViewSingleStream(webapp2.RequestHandler):
#TODO: split 'get(self):' into subroutines so that 'get(post)' can play along as well
  def post(self):
    postVarDict = {}
    # < read in options>
    try: # json input
      postVarDict = json.loads(self.request.body)
      if(not 'user_name' in postVarDict):
        postVarDict['user_name'] = DEFAULT_GUESTBOOK_NAME
    except: # x-www-form
      #redirect = self.request.get('redirect',1) # for now, simply check if true is defined
      for param in ['streamid', 'stream_id', 'geoview', 'range',]:
      #for param in ['streamid', 'range',]:
        postVarDict[param] = self.request.get(param, 'unspecified')
    #</read in options>
    # set internal vars
#    user_name = postVarDict['user_name']
    stream_id = postVarDict['stream_id']

    # by key: uses 'parent' to help avoid incorrect results
    streamInst = ndb.Key(Greeting,stream_id, parent = guestbook_key()).get()
    #self.response.write(str(streamInst)) # for debug, examine the 'key=Key(...)'
    imgList = [] 
    # see if there are any urls attached; if so then display them
    jsonDataDict = {}
    if streamInst.imgurls:
      imgList = streamInst.imgurls
      jsonDataDict['imgurls'] = streamInst.imgurls
      jsonDataDict['range'] = len(streamInst.imgurls)
    if streamInst.coverurl:
      jsonDataDict['coverurl'] = streamInst.coverurl

    # GPS data - add mock gps coordinates for now
    # TODO: if stream has gps data don't add it, blah blah
    if('geoview' in postVarDict):
      jsonDataDict = self.genGeoViewJson(streamInst)

    
    #TODO: range - "pagination" through DB of images, i.e return <range_lower>:<range_upper> images at a time
    range = len(imgList)
    jsonStr = json.dumps({'imgurls':imgList,'range':range})
    jsonStr = json.dumps(jsonDataDict)
    # update view-count
    streamInst.views += 1
    import datetime
    streamInst.viewtimes.append(datetime.datetime.now())
    # loop through list and look for entries older than one hour
    streamInst.put()

    self.response.write(jsonStr)
  # accept streamInst and extract information
  def genGeoViewJson(self, streamInst):
  # json format:
  # {"markers":[
  # { "latitude":57.9969944, "longitude":12.9865, "title":"thing",      "content":"<p>thing1</p><img width='100px' height='100px' src=\"<imgurl>\"/>"  , "timestamp":"20140530"},
  # ]}
    gpsJsonList = []
    dateTime = 0
    if (streamInst.date):
      #dateTime = str(streamInst.date)
      dateTime += streamInst.date.year  * 1000
      dateTime += streamInst.date.month * 100
      dateTime += streamInst.date.day

    if (streamInst.imgurls):
      for imgUrl in streamInst.imgurls:
        gpsJsonDict = {}
        gpsJsonDict['latitude'], gpsJsonDict['longitude'] = self.genMockGpsCoord()
        gpsJsonDict['content']  = "<img width='100px' height='100px' src=\"%s\"/>" % (imgUrl)
        gpsJsonDict['timestamp'] = dateTime
        gpsJsonList.append(gpsJsonDict)
    #self.response.write(json.dumps(gpsJsonList))
    return {'markers':gpsJsonList}
  def genMockGpsCoord(self):
    import random
    latitude  = random.randint(-900000000,900000000) / 10000000
    longitude = random.randint(-900000000,900000000) / 10000000
    return (latitude,longitude)





  def get(self):
    response = '' # store request response
    response += TEMPLATE_NAVIGATION
    # get stream name
    stream_name = self.request.get('streamid','stream_unspecified')
    # http://localhost:8080/viewsinglestream?streamid=kjljljkl
    query_params = urllib.urlencode({'streamid': stream_name})
    actionFuture = '/img_upload?' + query_params 
    #blobstore
    upload_url = blobstore.create_upload_url('/upload_fromform?' + query_params)
    action = upload_url


    # < image gallery>
    # Note: keys: imgurls, coverurl, range
    imgJson = sendJson(self, jsondata={'stream_id':stream_name}, service_name = 'viewsinglestream')
    #imgJson = sendJson(self, jsondata=json.dumps({'stream_id':stream_name}), service_name = 'viewsinglestream')

    html_imggallery = ''
    imgDict = json.loads(imgJson)
    if('imgurls' in imgDict):
      imgList = imgDict['imgurls']
      # TODO: range (default 3?), 'more pictures'
      html_imggallery = '<h2>%s Gallery</h2>' % (stream_name.title())
      html_imggallery += bilder_templates.gen_html_gallery(imgList = imgList, imgrange = 5)
    # </image gallery>
    html_uploader = '<h2>Add Images</h2>'
    html_uploader += load_template(self, file = 'templates/blueimp_uploader.html',
      type='jinja',
      )

    # GeoView link generation:
    geoview_href = '<a class="btn btn-primary" href=%s/geoview?streamid=%s>Geo View</a>' % (self.request.host_url, stream_name)
    html_geoview = bilder_templates.generateContainerDivBlue(geoview_href)

    #response += bilder_templates.generateContainerDivBlue(
    #    bilder_templates.get_page_template_upload_file(action)
    #    + 'Add an Image')
    subscriptionUrlJunk = '/%s?' % ('form2json')
    #response += bilder_templates.generateContainerDivBlue(bilder_templates.get_html_template_stream_subscribe(subscriptionUrlJunk))
    html_subscribe = bilder_templates.generateContainerDivBlue(
        bilder_templates.get_html_template_stream_subscribe(
          subscriptionUrlJunk,
          stream_name,

          )
        )
    response += html_subscribe
    response += html_imggallery
    response += html_geoview
    response += html_uploader
    # boilerplate
    response = bilder_templates.generateContainerDiv('<h1>Handler: ViewSingleStream</h1>' + response,'#000000')#'#C0C0C0')
    response = bilder_templates.get_html_body_template(response)
    self.response.write(response)
#</class ViewSingleStream>
###############################################################################

###############################################################################
# print json strings in html-friendly format
def htmlPprintJson(jsonParam):
  jsonStr = ''
  #jsonParam = json.dumps(object)
  jsonData = json.loads(jsonParam)
  import pprint
  jsonStr += '<br />\njson.loads jsonString:<br/>' + '<pre>' +  pprint.pformat(jsonData,indent=4) + '</pre>'
  return jsonStr
###############################################################################

###############################################################################
#< class_ViewAllStreamsService>
#* view all streams (which returns a list of names of streams and their cover images)
# balsamiq1:
# * show cover img of each stream.
# * sort in order of increasing creation time, starting top left
class ViewAllStreamsService(webapp2.RequestHandler):
  def post(self):
    response = ''

    # TODO: ?look up all users?
    user_name = self.request.get('user_name', DEFAULT_GUESTBOOK_NAME)
    # look up streams
    streams_query = Greeting.query(
        ancestor=guestbook_key(user_name)).order(-Greeting.date)
    streams = streams_query.fetch()
    response += 'total queries found: ' + str(len(streams))

    # list of hashes
    #TODO: use 'GenericQueryService' 
    streamsList = []
    for stream in streams:
      streamDescDict = {}
      # https://developers.google.com/appengine/docs/python/ndb/modelclass#Model_to_dict
      streamDescDict = stream.to_dict(include=['streamid','coverurl'])
      streamsList.append(streamDescDict)

    
    jsonStr = json.dumps(streamsList)

    response += 'json data:<br/>\n' + jsonStr

    response = bilder_templates.generateContainerDivBlue(response)
    if(0): # DEBUG: change 'def post(self)' to 'def get(self)' and comment out '''\ndef get(self)\n'''
      self.response.write(response)
    self.response.write(jsonStr)

# debug post, then do get 
  def get(self):
    response = '' # content

    # < query>
    # create query_params
    jsonStr = ''
    url = self.request.host_url
    service_url = '/viewallstreams'
    #service_url = '/jsonreturntest'
    url += service_url
    #result = urlfetch.fetch(url + urllib.urlencode(query_params),method=urlfetch.POST)
    result = urlfetch.fetch(url,method=urlfetch.POST)
    if(result.status_code == 200):
      jsonStr = 'Total Streams:<br/>\n'
      jsonData = result.content
      jsonStr += htmlPprintJson(jsonData)
      #jsonStr += json.loads(result.content)
    else:
      jsonStr = 'request failed: ' + str(result.status_code)
    response += bilder_templates.generateContainerDivBlue(jsonStr)
    # < query>

    # <covers>
    # cover images
    if(1):
      streamDescList = json.loads(jsonData)
      streamCoverList = []
      galleryConfList = []
      for streamDict in streamDescList:
        streamCoverList.append(streamDict['coverurl'])
        tmpConf = {
          'src'     : streamDict['coverurl'],
          'caption' : streamDict['streamid'],
        }
        galleryConfList.append(tmpConf)
#working till here

      # legacy:
      #response += bilder_templates.gen_html_gallery(imgList = streamCoverList,)# imgrange = 5)
      # for upcoming better gallery:
      response += bilder_templates.gen_html_gallery(imgConfJson = json.dumps(galleryConfList),) # imgrange = 5)
    # </covers>

    # < consolidate and write response>
    ## make navigation sit on top
    response = TEMPLATE_NAVIGATION + response
    ## make header sit on top
    response = bilder_templates.generateContainerDiv('<h1>Handler: ViewAllStreamsService</h1>' + response,'#C0C0C0')
    response = bilder_templates.get_html_body_template(response)
    self.response.write(response)
#</class_ViewAllStreamsService>
###############################################################################


###############################################################################
#< class_GenericSearchQuery>
# * search streams (which takes a query string and returns a list of streams (titles and cover image urls) that contain matching text
class GenericQueryService(webapp2.RequestHandler):
  def get(self):
    self.post()
  def post(self):
    querydebug = 0 # 1: add bogus results 2: disable redirect, print some junk
    response = ''
    ## store values
    # HACK: for automation, a script can pass in 'redirect=0' to prevent the redirect-induced error : '302|Found'
    redirect = ''
    user_name = ''
    search_query = ''
    jquery_keywords_bool = 0  # jquery autcomplete requires special format. set if 'term' passed in query_params
    # load in values
    #self.response.write(self.response.__dict__)
    #return
    #if(self.response.headers["Content-Type"] == 'application/json'):
    try: #( json.loads(self.request.body)):
      jsonDict = json.loads(self.request.body)
      if(not 'user_name' in jsonDict):
        jsonDict['user_name'] = DEFAULT_GUESTBOOK_NAME
      user_name          = jsonDict['user_name']
      if('search_query' in jsonDict):
        search_query = jsonDict['search_query']
      # for debug
      if('redirect' in jsonDict):
        redirect = jsonDict['redirect']
      else:
        redirect = 1
    except: # x-www-form
      redirect = self.request.get('redirect',1) # for now, simply check if true is defined
      postVarDict = {}
      for param in ['search_query','term']:
        postVarDict[param] = self.request.get(param, 'unspecified')
      # set defaults:
      # if jqueryui-autocomplete is making the request it will use '?term=<query>'
      if('term' in postVarDict and postVarDict['term'] != 'unspecified'):
        postVarDict['search_query'] = postVarDict['term']
        jquery_keywords_bool = 1

      # TODO: ?look up all users?
      user_name = self.request.get('user_name', DEFAULT_GUESTBOOK_NAME)
      #guestbook_name     = jsonDict['guestbook_name']
      #NOTE: default_value is only good if the form element was not submitted; even an empty box counts as data
      #queryExpression = self.request.get('search_query', default_value='*') # TODO: use the * for returning all results
      search_query = postVarDict['search_query']
    # done
    queryExpression = search_query
    # look up streams
    #TODO: add a search
    #   implement several modes
    #   lookup: do the query by name, as for 'view single stream'
    #   search: get everything, then regex match
    #queryExpression = 'nerfherder'
    # list of matched streams
    queriedStreams = []
    # exact filter
    # 1. get exact string #TODO
          #<stub> http://stackoverflow.com/a/12267140
          #streams_query = Greeting.query(Greeting.content==queryExpression,
          #    ancestor=guestbook_key(user_name)).order(-Greeting.date)
          #</stub>
    # no filter
    # 2. get everything - no partial matches anyway
    streams_query = Greeting.query(
        ancestor=guestbook_key(user_name)).order(-Greeting.date)
    queriedStreams = streams_query.fetch()
      
    streams = streams_query.fetch()
    response += 'total queries found: ' + str(len(streams)) + '<br/>\n'

    # list of hashes
    streamsList = []
    # TODO: return real results; these are placeholders
    #TODO: form a real query instead of try...except
    #TODO: once 'Greeting' object is fixed, remove check for 'content'
    # define 'content' as 'name'
    for stream in streams:
      streamDescDict = {}

      # https://developers.google.com/appengine/docs/python/ndb/modelclass#Model_to_dict
      streamDescDict = stream.to_dict(include=['tags','streamid'])

      # regex - don't add dict if no match
      add = 0
      if(queryExpression):
        import re
        #special case: raise error, v # invalid expression ; error: nothing to repeat
        if(queryExpression == '*'):
          queryExpression = '.*.%s.*' % queryExpression
        else: # match anything before and after query
          queryExpression = '.*%s.*' % queryExpression
        # "search" is meant to be performed on certain attribs of Stream
        #  however, some attribs are string, some could be int, some are repeated (list), etc
        #  This means we can not simply re.match on the values of the dict because re.match does not accept list as an argument
        # simplest way, off-hand, is to put all attribs meant for search into a list,
        #   then re.match on each of the elements. 
        stringList = []
        # string attribs
        for field in ['streamid']:
          stringList.append(streamDescDict[field])
        # repeated attribs (list)
        for field in ['tags']:
          stringList.extend(streamDescDict[field])
        for field in stringList:
          if(re.match(queryExpression ,field)):
            add |= 1 # or with one
            #continue
      else:
        add = 1
      if(add == 1):
        if( jquery_keywords_bool == 1):
          streamDescDict = stream.getKeyWordsDict()
        streamsList.append(streamDescDict)
    # 3. do a regex
    # note: this is not a good idea; only supports full-word matches
    #streams_query = Greeting.query( Greeting.content == queryExpression )
    #if(queryExpression):
    #for streamDict in streamsList

    # < DEBUG - add fake results>
    #TODO: fix this
    if(querydebug >= 1):
      tmpStreamsList = []
      tmpStreamsList.append({'TODO':'return real results!'})
      tmpStreamsList.append({'Service':'GenericQueryService'})
      tmpStreamsList.append({'stream1':'title1'})
      tmpStreamsList.append({'stream2':'title2'})
      tmpStreamsList.append({'NOTE':'end_fakeresults'})
      #streamsList.extend(tmpStreamsList)
      #tmpStreamsList.extend(StreamsList)
      #streamsList = tmpStreamsList
      streamsList = tmpStreamsList + streamsList
    # </DEBUG - add fake results>

    # prepare response as json
    jsonStr = json.dumps(streamsList)
    response = jsonStr

    # encode json for returning via GET
    query_params = urllib.urlencode({'jsonstring': jsonStr})
    action = '/searchallstreams?' + query_params 
    #action = '/searchallstreams'

    if(querydebug >= 2): #DEBUG
      import pprint
      self.response.write('streams list:\n' + pprint.pformat(streamsList))

      response = 'json data:<br/>\n' + response
      response = bilder_templates.generateContainerDivBlue(response)
      response = bilder_templates.generateContainerDivBlue('<p>query params:</p>\n' + query_params)
      response = bilder_templates.generateContainerDivBlue('<p>search_query:</p>\n' + queryExpression)
      self.response.write(response)
    else:
      self.response.write(response)
      #TODO: make 'action' a dynamic value (or create a form-handler that routes form requests)
      if(redirect == 1): # self.redirect breaks other scripts with a '302|Found'
        self.redirect(action)
#</class_GenericSearchQuery>
###############################################################################


###############################################################################
#< class_SearchAllStreamsService>
# * search streams (which takes a query string and returns a list of streams (titles and cover image urls) that contain matching text
#TODO: all of thisvvvv
  '''
   balsamiq1:
   * return to self on form submit
   * show first 5 results and cover img
   * click on cover img -> view stream page
   * click on cover img -> incr numviews 
      Note: this is in common with the normal 'view a stream' - reuse somehow!
  '''
#TODO: return only five results!!!!

class SearchAllStreamsService(webapp2.RequestHandler):
  def get(self):
    response = '' # content

    jsonParam = self.request.get('jsonstring')

    # < parse_json>
    jsonStr = ''
    if(jsonParam):
      #TODO: validate json data - use function from failed start of this project
      jsonData = json.loads(jsonParam)
      jsonStr = jsonParam
      if(1): #DEBUG info
        jsonStr = '<br />\njson data:<br/> ' + jsonParam
        import pprint
        jsonStr += '<br/><br />\ndeserialised:<br/>' + '<pre>' +  pprint.pformat(jsonData,indent=4) + '</pre>'
    # </parse_json>
    # <start the gallery rendering>
    galleryStr = ''
    if(jsonStr):
      galleryStr += jsonStr
    else:
      galleryStr += '<p>no images</p>'

    response += bilder_templates.generateContainerDiv(galleryStr,'wheat',title='Stream Gallery')
    #response += bilder_templates.generateContainerDiv(jsonStr,bgcolor='wheat',title='Stream Gallery')

    # output page
    response = self.genPageContent(response)
    self.response.write(response)

  def genPageContent(self,response):

    #response = ''
    form = bilder_templates.get_html_template_search_form(action='/genericquery')
    response += bilder_templates.generateContainerDivBlue("<p>Conventional Search</p>" + form)

    # add html form 
    response += bilder_templates.generateContainerDivBlue(
                  "<p>Search with Autocompletion</p>" + 
                  #load_template(self, file = 'templates/autocomplete_template.html')
                  load_template(self, file = 'templates/autocomplete_template.html',
                    type='jinja',
                    values = {'host':self.request.host_url + '/genericquery?redirect=0'}

                    )
                )

    # < consolidate and write response>
    ## make navigation sit on top
    response = TEMPLATE_NAVIGATION + response
    ## make header sit on top
    response = bilder_templates.generateContainerDiv('<h1>Handler: SearchAllStreamsService</h1>' + response,'#C0C0C0')
    response = bilder_templates.get_html_body_template(response)
    return response
#</class_SearchAllStreamsService>
###############################################################################


#< class ImgUpload>
#TODO: for now, just store strings; do photos later
#TODO: see https://developers.google.com/appengine/docs/python/tools/webapp/blobstorehandlers
# class PhotoUploadHandler(blobstore_handlers.BlobstoreUploadHandler):
class ImgUpload(webapp2.RequestHandler):
  def post(self):
    response = ''

    # look up stream
    # TODO: determine whether 'stream_name' is needed
    stream_name = self.request.get('streamid')
    
    #< read in options>
    #TODO: convert to - postVarDict = {}
    paramDict = {}
    try: # json input
      paramDict = json.loads(self.request.body)
      # TODO: move after try/catch
      if(not 'user_name' in paramDict):
        paramDict['user_name'] = get_user_data()
    except: # x-www-form
      for param in ['streamid', 'file_name', 'file_comments']:
        paramDict[param] = self.request.get(param, 'unspecified')
        response += param + ': ' + paramDict[param] + '<br/>'
    #</read in options>

    # have to retrieve stream from DB
    # stream = get the thingy
    #TODO: what about the ancestor query? it did not work with that.
    #TODO: what about spaces? will stored streamid have spaces or no?
    #TODO: do I need to loop through the query? How do I know if I got the object I want?
    #NOTE: the printout of a few DB objects:
    # streams_query:
    # Query(kind='Greeting', filters=FilterNode('content', '=', 'indexedibix'))
    # streams: 
    # v this is an array with only one element: [Greeting( <etc> )]
    # [Greeting(key=Key('Guestbook', 'default_guestbook', 'Greeting', 6333186975989760), author=None, content=u'indexedibix', date=datetime.datetime(2014, 9, 14, 9, 24, 32, 37000), streamid=None)]
    # streamInstance: # note the various 'imgurls'
    # Greeting(key=Key('Guestbook', 'default_guestbook', 'Greeting', 6333186975989760), author=None, content=u'indexedibix', date=datetime.datetime(2014, 9, 14, 9, 24, 32, 37000), imgurls=[u'File Name', u'File Name', u'File Name', u'File Name', u'File Name', u'indexedibix'], streamid=None)
    # 
    streams_query = Greeting.query( Greeting.content == paramDict['streamid'])
    response += 'streams_query:<br/>'+ repr(streams_query)
    response +=  '<br/>'
    streams = streams_query.fetch()
    response += 'streams: <br/>' + repr(streams)
    response +=  '<br/>'

    #TODO: iterate later...
    for streamInstance in streams:
      response += 'streamInstance:<br/>' + repr(streamInstance)
      response +=  '<br/>'
      # image should be first, also better to overwrite existing list than manipulate (see doc for 'class Greeting'
      # "prepend" current image
      imgList = [paramDict['file_name']]

      #TODO:
      # append the current list if available
      if streamInstance.imgurls :
        imgList.extend(streamInstance.imgurls)
      # write new list to object
      streamInstance.imgurls = imgList
      streamInstance.img_amount = len(imgList)
      # update coverurl if not defined
      if(not streamInstance.coverurl):
        streamInstance.coverurl = streamInstance.imgurls[-1]
      # re-store object
      streamInstance.put()

    # create response:
    response = bilder_templates.generateContainerDivBlue(response)
    response = bilder_templates.generateContainerDiv('<h1>Handler: ViewSingleStream</h1>' + response,'#C0C0C0')
    #stream_query = Greeting.query
#TODO: redirect back
    query_params = urllib.urlencode({'streamid': stream_name})
    action = '/viewsinglestream?' + query_params 
    #DEBUG: 
    if(0):
      self.redirect(action)
    else:
      self.response.write(response)
#< class ImgUpload>
###############################################################################


class UploadHandlerFromForm(blobstore_handlers.BlobstoreUploadHandler):
  def post(self):
    #< read in options>
    #TODO: convert to - postVarDict = {}
    paramDict = {}
    try: # json input
      paramDict = json.loads(self.request.body)
      # TODO: move after try/catch
      if(not 'user_name' in paramDict):
        paramDict['user_name'] = get_user_data()
    except: # x-www-form
      for param in ['streamid', 'file_name', 'file_comments']:
        paramDict[param] = self.request.get(param, 'unspecified')
    #</read in options>


    upload_files = self.get_uploads('img')  # 'file' is file upload field in the form
    self.printinfo() # dump environment info; i ain't got no clue..
    #TODO: check if no file uploaded
    if(upload_files):
      blob_info = upload_files[0]
      #TODO: before redirect:
      # 1. get streamid 
      # 2. json-store the blob_info.key() in the right streamid
      #hard-coded values for now 
      #TODO: pass key, in 'img_upload' (class ImgUpload) need to parse key (see ServeHandler)
      # one way: send url directly, don't worry about saving blob key
      if(1):
        from google.appengine.api import images
        blob_url = images.get_serving_url(blob_key = blob_info.key())
      jsonStr = sendJson(self, jsondata={"file_name": blob_url , "streamid": paramDict['streamid']}, service_name = 'img_upload')
      #self.redirect('/serve/%s' % blob_info.key())
    query_params = urllib.urlencode({'streamid': paramDict['streamid']})
    action = '/viewsinglestream?' + query_params 
    #DEBUG: 
    if(1):
      self.redirect(action)
  def printinfo(self):
    paramDict = {}
    response = ''
    for param in ['streamid', 'file_name', 'file_comments']:
      paramDict[param] = self.request.get(param)
      response += param + ': ' + paramDict[param] + '<br/>'
      
    self.response.write("<p>request body</p>")
    self.response.write(self.request.body)
    self.response.write("<p>form stuff</p>")
    self.response.write(response)

class ServeHandler(blobstore_handlers.BlobstoreDownloadHandler):
  def get(self, resource):
    resource = str(urllib.unquote(resource))
    blob_info = blobstore.BlobInfo.get(resource)
    self.send_blob(blob_info)



#< htmlParen>
# wrap in p-tags
def htmlParen(string):
  string = '<p>%s</p>\n' % string
  return string
#</htmlParen>


###############################################################################
# pass in stream by name
# create new 'subscripton' for user, stream
# json in: {"action": "unsubscribe", "stream_name": stream_name}
# json in: {"action": "subscribe",   "stream_name": stream_name}
# step1: copy in 'CreateStreamService' and verify functionality
# step2: remove unneeded chunks
# caveat: some are needed to make original function work but are not needed here
# step3: add in new stuff
# TODO: run this from the 'viewsinglestream' page
class SubscribeStreamService(webapp2.RequestHandler):
  def post(self):
    # expect 'jsonstr' with everything in it
    #jsonInputDict = json.loads(self.request.get('jsonstr'))
    jsonOutputDict = {}
    jsonOutputDict['stream_info'] = {}
    jsonOutputDict['sub_info'] = {}
    jsonOutputDict['sub_info']['status'] = 'nothingdone' # change to success/fail

    # TODO: rename
    guestbook_name = self.request.get('guestbook_name', DEFAULT_GUESTBOOK_NAME)
    user_name      = self.request.get('user_name', DEFAULT_GUESTBOOK_NAME)
    streamid       = self.request.get('stream_name')


    # sub or rm?
    subscriptionAction = self.request.get('action')
    
    # do the json correction application/json
    jsonDict           = json.loads(self.request.body)
    if(not 'user_name' in jsonDict):
      jsonDict['user_name'] = DEFAULT_GUESTBOOK_NAME
    #guestbook_name     = jsonDict['guestbook_name']
    user_name          = jsonDict['user_name']
    streamid           = jsonDict['stream_name']
    if('submanage' in jsonDict):
      subscriptionAction = jsonDict['submanage']

    # TEMP - look up string by id - TODO: handle with GenericQueryService
    queryExpression = streamid
    streams_query = Greeting.query(
        Greeting.content==queryExpression,
        ancestor=guestbook_key(user_name)).order(-Greeting.date)
    queriedStreams = streams_query.fetch()
    jsonOutputDict['stream_info']['number_found_streams'] = len(queriedStreams)

    streamReprList = []
    for stream in queriedStreams:
      streamReprList.append(stream.to_dict(exclude = ['date','author','viewtimes']))
    jsonOutputDict['stream_info']['total_streams'] = streamReprList
    #VIM: jump to empty line: shift^] shift^[

    #stream = streams_query.fetch()[0]
    stream = streams_query.get()
    #jsonOutputDict['stream_info']['found_streams_properites'] = stream.to_dict(exclude = ['date','author'])

    if users.get_current_user():
        stream.author = users.get_current_user()
    else:
      #  stream.author = 'anonymous' - nono! it's a usertype, can't simply asign
      # < mock user>
      # mock user: # src: http://stackoverflow.com/a/6230083
      import os
      os.environ['USER_EMAIL'] = 'poland.barker@swedishcomedy.com'
      os.environ['USER_ID'] = 'pbarker'
      #   < more mock user values>
      #os.environ['AUTH_DOMAIN'] = 'testbed' # To avoid  /google/appengine/api/users.py:115 - AssertionError: assert _auth_domain
      #os.environ['USER_IS_ADMIN'] = '1'     #  for an administrative user
      #   </more mock user values>
      # </mock user>
    user_name = stream.author

    ####################################################################
    # NOTE: key can be  '.key' returns either 'ID' or 'Key Name':
    #   GuestbookNDB: name=default_guestbook > Greeting: name=this_has_a_subscription
    #   GuestbookNDB: name=default_guestbook > Greeting: id=6650945836417024
    if(subscriptionAction):
      ################################ 
      if(subscriptionAction == 'subscribe'):
        jsonOutputDict['sub_info']['sub'] = {}
        jsonOutputDict['sub_info']['sub']['sub_matches'] = []
        jsonOutputDict['sub_info']['sub']['sub_fail'] = []
        jsonOutputDict['sub_info']['sub']['total_matches'] = []
        streamSub = StreamSubscription(
            parent     = guestbook_key(guestbook_name),
            id         = "subscription_%s_streamid_%s" % (user_name, streamid),
            stream_id  = stream.key, # key -  Special property to store the Model key. 

            user_id    = user_name,
            subscribed = True,
          )
        # NOTE: this puts AND logs
        jsonOutputDict['sub_info']['sub_key'] = repr(streamSub.put())
        jsonOutputDict['sub_info']['subscription_properites'] = streamSub.to_dict(exclude = ['stream_id','user_id','date','author'])
        jsonOutputDict['sub_info']['status'] = '0'
      ################################ 
      # this will be called from a form where the subscription already exists; don't worry about duplicates as we are supposed to prevent those...
      # loop through all user_name subscriptions and find the ones pointing to 'stream_id'
      #   NOTE: duplicates would be bad
      if(subscriptionAction == 'unsubscribe'):
        jsonOutputDict['sub_info']['unsub'] = {}
        jsonOutputDict['sub_info']['unsub']['unsub_success'] = []
        jsonOutputDict['sub_info']['unsub']['unsub_failure'] = []
        jsonOutputDict['sub_info']['unsub']['total_matches'] = []
        # query all subscriptions
        # Note: assume user_name is already spoofed/set as we are within the SubscribeStreamService and that is done a few lines above
        # get all user_name subscriptions
        subscription_query = StreamSubscription.get_subscribed_streams(user_name)
        subsMatchList = subscription_query
        jsonOutputDict['sub_info']['unsub']['amount_found'] = len(subsMatchList) # this matches
        userSubsList = []
        subReprList = []
        for user_sub in subsMatchList:
          tmpSubDict = user_sub.to_dict(exclude = ['user_id','date','stream_id'])
          tmpSubDict['date'] = repr(user_sub.date)
          tmpSubDict['type'] = type(user_sub).__name__
          subReprList.append(tmpSubDict)
          # vvv probably don't need this vvvv
          if(user_sub.stream_id == stream.key):
            #TODO: add the subscription key, as we do for adding a subscription: "sub_key": "Key('GuestbookNDB', 'default_guestbook', 'StreamSubscription', 6225984592281600)",
            jsonOutputDict['sub_info']['unsub']['sub_key'] = repr(user_sub.stream_id)
            jsonOutputDict['sub_info']['unsub']['streammatch_name'] = repr(stream.streamid)
            if(user_sub.key.delete()): #TODO: why does success lead to else?
              jsonOutputDict['sub_info']['unsub']['unsub_failure'].append(repr(user_sub.stream_id))
            else:
              jsonOutputDict['sub_info']['unsub']['unsub_success'].append(repr(user_sub.stream_id))
            jsonOutputDict['sub_info']['status'] = '0'
        jsonOutputDict['sub_info']['unsub']['total_matches'] = subReprList
        #jsonOutputDict['sub_info']['sub_key'] = repr(streamSub.put())
        #jsonOutputDict['sub_info']['subscription_properites'] = streamSub.to_dict(exclude = ['stream_id','user_id','date','author'])
      #</unsubscribe>

    self.response.write(json.dumps(jsonOutputDict))
    return 
###############################################################################


###############################################################################
# < class ManageStreamService>
class ManageStreamService(webapp2.RequestHandler):
  def post(self):
    logList = []
    postVarDict = {}
    # < read in options>
    try: # json input
      postVarDict = json.loads(self.request.body)
    except: # x-www-form
      #redirect = self.request.get('redirect',1) # for now, simply check if true is defined
      for param in ['streamid','manage_action']:
        postVarDict[param] = self.request.get(param)
    # set defaults:
    if(not 'user_name' in postVarDict):
      postVarDict['user_name'] = get_user_data()
    #</read in options>
    #self.response.write(json.dumps(postVarDict))


    # Note: remove both stream and subscription
    if(postVarDict['manage_action'] == 'delete'):
      # find streams
      # TEMP - look up string by id - TODO: handle with GenericQueryService
      streamInst = ndb.Key(Greeting,postVarDict['streamid'], parent = guestbook_key()).get()
      # delete stream subscription
      jsonStr = sendJson(self, jsondata={"stream_name": postVarDict['streamid'], "submanage": "unsubscribe"}, service_name = 'streamsubscribe')
      streamInst.key.delete()
#    self.redirect('/manage')



# < class ManageStreamService>
###############################################################################


###############################################################################
#< class CreateStreamService>
# * create a stream (which takes a stream definition and returns a status code)
#NOTE: 
# Is not an explicit 'ndb.Model' class, probably where some of my confusion is coming from 
#   creates and stores a 'Stream/Greeting' and uses 'ancestor key' to track it (the 'guestbook_key')
# CreateStreamService equ create stream
class CreateStreamService(webapp2.RequestHandler):
  def post(self):
    # < read values>
    ######################################################################
    # We set the same parent key on the 'Greeting' to ensure each Greeting
    # is in the same entity group. Queries across the single entity group
    # will be consistent. However, the write rate to a single entity group
    # should be limited to ~1/second.
    guestbook_name = self.request.get('guestbook_name',
                                      DEFAULT_GUESTBOOK_NAME)

    # set streamid to stream name to avoid issues
    #NOTE: guestbook_key is set to: ndb.Key('GuestbookNDB', DEFAULT_GUESTBOOK_NAME)
    streamid = self.request.get('stream_name')
    if(streamid):
      stream = Greeting(
          parent = guestbook_key(guestbook_name),
          id     = streamid, # override default for legibility
          )
    else:
      stream = Greeting( parent=guestbook_key(guestbook_name),)

    # < create stream>

    # mock user: # src: http://stackoverflow.com/a/6230083
    import os
    os.environ['USER_EMAIL'] = 'poland.barker@swedishcomedy.com'
    os.environ['USER_ID'] = 'pbarker'
    #   < more mock user values>
    #os.environ['AUTH_DOMAIN'] = 'testbed' # To avoid  /google/appengine/api/users.py:115 - AssertionError: assert _auth_domain
    #os.environ['USER_IS_ADMIN'] = '1'     #  for an administrative user
    #   </more mock user values>
    #user_name = 'poland_barker'
    if users.get_current_user():
        stream.author = users.get_current_user()
    #else:
    #  stream.author = 'anonymous'
    user_name = stream.author

    # TODO: add error checking for the return code
    # TODO: do not create nameless objects
    # TODO: do not create duplicate objects
    # here come the hacks :-(
    # set attributes, some are defaults
    stream.content = self.request.get('content')
    stream.content = self.request.get('stream_name')
    streamid = self.request.get('stream_name')
    if(streamid):
      stream.streamid = streamid
    coverurl = self.request.get('stream_cover_url')
    if(0):
      if(not coverurl):
        defaulturl = 'http://google.com/images'
        coverurl = defaulturl
      stream.coverurl = coverurl

    # update repeated properties
    # TODO: move all of this into the stream model
    # TODO: see 'validator' under https://developers.google.com/appengine/docs/python/ndb/properties#options
    # validator: Optional function to validate and possibly coerce the value.
    # stream_tags -> tags
    # stream_subscribers -> subscribers
    # map request data to model data:
    paramDict = {
      #'stream_tags':stream.tags,
      'stream_tags':'tags',
      'stream_subscribers':'subscribers',
    }
    for param in paramDict:                         # e.g. 'stream_tags'
      requestGetValue = self.request.get(param)     # e.g. #yolo #yolo #deletelastword
      if(requestGetValue):
        property = paramDict[param]                 # e.g. 'tags'
        # < uniqify list>
        #TODO: check type before uniqifying, or just add this as a function to the class
        listStr   = requestGetValue
        tmpList  = listStr.split(' ') #TODO: check for newline, ';', ',', etc 
        tmpSet   = set(tmpList)
        tmpList  = list(tmpSet)
        value = tmpList                             # e.g. #yolo #deletelastword
        # </uniqify list>
        setattr(stream,property,value) # http://stackoverflow.com/q/18682517

    # < put operation>
    # doc: https://developers.google.com/appengine/docs/python/ndb/modelclass#introduction
    # The return value from put() is a Key, which can be used to retrieve the same entity later:
    # p = Person(name='Arthur Dent', age=42)
    # k = p.put()
    #TODO: return error code from this operation
    try:
      stream.put()
    except: # BadValueError: Entity has uninitialized properties: streamid
    # https://wiki.python.org/moin/HandlingExceptions
      error = "unknown - could not stream.put()"
      self.response.write("bad query, returned:%s" % error)


    query_params = {'guestbook_name': guestbook_name}
    self.redirect('/manage?' + urllib.urlencode(query_params))

  def get(self):
    # look up guestbook
    guestbook_name = self.request.get('guestbook_name', DEFAULT_GUESTBOOK_NAME)

    # generate form content 
    # Write the submission form and the footer of the page
    # TODO: not all form parameters are stored!
    sign_query_params = urllib.urlencode({'guestbook_name': guestbook_name})

    thisTemplate = bilder_templates.get_page_template_create_stream()
    url = 'delete this part'
    url_linktext = 'delete this part'
    populatedTemplate = (thisTemplate %
                        (sign_query_params, cgi.escape(guestbook_name),
                         url, url_linktext))

    contentList = []
    contentList.append(populatedTemplate)
    #TODO: add form to table to delete selected streams - just have a checkbox with the stream id
    # https://apt.mybalsamiq.com/mockups/1083489.png?key=c6286db5bf27f95012252833d5214a336f17922c
    response = TEMPLATE_NAVIGATION
    for content in contentList:
      response += content + '\n'
    #response += bilder_templates.get_html_template_table()
    # wrap in grey div
    response = bilder_templates.generateContainerDiv('<h1>Handler: CreateStreamService</h1>' + response,'#C0C0C0')
    response = '<html>\n  <body>\n' + response + '\n  </body>\n</html>'
    self.response.write(response)
#</class CreateStreamService>
###############################################################################

###############################################################################
#< class_JsonTest>
# inspiration: http://stackoverflow.com/a/12664865
# doc: https://developers.google.com/appengine/docs/python/tools/webapp/responseclass#Response_out
# The contents of this object are sent as the body of the response when the request handler method returns.
#   http://stackoverflow.com/a/10871211
#   self.response.write and self.response.out.write are same thing
'''
Sample Usage:
  assumes that service accepts query params in to decide what to do
  from google.appengine.api import urlfetch
  # create query_params
  url = self.request.host_url
  result = urlfetch.fetch(url + urllib.urlencode(query_params),method=urlfetch.POST)
  if(result.status_code == 200):
    jsonStr += json.loads(result.content)
'''
class JsonTest(webapp2.RequestHandler):
  def post(self):
    jsonStr = self.get_json_str()
    self.response.write(jsonStr)
    #self.response.write('{"success": "some var", "payload": "some var"}')
  #TODO: adding 'return' breaks the page. This may be due to 'self.response.out.write'
  #return
  def get(self):
    response = '' # store request response
    # get stream name
    stream_name = self.request.get('streamid','stream_unspecified')
    query_params = urllib.urlencode({'streamid': stream_name})
    #< send POST request>
    if(1):
      result = self.test_urlfetch()
      result = bilder_templates.generateContainerDiv(result,'salmon') # yah, websafe colours are pretty awesome
      response += result

    greetText = 'This page generates the following json string when visited with POST:<br/>\n' + self.get_json_str()
    response += bilder_templates.generateContainerDivBlue(greetText) # yah, websafe colours are pretty awesome
    # wrap in grey div
    response = bilder_templates.generateContainerDiv('<h1>Handler: JsonTest</h1>' + response,'#C0C0C0')
    response = '<html>\n  <body>\n' + response + '\n  </body>\n</html>'
    self.response.write(response)
  #< def_get_json_str>
  def get_json_str(self):
    return json.dumps('{"success": "some var", "payload": "some var"}')
  #</def_get_json_str>
  #< def test_urlfetch>
  def test_urlfetch(self):
    #TODO: as a testing exercise, rewrite to capture status messages and print summary
    #NOTE: this is how I learned that port 80 is the default port that non-specific query will use
    #      that is why this "coverage tests" all urls with "no port", 80, and 8080 
    from google.appengine.api import urlfetch

    result = '<h1>TESTCODE OUTPUT</h1>'
    result += 'self.request.url is ' + self.request.url + '<br/>' + '\n'
    result += 'self.request.path is ' + self.request.path + '<br/>' + '\n'
    result += 'self.request.host_url is ' + self.request.host_url + '<br/>' + '\n'
    relpath = 'jsonreturntest'
    testUrls =  [
        self.request.host_url,
        self.request.host_url + '/' + relpath,
        '' + relpath,
        '/' + relpath,
        # find out why running on port :80 allowed '/<path>' to work
        'localhost/' + relpath,
        'localhost:80/' + relpath,
        'localhost:8080/' + relpath,
        'http://localhost/' + relpath,
        'http://localhost:80/' + relpath,
        'http://localhost:8080/' + relpath
        ]
    for url in testUrls:
      result += '>try:> urlfetch.fetch(\'%s\',method=urlfetch.POST)' % url
        
      result += '<br/>' + '\n'
      try:
        urlfetch.fetch(url,method=urlfetch.POST)
        result+='SUCESS'
      except:
        result+='&nbsp;&nbsp;&nbsp;failure'
      result += '<br/>' + '\n'
    return result
    response += '\n'+result+'\n'
    #</send POST request>
    self.response.write(response)
  #<def test_urlfetch>
#</class_JsonTest>
###############################################################################

###############################################################################
#< class_form2json>
# input x-www-form
# output: ????
# convert form data to json, send to service specified in form, 
class form2json(webapp2.RequestHandler):
  def post(self):
    debug = 0
    debug = self.request.get('debug',0) # for now, simply check if true is defined
    if(debug >= 1):
      self.response.write(html_generateContainerDiv('<h1>Handler: JsonTest</h1>' ,'#C0C0C0'))
      self.response.write(htmlParen('> self.request.body'))
      self.response.write(self.request.body)
  
    # dict of lists: https://docs.python.org/2/library/urlparse.html#urlparse.parse_qs
    jsondata  = json.dumps(urlparse.parse_qs(self.request.body))
    # dict of key-value:  http://stackoverflow.com/a/8239167
    jsondata  = json.dumps(dict(urlparse.parse_qsl(self.request.body)))
    #debug printout
    if(debug >= 1):    
      self.response.write(htmlParen('> json.dumps(self.request.body)'))
      self.response.write(htmlParen(jsondata))
    
    jsonRetStr = ''
    formDict = json.loads(jsondata)
    # make the request
    url = self.request.host_url
    # default action is 'dataprocess'
    if('action' in formDict):
      if(debug >= 1):    
        self.response.write(htmlParen('TODO: add one redirect per service that needs a form then read something like the request path to determine the action'))
        self.response.write(htmlParen('found action in formDict'))
      # URL_method:
      # url += '/%s?jsonstr=' % formDict['action']
      #json_method:
      url = self.request.host_url + '/' + formDict['action']
    else:
      #TODO: figure out a default
      url += '/%s?jsonstr=' % 'dataprocess'
    # src: https://developers.google.com/appengine/docs/python/appidentity/#Python_Asserting_identity_to_Google_APIs
    #TODO: validate response
    result = urlfetch.fetch(
        url,
        payload = jsondata,
        method=urlfetch.POST,
        headers = {'Content-Type' : "application/json"},
        )
    # store return string
    jsonRetStr = 'the_if_else_broke_in_form2json'
    if(result.status_code == 200):
      #jsonRetStr = json.loads(result.content)
      jsonRetStr = result.content
    else:
      jsonRetStr = ("Call failed. Status code %s. Body %s" % (result.status_code, result.content))
      # Note on error-handling from above google page: # raise Exception(jsonRetStr)
      jsonRetStr = json.dumps({'error':jsonRetStr})

    #self.response.write(html_generateContainerDivBlue(htmlParen(jsonRetStr)))
    if(debug >= 1):    
      responseStr = htmlParen('response from dataprocess')
      responseStr += htmlParen('raw output:' + htmlParen(jsonRetStr))
    jsonDict = {}# = json.loads(jsonRetStr)
    response = jsonRetStr
    if(debug >= 1):    
      if('greeting' in jsonDict):
        responseStr += htmlParen('message:' + jsonDict['greeting'])
      response = html_generateContainerDivBlue(responseStr)
    self.response.write(response)
    
    # TODO: not sure what to do with this now
    #self.redirect('/formtest')
#</class_form2json>
###############################################################################

###############################################################################
def trends_calculate(self,streamList):
    # calculate trending
    # 1. store all viewcounts as 'viewcount->streamObject
    # 2. sort dict
    # 3. store top three results
    viewsDict = {}
    #step1:
    for streamInst in streamList:
      viewsDict[streamInst.views] = streamInst
    #step2:
    numTrendStreams = 3
    orderedList = sorted(viewsDict)
    orderedList.reverse()
    trendingList = orderedList[0:numTrendStreams]
    #^^^^ works ^^^^

    #step3: storage
    trendSetter = TrendingStream(
        id = 'theonlytrendingstreamtrackerwewilleverneedasfarasicantell'
        )
    for viewCount in trendingList:
      trendSetter.streamsList.append(viewsDict[viewCount].key)
    trendSetter.put()
###############################################################################


###############################################################################
def trends_retreive(self):
  trendingStreamsList = []
  # get trending streams
  trend_query_list = TrendingStream.query().fetch()
  if(trend_query_list):
    streamKeyList = trend_query_list[0].streamsList
    for streamKey in streamKeyList:
      trendingStreamsList.append(streamKey.get())
  return trendingStreamsList
###############################################################################


###############################################################################
#< class_TrendingHandler>
class TrendingHandler(webapp2.RequestHandler):
  def post(self):
    #< DEBUG: calculate trends - send to 'CronHandler'>
    if(0):
      streams_query = Greeting.query()
      queriedStreams = streams_query.fetch()
      trends_calculate(self,queriedStreams)
    #</DEBUG: calculate trends - send to 'CronHandler'>
    # display 
    streamsList = trends_retreive(self)
    streamDescList = []
    for stream in streamsList:
      streamDescDict = {}
      streamDescDict = stream.to_dict(include=['streamid','coverurl'])
      streamDescList.append(streamDescDict)
    jsonStr = json.dumps(streamDescList)
    self.response.write(jsonStr)

  def get(self):
    response = ''
    tile = '<h1>Top 3 Trending Streams</h1>'

    # get top3 trending streams
    jsonStr = sendJson(self, jsondata={}, service_name = 'trending')
    # <covers>
    # cover images
    if(1):
      streamDescList = json.loads(jsonStr)
      streamCoverList = []
      galleryConfList = []
      for streamDict in streamDescList:
        streamCoverList.append(streamDict['coverurl'])
        tmpConf = {
          'src'     : streamDict['coverurl'],
          'caption' : streamDict['streamid'],
        }
        galleryConfList.append(tmpConf)
    galleryHtml = bilder_templates.gen_html_gallery(imgConfJson = json.dumps(galleryConfList),) # imgrange = 5)
#working till here


    # html content render
    contentList = []
    contentList.append(tile)
    contentList.append(TEMPLATE_NAVIGATION)
    #contentList.append(htmlPprintJson(jsonStr))
    contentList.append(galleryHtml)
    contentList.append(
      bilder_templates.gen_html_form_emailrate(action = '/managenotifications')
      )

    for content in contentList:
      response += content + '\n'
    response = bilder_templates.generateContainerDiv(response,'#C0C0C0')
    self.response.write(response)

#< class_TrendingHandler>
###############################################################################


###############################################################################
def email_digest_update(self,emailrate):
  varDict = {}
  varDict['emailrate'] = emailrate
  user = get_user_data()
  if(not emailrate):
    # if no emailrate spec'd then assume user wanted to unsubscribe
    varDict['emailrate'] = 0
  userEmailPref = DigestInformation(
    id          = user.email(),
    #DEBUG:
    #id          = user.email() + '_' + str(emailrate),
    useraccount = user,
    frequency   = int(varDict['emailrate']),
    )
  userEmailPref.put()
  #TODO: remove if '0' specified, no use keeping that around
  #debug
  if(1):
    log = '-email_digest_update- added or updated user: %s' % str(user)
    #self.response.write(htmlParen('"email_digest_update" added user: %s' % str(user)))
  return log
###############################################################################


###############################################################################
# retreive all registered emails
# notify based on preferences
def email_digest_retreive(self,**kwargs):
  # get all digest-subscriptions
  digestInfoList = DigestInformation.query().fetch()
  # get all digest-subscriptions of specified frequency
  if('frequency' in kwargs):
    digestInfoList = DigestInformation.query(DigestInformation.frequency == int(kwargs['frequency'])).fetch()
  # store emails and logs
  emailList = []
  logList = []
  if(len(digestInfoList) == 0):
    logList.append('no matches found for frequency %s' % (kwargs['frequency']))
  for info in digestInfoList:
    emailList.append(info.useraccount.email())
    #debug
    #logList.append(info.frequency)
    if(1):
      logList.append('-email_digest_retreive- digest rate: %s' % str(info.frequency))
  jsonRetDict = {'log':logList, 'emailList':emailList}
  return json.dumps(jsonRetDict)
  return emailList
###############################################################################


###############################################################################
def email_digest_sendmaillist(self,**kwargs):
  maillist = []
  varDict = {}
  varDict['maillist'] = [] # to be used
  varDict['subject']  = 'trending update at connexus'
  varDict['body']     = 'connexus trending summary'
  if('maillist' in kwargs):
    maillist = kwargs['maillist']


  from google.appengine.api import mail

  for email in maillist:
    recipient = email
    mail.send_mail(sender="leewatson1@gmail.com",
                  to=recipient,
                  subject="trending update at connexus",
                  body="""
                  connexus trending summary
                  """)
  return

###############################################################################

################################################################
# < class_EmailDigestHandler>
class EmailDigestHandler(webapp2.RequestHandler):
  def get(self):
    self.response.write('hi')
    #self.response.write(self.request.url)
    self.response.write(self.request.get('emailrate',0))
    #jsonStr = sendJson(self, jsondata={''}, service_name = 'managenotifications')

  def post(self):
    postVarDict = {}
    # < read in options>
    try: # json input
      postVarDict = json.loads(self.request.body)
      # TODO: move after try/catch
      if(not 'user_name' in postVarDict):
        postVarDict['user_name'] = get_user_data()
    except: # x-www-form
      #redirect = self.request.get('redirect',1) # for now, simply check if true is defined
      for param in ['emailrate',]:
        postVarDict[param] = self.request.get(param, '0')
    #</read in options>

    logList = []
    # update email frequency
    if 'emailrate' in postVarDict:
      logList.append(email_digest_update(self, postVarDict['emailrate']))
    # send email to registered people
    if 'mailtime' in postVarDict:
      emailList = []
      # vvvv working vvvv
      if(0):
        emailList = email_digest_retreive(self, frequency = postVarDict['mailtime'])
        logList.append(emailList)
      # ^^^^ working ^^^^
      else:
        jsonStr =  email_digest_retreive(self, frequency = postVarDict['mailtime'])
        # get list of emails
        jsonDict = json.loads( email_digest_retreive(self, frequency = postVarDict['mailtime']))
        emailList = jsonDict['emailList']
        # add trends to dict for debug output
        #trendingStreamsList = trends_retreive(self)
        #jsonDict['trending'] = trendingStreamsList
        jsonDict['trending'] = json.loads(sendJson(self, jsondata={}, service_name = 'trending'))
        #jsonDict['trending'] = trendingStreamsList
        ####
        jsonStr = json.dumps(jsonDict)
        self.response.write(jsonStr)
        email_digest_sendmaillist(self,
          maillist = emailList,
          body     = json.dumps(jsonDict['trending'])
        )
        return
      

      #self.response.write(emailList)

    #self.response.write(self.request.body)
    #DEBUG purposes:
    if 'user_name' in postVarDict:
      postVarDict['user_name'] = str(postVarDict['user_name'])
    postVarDict['log'] = logList
    self.response.write(json.dumps(postVarDict))

# </class_EmailDigestHandler>
################################################################


###############################################################################
#< class_CronHandler>
# receive json, do something, output json
# DEFINITELY need a statistics db object 
# Note: may be best to create new object for statistics (e.g. view times) to simplify this
# show top <3> streams, sorted by number of views
# loop through all users
#   loop through all streams
#     * cull any times > 1 hour #TODO: add function to object to do this
#     * calculate "stream queue size" i.e. number of views
#     * sort by most views
####
# post: generate the stats; run from cron and NEVER user/other things
# get : show the stats + subscription-option checkboxes
class CronHandler(webapp2.RequestHandler):
  def get(self):
    self.post()

  def post(self):
    # get streams, remove views older than one hour
    jsonDictUnique = self.getStreams()
    jsonStr = json.dumps(jsonDictUnique)
    self.response.write(jsonStr)

  #TODO: consolidate into the query services...
  #TODO: loop for all users, not just...
  def getStreams(self):
    jsonRetDict = {}
    user_name = DEFAULT_GUESTBOOK_NAME
    # get all possible streams 
    # TODO: get statistics object that 'viewsinglestream' is to maintain, e.g.: subscription
    streams_query = Greeting.query()
    queriedStreams = streams_query.fetch()

    streamPruneLog = []
    
    maxTimeDelta = 3600 # 1 hour
    #debug: # maxTimeDelta = 40
    #self.response.write(('generating views 1/s for %s seconds') % (testDuration))
    for streamInst in queriedStreams:
      jsonRetDict[streamInst.streamid] = {}
      #jsonRetDict[streamInst.streamid]['times_previous'] = streamInst.viewtimes
      jsonRetDict[streamInst.streamid]['times_previous_amount'] = streamInst.views
      if(1): #DEBUG
        streamInst.viewtimes = self.pruneViewTimes(list = streamInst.viewtimes, maxTimeDelta = maxTimeDelta)
      else:
        ## get updated viewtimes and the log
        streamInst.viewtimes, tmpLog = self.pruneViewTimes(list = streamInst.viewtimes, maxTimeDelta = maxTimeDelta)
        streamPruneLog.append(tmpLog)
#      streamInst.viewtimes     = []
      streamInst.views     = len(streamInst.viewtimes)
      # report updated times
      #jsonRetDict[streamInst.streamid]['times_updated'] = streamInst.viewtimes
      jsonRetDict[streamInst.streamid]['times_updated_amount'] = streamInst.views
      streamInst.put()

    # calculate trending
    trends_calculate(self,queriedStreams)

    jsonRetDict['log'] = streamPruneLog
    return jsonRetDict

  ################################################################
  # input: one list of viewtimes
  def pruneViewTimes(self, **kwargs):
    varDict = {}
    #varDict['maxTimeDelta'] = 3600 # 1 hour = 60min/h * 60s/min = 3600 s/h
    # < read in options>
    if kwargs:
      for param in ['list','maxTimeDelta']:
        if param in kwargs:
          varDict[param] = kwargs[param]
    #</read in options>
    viewtimeList = varDict['list']
    # if list is null don't process
    if(len(viewtimeList) == 0):
      return viewtimeList

    # store non-removed times
    viewTimePrunedList = []

    logList = []
    # assume sorted
    import datetime
    timeDelta = datetime.timedelta(seconds = varDict['maxTimeDelta'])
    # compare 0th to last and work backwards until done - it is sorted!
    #latestViewTime = viewtimeList[0]
    latestViewTime = datetime.datetime.now()
    logList.append('datetime.now(): %s' % (str(latestViewTime)))
    for viewTime in (viewtimeList):
      ## desc: if latest - current > 3600
      #if((viewTime - latestViewTime) > timeDelta):
      #nope if((viewTime - latestViewTime).total_seconds() > timeDelta):
      logList.append('comparing: %s - %s > %s' % (str(viewTime), str(latestViewTime), str(varDict['maxTimeDelta'])))
      #if((viewTime - latestViewTime).total_seconds() > varDict['maxTimeDelta']):
      if((latestViewTime - viewTime).total_seconds() > varDict['maxTimeDelta']):
        logList.append('result: yes')
        del viewTime 
      else:
        viewTimePrunedList.append(viewTime)
        logList.append('result: no')

    return viewTimePrunedList
    #debug:# return viewTimePrunedList, logList
  ################################################################
#</class_CronHandler>
###############################################################################


###############################################################################
#< class_genSearchTerms>
class genSearchTerms(webapp2.RequestHandler):
  def get(self):
    self.post()

  def post(self):
    # get streams, remove views older than one hour
    jsonDictUnique = self.getStreams()
    jsonStr = json.dumps(jsonDictUnique)
    self.response.write(jsonStr)

  def getStreams(self):
    jsonRetDict = {}
    # get all possible streams 
    # TODO: get statistics object that 'viewsinglestream' is to maintain, e.g.: subscription
    streams_query = Greeting.query()
    queriedStreams = streams_query.fetch()

    keyWordArr = [];
    for streamInst in queriedStreams:
      jsonRetDict[streamInst.streamid] = {}
      if(0):
        keyWordArr.append(streamInst.streamid)
        keyWordArr.extend(streamInst.tags)
      elif(0):
        keyWordArr.extend( streamInst.getKeyWords() )
        #TODO: determine whether to associate a stream with the keywords
        #jsonRetDict[streamInst.streamid] = streamInst.getKeyWords()
      else:
        keyWordArr.append( streamInst.getKeyWordsDict() )
    # < uniqify_list>
    # remove duplicate keywords
    # Note: uniqify if not trying to associate keywords with a stream
    if(0):
      tmpSet   = set(keyWordArr)
      tmpList  = list(tmpSet)
      keyWordArr = list(tmpSet)
    # </uniqify_list>
    jsonRetDict['keywords'] = keyWordArr
    jsonRetDict = keyWordArr


    return jsonRetDict
#< class_getStreams>
###############################################################################


###############################################################################
#< class_GenerateGeoView>
class GenerateGeoView(webapp2.RequestHandler):
  def get(self):
    response = ''
    html_geoview = '<h2>GeoView</h2>'
    html_geoview += load_template(self, file = 'templates/map_slider_img.html',
      type='jinja',
      )
    html_geoview = bilder_templates.generateContainerDivBlue(html_geoview)

    # < consolidate and write response>
    ## make navigation sit on top
    response = TEMPLATE_NAVIGATION + response
    response += html_geoview
    response = bilder_templates.generateContainerDiv('<h1>GeoView</h1>' + response,'#C0C0C0')
    response = bilder_templates.get_html_body_template(response)
    self.response.write(response)


#</class_GenerateGeoView>
###############################################################################


#TODO: use 'genNav' to autogenerate links, redirection OR somehow retrieve this list of tuples 
application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/create', CreateStreamService),
    ('/managestream', ManageStreamService),
    ('/sign', CreateStreamService), #TODO: rename
    ('/manage', Manage),
    ('/viewsinglestream', ViewSingleStream),
    ('/viewallstreams', ViewAllStreamsService),
    ('/searchallstreams', SearchAllStreamsService),
    ('/genericquery', GenericQueryService),
    ('/img_upload', ImgUpload),
    ('/jsonreturntest',JsonTest),
    ('/streamsubscribe',SubscribeStreamService),
    ('/managestreamsub',SubscribeStreamService),
    ('/form2json',form2json),
    ('/cron_summarygen',CronHandler),
    ('/trending',TrendingHandler),
    ('/managenotifications',EmailDigestHandler),
    ('/upload_fromform', UploadHandlerFromForm),
    ('/serve/([^/]+)?', ServeHandler),
    ('/getsearchterms', genSearchTerms),
    ('/geoview', GenerateGeoView),
], debug=True)

###############################################
# notes

# Still converting from 'guestbook' example
# Guestbook equ User (has a db key)
# `- Greeting equ Stream
#   `- photoList (simple list of urls to blobstore)

############# services ########################
# TODO: all current handlers are written in one go to get things done. 
#       Split them into sub-handlers to satisfy the below requirements
#       epiphany: one handler is the client, one handler is the service
'''
Write specific services for
* management (in which you take a user id and return two lists of streams)
https://apt.mybalsamiq.com/mockups/1083489.png?key=c6286db5bf27f95012252833d5214a336f17922c
* create a stream (which takes a stream definition and returns a status code)
https://apt.mybalsamiq.com/mockups/1083503.png?key=c6286db5bf27f95012252833d5214a336f17922c
* view a stream (which takes a stream id and a page range and returns a list of URLs to images and a page range)
* image upload (which takes a stream id and a file)
  # blobstore https://developers.google.com/appengine/docs/python/tools/webapp/blobstorehandlers
* view all streams (which returns a list of names of streams and their cover images)
* search streams (which takes a query string and returns a list of streams (titles and cover image urls) that contain matching text
* most viewed streams (which returns a list of streams sorted by recent access frequency)
* and reporting request.
'''

#NOTES:
# for 'json request' https://developers.google.com/appengine/docs/python/tools/webapp/buildingtheresponse
# blobstore https://developers.google.com/appengine/docs/python/tools/webapp/blobstorehandlers
# request handler: https://developers.google.com/appengine/docs/python/tools/webapp/requesthandlerclass
# request class, forms: https://developers.google.com/appengine/docs/python/tools/webapp/requestclass


