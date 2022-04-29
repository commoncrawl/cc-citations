#!/usr/bin/python3

"""Extract citations from Google Scholar alter e-mails (in EML format)"""

import datetime
import email
import email.parser
import json
import os
import re
import urllib
import sys

from html.parser import HTMLParser


class Citation:
    boilerplate_lines = {
        'cancel alert',
        'update alert to receive fewer, more relevant',
        'update alert to receive only top results',
        'showing top results above and other results below.',
        'skip to content …',
        'saved to',
        'your library',
        'this google scholar alert is brought to you by google.',
        'this alert is sent by google scholar. google scholar is a service by google.',
        "this message was sent by google scholar because you're following new results for",
        "this message was sent by google scholar because you're following new results for [commoncrawl].",
        'showing less relevant results because there are no great results',
        'showing most relevant results above and less relevant results below'
    }

    def __init__(self, date, refs):
        self.date = set([date])
        self.title = ''
        self.authors = dict()
        self.snippet = ''
        self.url = set()
        self.link = set()
        self.idx = ''
        self.ref = set(refs)
        self.data = '' # temporary data
        self.end_of_input = False

    @staticmethod
    def clean_title(st):
        if st[0] == '[':
            st = st[st.find(']')+1:]
        return re.sub(r'\s+', ' ', st.replace('\\xe2\\x80\\x8f', '')).strip()

    def add_title(self, data):
        title = Citation.clean_title(data)
        if title.lower() in Citation.boilerplate_lines:
            return
        if title and self.title:
            self.title += ' '
        self.title += title
        self.idx = self.title.lower()

    def add_link(self, link):
        """Add a Google Scholar link"""
        self.link.add(link)
        u = urllib.parse.urlparse(link)
        if u.query:
            q = urllib.parse.parse_qs(u.query)
            if 'url' in q:
                self.url.add(q['url'][0])

    def add_line_break(self):
        self.data += '\n'
        if self.snippet and not self.snippet[-1] == '\n':
            self.snippet += ' '

    def add_data(self, data):
        self.data += data + "\n"
        lines = data.split('\n')
        if len(lines) > 0:
            snippet = []
            for line in lines:
                line = re.sub(r'\s+', ' ', line)
                line_normalized = line.lower()
                if not line:
                    continue
                if line_normalized in Citation.boilerplate_lines:
                    continue
                if not self.authors:
                    # authors are in the first line
                    self.authors[line_normalized] = line
                    continue
                snippet.append(line)
            if snippet:
                self.snippet += ' '.join(snippet)

    def update(self, other):
        self.authors.update(other.authors)
        self.date.update(other.date)
        self.ref.update(other.ref)
        self.link.update(other.link)
        self.url.update(other.url)

    def __eq__(self, other):
        return self.idx == other.idx

    def __hash__(self):
        return hash(self.idx)

    def __str__(self):
        return '\n'.join([self.title, self.get_year(), self.authors])

    def __repr__(self):
        return self.title

    def get_year(self):
        return sorted(self.date)[0][0:4]

    def to_dict(self):
        d = {}
        if self.date:
            d['year'] = self.get_year()
        if self.idx:
            d['idx'] = self.idx
        if self.title:
            d['title'] = self.title
        if self.authors:
            d['authors'] = sorted(self.authors.values())
        if self.snippet:
            # normalize white space and try to remove hyphenations
            snippet = re.sub(r'\s+', ' ', self.snippet.strip())
            snippet = re.sub(r'(?<=\w{3})- (?=\w{3})', '', snippet)
            d['snippet'] = snippet
        if self.url:
            d['url'] = sorted(self.url)
        if self.link:
            d['link'] = sorted(self.link)
        if self.ref:
            d['ref'] = sorted(self.ref)
        if self.date:
            d['date'] = sorted(self.date)
        if self.data:
            d['data'] = self.data
        return d

    def json(self):
        return json.dumps(self.to_dict())


class CitationsHTMLParser(HTMLParser):
    def __init__ (self, date, author_ref, msg_ref):
        HTMLParser.__init__(self)
        self.in_title = False
        self.in_script = False
        self.end_of_citations = False
        self.citations = []
        self.date = date
        self.ref = [msg_ref, author_ref]

    def handle_starttag(self, tag, attrs):
        if tag == 'h3':
            # <h3> marks the title of the paper, book, etc.
            self.citations.append(Citation(self.date, self.ref))
            self.in_title = True
        elif tag == 'script':
            self.in_script = True
        elif tag == 'b':
            self.inline = True
        elif tag == 'a' and self.in_title:
            # <a href="..."> - link to Google Scholar record
            for attr in attrs:
                if attr[0].lower() == 'href':
                    self.citations[-1].add_link(attr[1])
        elif tag == 'br' or tag == '<p>':
            if self.citations:
                self.citations[-1].add_line_break()
        else:
            pass # sys.stderr.write('Unhandled tag: %s\n' % tag)

    def handle_endtag(self, tag):
        if tag == 'h3':
            self.in_title = False
        elif tag == 'script':
            self.in_script = False
        elif tag == 'b':
            self.inline = False

    def handle_data(self, data):
        data_normalized = re.sub(r'\s+', ' ', data.lower())
        if not self.citations:
            return
        if self.end_of_citations:
            return
        if self.in_title:
            self.citations[-1].add_title(data)
        elif self.in_script:
            pass
        elif data_normalized.startswith("this message was sent by google scholar because you're following new results for"):
            self.end_of_citations = True            
        else:
            self.citations[-1].add_data(data)


def message_get_payload(msg):
    if msg.get_content_type() == 'text/html':
        payload = msg.get_payload(decode=True)
    elif msg.get_content_type() == 'text/x-amp-html':
        payload = msg.get_payload(decode=True)
    else:
        payload = msg.get_payload()
    if isinstance(payload, str):
        yield (msg.get_content_type(), payload)
    elif isinstance(payload, list):
        for sub in payload:
            for pld in message_get_payload(sub):
                yield pld
    elif isinstance(payload, bytes):
        yield (msg.get_content_type(), payload.decode('utf-8'))
    else:
        yield (msg.get_content_type(), payload)


def parse_eml(eml_file):
    date = os.path.basename(eml_file).split('-')[0]
    with open(eml_file, 'rb') as eml:
        msg = email.message_from_binary_file(eml)
        for (mime, body) in list(message_get_payload(msg)):
            parser = CitationsHTMLParser(date, msg['subject'], eml_file)
            parser.feed(body)
            for citation in parser.citations:
                yield citation



if __name__ == '__main__':

    if len(sys.argv) <= 1:
        sys.stderr.write(sys.argv[0] + ' <eml_folder>')
        sys.exit(1)

    emls = os.listdir(sys.argv[1])
    sys.stderr.write('Found %d messages\n' % len(emls))

    citations = dict()

    for eml in emls:
        for citation in parse_eml(os.path.join(sys.argv[1], eml)):
            if citation in citations:
                citations[citation].update(citation)
            else:
                citations[citation] = citation

    sys.stderr.write('Found %d citations\n' % len(citations))

    for citation in citations:
        print(citation.json())
