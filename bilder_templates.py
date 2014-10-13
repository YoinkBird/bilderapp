import json
################################################################
# < def_functionTemplate>
#def functionTemplate:
# </def_functionTemplate>
################################################################

################################################################
# < class_classTemplate>
#class classTemplate(webapp2.RequestHandler):
#    def post(self):
#      # kwargs
#      jsonStr = sendJson(self, jsondata={}, service_name = 'trending')
# </class_classTemplate>
################################################################


#< def generateContainerDiv>
#TODO: add kwargs and a 'header' option
#TODO: convert all calls to use kwargs style
def generateContainerDiv(containerTitle,bgcolor,**kwargs):
  if(kwargs):
    if('title' in kwargs):
      titleP = '<p style="font-weight:bold">%s</p>' % kwargs['title']
      containerTitle = titleP + containerTitle
  divStyle = "border-style:solid;border-width:1px;padding:0.5em 0.5em 0.5em 0.5em;background-color:%s;" % bgcolor
  handlerContainer = '<div style="%s">%s</div>' % (divStyle, containerTitle )
  return handlerContainer
#</def generateContainerDiv>

#< def generateContainerDivBlue>
#TODO: add kwargs and a 'header' option
#TODO: i guess this means inheritance would be nice
def generateContainerDivBlue(containerTitle):
  divColor = 'lightsteelblue' # reference: http://www.w3schools.com/html/html_colornames.asp
  return generateContainerDiv(containerTitle, divColor)
#</def generateContainerDivBlue>

#< generateTableRow>
def generateTableRow(list):
  tableRow = ''
  for td in list:
    #tmplink = '<a href=%s>%s</a>' % (navDict[param], param)
    tmptd   = '<td>%s</td>' % td
    tableRow += tmptd
    #del tmplink
    del tmptd
  tableRow = '<tr>\n  %s\n</tr>' % tableRow
  return tableRow
#</generateTableRow>

#< def get_html_body_template>
def get_html_body_template(bodycontent):
  return '<html>\n  <body>\n' + bodycontent + '\n  </body>\n</html>'
#</def get_html_body_template>

#< def gen_html_input_tag>
def gen_html_input_tag(**kwargs):
  html_attrib_list = []
  submit_type = 'submit'
  if(kwargs):
    if('css_class' in kwargs):
      html_attrib_list.append('class="%s"' % kwargs['css_class'])
    if('value' in kwargs):
      html_attrib_list.append('value="%s"' % kwargs['value'])
  miscAttrib = ' '.join(html_attrib_list)
  html_input = '<input type="%s" %s>' % (submit_type, miscAttrib)
  return html_input
#</def gen_html_input_tag>

#< def gen_html_form_best>
def gen_html_form_best(action,method,form_content,**kwargs):
  html_attrib_list = []
  input_tag = ''
  if(kwargs):
    if('css_class' in kwargs):
      html_attrib_list.append('class="%s"' % kwargs['css_class'])
    if('action' in kwargs):
      html_attrib_list.append('action="%s"' % kwargs['action'])
    if('input_tag' in kwargs):
      input_tag = kwargs['input_tag']
  miscAttrib = ' '.join(html_attrib_list)
 
  html_form = '<form action="%s" method="%s">\n  %s\n  %s\n</form>\n' % (action, method, form_content,input_tag)
  return html_form
#</def gen_html_form_best>

#< def gen_html_form>
#TODO: replace the lambda in 'class Manage' with this function
def gen_html_form(action,method,submit_value,contents):
  html_form = '<form action="%s" method="%s">\n  %s\n  <input type="submit" value="%s">\n</form>\n' % (action, method, contents,submit_value)
  return html_form
#</def gen_html_form>

#< def gen_html_form_flexible>
#TODO: replace the lambda in 'class Manage' with this function
def gen_html_form_flexible(action,method,submit_value,contents,**kwargs):
  inputVarDict = {}
  if('enctype' in kwargs):
    inputVarDict['enctype'] = kwargs['enctype']
  formTagAttrib = ''
  if('enctype' in inputVarDict):
    formTagAttrib += 'enctype="%s"' % inputVarDict['enctype']
  html_form = '<form action="%s" method="%s" %s>\n  %s\n  <input type="submit" value="%s">\n</form>\n' % (action, method, formTagAttrib, contents,submit_value)
  return html_form
#</def gen_html_form_flexible>

#< get_html_template_table>
def get_html_template_table(tableRows):
  template = """\
    <table border=1 cellspacing=0>
        %s
    </table>
    </body>
  </html>
      """
#  headerOwn = generateTableRow(['Name','Last New Picture','Number of Pictures','Delete'])
#  headerSub = generateTableRow(['Name','Last New Picture','Number of Pictures','Views','Unsubscribe'])
  # return both rows in the table
#  return template % (headerOwn + '\n' + headerSub)
  return template % tableRows
  return template
#</get_html_template_table>

################################################################
# < def_gen_html_form_checkbox>
# works as tested on 'manage' service
def gen_html_form_checkbox(name,value):
  checkbox = '<input type="checkbox" name="%s" value="%s">' % (name,value)
  return checkbox
# </def_gen_html_form_checkbox>
################################################################


################################################################
# < def_gen_html_form_emailrate>
def gen_html_form_emailrate(**kwargs):
  #< read in options>
  paramDict = {}
  if(kwargs):
    for param in ['action']:
      if param in kwargs:
        paramDict[param] = kwargs[param]
      else:
        paramDict['param'] = 'default_%s' % (param)
  #paramDict['action'] = 'default' # HACK TODO:
  inputValue = 'Update Notifcation Rate'
  #</read in options>
  # det up values
  template = ''
  #impl note: run cron every 5 minutes and read this data
  checkBoxConfigList = [
      ('0','No reports'),
      ('5','Every 5 minutes'),  # 1 min is smallest unit I will use for an email rate :-)
      ('60','Every 1 hour'),    # 1 h == 60 min
      ('1440','Every day'),     # 24 * 60 min == 1440 min
      ]
  cboxGroup = 'emailrate'
  cboxFormComponent = ''
  for cboxConf in checkBoxConfigList:
    #TODO: use a label
    #cboxFormComponent += gen_html_form_checkbox(cboxGroup, cboxConf[1]) + str(cboxConf[1])
    cboxFormComponent += gen_html_form_checkbox(cboxGroup, cboxConf[0]) + cboxConf[1]
    cboxFormComponent += '<br/>\n'
  
  template += generateContainerDivBlue(cboxFormComponent)
  template = gen_html_form(paramDict['action'] , 'post', inputValue, template)
  return template
# </def_gen_html_form_emailrate>
################################################################

################################################################
# < def_gen_html_gallery>
# usage:
#    response += bilder_templates.gen_html_gallery(jsonImgStr = jsonParam, imgrange = 5)
def gen_html_gallery(**kwargs):
  imgDataDict = {}
  #imgDataDict = 'no_images'
  if('jsonImgStr' in kwargs):
    imgDataDict['imgList'] = json.loads(kwargs['jsonImgStr'])
  if('imgList' in kwargs):
    imgDataDict['imgList'] = kwargs['imgList']
  for param in ['imgConfJson']:
    if(param in kwargs):
      imgDataDict[param] = kwargs[param]
  # defaults
   # default num photos to display - show entire list by default
  if(0):
    if(range not in imgDataDict):
      imgDataDict['imgrange'] = len(imgDataDict['imgList'])
  # </options>
  # desired data format:
  # img->tag
  # streamid->name
  # tags -> tags
  # needs:
  # coverurl -> <string>

  # configure gallery properties
  # pass in imgConfig:
  # imgConfig{
  #   src     : url
  #   alt     : description
  #   caption : label
  # }
  # full options:
  # src-url, alt-text, caption-text
  # second tier:
  # src-url, alt-text (should we set this as caption-text?)
  # src-url, caption-text (set as  alt-text)
  # basic:
  # src-url, becomes alt-text, no caption-text
  imgConfigList = []

  if('imgConfJson' in imgDataDict):
    imgConfigList = json.loads(imgDataDict['imgConfJson'])
    # set default alt
    for imgConf in imgConfigList:
      # set 'alt' to 'caption' if undef:
      if('caption' in imgConf and 'alt' not in imgConf):
        imgConf['alt'] = imgConf['caption']
      # set 'caption' to 'label' if undef:
      if('alt' in imgConf and 'caption' not in imgConf):
        imgConf['caption'] = imgConf['alt']
    #return (json.dumps(imgConfigList));

    
  # populate defaults attribs if simple list of urls
  elif('imgList' in imgDataDict):
    for imgurl in imgDataDict['imgList']:
      tmpConf = {
        'src'     : imgurl,
        'alt'     : imgurl,
      }
      imgConfigList.append(tmpConf)

  # specify default range - alt: check for range further down
  if(range not in imgDataDict):
    imgDataDict['imgrange'] = len(imgConfigList)


  
  # div
  bgcolor = '#93C572' #pistachio' # tried: ['seagreen']
  divStyleTemplate = \
    '''
    border-style:solid;
    border-width:1px;
    padding:0.5em 0.5em 0.5em 0.5em;
    background-color:%s;
    height: 100px
    width: 100px
    '''
  divStyle = divStyleTemplate % (bgcolor)
  # /div

  galleryList = []
  # new:
  #return (json.dumps(imgConfigList));
  for imgConfDict in (imgConfigList):
  #for imgConfDict in (imgConfigList[:imgDataDict['imgrange']]):
    htmlImgTag = '<img src="%s" alt="%s" height=80px/>' % (imgConfDict['src'], imgConfDict['alt'])
    if('caption' in imgConfDict):
      htmlPTag = '<p>%s</p>' % (imgConfDict['caption'])
      htmlImgTag += htmlPTag
    imgDiv     = '<div style="%s">%s</div>' % (divStyle, htmlImgTag )
    #imgDiv += '<p>%s</p>' % (imgConfDict) # make sure this doesn't break 'viewsinglestream'
    galleryList.append(imgDiv)

  galleryStrTable = get_html_template_table(
     generateTableRow(galleryList)
     )

  galleryStr = galleryStrTable
  return generateContainerDiv(galleryStr,'wheat',title='Stream Gallery')
  #response += bilder_templates.generateContainerDiv(jsonStr,bgcolor='wheat',title='Stream Gallery')

# </def_gen_html_gallery>
################################################################


def get_html_template_search_form(**kwargs):
  # default
  action = '/searchallstreams'
  # < speak now...>
  if(kwargs): #TODO: json
    if 'action' in kwargs:
      action = kwargs['action']
  # </or forever hold your peace.>
  template = ''
  template = """\
  <!--<p>#TODO: </p>-->
  <label for="input">Riddle Me This:</label>
  <input name="search_query">
  """
  template = gen_html_form(action , 'post', 'Search File', template)
  return template
#< get_html_template_search_form

#< get_page_template_upload_file>
def get_page_template_upload_file(action):
  template = """\
  <div>
    <textarea name="file_comments" rows="1" cols="60">Comments</textarea><br/>
    <input type="file" name="img"/><br/>
    <!--<input type="submit" value="Upload File"><br/>-->
  </div> 
  """
  #action = 'img_upload'
  template = gen_html_form_flexible(action , 'post', 'Upload File', template,  enctype="multipart/form-data")
  return template
#</get_page_template_upload_file>

################################################################
#< get_html_template_stream_subscribe>
def get_html_template_stream_subscribe(action, stream_name):
  # service: 
  # need to pass {"action": "unsubscribe", "stream_name": "testname"}
  template = """\
  <div>
    <!--
    <textarea name="file_comments" rows="1" cols="60">Comments</textarea><br/>
    <input type="file" name="img"/><br/>
    -->
    <div><input name="action" value="managestreamsub" type='hidden'></div>
    <div><input name="stream_name" value="%s" type='hidden'></div>
    <div><input name="submanage" value="subscribe" type='hidden'></div>
  </div> 
  """
  template2 = template % (stream_name)
  template = gen_html_form(action , 'post', 'Subscribe', template2)
  return template
#</get_html_template_stream_subscribe>
################################################################

def get_page_template_create_stream():
  # TODO: automate div generation, i.e. <div %s><label>%s</label> and name=%s
  # TODO: move labels beneath boxes
  # http://www.w3schools.com/css/css_border.asp
  # READ: http://www.w3schools.com/css/css_boxmodel.asp
  PAGE_TEMPLATE_CREATE_STREAM = """\
      <style>
        div.outline {border-style:solid;border-width:1px;padding:0.5em 0 0.5em 0.5em;background-color:#b0c4de;}
      </style>
      <p>TODO: rm this INFO when done<br/>
      INFO: this form sends below fields to action='sign'->'handler:Guestbook'
      <form action="/sign?%s" method="post">
        <div class="outline">
          <label for="textarea">Name Your Stream:</label><br/>
          <textarea name="stream_name" rows="2" cols="60"></textarea></div>
        <div class="outline">
          <!-- TODO: find the javascript to have clear-on-click grey text -->
          <!-- <label for="textarea">Emails:</label><br/>-->
          <textarea name="stream_subscribers" rows="2" cols="60">test@example.com</textarea>
          </br/>
        <!--  </div>
        <div class="outline">-->
          <!--<label for="textarea">Optional message for invite</label><br/>-->
          <textarea name="invite_message" rows="2" cols="60">Optional message for invite</textarea><br/>
          <label for="textarea">Add Subscribers</label><br/>
        </div>
        <div class="outline">
          <label for="textarea">Tag Your Stream</label><br/>
          <textarea name="stream_tags" rows="2" cols="60">stream tags data</textarea>
        </div>
        <div class="outline">
          <label for="textarea">URL to Cover Image<br/>(optional)</label><br/>
          <textarea name="stream_cover_url" rows="2" cols="60"></textarea>
        </div>
        <div><input type="submit" value="Create Stream"></div>
      </form>
      <hr>
      <p>Select different User/Guestbook:</p>
      <form>Guestbook name:
        <input value="%s" name="guestbook_name">
        <input type="submit" value="switch">
      </form>
      <a href="%s">%s</a>
    </body>
  </html>
  """
  return PAGE_TEMPLATE_CREATE_STREAM

################################################################
#< def html_generate_body_template>
# TODO: kwargs, make title optional, etc
def html_generate_body_template(titleText,bodyHtml):
  html = \
    '''
    <html>
      <head>
        <title>%s</title>
      </head>
      <body>
        %s
      </body>
    </html>
    '''
  htmlOutPut = (html % (titleText,bodyHtml))
  return htmlOutPut
#</def html_generate_body_template>
################################################################

