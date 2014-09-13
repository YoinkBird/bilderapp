
#< def generateContainerDiv>
def generateContainerDiv(containerTitle,bgcolor):
  handlerContainer = '<div style="border-style:solid;border-width:1px;padding:0.5em 0 0.5em 0.5em;background-color:%s;">%s</div>' % (bgcolor, containerTitle )
  return handlerContainer
#</def generateContainerDiv>

#< def generateContainerDivBlue>
def generateContainerDivBlue(containerTitle):
  divColor = '#B0C4DE'
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

#< def gen_html_form>
#TODO: replace the lambda in 'class Manage' with this function
def gen_html_form(action,method,submit_value,contents):
  html_form = '<form action="%s" method="%s">\n  %s\n  <input type="submit" value="%s">\n</form>\n' % (action, method, contents,submit_value)
  return html_form
#</def gen_html_form>

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

#< get_page_template_upload_file>
def get_page_template_upload_file(action):
  template = """\
  <div>
    <p>#TODO: filename is probably 'friendly name', i.e. 'waterfall' instead of DSC02093</p>
    <textarea name="file_name" rows="1" cols="60">File Name</textarea><br/>
    <textarea name="file_comments" rows="1" cols="60">Comments</textarea><br/>
    <input type="file" name="img"/><br/>
    <!--<input type="submit" value="Upload File"><br/>-->
  </div> 
  """
  #action = 'img_upload'
  template = gen_html_form(action , 'post', 'Upload File', template)
  return template
#</get_page_template_upload_file>
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
          <textarea name="add_subscribers" rows="2" cols="60">test@example.com</textarea>
          </br/>
        <!--  </div>
        <div class="outline">-->
          <!--<label for="textarea">Optional message for invite</label><br/>-->
          <textarea name="invite_message" rows="2" cols="60">Optional message for invite</textarea><br/>
          <label for="textarea">Add Subscribers</label><br/>
        </div>
        <div class="outline">
          <label for="textarea">Tag Your Stream</label><br/>
          <textarea name="stream_tags" rows="2" cols="60"></textarea>
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
