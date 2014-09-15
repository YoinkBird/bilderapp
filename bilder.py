import json
import cgi
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.api import urlfetch

import webapp2

import bilder_templates
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
      'Search'   : 'searchallstreams',
      'Trending'   : 'trending',
      'Social'   : 'social',
      }
  #TODO: convert to 2d list or object or whatever, try to autogenerate initial link->target
  navList = [ "Home", "Manage", "Create", "View", "Search", "Trending", "Social", ]
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
        <td colspan=%s>TODO: assign correct link targets</td>
      <tr>
        %s
      </tr>
    </table>
    """
  navTable = TEMPLATE_NAVIGATION % (colspan,navTr)
  return navTable
#</genNav>

    
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
# user_key
def guestbook_key(guestbook_name=DEFAULT_GUESTBOOK_NAME):
    """Constructs a Datastore key for a Guestbook entity with guestbook_name."""
    return ndb.Key('GuestbookNDB', guestbook_name)

###############################################################################
#< class_Stream>
# class Stream aka Greeting
# doc on internal properties: https://developers.google.com/appengine/docs/python/ndb/properties
class Greeting(ndb.Model):
#class Stream(ndb.Model):
    #TODO: implement all the internal methods
    """Models an individual Guestbook entry."""
    author = ndb.UserProperty()
    content = ndb.StringProperty() # TODO: convert to 'streamid'
    #streamid = content              # TODOno: created a stream and then double-check in the console - only 'streamid' gets updated for some reason
    streamid = ndb.StringProperty(required=True) # TODO: convert to 'streamid'
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

    #TODO: implement these mocks
    img_amount = ndb.IntegerProperty()
    views = ndb.IntegerProperty()
#</class_Stream>
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
  def get(self):
    if users.get_current_user():
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'
    else:
        url = users.create_login_url(self.request.uri)
        url_linktext = 'Login'
    
    # look up guestbook
    guestbook_name = self.request.get('guestbook_name', DEFAULT_GUESTBOOK_NAME)
    #< retrieve greetings>
    # TODO: this part is good for 'manage'
    # Ancestor Queries, as shown here, are strongly consistent with the High Replication Datastore. 
    # Queries that span entity groups are eventually consistent.
    # If we omitted the ancestor from this query there would be a slight chance 
    #  that 'Greeting' that had just been written would not show up in a query.

    greetings_query = Greeting.query(
        ancestor=guestbook_key(guestbook_name)).order(-Greeting.date)
    greetings = greetings_query.fetch(10)

    #TODO: stop calling it a greeting:

    # calling it 'greetingsOwnList' for better conversion to 'streams i own' and 'streams i subscribe to'
    #TODO: check that parameters in 'greeting' exist before assigning. even better, use getter methods
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
      greetingDict['content'] = contentHref
      #</HACK>
      greetingDict['date'] = str(greeting.date)
      greetingDict['img_amount'] = str(greeting.img_amount)
      greetingDict['views'] = str(greeting.views)
      greetingsOwnList.append(greetingDict)
    #</retrieve greetings>
    greetSubTr = ''
    greetOwnTr = ''

    html_form_checkbox = lambda name,value: '<input type="checkbox" name="%s" value="%s">' % (name,value)
    # own
    # loop through all greetings
    for greetDict in greetingsOwnList:
      valueList = [] 
      #TODO: make a list with common elements to 'own' and 'sub' and then just add on for 'sub'
      attribOrderList = ['content','date','img_amount']
      for attrib in attribOrderList:
        valueList.append(greetDict[attrib])
      # add the checkbox
      # table 'delete' template
      valueList.append(html_form_checkbox('stream_delete',greetDict['content']))
      # build the row
      greetOwnTr += bilder_templates.generateTableRow(valueList)
    # subscribed
    # loop through all greetings
    for greetDict in greetingsOwnList:
      valueList = [] 
      attribOrderList = ['content','date','img_amount','views']
      for attrib in attribOrderList:
        valueList.append(greetDict[attrib])

      # add the checkbox
      valueList.append(html_form_checkbox('stream_unsub',greetDict['content']))
      # build the row
      greetSubTr += bilder_templates.generateTableRow(valueList)
    #greetTable = bilder_templates.get_html_template_table(greetSubTr)


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
    form_streams_own = gen_html_form('delete_stream','post','(X) Delete Checked Streams',table_streams_own)
    form_streams_sub = gen_html_form('delete_stream','post','(X) Unsubscribed Checked Streams',table_streams_sub)



    contentList = []
    #TODO: add form to table to delete selected streams - just have a checkbox with the stream id
    # https://apt.mybalsamiq.com/mockups/1083489.png?key=c6286db5bf27f95012252833d5214a336f17922c
    response = TEMPLATE_NAVIGATION
    #response += greetTable
    contentList.append('<h3>Streams I Own</h3>')
    contentList.append(form_streams_own)
    contentList.append('<h3>Streams I Subscribe to</h3>')
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
# return all user streams instead of having to loop each time
def getStreamImg(stream_id): # TODO: page range
  # start with single stream
  # TODO: fail if stream not present - should only get here if one has been created already
  # have to retrieve stream from DB
  # make a query #TODO: figure out how to just get the one and only entry without needing an iterator
  streams_query = Greeting.query( Greeting.content == stream_id)
  # get results of query
  streams = streams_query.fetch()
  if(0): # DEBUG
    response += 'streams_query:<br/>'+ repr(streams_query)
    response +=  '<br/>'
    response += 'streams: <br/>' + repr(streams)
    response +=  '<br/>'
  # loop through aaaaalllll of them (there should only be one)
  range = 0
  imgList = []
  for streamInstance in streams:
    # see if there are any urls attached; if so then display them
    if streamInstance.imgurls :
      imgList = streamInstance.imgurls
  # </image gallery>

  #TODO: return as json
  range = len(imgList)
  jsonStr = json.dumps({'imgurls':imgList,'range':range})
  return jsonStr
  return imgList
#</def getStreamImg>
###############################################################################

###############################################################################
#< class ViewSingleStream>
# * view a stream (which takes a stream id and a page range and returns a list of URLs to images and a page range)
# doc: different kinds of request handlers
# https://developers.google.com/appengine/docs/python/tools/webapp/requesthandlers
#TODO: 'more pictures' https://piazza.com/class/hz1r799mk0ah?cid=56
class ViewSingleStream(webapp2.RequestHandler):
  def get(self):
    response = '' # store request response
    response += TEMPLATE_NAVIGATION
    # get stream name
    stream_name = self.request.get('streamid','stream_unspecified')
    query_params = urllib.urlencode({'streamid': stream_name})
    action = '/img_upload?' + query_params 

    # < quick json POST test>
    if(0):
      # TODO: implement 'getStreamImg' this way
      from google.appengine.api import urlfetch
      #result = urlfetch.fetch(url + urllib.urlencode(query_params),method=urlfetch.POST)
      result = urlfetch.fetch('http://localhost:8080/jsonreturntest',method=urlfetch.POST)
      jsonStr = ''
      if(result.status_code == 200):
        jsonStr = 'Sample json string that service \'view single stream\' could use:<br/>\n'
        jsonStr += json.loads(result.content)
      response += bilder_templates.generateContainerDivBlue(jsonStr)
    # </quick json POST test>

    # < image gallery>
    imgDict = json.loads(getStreamImg(stream_name))
    imgList = imgDict['imgurls']
    # TODO: range (default 3?), 'more pictures'
    imageGalleryStr = '<p>Image Gallery</p>\n<p>TODO: implement proper images</p>'
    imageGalleryRange = 3
    if imgList:
      imageGalleryStr += '<div>|' + ' | '.join(imgList[:imageGalleryRange]) + '|</div>'
    # </image gallery>

    response += bilder_templates.generateContainerDivBlue(imageGalleryStr)
    response += bilder_templates.generateContainerDivBlue(bilder_templates.get_page_template_upload_file(action))
    # boilerplate
    response = bilder_templates.generateContainerDiv('<h1>Handler: ViewSingleStream</h1>' + response,'#C0C0C0')
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
    streamsList = []
    #TODO: form a real query instead of try...except
    #TODO: once 'Greeting' object is fixed, remove check for 'content'
    # define 'content' as 'name'
    for stream in streams:
      streamDescDict = {}
      #for param in ['content','name','cover']
      try: # content
        streamDescDict['name'] = stream.content
      except:
        streamDescDict['name'] = 'no_content'
      try: # name
        streamDescDict['name'] = stream.name
      except:
        streamDescDict['name'] = 'no_name'
      try: # cover
        streamDescDict['cover'] = stream.content
      except:
        streamDescDict['cover'] = 'no_cover'
      streamsList.append(streamDescDict)

    #response += '<br/>\n'.join(streamsList)
    
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
      jsonStr += result.content
      #jsonStr += json.loads(result.content)
    else:
      jsonStr = 'request failed: ' + str(result.status_code)
    response += bilder_templates.generateContainerDivBlue(jsonStr)
    # < query>

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
  def post(self):
    querydebug = 1 # 1: add bogus results 2: disable redirect, print some junk
    response = ''

    # TODO: ?look up all users?
    user_name = self.request.get('user_name', DEFAULT_GUESTBOOK_NAME)
    # look up streams
    #TODO: add a search
    streams_query = Greeting.query(
        ancestor=guestbook_key(user_name)).order(-Greeting.date)
    streams = streams_query.fetch()
    response += 'total queries found: ' + str(len(streams)) + '<br/>\n'

    # list of hashes
    streamsList = []
    # TODO: return real results; these are placeholders
    if(querydebug >= 1):
      tmpStreamsList = []
      tmpStreamsList.append({'TODO':'return real results!'})
      tmpStreamsList.append({'Service':'GenericQueryService'})
      tmpStreamsList.append({'stream1':'title1'})
      tmpStreamsList.append({'stream2':'title2'})
      streamsList.extend(tmpStreamsList)
    #TODO: form a real query instead of try...except
    #TODO: once 'Greeting' object is fixed, remove check for 'content'
    # define 'content' as 'name'
    for stream in streams:
      streamDescDict = {}
      #for param in ['content','name','cover']
      try: # content
        streamDescDict['name'] = stream.content
      except:
        streamDescDict['name'] = 'no_content'
      try: # name
        streamDescDict['name'] = stream.name
      except:
        streamDescDict['name'] = 'no_name'
      try: # cover
        streamDescDict['cover'] = stream.content
      except:
        streamDescDict['cover'] = 'no_cover'
      streamsList.append(streamDescDict)

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
      self.response.write(response)
    else:
      self.response.write(response)
      #TODO: dynamic
      self.redirect(action)
#</class_GenericSearchQuery>
###############################################################################


###############################################################################
#< class_SearchAllStreamsService>
# * search streams (which takes a query string and returns a list of streams (titles and cover image urls) that contain matching text
  '''
   balsamiq1:
   * return to self on form submit
   * show first 5 results and cover img
   * click on cover img -> view stream page
   * click on cover img -> incr numviews 
      Note: this is in common with the normal 'view a stream' - reuse somehow!
  '''

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

    # < consolidate and write response>
    ## make navigation sit on top
    response = TEMPLATE_NAVIGATION + response
    response += bilder_templates.generateContainerDivBlue(form)
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
    stream_name = self.request.get('streamid')
    
    #< read in options>
    #TODO: get dict directly from self.request.get
    paramDict = {}
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
      # re-store object
      streamInstance.put()

    # create response:
    response = bilder_templates.generateContainerDivBlue(response)
    response = bilder_templates.generateContainerDiv('<h1>Handler: ViewSingleStream</h1>' + response,'#C0C0C0')
    #stream_query = Greeting.query
    #DEBUG: self.response.write(response)
#TODO: redirect back
    query_params = urllib.urlencode({'streamid': stream_name})
    action = '/viewsinglestream?' + query_params 
    self.redirect(action)
#< class ImgUpload>
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
    # We set the same parent key on the 'Greeting' to ensure each Greeting
    # is in the same entity group. Queries across the single entity group
    # will be consistent. However, the write rate to a single entity group
    # should be limited to ~1/second.
    guestbook_name = self.request.get('guestbook_name',
                                      DEFAULT_GUESTBOOK_NAME)
    #NOTE: def guestbook_key: return ndb.Key('GuestbookNDB', DEFAULT_GUESTBOOK_NAME)
    stream = Greeting(parent=guestbook_key(guestbook_name))

    if users.get_current_user():
        stream.author = users.get_current_user()
    #else:
    #  stream.author = 'anonymous'

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

#TODO: use 'genNav' to autogenerate links, redirection OR somehow retrieve this list of tuples 
application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/create', CreateStreamService),
    ('/sign', CreateStreamService), #TODO: rename
    ('/manage', Manage),
    ('/viewsinglestream', ViewSingleStream),
    ('/viewallstreams', ViewAllStreamsService),
    ('/searchallstreams', SearchAllStreamsService),
    ('/genericquery', GenericQueryService),
    ('/img_upload', ImgUpload),
    ('/jsonreturntest',JsonTest),
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


