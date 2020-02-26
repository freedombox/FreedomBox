# SPDX-License-Identifier: AGPL-3.0-or-later
"""
MoinMoin wiki parser
"""

from enum import Enum
from pathlib import Path
from xml.sax.saxutils import escape
import logging
import re


class Element:
    """Represents an element of a MoinMoin wiki page."""

    def __repr__(self, *args):
        rep = self.__class__.__name__ + '('
        if args:
            rep += repr(args[0])

        for arg in args[1:]:
            rep += ', ' + repr(arg)

        rep += ')'
        return rep

    def to_docbook(self, context=None):
        return '<' + self.__class__.__name__ + '/>'


class Heading(Element):

    def __init__(self, level, content):
        self.level = min(level, 5)
        self.content = content

    def __repr__(self):
        return super().__repr__(self.level, self.content)

    def to_docbook(self, context=None):
        return f'<title>{escape(self.content)}</title>'


class TableOfContents(Element):

    def __init__(self, max_level=None):
        self.max_level = max_level

    def __repr__(self):
        if self.max_level:
            return super().__repr__(self.max_level)
        else:
            return super().__repr__()

    def to_docbook(self, context=None):
        return ''


class Text(Element):

    def __init__(self, content):
        self.content = content

    def __repr__(self):
        return super().__repr__(self.content)

    def to_docbook(self, context=None):
        return escape(self.content)


class PlainText(Text):
    pass


class Url(Text):

    def to_docbook(self, context=None):
        return f'<ulink url="{self.content}"/>'


class ItalicText(Text):

    def to_docbook(self, context=None):
        return f'<emphasis>{escape(self.content)}</emphasis>'


class BoldText(Text):

    def to_docbook(self, context=None):
        return f'<emphasis role="strong">{escape(self.content)}</emphasis>'


class MonospaceText(Text):

    def to_docbook(self, context=None):
        return f'<code>{escape(self.content)}</code>'


class CodeText(Text):

    def to_docbook(self, context=None):
        if context and 'in_paragraph' in context and context['in_paragraph']:
            return f'<code>{escape(self.content)}</code>'
        else:
            return f'<screen><![CDATA[{self.content}]]></screen>'


class UnderlineText(Text):

    def to_docbook(self, context=None):
        return f'<emphasis role="underline">{escape(self.content)}</emphasis>'


class SmallerTextWarning(Element):

    def to_docbook(self, context=None):
        return '<!--"~-smaller-~" is not applicable to DocBook-->'


class Paragraph(Element):

    def __init__(self, content, indent=0):
        self.content = content
        self.indent = indent

    def __repr__(self):
        if self.indent:
            rep = super().__repr__(self.content, self.indent)
        else:
            rep = super().__repr__(self.content)
        return rep

    def add_content(self, content):
        self.content += content

    def to_docbook(self, context=None):
        xml = '<para>'
        if context is not None:
            context['in_paragraph'] = True

        item_xml = [item.to_docbook(context) for item in self.content]
        if context is not None:
            context['in_paragraph'] = False

        xml += ' '.join(item_xml) + ' </para>'
        return xml


class Link(Element):

    def __init__(self, target, text=None, params=None):
        self.target = target
        self.text = text
        self.params = params

    def __repr__(self):
        if self.text and self.params:
            rep = super().__repr__(self.target, self.text, self.params)
        elif self.text:
            rep = super().__repr__(self.target, self.text)
        else:
            rep = super().__repr__(self.target)
        return rep

    def to_docbook(self, context=None):
        target = escape(self.target)
        if target.startswith('FreedomBox/') or \
           target.startswith('InstallingDebianOn/'):
            target = 'https://wiki.debian.org/' + target + '#'

        link_text = ''
        if self.text:
            for element in self.text:
                link_text += element.to_docbook(context)

        xml = f'<ulink url="{target}">{link_text}</ulink>'
        return xml


class EmbeddedLink(Link):
    pass


class EmbeddedAttachment(EmbeddedLink):

    def __init__(self, target, text=None, params=None, context=None):
        self.page_title = context.get('title', None) if context else None
        if not text:
            text = [PlainText(target)]

        return super().__init__(target, text, params)

    def to_docbook(self, context=None):
        if self.page_title:
            target = 'https://wiki.debian.org/' + self.page_title \
                + '?action=AttachFile&amp;do=get&amp;target=' \
                + escape(self.target)
        else:
            target = escape(self.target)

        xml = '<inlinemediaobject><imageobject>'
        xml += f'<imagedata fileref="{target}"'
        if self.params:
            params = self.params.split(',')
            for param in params:
                prop, value = param.split('=')
                if prop == 'height':
                    prop = 'depth'

                xml += ' ' + prop + '="' + value + '"'

        xml += '/>'
        xml += '</imageobject>'
        if self.text:
            xml += '<textobject><phrase>'
            for element in self.text:
                xml += element.to_docbook(context)

            xml += '</phrase></textobject>'

        xml += '</inlinemediaobject>'
        return xml


class ListItem(Element):

    def __init__(self, content=None, override_marker=False):
        self.content = content or []
        self.override_marker = override_marker

    def __repr__(self):
        return super().__repr__(self.content)

    def add_content(self, content):
        self.content.append(content)

    def to_docbook(self, context=None):
        if self.override_marker:
            xml = '<listitem override="none">'
        else:
            xml = '<listitem>'

        item_xml = [item.to_docbook(context) for item in self.content]
        xml += ' '.join(item_xml) + '</listitem>'
        return xml


class ListType(Enum):
    PLAIN = 1
    BULLETED = 2
    NUMBERED = 3


class List(Element):

    def __init__(self, list_type=ListType.PLAIN, items=None):
        if isinstance(list_type, str):
            if list_type == 'plain':
                self.list_type = ListType.PLAIN
            elif list_type == 'bulleted':
                self.list_type = ListType.BULLETED
            else:
                self.list_type = ListType.NUMBERED
        else:
            self.list_type = list_type

        self.items = items or []

    def __repr__(self):
        if self.list_type == ListType.PLAIN:
            list_type = 'plain'
        elif self.list_type == ListType.BULLETED:
            list_type = 'bulleted'
        else:
            list_type = 'numbered'

        return super().__repr__(list_type, self.items)

    def add_item(self, item):
        self.items.append(item)

    def to_docbook(self, context=None):
        if self.list_type == ListType.PLAIN:
            xml = '<itemizedlist>'
        elif self.list_type == ListType.BULLETED:
            xml = '<itemizedlist>'
        else:
            xml = '<orderedlist numeration="arabic">'

        for item in self.items:
            xml += item.to_docbook(context)

        if self.list_type == ListType.PLAIN:
            xml += '</itemizedlist>'
        elif self.list_type == ListType.BULLETED:
            xml += '</itemizedlist>'
        else:
            xml += '</orderedlist>'

        return xml


class HorizontalRule(Element):

    def __init__(self, dashes):
        self.dashes = dashes

    def __repr__(self):
        return super().__repr__(self.dashes)

    def to_docbook(self, context=None):
        return '<!--rule (<hr>) is not applicable to DocBook-->'


class TableItem(Element):

    def __init__(self, content=None, align=None):
        self.content = content
        self.align = align

    def __repr__(self):
        if self.content and self.align:
            rep = super().__repr__(self.content, self.align)
        elif self.content:
            rep = super().__repr__(self.content)
        else:
            rep = super().__repr__()

        return rep

    def to_docbook(self, context=None):
        if self.align:
            align = f'align="{self.align}" '
        else:
            align = ''

        if self.content:
            xml = f'<entry {align}colsep="1" rowsep="1">'
            for item in self.content:
                xml += item.to_docbook(context)
            xml += '</entry>'

        else:
            xml = ''

        return xml


class TableRow(Element):

    def __init__(self, items):
        self.items = items

    def __len__(self):
        return len(self.items)

    def __repr__(self):
        return super().__repr__(self.items)

    def to_docbook(self, context=None):
        xml = '<row rowsep="1">'
        for item in self.items:
            xml += item.to_docbook(context)
        xml += '</row>'
        return xml


class Table(Element):

    def __init__(self, rows, style=None):
        self.rows = rows
        self.style = style

    def __repr__(self):
        if self.style:
            rep = super().__repr__(self.rows, self.style)
        else:
            rep = super().__repr__(self.rows)
        return rep

    def to_docbook(self, context=None):
        cols = len(self.rows[0]) if self.rows else 0
        xml = f'<informaltable><tgroup cols="{cols}"><tbody>'
        for row in self.rows:
            xml += row.to_docbook(context)
        xml += '</tbody></tgroup></informaltable>'
        return xml


class Include(Element):

    def __init__(self, page, from_marker=None, to_marker=None):
        self.page = page
        self.from_marker = from_marker
        self.to_marker = to_marker

    def __repr__(self):
        if self.from_marker and self.to_marker:
            rep = super().__repr__(self.page, self.from_marker, self.to_marker)
        elif self.to_marker:
            rep = super().__repr__(self.page, self.to_marker)
        else:
            rep = super().__repr__(self.page)
        return rep

    def to_docbook(self, context=None):
        if context and 'path' in context:
            include_folder = context['path'].parent
        else:
            include_folder = Path('.')

        include_file = include_folder / Path(
            self.page.split('/')[-1] + '.raw.wiki')
        if not include_file.exists():
            logging.warning('Included page not found:' + str(include_file))
            return ''

        with include_file.open() as wiki_file:
            wiki_text = wiki_file.read()

        context = get_context(include_file)
        parsed_wiki = parse_wiki(wiki_text, context, self.from_marker,
                                 self.to_marker)
        return generate_inner_docbook(parsed_wiki, context)


class Admonition(Element):

    def __init__(self, style, content):
        self.style = style
        self.content = content

    def __repr__(self):
        return super().__repr__(self.style, self.content)

    def to_docbook(self, context=None):
        xml = '<' + self.style + '>'
        item_xml = [item.to_docbook(context) for item in self.content]
        xml += ' '.join(item_xml) + '</' + self.style + '>'
        return xml


class Comment(Text):

    def to_docbook(self, context=None):
        return f'<para><remark>{escape(self.content)}</remark></para>'


class BeginInclude(Element):

    def to_docbook(self, context=None):
        return ''


class EndInclude(Element):

    def to_docbook(self, context=None):
        return ''


class Category(Element):

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return super().__repr__(self.name)

    def to_docbook(self, context=None):
        return ''


class Anchor(Element):

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return super().__repr__(self.name)

    def to_docbook(self, context=None):
        return f'<anchor id="{self.name}"/>'


def split_formatted(text, delimiter, end_delimiter=None):
    """
    Split formatted text marked by delimiter, if it is found at beginning.
    A distinct end delmiter can be specified, or it is same as delimiter.
    Return (formatted_text, remaining_text) if it is found.
    Return (None, text) otherwise.
    """
    text = text.strip()
    end_delimiter = end_delimiter or delimiter
    content = None
    if text.startswith(delimiter):
        text = text.lstrip(delimiter)
        end = text.find(end_delimiter)
        content = text[:end]
        text = text[end:].lstrip(end_delimiter)

    return (content, text)


def parse_text(line, context=None):
    """
    Parse a line of MoinMoin wiki text.
    Returns a list of objects representing text.
    """
    # Handle !WikiWords which suppress automatic links.
    words = [word.lstrip('!') for word in line.split()]
    line = ' '.join(words)

    result = []
    while line:
        content, line = split_formatted(line, '~-', '-~')
        if content:
            result.append(SmallerTextWarning())
            line = content + line
            # continue processing line

        content, line = split_formatted(line, "'''")
        if content:
            result.append(BoldText(content))
            continue

        content, line = split_formatted(line, "''")
        if content:
            if content.startswith('[[') and content.endswith(']]'):
                # Special handling for links within emphasis
                content = content.lstrip('[[').rstrip(']]')
                target, _, remaining = content.partition('|')
                text = None
                if remaining:
                    text, _, remaining = remaining.partition('|')

                params = None
                if remaining:
                    params, _, remaining = remaining.partition('|')

                link = Link(target, [ItalicText(text)], params)
                result.append(link)
                continue

            else:
                result.append(ItalicText(content))
                continue

        content, line = split_formatted(line, '`')
        if content:
            result.append(MonospaceText(content))
            continue

        content, line = split_formatted(line, '{{{', '}}}')
        if content:
            result.append(CodeText(content))
            continue

        content, line = split_formatted(line, '__')
        if content:
            result.append(UnderlineText(content))
            continue

        content, line = split_formatted(line, '[[', ']]')
        if content:
            target, _, remaining = content.partition('|')
            text = None
            if remaining:
                # Handle embedded attachments inside links
                if '{{' in remaining and '}}' in remaining:
                    index = remaining.find('}}')
                    text = remaining[:index + 1]
                    remaining = remaining[index + 2:]
                    more_text, _, remaining = remaining.partition('|')
                    text += more_text
                else:
                    text, _, remaining = remaining.partition('|')

                text = parse_text(text)

            params = None
            if remaining:
                params, _, remaining = remaining.partition('|')

            link = Link(target, text, params)
            result.append(link)
            continue

        content, line = split_formatted(line, '{{', '}}')
        if content:
            target, _, remaining = content.partition('|')
            text = None
            if remaining:
                # Handle embedded attachments inside links
                if '{{' in remaining and '}}' in remaining:
                    index = remaining.find('}}')
                    text = remaining[:index + 1]
                    remaining = remaining[index + 2:]
                    more_text, _, remaining = remaining.partition('|')
                    text += more_text
                else:
                    text, _, remaining = remaining.partition('|')

                text = parse_text(text)

            params = None
            if remaining:
                params, _, remaining = remaining.partition('|')

            if target.startswith('attachment:'):
                link = EmbeddedAttachment(target[11:], text, params, context)
            else:
                link = EmbeddedLink(target, text, params)

            result.append(link)
            continue

        content = re.split(r"''|`|{{|__|\[\[", line)[0]
        if content:
            line = line.replace(content, '', 1)
            content = content.strip()
            while content:
                if '<' not in content and '>' not in content \
                   and (content.startswith('http://')
                        or content.startswith('https://')):
                    contents = content.split(' ', 1)
                    result.append(Url(contents[0]))
                    if len(contents) > 1:
                        content = contents[1]
                    else:
                        break
                else:
                    found_http = content.find('http://')
                    found_https = content.find('https://')
                    if found_http >= 0:
                        if found_https >= 0:
                            length = min(content.find('http://'),
                                         content.find('https://'))
                        else:
                            length = found_http
                    else:
                        length = found_https

                    if length > 0:
                        result.append(PlainText(content[:length]))
                        content = content[length:]
                    else:
                        result.append(PlainText(content))
                        break

                continue

            continue

        break

    return result


def parse_table_row(line, context=None):
    """Parse a line of MoinMoin wiki text. Returns a TableRow."""
    row_cells = re.split(r'\|\|', line)[1:-1]
    row_items = []
    for cell in row_cells:
        content = cell.strip()
        if content:
            # remove <tablestyle=...> that was already processed
            content = re.sub('<tablestyle=[^>]+>', '', content)
            align = None
            match = re.match('<style=([^>]+)>', content)
            if match:
                style = match.group(1)
                if 'text-align: center' in style:
                    align = 'center'

                # remove <style=...>
                content = re.sub('<style=[^>]+>', '', content)

            paragraphs = content.split('<<BR>>')
            paragraphs = [
                Paragraph(parse_text(paragraph, context))
                for paragraph in paragraphs
            ]
            row_items.append(TableItem(paragraphs, align))
        else:
            row_items.append(TableItem())

    return TableRow(row_items)


def parse_list(list_data, context=None):
    """Parse a list of (list_type, indent, content) tuples representing a
    MoinMoin wiki list.  Returns a List and list of any remaining data.
    """
    if not list_data:
        return None, list_data

    list_type = list_data[0][0]
    current_level = list_data[0][1]
    parsed_list = List(list_type)
    override_marker = True if list_type == ListType.PLAIN else False
    while list_data:
        level = list_data[0][1]
        if level > current_level:
            new_list, list_data = parse_list(list_data, context)
            if new_list:
                parsed_list.items[-1].add_content(new_list)

        elif level < current_level:
            break

        else:
            content = list_data.pop(0)[2]
            parsed_list.add_item(
                ListItem([Paragraph(parse_text(content, context))],
                         override_marker=override_marker))

    return parsed_list, list_data


def parse_wiki(text, context=None, begin_marker=None, end_marker=None):
    """Parse MoinMoin wiki text. Returns a list of Elements.

    >>> parse_wiki('')
    []

    >>> parse_wiki('<<TableOfContents()>>')
    [TableOfContents()]
    >>> parse_wiki('<<TableOfContents(2)>>')
    [TableOfContents(2)]

    >>> parse_wiki('= heading 1st level =')
    [Heading(1, 'heading 1st level')]
    >>> parse_wiki('===== heading 5th level =====')
    [Heading(5, 'heading 5th level')]

    >>> parse_wiki('plain text')
    [Paragraph([PlainText('plain text')])]
    >>> parse_wiki('https://freedombox.org')
    [Paragraph([Url('https://freedombox.org')])]
    >>> parse_wiki("''italic''")
    [Paragraph([ItalicText('italic')])]
    >>> parse_wiki("'''bold'''")
    [Paragraph([BoldText('bold')])]
    >>> parse_wiki("normal text followed by '''bold text'''")
    [Paragraph([PlainText('normal text followed by'), BoldText('bold text')])]
    >>> parse_wiki('`monospace`')
    [Paragraph([MonospaceText('monospace')])]
    >>> parse_wiki('{{{code}}}')
    [Paragraph([CodeText('code')])]
    >>> parse_wiki('__underline__')
    [Paragraph([UnderlineText('underline')])]
    >>> parse_wiki('~-smaller text-~')
    [Paragraph([SmallerTextWarning(), PlainText('smaller text')])]
    >>> parse_wiki('!FreedomBox')
    [Paragraph([PlainText('FreedomBox')])]
    >>> parse_wiki('making a point!')
    [Paragraph([PlainText('making a point!')])]
    >>> parse_wiki('Back to [[FreedomBox/Manual|manual]] page.')
    [Paragraph([PlainText('Back to'), Link('FreedomBox/Manual', \
[PlainText('manual')]), PlainText('page.')])]
    >>> parse_wiki('[[attachment:Searx.webm|Searx installation and first steps\
|&do=get]]')
    [Paragraph([Link('attachment:Searx.webm', \
[PlainText('Searx installation and first steps')], '&do=get')])]
    >>> parse_wiki('[[https://onionshare.org/|Onionshare]]')
    [Paragraph([Link('https://onionshare.org/', [PlainText('Onionshare')])])]

    >>> parse_wiki('{{attachment:cockpit-enable.png}}')
    [Paragraph([EmbeddedAttachment('cockpit-enable.png', \
[PlainText('cockpit-enable.png')])])]
    >>> parse_wiki('{{attachment:Backups_Step1_v49.png|Backups: Step 1|\
width=800}}')
    [Paragraph([EmbeddedAttachment('Backups_Step1_v49.png', \
[PlainText('Backups: Step 1')], 'width=800')])]

    >>> parse_wiki(' * first item\\n * second item')
    [List('bulleted', [ListItem([Paragraph([PlainText('first item')])]), \
ListItem([Paragraph([PlainText('second item')])])])]
    >>> parse_wiki('text to introduce\\n * a list')
    [Paragraph([PlainText('text to introduce')]), \
List('bulleted', [ListItem([Paragraph([PlainText('a list')])])])]
    >>> parse_wiki(' . first item\\n . second item')
    [List('plain', [ListItem([Paragraph([PlainText('first item')])]), \
ListItem([Paragraph([PlainText('second item')])])])]
    >>> parse_wiki(' * item 1\\n  * item 1.1')
    [List('bulleted', [ListItem([Paragraph([PlainText('item 1')]), \
List('bulleted', [ListItem([Paragraph([PlainText('item 1.1')])])])])])]
    >>> parse_wiki(' 1. item 1\\n  1. item 1.1')
    [List('numbered', [ListItem([Paragraph([PlainText('item 1')]), \
List('numbered', [ListItem([Paragraph([PlainText('item 1.1')])])])])])]

    >>> parse_wiki('----')
    [HorizontalRule(4)]
    >>> parse_wiki('----------')
    [HorizontalRule(10)]

    >>> parse_wiki("||'''A'''||'''B'''||'''C'''||\\n||1    ||2    ||3    ||")
    [Table([TableRow([TableItem([Paragraph([BoldText('A')])]), \
TableItem([Paragraph([BoldText('B')])]), \
TableItem([Paragraph([BoldText('C')])])]), \
TableRow([TableItem([Paragraph([PlainText('1')])]), \
TableItem([Paragraph([PlainText('2')])]), \
TableItem([Paragraph([PlainText('3')])])])])]

    >>> parse_wiki("||<tablestyle='border:1px solid black;width: 80%'>A||")
    [Table([TableRow([TableItem([Paragraph([PlainText('A')])])])], \
'border:1px solid black;width: 80%')]

    >>> parse_wiki('/* comment */')
    [Comment('comment')]

    >>> parse_wiki('## BEGIN_INCLUDE')
    [BeginInclude()]

    >>> parse_wiki('## END_INCLUDE')
    [EndInclude()]

    >>> parse_wiki('CategoryFreedomBox')
    [Category('FreedomBox')]

    >>> parse_wiki('<<Anchor(gettinghelp)>>')
    [Anchor('gettinghelp')]

    >>> parse_wiki('<<Include(FreedomBox/Portal)>>')
    [Include('FreedomBox/Portal')]
    >>> parse_wiki('<<Include(FreedomBox/Hardware, , \
from="## BEGIN_INCLUDE", to="## END_INCLUDE")>>')
    [Include('FreedomBox/Hardware', '## BEGIN_INCLUDE', '## END_INCLUDE')]

    >>> parse_wiki('{{{\\nnmcli connection\\n}}}')
    [CodeText('nmcli connection')]
    >>> parse_wiki("{{{#!wiki caution\\nDon't overuse admonitions\\n}}}")
    [Admonition('caution', [Paragraph(\
[PlainText("Don't overuse admonitions")])])]

    >>> parse_wiki('a\\n\\n## END_INCLUDE\\n\\nb', \
    None, None, '## END_INCLUDE')
    [Paragraph([PlainText('a')])]
    >>> parse_wiki('a\\n\\n## BEGIN_INCLUDE\\n\\nb' \
    '\\n\\n## END_INCLUDE\\n\\nc', \
    None, '## BEGIN_INCLUDE', '## END_INCLUDE')
    [Paragraph([PlainText('b')])]

    >>> parse_wiki('a<<BR>>\\nb')
    [Paragraph([PlainText('a')]), Paragraph([PlainText('b')])]
    >>> parse_wiki('{{{#!wiki caution\\n\\nOnce some other app is set as the \
home page, you can only navigate to the !FreedomBox Service (Plinth) by \
typing https://myfreedombox.rocks/plinth/ into the browser. <<BR>>\\n\
''/freedombox'' can also be  used as an alias to ''/plinth''\\n}}}')
    [Admonition('caution', [Paragraph([PlainText('Once some other app is set \
as the home page, you can only navigate to the FreedomBox Service (Plinth) by \
typing '), Url('https://myfreedombox.rocks/plinth/'), PlainText('into the \
browser.')]), Paragraph([PlainText('/freedombox can also be used as an alias \
to /plinth')])])]

    >>> parse_wiki('     {{{\\n     nmap -p 80 --open -sV 192.168.0.0/24 \
(replace the ip/netmask with the one the router uses)\\n     }}}\\n     In \
most cases you can look at your current IP address, and change the last \
digits with zero to find your home network, like so: XXX.XXX.XXX.0/24')
    [CodeText('     nmap -p 80 --open -sV 192.168.0.0/24 (replace the \
ip/netmask with the one the router uses)'), Paragraph([PlainText('In \
most cases you can look at your current IP address, and change the last \
digits with zero to find your home network, like so: XXX.XXX.XXX.0/24')])]

    >>> parse_wiki('  If this command shows an error such as ''new key but \
contains no user ID - skipped'', then use a different keyserver to download \
the keys:\\n  {{{\\n$ gpg --keyserver keys.gnupg.net --recv-keys \
BCBEBD57A11F70B23782BC5736C361440C9BC971\\n$ gpg --keyserver keys.gnupg.net \
--recv-keys 7D6ADB750F91085589484BE677C0C75E7B650808\\n$ gpg --keyserver \
keys.gnupg.net --recv-keys 013D86D8BA32EAB4A6691BF85D4153D6FE188FC8\\n  }}}')
    [Paragraph([PlainText('If this command shows an error such as new key but \
contains no user ID - skipped, then use a different keyserver to download the \
keys:')]), CodeText('$ gpg --keyserver keys.gnupg.net --recv-keys \
BCBEBD57A11F70B23782BC5736C361440C9BC971\\n$ gpg --keyserver keys.gnupg.net \
--recv-keys 7D6ADB750F91085589484BE677C0C75E7B650808\\n$ gpg --keyserver \
keys.gnupg.net --recv-keys 013D86D8BA32EAB4A6691BF85D4153D6FE188FC8')]

    >>> parse_wiki('User documentation:\\n * List of \
[[FreedomBox/Features|applications]] offered by !FreedomBox.')
    [Paragraph([PlainText('User documentation:')]), List('bulleted', \
[ListItem([Paragraph([PlainText('List of'), Link('FreedomBox/Features', \
[PlainText('applications')]), PlainText('offered by FreedomBox.')])])])]

    >>> parse_wiki('\
 * Within !FreedomBox Service (Plinth)\\n\
  1. select ''Apps''\\n\
  2. go to ''Radicale (Calendar and Addressbook)'' and \\n\
  3. install the application. After the installation is complete, make sure \
the application is marked "enabled" in the !FreedomBox interface. Enabling \
the application launches the Radicale CalDAV/CardDAV server. \\n\
  4. define the access rights:\\n\
   * Only the owner of a calendar/addressbook can view or make changes\\n\
   * Any user can view any calendar/addressbook, but only the owner can make \
changes\\n\
   * Any user can view or make changes to any calendar/addressbook')
    [List('bulleted', [\
ListItem([Paragraph([PlainText('Within FreedomBox Service (Plinth)')]), \
List('numbered', [ListItem([Paragraph([PlainText('select Apps')])]), \
ListItem([Paragraph([PlainText('go to Radicale (Calendar and Addressbook) \
and')])]), \
ListItem([Paragraph([PlainText('install the application. After the \
installation is complete, make sure the application is marked "enabled" in \
the FreedomBox interface. Enabling the application launches the Radicale \
CalDAV/CardDAV server.')])]), \
ListItem([Paragraph([PlainText('define the access rights:')]), \
List('bulleted', [ListItem([Paragraph([PlainText('Only the owner of a \
calendar/addressbook can view or make changes')])]), \
ListItem([Paragraph([PlainText('Any user can view any calendar/addressbook, \
but only the owner can make changes')])]), \
ListItem([Paragraph([PlainText('Any user can view or make changes to any \
calendar/addressbook')])])])])])])])]

    >>> parse_wiki('[[attachment:freedombox-screenshot-home.png|\
{{attachment:freedombox-screenshot-home.png|Home Page|width=300}}]]')
    [Paragraph([Link('attachment:freedombox-screenshot-home.png', \
[EmbeddedAttachment('freedombox-screenshot-home.png', \
[PlainText('Home Page')], 'width=300')])])]

    >>> parse_wiki(" * New wiki and manual content licence: \
''[[https://creativecommons.org/licenses/by-sa/4.0/|Creative Commons \
Attribution-ShareAlike 4.0 International]]'' (from June 13rd 2016).")
    [List('bulleted', [ListItem([Paragraph([PlainText('New wiki and manual \
content licence:'), Link('https://creativecommons.org/licenses/by-sa/4.0/', \
[ItalicText('Creative Commons Attribution-ShareAlike 4.0 International')]), \
PlainText('(from June 13rd 2016).')])])])]

    >>> parse_wiki('An alternative to downloading these images is to \
[[InstallingDebianOn/TI/BeagleBone|install Debian]] on the !BeagleBone and \
then [[FreedomBox/Hardware/Debian|install FreedomBox]] on it.')
    [Paragraph([PlainText('An alternative to downloading these images is to'),\
 Link('InstallingDebianOn/TI/BeagleBone', [PlainText('install Debian')]), \
PlainText('on the BeagleBone and then'), Link('FreedomBox/Hardware/Debian', \
[PlainText('install FreedomBox')]), PlainText('on it.')])]

    >>> parse_wiki("'''Synchronizing contacts'''\\n 1. Click on the hamburger \
menus of CalDAV and CardDAV and select either \\"Refresh ...\\" in case of \
existing accounts or \\"Create ...\\" in case of new accounts (see the second \
screenshot below).\\n 1. Check the checkboxes for the address books and \
calendars you want to synchronize and click on the sync button in the header. \
(see the third screenshot below)")
    [Paragraph([BoldText('Synchronizing contacts')]), List('numbered', \
[ListItem([Paragraph([PlainText('Click on the hamburger menus of CalDAV and \
CardDAV and select either "Refresh ..." in case of existing accounts or \
"Create ..." in case of new accounts (see the second screenshot below).')])]),\
 ListItem([Paragraph([PlainText('Check the checkboxes for the address books \
and calendars you want to synchronize and click on the sync button in the \
header. (see the third screenshot below)')])])])]

    >>> parse_wiki("After Roundcube is installed, it can be accessed at \
{{{https://<your freedombox>/roundcube}}}. Enter your username and password. \
The username for many mail services will be the full email address such as \
''exampleuser@example.org'' and not just the username like ''exampleuser''. \
Enter the address of your email service's IMAP server address in the \
''Server'' field. You can try providing your domain name here such as \
''example.org'' for email address ''exampleuser@example.org'' and if this \
does not work, consult your email provider's documentation for the address of \
the IMAP server. Using encrypted connection to your IMAP server is strongly \
recommended. To do this, prepend 'imaps://' at the beginning of your IMAP \
server address. For example, ''imaps://imap.example.org''.")
    [Paragraph([PlainText('After Roundcube is installed, it can be accessed \
at'), CodeText('https://<your freedombox>/roundcube'), PlainText('. Enter \
your username and password. The username for many mail services will be the \
full email address such as'), ItalicText('exampleuser@example.org'), \
PlainText('and not just the username like'), ItalicText('exampleuser'), \
PlainText(". Enter the address of your email service's IMAP server address in \
the"), ItalicText('Server'), PlainText('field. You can try providing your \
domain name here such as'), ItalicText('example.org'), PlainText('for email \
address'), ItalicText('exampleuser@example.org'), PlainText("and if this does \
not work, consult your email provider's documentation for the address of the \
IMAP server. Using encrypted connection to your IMAP server is strongly \
recommended. To do this, prepend 'imaps://' at the beginning of your IMAP \
server address. For example,"), ItalicText('imaps://imap.example.org'), \
PlainText('.')])]

    >>> parse_wiki('Tor Browser is the recommended way to browse the web \
using Tor. You can download the Tor Browser from \
https://www.torproject.org/projects/torbrowser.html and follow the \
instructions on that site to install and run it.')
    [Paragraph([PlainText('Tor Browser is the recommended way to browse the \
web using Tor. You can download the Tor Browser from '), Url('\
https://www.torproject.org/projects/torbrowser.html'), PlainText('and follow \
the instructions on that site to install and run it.')])]

    >>> parse_wiki('After installation a web page becomes available on \
https://<your-freedombox>/_minidlna.')
    [Paragraph([PlainText('After installation a web page becomes available on \
'), PlainText('https://<your-freedombox>/_minidlna.')])]

    >>> parse_wiki('||<style="text-align: center;"> [[FreedomBox/Hardware/\
A20-OLinuXino-Lime2|{{attachment:a20-olinuxino-lime2_thumb.jpg|A20 OLinuXino \
Lime2|width=235,height=159}}]]<<BR>> [[FreedomBox/Hardware/A20-OLinuXino-Lime2\
|A20 OLinuXino Lime2]] ||<style="text-align: center;"> [[FreedomBox/Hardware/\
A20-OLinuXino-MICRO|{{attachment:a20-olinuxino-micro_thumb.jpg|A20 OLinuXino \
MICRO|width=235,height=132}}]]<<BR>> [[FreedomBox/Hardware/A20-OLinuXino-MICRO\
|A20 OLinuXino MICRO]] ||<style="text-align: center;"> [[FreedomBox/Hardware/\
APU|{{attachment:apu1d_thumb.jpg|PC Engines APU|width=235,height=157}}]]<<BR>>\
 [[FreedomBox/Hardware/APU|PC Engines APU]] ||')
    [Table([TableRow([TableItem([Paragraph([Link('FreedomBox/Hardware/\
A20-OLinuXino-Lime2', [EmbeddedAttachment('a20-olinuxino-lime2_thumb.jpg', [\
PlainText('A20 OLinuXino Lime2')], 'width=235,height=159')])]), Paragraph([\
Link('FreedomBox/Hardware/A20-OLinuXino-Lime2', [PlainText('A20 OLinuXino \
Lime2')])])], 'center'), TableItem([Paragraph([Link('FreedomBox/Hardware/\
A20-OLinuXino-MICRO', [EmbeddedAttachment('a20-olinuxino-micro_thumb.jpg', [\
PlainText('A20 OLinuXino MICRO')], 'width=235,height=132')])]), Paragraph([\
Link('FreedomBox/Hardware/A20-OLinuXino-MICRO', [PlainText('A20 OLinuXino \
MICRO')])])], 'center'), TableItem([Paragraph([Link('FreedomBox/Hardware/\
APU', [EmbeddedAttachment('apu1d_thumb.jpg', [PlainText('PC Engines APU')], \
'width=235,height=157')])]), Paragraph([Link('FreedomBox/Hardware/APU', [\
PlainText('PC Engines APU')])])], 'center')])])]

    >>> parse_wiki(" 1. When created, go to the virtual machine's Settings -> \
[Network] -> [Adapter 1]->[Attached to:] and choose the network type your \
want the machine to use according to the explanation in Network Configuration \
below. The recommended type is the ''Bridged adapter'' option, but be aware \
that this exposes the !FreedomBox's services to your entire local network.")
    [List('numbered', [ListItem([Paragraph([PlainText("When created, go to \
the virtual machine's Settings -> [Network] -> [Adapter 1]->[Attached to:] \
and choose the network type your want the machine to use according to the \
explanation in Network Configuration below. The recommended type is the"), \
ItalicText('Bridged adapter'), PlainText("option, but be aware that this \
exposes the FreedomBox's services to your entire local network.")])])])]

    >>> parse_wiki('After logging in, you can become root with the command \
`sudo su`.\\n \\n=== Build Image ===')
    [Paragraph([PlainText('After logging in, you can become root with the \
command'), MonospaceText('sudo su'), PlainText('.')]), \
Heading(3, 'Build Image')]
    """
    elements = []
    lines = text.split('\n')

    # Skip lines before begin_marker, if given.
    if begin_marker:
        while lines:
            line = lines.pop(0).strip()
            if line.startswith(begin_marker):
                break

    while lines:
        line = lines.pop(0)
        if end_marker and line.strip().startswith(end_marker):
            break  # end parsing

        # Handle macros when file is not included.
        if line.strip().startswith('## BEGIN_INCLUDE'):
            elements.append(BeginInclude())
            continue

        if line.strip().startswith('## END_INCLUDE'):
            elements.append(EndInclude())
            continue

        if line.strip().startswith('##'):
            # Seems to be another type of comment that is not rendered
            # in the docbook.
            continue

        match = re.match(r'<<TableOfContents\((\d*)\)>>', line)
        if match:
            level = match.group(1)
            if level:
                elements.append(TableOfContents(int(level)))
            else:
                elements.append(TableOfContents())
            continue

        match = re.match(r'(=+) (.+) (=+)', line)
        if match:
            level = len(match.group(1))
            content = match.group(2)
            elements.append(Heading(level, content))
            continue

        match = re.match(r'---(-+)', line)
        if match:
            dashes = len(match.group(1)) + 3
            elements.append(HorizontalRule(dashes))
            continue

        if line.strip().startswith('||'):
            rows = []
            style = None
            match = re.match(r'.*<tablestyle=(.*)>.*', line)
            if match:
                style = match.group(1).strip('\'"')

            rows.append(parse_table_row(line, context))
            while lines and lines[0].strip().startswith('||'):
                line = lines.pop(0)
                rows.append(parse_table_row(line, context))

            elements.append(Table(rows, style))
            continue

        match = re.match(r'(\s+)(\*|\.|\d\.|I\.|A\.)\s+(.*)', line)
        if match:
            # Collect lines until end of List is reached.
            list_lines = [line]
            while lines:
                match = re.match(r'(\s+)(\*|\.|\d\.|I\.|A\.)\s+(.*)', lines[0])
                if match:
                    list_lines.append(lines.pop(0))
                    continue
                else:
                    break

            # Parse List info for each line.
            list_data = []
            for line in list_lines:
                match = re.match(r'(\s+)(\*|\.|\d\.|I\.|A\.)\s+(.*)', line)
                indent = len(match.group(1))
                marker = match.group(2)
                if marker == '.':
                    list_type = ListType.PLAIN
                elif '*' in marker:
                    list_type = ListType.BULLETED
                else:
                    list_type = ListType.NUMBERED
                content = line.lstrip(match.group(2) + ' ')
                list_data.append((list_type, indent, content))

            new_list, _ = parse_list(list_data, context)
            elements.append(new_list)
            continue

        match = re.match(r'\/\* (.+) \*\/', line)
        if match:
            content = match.group(1)
            elements.append(Comment(content))
            continue

        if line.strip().startswith('{{{') and '}}}' not in line:
            match = re.match(r'{{{#!wiki\s(.*)', line)
            if match:
                # admonition
                content = []
                paragraph = Paragraph([])
                while lines:
                    line = lines.pop(0)
                    if line == '}}}':
                        break

                    br = '<<BR>>'
                    paragraph.add_content(parse_text(line.rstrip(br), context))
                    if br in line:
                        content.append(paragraph)
                        paragraph = Paragraph([])

                content.append(paragraph)
                style = match.group(1)
                elements.append(Admonition(style, content))
                continue

            else:
                # multi-line preformatted text
                texts = []
                while lines:
                    line = lines.pop(0)
                    if line.strip().startswith('}}}'):
                        break

                    texts.append(line)

                elements.append(CodeText('\n'.join(texts)))
                continue

        match = re.match(r'Category(\w+)', line)
        if match:
            content = match.group(1)
            elements.append(Category(content))
            continue

        match = re.match(r'<<Anchor\((.+)\)>>', line)
        if match:
            content = match.group(1)
            elements.append(Anchor(content))
            continue

        match = re.match(r'<<Include\((.+)\)>>', line)
        if match:
            contents = match.group(1).split(',')
            page = contents.pop(0)
            from_marker = None
            to_marker = None
            for content in contents:
                if content.startswith(' from='):
                    from_marker = content.lstrip(' from="').rstrip('"')
                elif content.startswith(' to='):
                    to_marker = content.lstrip(' to="').rstrip('"')

            elements.append(Include(page, from_marker, to_marker))
            continue

        if line.strip():
            # Nothing else matches, assume its a paragraph of text.
            texts = []
            br = '<<BR>>'
            texts.extend(parse_text(line.rstrip(br), context))
            if br not in line:
                # Collect text until next empty line is reached.
                while lines and lines[0].strip():
                    if end_marker and lines[0].strip().startswith(end_marker):
                        break

                    # start of multi-line CodeText
                    if lines[0].strip().startswith('{{{'):
                        break

                    if re.match(r'\s+(\*|\.|\d\.|I\.|A\.)\s+.*', lines[0]):
                        break

                    line = lines.pop(0)
                    texts.extend(parse_text(line.rstrip(br), context))

            elements.append(Paragraph(texts))

    return elements


def generate_inner_docbook(parsed_wiki, context=None):
    """Generate docbook contents from the wiki parse list.

    >>> generate_inner_docbook([Heading(1, 'heading 1st level')])
    '<section><title>heading 1st level</title></section>'

    >>> generate_inner_docbook([\
Heading(1, 'heading 1st level'), \
Heading(2, 'heading 2nd level'), \
Paragraph([PlainText('plain text')]), \
Heading(3, 'heading 3rd level'), \
Heading(2, 'heading 2nd level'), \
])
    '<section><title>heading 1st level</title>\
<section><title>heading 2nd level</title>\
<para>plain text </para>\
<section><title>heading 3rd level</title>\
</section></section>\
<section><title>heading 2nd level</title>\
</section></section>'

    >>> generate_inner_docbook([Heading(1, 'Date & Time')])
    '<section><title>Date &amp; Time</title></section>'

    >>> generate_inner_docbook([Paragraph([PlainText('plain text')])])
    '<para>plain text </para>'

    >>> generate_inner_docbook([Paragraph([Url('https://freedombox.org')])])
    '<para><ulink url="https://freedombox.org"/> </para>'

    >>> generate_inner_docbook([Paragraph([ItalicText('italic')])])
    '<para><emphasis>italic</emphasis> </para>'

    >>> generate_inner_docbook([Paragraph([BoldText('bold')])])
    '<para><emphasis role="strong">bold</emphasis> </para>'

    >>> generate_inner_docbook([Paragraph([\
PlainText('normal text followed by'), BoldText('bold text')])])
    '<para>normal text followed by \
<emphasis role="strong">bold text</emphasis> </para>'

    >>> generate_inner_docbook([Paragraph([MonospaceText('monospace')])])
    '<para><code>monospace</code> </para>'

    >>> generate_inner_docbook([Paragraph([MonospaceText('Save & Connect')])])
    '<para><code>Save &amp; Connect</code> </para>'

    >>> generate_inner_docbook([CodeText('code')])
    '<screen><![CDATA[code]]></screen>'
    >>> generate_inner_docbook([CodeText('apt source <package_name>')])
    '<screen><![CDATA[apt source <package_name>]]></screen>'

    >>> generate_inner_docbook([Link('https://onionshare.org/', \
[PlainText('Onionshare')])])
    '<ulink url="https://onionshare.org/">Onionshare</ulink>'

    >>> generate_inner_docbook([Link('https://f-droid.org/repository/browse/\
?fdfilter=quassel&fdid=com.iskrembilen.quasseldroid', [PlainText('F-Droid')])])
    '<ulink url="https://f-droid.org/repository/browse/?fdfilter=quassel\
&amp;fdid=com.iskrembilen.quasseldroid">F-Droid</ulink>'

    >>> generate_inner_docbook([Link('FreedomBox/Features', \
[PlainText('Features introduction')])])
    '<ulink url="https://wiki.debian.org/FreedomBox/Features#">\
Features introduction</ulink>'

    >>> generate_inner_docbook([EmbeddedAttachment('cockpit-enable.png')])
    '<inlinemediaobject><imageobject>\
<imagedata fileref="cockpit-enable.png"/></imageobject>\
<textobject><phrase>cockpit-enable.png</phrase></textobject>\
</inlinemediaobject>'
    >>> generate_inner_docbook([EmbeddedAttachment('Backups_Step1_v49.png', \
[PlainText('Backups: Step 1')], 'width=800')])
    '<inlinemediaobject><imageobject>\
<imagedata fileref="Backups_Step1_v49.png" width="800"/></imageobject>\
<textobject><phrase>Backups: Step 1</phrase></textobject>\
</inlinemediaobject>'

    >>> generate_inner_docbook([Table([TableRow([\
TableItem([Paragraph([PlainText('A')])]), \
TableItem([Paragraph([PlainText('B')])])]), \
TableRow([TableItem([Paragraph([PlainText('1')])]), \
TableItem([Paragraph([PlainText('2')])])])])])
    '<informaltable><tgroup cols="2"><tbody>\
<row rowsep="1">\
<entry colsep="1" rowsep="1"><para>A </para></entry>\
<entry colsep="1" rowsep="1"><para>B </para></entry></row>\
<row rowsep="1">\
<entry colsep="1" rowsep="1"><para>1 </para></entry>\
<entry colsep="1" rowsep="1"><para>2 </para></entry></row>\
</tbody></tgroup></informaltable>'

    >>> generate_inner_docbook([List('bulleted', [\
ListItem([Paragraph([PlainText('first item')])]), \
ListItem([Paragraph([PlainText('second item')])])])])
    '<itemizedlist><listitem><para>first item </para></listitem>\
<listitem><para>second item </para></listitem></itemizedlist>'

    >>> generate_inner_docbook([Comment('comment')])
    '<para><remark>comment</remark></para>'

    >>> generate_inner_docbook([Category('CategoryFreedomBox')])
    ''

    >>> generate_inner_docbook([Anchor('gettinghelp')])
    '<anchor id="gettinghelp"/>'

    >>> generate_inner_docbook([HorizontalRule(4)])
    '<!--rule (<hr>) is not applicable to DocBook-->'

    >>> generate_inner_docbook([EndInclude()])
    ''

    >>> generate_inner_docbook([Admonition('caution', \
[Paragraph([PlainText("Don't overuse admonitions")])])])
    "<caution><para>Don't overuse admonitions </para></caution>"

    >>> generate_inner_docbook([TableOfContents()])
    ''

    >>> generate_inner_docbook([Paragraph([\
PlainText('User documentation:')]), \
List('bulleted', [ListItem([Paragraph([PlainText('List of'), \
Link('FreedomBox/Features', [PlainText('applications')]), \
PlainText('offered by FreedomBox.')])])])])
    '<para>User documentation: </para><itemizedlist><listitem><para>List of \
<ulink url="https://wiki.debian.org/FreedomBox/Features#">applications\
</ulink> offered by FreedomBox. </para></listitem></itemizedlist>'

    >>> generate_inner_docbook([List('bulleted', [\
ListItem([Paragraph([PlainText('Within FreedomBox Service (Plinth)')]), \
List('numbered', [ListItem([Paragraph([PlainText('select Apps')])]), \
ListItem([Paragraph([PlainText('go to Radicale (Calendar and Addressbook) \
and')])]), \
ListItem([Paragraph([PlainText('install the application. After the \
installation is complete, make sure the application is marked "enabled" in \
the FreedomBox interface. Enabling the application launches the Radicale \
CalDAV/CardDAV server.')])]), \
ListItem([Paragraph([PlainText('define the access rights:')]), \
List('bulleted', [ListItem([Paragraph([PlainText('Only the owner of a \
calendar/addressbook can view or make changes')])]), \
ListItem([Paragraph([PlainText('Any user can view any calendar/addressbook, \
but only the owner can make changes')])]), \
ListItem([Paragraph([PlainText('Any user can view or make changes to any \
calendar/addressbook')])])])])])])])])
    '<itemizedlist>\
<listitem><para>Within FreedomBox Service (Plinth) </para> \
<orderedlist numeration="arabic">\
<listitem><para>select Apps </para></listitem>\
<listitem><para>go to Radicale (Calendar and Addressbook) and </para>\
</listitem>\
<listitem><para>install the application. After the installation is complete, \
make sure the application is marked "enabled" in the FreedomBox interface. \
Enabling the application launches the Radicale CalDAV/CardDAV server. </para>\
</listitem>\
<listitem><para>define the access rights: </para> \
<itemizedlist>\
<listitem><para>Only the owner of a calendar/addressbook can view or make \
changes </para></listitem>\
<listitem><para>Any user can view any calendar/addressbook, but only the \
owner can make changes </para></listitem>\
<listitem><para>Any user can view or make changes to any calendar/addressbook \
</para></listitem></itemizedlist>\
</listitem></orderedlist>\
</listitem></itemizedlist>'

    >>> generate_inner_docbook([Paragraph([PlainText('An alternative to \
downloading these images is to'), Link('InstallingDebianOn/TI/BeagleBone', \
[PlainText('install Debian')]), PlainText('on the BeagleBone and then'), \
Link('FreedomBox/Hardware/Debian', [PlainText('install FreedomBox')]), \
PlainText('on it.')])])
    '<para>An alternative to downloading these images is to \
<ulink url="https://wiki.debian.org/InstallingDebianOn/TI/BeagleBone#">\
install Debian</ulink> on the BeagleBone and then \
<ulink url="https://wiki.debian.org/FreedomBox/Hardware/Debian#">install \
FreedomBox</ulink> on it. </para>'

    >>> generate_inner_docbook([Paragraph([PlainText('After Roundcube is \
installed, it can be accessed at'), CodeText('https://<your freedombox>\
/roundcube'), PlainText('.')])])
    '<para>After Roundcube is installed, it can be accessed at <code>\
https://&lt;your freedombox&gt;/roundcube</code> . </para>'
    """
    doc_out = ''
    sections = []
    if context is None:
        context = {}

    for element in parsed_wiki:
        if isinstance(element, Heading):
            while sections and element.level <= sections[-1]:
                doc_out += '</section>'
                sections.pop()

            doc_out += '<section>'
            sections.append(element.level)

        doc_out += element.to_docbook(context)

    for section in sections:
        doc_out += '</section>'

    return doc_out


def get_context(file_path):
    """Get dict with page path, name, language, and title."""
    page_name = Path(file_path.stem).stem
    if page_name == 'freedombox-manual':
        name = 'FreedomBox Manual'
    else:
        name = page_name

    language = 'es' if 'es' in file_path.parts else 'en'
    if language == 'es':
        title = f'es/FreedomBox/Manual/{page_name}'
    else:
        title = f'FreedomBox/Manual/{page_name}'

    context = {
        'path': file_path,
        'name': name,
        'language': language,
        'title': title,
    }
    return context


def generate_docbook(parsed_wiki, context=None):
    """Generate a docbook article from the wiki parse list."""
    doc_out = '<?xml version="1.0" encoding="utf-8"?>'
    doc_out += '<!DOCTYPE article PUBLIC "-//OASIS//DTD DocBook XML V4.4//EN" \
"http://www.docbook.org/xml/4.4/docbookx.dtd">'

    if context and 'name' in context:
        doc_out += '<article><articleinfo><title>'
        doc_out += context['name']
        doc_out += '</title></articleinfo>'

    doc_out += generate_inner_docbook(parsed_wiki, context)
    doc_out += '</article>'
    return doc_out


if __name__ == '__main__':
    import argparse
    import doctest

    parser = argparse.ArgumentParser(
        description='Parse MoinMoin wiki files, and convert to Docbook.')
    parser.add_argument('--skip-tests', action='store_true',
                        help='Skip module doctests')
    parser.add_argument('--debug', action='store_true',
                        help='Show parser output')
    parser.add_argument('input', type=Path, nargs='*',
                        help='input file path(s)')
    arguments = parser.parse_args()

    if not arguments.skip_tests:
        # Make tests verbose if no input files given
        verbose = not arguments.input
        doctest.testmod(verbose=verbose)

    for in_file in arguments.input:
        with in_file.open() as wiki_file:
            wiki_text = wiki_file.read()

        context = get_context(in_file)
        parsed_wiki = parse_wiki(wiki_text, context)
        if arguments.debug:
            import pprint
            pprint.pprint(parsed_wiki, indent=4)

        doc_out = generate_docbook(parsed_wiki, context)
        print(doc_out)
