# -*- coding: utf-8 -*-

import tkinter                                  # the main Python GUI library
import re                                       # regular expressions
import urllib.request                           # grabbing URLs
import os                                       # creating files, etc.
import tkinter.filedialog                       # used to choose directories
import threading                                # omg multithreading
import zipfile                                  # apparently epub = zip :D
import shutil                                   # removing pesky directories


# standard xhtml header
HEADER = '<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"\n  "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">\n\n<html xmlns="http://www.w3.org/1999/xhtml">\n<head>\n  <title></title>\n<link href="../stylesheet.css" rel="stylesheet" type="text/css" />\n</head>'

# a css stylesheet for handsomeness
STYLESHEET = '''p{
    text-align: justify;
    text-justify: newspaper;
    text-indent: 0em;
    margin-top: .25em;
    margin-bottom: .25em;
    line-height: 110%;
    font-family: serif;
}

p+p{
    text-indent: 5%;
}

em{
    padding-right: 0.1em;
}'''



class Downloader_Gui(tkinter.Tk):
    """The main GUI which will enable downloading
    and converting the fanfiction."""
    
    def __init__(self, parent):                 # inherit from tkinter.Tk
        tkinter.Tk.__init__(self, parent)
        self.parent = parent
        self.initialize()
        
    def initialize(self):
        pass


# Elsanna we're testing this shit on:
# https://www.fanfiction.net/s/9906088/1/Frozen-Fractals

def ffconvert(url, filepath):
    urlroot = re.search(r"(.*fanfiction\.net/s/[0-9]*)", url) # search for url
    if urlroot:
        urlroot = urlroot.group(1)
    title = re.search(r".*fanfiction\.net/s/[0-9]*/[0-9]*/([^/]*)", url)
    if title:                               # search for title
        title = title.group(1)
    else:
        title = re.search(r".*fanfiction\.net/s/([0-9]*)", url).group(1)

    html_files = []

    ch = 1                                  # the chapter marker in the url
    while checkStory(urlroot + '/' + str(ch)):
        warn.set("Converting chapter %i..." % ch)
        download['state'] = 'disabled'
        chapter = convert(urlroot + '/' + str(ch), filepath, title)
        html_files.append(title +'/'+chapter)
        ch += 1

    stylesheet = open('stylesheet.css','w+')
    stylesheet.write(STYLESHEET)            # write the stylesheet
    stylesheet.close()
    epubConvert(filepath, title, html_files)
    shutil.rmtree(filepath+'/'+title)       # delete all the things
    os.remove('stylesheet.css')
    warn.set("")
    download['state'] = 'normal'


def epubConvert(filepath, title, html_files):
    # I stole this :(
    # http://www.manuel-strehl.de/dev/simple_epub_ebooks_with_python.en.html
    os.chdir(filepath)
    epub = zipfile.ZipFile(title + '.epub', 'w')

    epub.writestr("mimetype", "application/epub+zip")

    epub.writestr("META-INF/container.xml", '''<container version="1.0"
           xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/Content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>''');

    index_tpl = '''<package version="2.0"
  xmlns="http://www.idpf.org/2007/opf">
  <metadata/>
  <manifest>
    %(manifest)s
  </manifest>
  <spine toc="ncx">
    %(spine)s
  </spine>
</package>'''
    
    manifest = ""
    spine = ""

    for i, html in enumerate(html_files):
        basename = os.path.basename(html)
        manifest += '<item id="file_%s" href="%s" media-type="application/xhtml+xml"/>' % (
                  i+1, basename)
        spine += '<itemref idref="file_%s" />' % (i+1)
        epub.write(html, 'OEBPS/'+basename)
    
    epub.write('stylesheet.css', 'stylesheet.css')

    epub.writestr('OEBPS/Content.opf', index_tpl % {
  'manifest': manifest,
  'spine': spine,
})
    # thank you very much kind sir


def convert(url,filepath,title):
    os.chdir(filepath)
    title = ''.join(i for i in title if not i in "/\\?%*:|\"<>")
    if not os.path.exists(title):
        os.makedirs(title)          # make directory for xhtml files
    os.chdir(title)
    source = open('source2.txt','w+')
    text = extract_text(url)
    source.write(text)
    source.close()
    chapter  = re.search(r"\<h2\>([^<]*)\</h2\>",text)
    if chapter:
        chapter = chapter.group(1)
    else:
        chapter = (title + 
            re.search(r".*fanfiction\.net/s/[0-9]*/([0-9]*)", url).group(1))
    chapter = ''.join(i for i in chapter if not i in "/\\?%*:|\"<>")
    chapter = chapter + '.xhtml'
    fixer('source2.txt',chapter)
    os.remove('source2.txt')
    os.chdir('..')
    return chapter


def extract_text(url):
    site = urllib.request.urlopen(url)
    data = site.read()
    source_file = open('source.txt','wb')
    source_file.write(data)
    source_file.close()
    source_code = open('source.txt','r').read()
    chapter  = re.search(r"selected\>([^<]*)",source_code)
    if chapter:
        chapter = chapter.group(1)
    else:
        chapter = ('Chapter' + 
            re.search(r".*fanfiction\.net/s/[0-9]*/([0-9]*)", url).group(1))
    text = re.search(r"id=\'storytext\'\>([\S\s]*\</[pP]\>)\n\</div\>\n\</div\>",source_code)
    if text:
        source_code = text.group(1)
    os.remove('source.txt')
    text = "<body><h2>" + chapter + "</h2>\n\n" + source_code + "</body>"
    return text


def fixer(filename, destination):
    file = open(filename,'r')
    dest = open(destination,'w+')
    text = file.read()
    text = para_inserter(text)
    text = dash_fixer(text)
    text = ellipsis_fixer(text)
    text = italic_punct(text)
    text = dumb_to_smart_quotes(text)
    text = cleanup(text)
    dest.write(HEADER)
    dest.write(text)
    file.close()
    dest.close()


def checkStory(url):
    check = str(urllib.request.urlopen(url).read())
    error = re.search("<!DOCTYPE html>", check)
    if error:
        return True
    return False


def para_inserter(text):
    """Takes a string and inserts two line breaks between HTML paragraph
    markers."""
    text = re.sub('</p>','</p>\n',text)
    text = re.sub('<p>','\n<p>',text)
    return text


def dumb_to_smart_quotes(text):
    """Takes a string and returns it with dumb quotes, single and double,
    replaced by smart quotes. Accounts for the possibility of HTML tags
    within the string."""

    # Replace quotes beginning or ending paragraphs
    text = re.sub('<p>"','<p>&ldquo;',text)
    text = re.sub('"</p>','&rdquo;</p>',text)
    text = re.sub("</p>'","</p>&rsquo;",text)

    # Find dumb quotes at the beginning of sentences
    text = re.sub(r'"([A-Za-z])',r'&ldquo;\1',text)

    # Find dumb quotes with ending emphasis markers in the way
    text = re.sub(r'([a-zA-Z0-9.,?!;:…\-&mdash;\'\"])</em>"', r'\1</em>&rdquo;', text)
    text = re.sub(r"([a-zA-Z0-9.,?!;:…\-&mdash;\"\'])</em>'", r'\1</em>&rsquo;', text)
    text = re.sub(r'([a-zA-Z0-9.,?!;:…\-&mdash;\'\"])</em>&#8239;"', r'\1</em>&rdquo;', text)
    text = re.sub(r"([a-zA-Z0-9.,?!;:…\-&mdash;\"\'])</em>&#8239;'", r'\1</em>&rsquo;', text)

    # Find dumb double quotes coming directly after letters or punctuation,
    # and replace them with right double quotes.
    text = re.sub(r'([a-zA-Z0-9.,?!;:…\-&mdash;\'\"])"', r'\1&rdquo;', text)
    # Find any remaining dumb double quotes and replace them with
    # left double quotes.
    text = text.replace('"', '&ldquo;')
    # Reverse: Find any SMART quotes that have been (mistakenly) placed around
    # HTML attributes (following =) and replace them with dumb quotes.
    text = re.sub(r'=&ldquo;(.*?)&rdquo;', r'="\1"', text)
    # Follow the same process with dumb/smart single quotes
    text = re.sub(r"([a-zA-Z0-9.,?!;:…\-&mdash;\"\'])'", r'\1&rsquo;', text)
    text = text.replace("'", '&lsquo;')
    text = re.sub(r'=&lsquo;(.*?)&rsquo;', r"='\1'", text)

    # Fixing up any lingering mistakes
    text = re.sub('&rsquo; &rdquo;', '&rsquo;&rdquo;',text)
    text = re.sub('&ldquo; &lsquo;', '&ldquo;&lsquo;',text)

    right, left = 0, 0
    for item in text:
        if item == '&ldquo;': left+=1
        if item == '&rdquo;': right+=1
    if right != left:
        #print("Something may be wrong with the smart quotes.")
        #print("Left and right are not symmetrical.")
        #print("Left =",left)
        #print("Right =",right)
        pass
    return text
    

def dash_fixer(text):
    """Replaces dumb dashes (--) with real dashes (&mdash;)."""
    text = re.sub('--','&mdash;',text)
    text = re.sub(' &mdash;','&mdash;',text)
    text = re.sub('&mdash; ','&mdash;',text)
    text = re.sub(' - ','&mdash;',text)
    text = re.sub('- ','&mdash;',text)
    text = re.sub(' – ','&mdash;',text)
    text = re.sub('-&rdquo;','&mdash;&rdquo;',text)
    text = re.sub('&ldquo;-','&ldquo;&mdash;',text)
    text = re.sub('-"','&mdash;"',text)
    text = re.sub('"-','"&mdash;',text)
    text = re.sub('<p>-','<p>&mdash;',text)
    text = re.sub('-</p>','&mdash;</p>',text)
    text = re.sub(r'([^A-Za-z0-9])\-([^A-Za-z0-9])',r'\1&mdash;\2',text)
    return text


def italic_punct(text):
    """Fixes terminating punctuation with italics"""
    text = re.sub(r'</em>\?','?</em>',text)
    text = re.sub('</em>!','!</em>',text)
    text = re.sub('"</em>','</em>"',text)
    text = re.sub('<em>"','"<em>',text)
    text = re.sub("'</em>","</em>'",text)
    text = re.sub("<em>'","'<em>",text)
    return text
    

    # LET THE REGEX BEGIN
def ellipsis_fixer(text):
    """Replaces dumb ellipses(...) and unicode ellipses (…) with smart ellipses(.&#8239;.&#8239;.)"""
    text = re.sub('…','.&#8239;.&#8239;.',text)
    text = re.sub(r'\.\.\.','.&#8239;.&#8239;.',text)
    text = re.sub(r'\. \. \.','.&#8239;.&#8239;.',text)
    text = re.sub(r'\.&nbsp;\.&nbsp;\.','.&#8239;.&#8239;.',text)
    text = re.sub(r'\.&#8239;\.&#8239;\.!','.&#8239;.&#8239;.&#8239;!',text)
    text = re.sub(r'\.&#8239;\.&#8239;\. !','.&#8239;.&#8239;.&#8239;!',text)
    text = re.sub(r' \.&#8239;\.&#8239;\.&#8239;!','.&#8239;.&#8239;.&#8239;!',text)
    #text = re.sub(r'\.&#8239;\.&#8239;\.&#8239;!','&#8239;.&#8239;.&#8239;.&#8239;!',text)
    text = re.sub(r'\.&#8239;\.&#8239;\.\?','.&#8239;.&#8239;.&#8239;?',text)
    text = re.sub(r'\.&#8239;\.&#8239;\. \?','.&#8239;.&#8239;.&#8239;?',text)
    text = re.sub(r' \.&#8239;\.&#8239;\.&#8239;\?','.&#8239;.&#8239;.&#8239;?',text)
    #text = re.sub(r'\.&#8239;\.&#8239;\.&#8239;\?','&#8239;.&#8239;.&#8239;.&#8239;?',text)
    text = re.sub(r'\.&#8239;\.&#8239;\."</p>','.&#8239;.&#8239;.&#8239;.&rdquo;</p>',text)
    text = re.sub(r'\.&#8239;\.&#8239;\. "</p>','.&#8239;.&#8239;.&#8239;.&rdquo;</p>',text)
    text = re.sub(r'\.&#8239;\.&#8239;\.</p>','.&#8239;.&#8239;.&#8239;.</p>',text)
    text = re.sub(r'\.&#8239;\.&#8239;\. </p>','.&#8239;.&#8239;.&#8239;.</p>',text)
    text = re.sub(r'\.&#8239;\.&#8239;\. "','.&#8239;.&#8239;.&#8239;. &ldquo;',text)
    text = re.sub(r'\.&#8239;\.&#8239;\.</em>"</p>','.&#8239;.&#8239;.&#8239;.</em> &rdquo;</p>',text)
    text = re.sub(r'\.&#8239;\.&#8239;\.</em> "</p>','.&#8239;.&#8239;.&#8239;.</em>&rdquo;</p>',text)
    text = re.sub(r'\.&#8239;\.&#8239;\.</em></p>','.&#8239;.&#8239;.&#8239;.</em></p>',text)
    text = re.sub(r'\.&#8239;\.&#8239;\.</em> </p>','.&#8239;.&#8239;.&#8239;.</em></p>',text)
    text = re.sub(r'\.&#8239;\.&#8239;\." ([a-z])',r'.&#8239;.&#8239;.&#8239;,&rdquo; \1',text)
    text = re.sub(r'\.&#8239;\.&#8239;\."','.&#8239;.&#8239;.&#8239;.&rdquo;',text)
    text = re.sub(r'"\.&#8239;\.&#8239;\.','&ldquo;.&#8239;.&#8239;.&nbsp;',text)
    text = re.sub(r'<p>\.&#8239;\.&#8239;\.','<p>.&#8239;.&#8239;.&nbsp;',text)
    text = re.sub(r'<p><em>\.&#8239;\.&#8239;\.','<p><em>.&#8239;.&#8239;.&nbsp;',text)
    text = re.sub(r"&lsquo;\.&#8239;\.&#8239;\.","&lsquo;.&#8239;.&#8239;.&nbsp;",text)
    text = re.sub(r"\.&#8239;\.&#8239;\.' ([a-z])",".&#8239;.&#8239;.&#8239;,' \1",text)
    text = re.sub(r"([A-Za-z,])\.&#8239;\.&#8239;\.([a-z])",r"\1 .&#8239;.&#8239;. \2",text)
    text = re.sub(r"([A-Za-z,])\.&#8239;\.&#8239;\. ([a-z])",r"\1 .&#8239;.&#8239;. \2",text)
    text = re.sub(r"([A-Za-z,])\.&#8239;\.&#8239;\.<em>([a-z])",r"\1 .&#8239;.&#8239;. <em>\2",text)
    text = re.sub(r"([A-Za-z,])\.&#8239;\.&#8239;\. <em>([a-z])",r"\1 .&#8239;.&#8239;. <em>\2",text)
    text = re.sub(r"([A-Za-z])\.&#8239;\.&#8239;\.([A-Z])",r"\1.&#8239;.&#8239;.&#8239;. \2",text)
    text = re.sub(r"([A-Za-z])\.&#8239;\.&#8239;\. ([A-Z])",r"\1.&#8239;.&#8239;.&#8239;. \2",text)
    text = re.sub(r"\.&#8239;\.&#8239;\.&#8239;\.&#8239;,&rdquo;</p>",".&#8239;.&#8239;.&#8239;.&rdquo;</p>",text)
    text = re.sub(r"\.&#8239;\.&#8239;\.&nbsp;&#8239;\.",".&#8239;.&#8239;.",text)
    text = re.sub(r"\.&#8239;\.&#8239;\.&nbsp;\.",".&#8239;.&#8239;.",text)
    while re.search('&#8239;&#8239;',text):
        text = re.sub('&#8239;&#8239;','&#8239;',text)
    while re.search('\.&#8239;\.&#8239;\.&#8239;\.&#8239;\.',text):
        text = re.sub(r'\.&#8239;\.&#8239;\.&#8239;\.&#8239;\.','.&#8239;.&#8239;.&#8239;.',text)
    return text

    
def cleanup(text):
    """Fixes minor errors."""
    text = re.sub('&ldquo; <nobr>...</nobr>','&ldquo;<nobr>...</nobr>',text)
    text = re.sub('-&rdquo;','&mdash;&rdquo;',text)
    text = re.sub(r'&mdash;&rdquo;([a-z])',r'&mdash;&ldquo;\1',text)
    text = re.sub(' &mdash;&rdquo;','&mdash;&rdquo;',text)
    text = re.sub(' &mdash;</p>','&mdash;</p>',text)
    text = re.sub(' &mdash;</em>','&mdash;</em>',text)
    text = re.sub('&ldquo;&mdash; ','&ldquo;&mdash;',text)
    text = re.sub('<p>&mdash; ','<p>&mdash;',text)
    text = re.sub(' &mdash; ','&mdash;',text)
    text = re.sub('&mdash; <em>','&mdash;<em>',text)
    text = re.sub('</em> &mdash;','</em>&mdash;',text)
    text = re.sub("</em>&rdquo;","</em>&rdquo;",text)
    text = re.sub("</em>&rsquo;","</em>&rsquo;",text)
    text = re.sub(r'<h2>([0-9]*)\. ([^<]*)</h2>',r'<h2 style="text-align:center">Chapter \1:<br />\n\2</h2>',text)
    text = re.sub(r'<h2 style="text-align:center">Chapter [0-9]*:<br />\nChapter ([0-9]*)</h2>',r'<h2 style="text-align:center">Chapter \1</h2>',text)

    return text



def get_directory():
    filepath.set(tkinter.filedialog.askdirectory(parent = app,
        title = "Choose directory"))


def callback(url, filepath):
    warn.set("")
    filepath = os.path.expanduser(filepath)
    if (os.path.exists(filepath) and 
        re.search(r"(.*fanfiction\.net/s/[0-9]*)", url)):
        threading.Thread(target=ffconvert, args=(url, filepath)).start()
    else:
        warn.set("Invalid URL or directory.")


        
if __name__ == "__main__":
    app = Downloader_Gui(None)
    app.title('Fanfiction.net E-booker')
    app.geometry("500x300")

    instructions = tkinter.Label(app, text = "Please enter URL:")

    entry = tkinter.Entry(app, width = 40)

    filepath = tkinter.StringVar()

    download = tkinter.Button(app, text = "Download",
        command = lambda: callback(entry.get(), str(directory.get())))

    fileinstruc = tkinter.Label(app, text = "Save to:")

    directory = tkinter.Entry(app, width = 40, state = tkinter.DISABLED,
        textvariable = filepath)

    browse = tkinter.Button(app, text = "Browse", 
        command = get_directory)

    warn = tkinter.StringVar()
    warning = tkinter.Label(app, textvariable = warn)


    instructions.pack()
    entry.pack()
    download.pack(side = tkinter.BOTTOM)       # puts the bottom on the bottom
    warning.pack(side = tkinter.BOTTOM)
    fileinstruc.pack(side = tkinter.LEFT)
    directory.pack(side = tkinter.LEFT)
    browse.pack(side = tkinter.RIGHT)

    entry.focus_set()

    app.mainloop()