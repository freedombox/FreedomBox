"""
The Form class is a helper class that takes parameters and method
calls and can return html for a form with appropriate hooks for css
styling.  It should allow you to display a form but have the
formatting and styling added by the class.  You can worry less about
how it looks while still getting consistent, decent-looking forms.

Take a look at the FirstBoot class for an example of forms in action.

Copyright 2011-2013 James Vasile

This software is released to you (yes, you) under the terms of the GNU
Affero General Public License, version 3 or later, available at
<http://www.gnu.org/licenses/agpl.html>.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.
"""
class Form():
    def __init__(self, action=None, cls='form', title=None, onsubmit=None, name=None, message='', method="post"):

        action = self.get_form_attrib_text('action', action)
        onsubmit = self.get_form_attrib_text('onsubmit', onsubmit)
        name = self.get_form_attrib_text('name', name)

        self.pretext = '           <form class="%s" method="%s" %s%s%s>\n' % (cls, method, action, onsubmit, name)
        if title:
            self.pretext += '             <h2>%s</h2>\n' % title

        if message:
            self.message = "<h3>%s</h3>" % message
        else:
            self.message = ''
        self.text = ''
        self.end_text = "</form>\n"
    def get_form_attrib_text(self, field, val):
        if val:
            return ' %s="%s"' % (field, val)
        else:
            return ''
    def html(self, html):
        self.text += html
    def dropdown(self, label='', name=None, id=None, vals=None, select=None, onchange=''):
        """vals is a list of values.
        select is the index in vals of the selected item.  None means no item is selected yet."""
        name, id = self.name_or_id(name, id)
        self.text += ("""             <label>
                <span>%(label)s</span>
                <select name="%(name)s" id="%(id)s" onchange="%(onchange)s">\n""" 
                      % {'label':label, 'name':name, 'id':id, 'onchange':onchange})
        for i in range(len(vals)):
            v = vals[i]
            if i == select:
                selected = "SELECTED"
            else:
                selected = ''
            self.text +="                   <option value=\"%s\" %s>%s</option>\n" % (v, selected, v)
        self.text += """                </select>
             </label>\n"""

    def dotted_quad(self, label='', name=None, id=None, quad=None):
        name, id = self.name_or_id(name, id)
        if not quad:
            quad = [0,0,0,0]
        self.text += """             <label>
                <span>%(label)s</span>
                <input type="text" class="inputtextnowidth" name="%(name)s0" id="%(id)s0" value="%(q0)s" maxlength="3" size="1"/><strong>.</strong>
                <input type="text" class="inputtextnowidth" name="%(name)s1" id="%(id)s1" value="%(q1)s" maxlength="3" size="1"/><strong>.</strong>
                <input type="text" class="inputtextnowidth" name="%(name)s2" id="%(id)s2" value="%(q2)s" maxlength="3" size="1"/><strong>.</strong>
                <input type="text" class="inputtextnowidth" name="%(name)s3" id="%(id)s3" value="%(q3)s" maxlength="3" size="1"/>
             </label>""" % {'label':label, 'name':name, 'id':id, 'q0':quad[0], 'q1':quad[1], 'q2':quad[2], 'q3':quad[3]}

    def text_input(self, label='', name=None, id=None, type='text', value='', size=20):
        name, id = self.name_or_id(name, id)
        if type=="hidden":
            self.text += '<input type="%s" class="inputtext" name="%s" id="%s" value="%s"/>' % (type, name, id, value)
        else:
            self.text += """             <label>
                <span>%s</span>
                <input type="%s" class="inputtext" name="%s" id="%s" value="%s" size="%s"/>
             </label>""" % (label, type, name, id, value, size)
    def hidden(self, name=None, id=None, value=''):
        self.text_input(type="hidden", name=name, id=id, value=value)
    def text_box(self, label='', name=None, id=None, value=""):
        name, id = self.name_or_id(name, id)
        self.text += """
             <label>
                 <span>%s</span>
                 <textarea class="textbox" name="%s" id="%s">%s</textarea>
             </label>""" % (label, name, id, value)
    def submit(self, label='', name=None, id=None):
        name, id = self.name_or_id(name, id)
        self.text += """
             <div class="submit">
             <label><span></span>
                 <input type="submit" class="btn-primary" value="%s" name="%s" id="%s" />
             </label></div>\n""" % (label, name, id)
    def submit_row(self, buttons):
        """buttons is a list of tuples, each containing label, name, id.  Name and id are optional."""
        self.text += '<div class="submit"><label>'
        button_text = ''
        for button in buttons:
            label = button[0]
            try:
                name = button[1]
            except:
                name = None

            try:
                id = button[2]
            except:
                id = None

            name, id = self.name_or_id(name, id)

            if button_text != '':
                button_text += "&nbsp;"
            button_text += '<input type="submit" class="btn-primary" value="%s" name="%s" id="%s" />\n' % (label, name, id)
        self.text += '%s</div></label>' % button_text
    def name_or_id(self, name, id):
        if not name: name = id
        if not id: id = name
        if not name: name = ''
        if not id: id = ''
        return name, id
    def checkbox(self, label='', name='', id='', checked=''): 
        name, id = self.name_or_id(name, id)
        if checked:
            checked = 'checked="on"'
        self.text += """
             <div class="checkbox">
             <label>
                <span>%s</span>
                <input type=checkbox name="%s" id="%s" %s/>
             </label></div>\n""" % (label, name, id, checked)
    def radiobutton(self, label='', name='', id='', value='', checked=''): 
        name, id = self.name_or_id(name, id)
        if checked:
            checked = 'checked="on"'
        self.text += """
             <div class="radio">
             <label>
                <span>%s</span>
                <input type="radio" name="%s" id="%s" value="%s" %s/>
             </label></div>\n""" % (label, name, id, value, checked)
    def get_checkbox(self, name='', id=''):
        return '<input type=checkbox name="%s" id="%s" />\n' % self.name_or_id(name, id)
    def render(self):
        return self.pretext+self.message+self.text+self.end_text
