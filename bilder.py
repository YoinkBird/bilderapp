import cgi
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb

import webapp2

import bilder_templates
def genNav():
  #TODO: match link targets with the mockups, tie-in to 'application = webapp2.WSGIApplication'
  #TODO: autogenerate from dict with linktext->target
  #TODO: use bullet list
  #raw data: Manage Create View Search Trending Social 
  navDict = {
      'Manage'   : 'manage',
      'Create'   : 'create',
      'View'   : 'view',
      'Search'   : 'search',
      'Trending'   : 'trending',
      'Social'   : 'social',
      }
  #TODO: convert to 2d list or object or whatever, try to autogenerate initial link->target
  navList = [ "Manage", "Create", "View", "Search", "Trending", "Social", ]
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
 

DEFAULT_GUESTBOOK_NAME = 'default_guestbook'

# We set a parent key on the 'Greetings' to ensure that they are all in the same
# entity group. Queries across the single entity group will be consistent.
# However, the write rate should be limited to ~1/second.

def guestbook_key(guestbook_name=DEFAULT_GUESTBOOK_NAME):
    """Constructs a Datastore key for a Guestbook entity with guestbook_name."""
    return ndb.Key('Guestbook', guestbook_name)

class Greeting(ndb.Model):
    #TODO: implement all the internal methods
    """Models an individual Guestbook entry."""
    author = ndb.UserProperty()
    content = ndb.StringProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)

    #TODO: implement these mocks
    img_amount = 9
    views = '99'

###############################################################################
#< class MainPage>
# good for 'add stream'
# balsamiq1: return to 'manage' page on form submit
class MainPage(webapp2.RequestHandler):
    def get(self):
        #TODO: convert multiple self.response.write calls into multiple string concats and one call 
        self.response.write('<html><body>')
        handlerContainerOpen = '<div style="border-style:solid;border-width:1px;padding:0.5em 0 0.5em 0.5em;background-color:#C0C0C0">'
        self.response.write(handlerContainerOpen)
        self.response.write('<h1>MainPage aka Create Stream</h1>')
        # look up guestbook
        guestbook_name = self.request.get('guestbook_name',
                                          DEFAULT_GUESTBOOK_NAME)

        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        # Write the submission form and the footer of the page
        # TODO: not all form parameters are stored!
        sign_query_params = urllib.urlencode({'guestbook_name': guestbook_name})

        thisTemplate = TEMPLATE_NAVIGATION + bilder_templates.get_page_template_create_stream()
        self.response.write(thisTemplate %
                            (sign_query_params, cgi.escape(guestbook_name),
                             url, url_linktext))
        handlerContainerClose = '</div>'
        self.response.write(handlerContainerClose)
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
#< class ViewSingleStream>
# * view a stream (which takes a stream id and a page range and returns a list of URLs to images and a page range)
# doc: different kinds of reqeust handlers
# https://developers.google.com/appengine/docs/python/tools/webapp/requesthandlers
#TODO: 'more pictures' https://piazza.com/class/hz1r799mk0ah?cid=56
class ViewSingleStream(webapp2.RequestHandler):
  def get(self):
    # get stream name
    stream_name = self.request.get('streamid','stream_unspecified')
    query_params = urllib.urlencode({'streamid': stream_name})
    action = '/img_upload?' + query_params 

    # generate response
    response = ''
    response += bilder_templates.generateContainerDivBlue('image stream goes here')
    response += bilder_templates.generateContainerDivBlue(bilder_templates.get_page_template_upload_file(action))
    # boilerplate
    response = bilder_templates.generateContainerDiv('<h1>Handler: ViewSingleStream</h1>' + response,'#C0C0C0')
    response = bilder_templates.get_html_body_template(response)
    self.response.write(response)
#</class ViewSingleStream>
###############################################################################

#NOTE: 
# Does not output to screen
# Guestbook is user
# greeting is stream
class Guestbook(webapp2.RequestHandler):
    def post(self):
        # We set the same parent key on the 'Greeting' to ensure each Greeting
        # is in the same entity group. Queries across the single entity group
        # will be consistent. However, the write rate to a single entity group
        # should be limited to ~1/second.
        guestbook_name = self.request.get('guestbook_name',
                                          DEFAULT_GUESTBOOK_NAME)
        greeting = Greeting(parent=guestbook_key(guestbook_name))

        if users.get_current_user():
            greeting.author = users.get_current_user()

        greeting.content = self.request.get('content')
        greeting.content = self.request.get('stream_name')
        greeting.put()

        query_params = {'guestbook_name': guestbook_name}
        self.redirect('/manage?' + urllib.urlencode(query_params))

# inspiration: http://stackoverflow.com/a/12664865
# doc: https://developers.google.com/appengine/docs/python/tools/webapp/responseclass#Response_out
# The contents of this object are sent as the body of the response when the request handler method returns.
#   http://stackoverflow.com/a/10871211
#   self.response.write and self.response.out.write are same thing
class JsonTest(webapp2.RequestHandler):
  def post(self):
    self.response.out.write('{"success": "some var", "payload": "some var"}')
  #TODO: adding 'return' breaks the page. This may be due to 'self.response.out.write'
  #return

#TODO: use 'genNav' to autogenerate links, redirection OR somehow retrieve this list of tuples 
application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/manage', Manage),
    ('/viewsinglestream', ViewSingleStream),
    ('/sign', Guestbook),
    ('/jsonreturntest',JsonTest),
], debug=True)
