import json
import os.path
import random
import string
from lxml import etree

def buildURL(resource_path, host="httpbin.org", protocol="https", 
             extension=None, port=None):
    if resource_path[0] != '/':
        resource_path = '/' + resource_path
    
    if extension != None:
        resource_path += "." + extension
        
    if port != None:
        host = host + ":{}".format(port)
    
    url_template = "{}://{}{}"
    url = url_template.format(protocol, host, resource_path)
    return url

def read_creds(key, folder=".", file="creds.json"):
    path = os.path.join(folder, file)
    assert os.path.isfile(path)
    with open(path, "rt") as f:
        creds = json.load(f)
    assert key in creds
    return creds[key]

def update_creds(key, keycreds, folder=".", file="creds.json"):
    path = os.path.join(folder, file)
    assert os.path.isfile(path)
    with open(path, "rt") as f:
        creds = json.load(f)
    assert key in creds
    creds[key] = keycreds
    creds_string = json.dumps(creds, indent=2)
    with open(path, "wt") as f:
        f.write(creds_string)
        f.flush()

def getLocalXML(filename, datadir=".", parser=None):
    path =os.path.join(datadir, filename)
    if not os.path.isfile(path):
        return None
    
    try:
        if parser == None:
            parser = etree.XMLParser(remove_blank_text=True)
        tree = etree.parse(path, parser=parser)
    except Exception as e:
        return None
    
    return tree.getroot()

def processLine(line, width, truncate=False, 
                wrap=False, wrap_space=False, suffix="", prefix=""):
    assert line.count('\n') == 0
    if width == None or len(line) <= width:
        return [line]
    if not truncate and not wrap:
        return [line]
    assert not (truncate and wrap)
    if truncate:
        endindex = width - len(suffix)
        linepart = line[:endindex]
        line_prime = linepart + suffix
        return [line_prime]
    assert wrap
    indent = 0
    while line[indent] == ' ':
        indent += 1
    line2 = line[indent:]
    width2 = width - indent
    lines = []
    while len(line2):
        endindex = min(width2, len(line2))
        if wrap_space and len(line2) > endindex:
            line3 = line2[:width2]
            line4 = line3[::-1]
            spaceindex = line4.index(' ')
            if spaceindex > 0:
                endindex = width2 - 1 - line4.index(' ')
        lines.append(' '*indent + line2[:endindex])
        if len(line2[endindex:]) > 0:
            line2 = prefix + line2[endindex:]
        else:
            line2 = ""
    return lines
    
    
def print_text(s, nlines=None, width=80, truncate=False, 
               wrap=False, wrap_space = False, suffix="...", prefix="_ ",
               json_string=False):
    """
    Print a text string, limiting width and number of lines.
    
    Arguments:
    
    s: input string
    nlines: limit on number of lines of s to be processed
    width: limit on number of characters in a line
    trancate: boolean--whether to truncate lines > width 
    wrap: boolean--whether to wrap lines > width
    wrap_space: look for space for breaking wrapped lines
    suffix: character string to suffix long lines if truncate
    prefix: character string to prefix wrapped lines if wrap
    """
    if json_string:
        data = json.loads(s)
        s = json.dumps(data, indent=2)

    lines = s.split('\n')
    if lines[-1] == "":
        del lines[-1]
    linecount = 0
    if nlines == None:
        nlines = len(lines)
    else:
        nlines = min(nlines, len(lines))
    while linecount < nlines:
        linesout = processLine(lines[linecount], width,
                               truncate, wrap, wrap_space,
                               suffix, prefix)
        for subline in linesout:
            print(subline)
        linecount += 1
        
def print_data(data, nlines=None, width=60, truncate=True, 
               wrap=False, wrap_space = False, suffix="...", 
               prefix="_ ", depth=None, nchild=None):
    if depth!= None or nchild!=None:
        if depth==None:
            depth=100
        if nchild==None:
            nchild=depth
        s = traverse_json(data, level=0, maxlevel=depth, maxchildren=nchild)
        print_text(s, nlines, width, truncate, wrap, wrap_space, suffix, prefix)
        return
    json_string = json.dumps(data, indent=2)
    print_text(json_string, nlines, width, truncate, wrap, wrap_space, suffix, prefix)

def print_headers(data, nlines=None, width=60, truncate=True, 
               wrap=False, wrap_space = False, suffix="...", prefix="_ "):
    """
    Wrapper function over print_data, needed to convert from CaseInsensitiveDict
    of headers into a normal dictionary, as needed for JSON serializability.
    """
    data2 = {}
    for k, v in data.items():
        data2[k] = v
    print_data(data2, nlines, width, truncate, 
               wrap, wrap_space, suffix, prefix)

def print_xml(node, nlines=None, width=59, truncate=True, 
               wrap=False, wrap_space=True, suffix="", prefix="", depth=None, nchild=None):
    if depth!= None or nchild!=None:
        if depth==None:
            depth=100
        if nchild==None:
            nchild=depth
        s = traverse_levels(node, level=0, maxlevel=depth, maxchildren=nchild)
        print_text(s, nlines, width, truncate, wrap, wrap_space, suffix, prefix)
        return
    
    encoding = 'utf-8'
    snode = etree.tostring(node, pretty_print=True)
    if isinstance(snode, bytes):
        snode = snode.decode(encoding)
        
    myparser = etree.XMLParser(remove_blank_text=True)

    node2 = etree.fromstring(snode, parser=myparser)
    snode2 = etree.tostring(node2, pretty_print=True)
    if isinstance(snode2, bytes):
        snode2 = snode2.decode(encoding)
    print_text(snode2, nlines, width, truncate, wrap, wrap_space, suffix, prefix)
    
def json_head(json_ds, numlines=5):
    json_string = json.dumps(json_ds, indent=2)
    i = 0
    linecount = 0
    while i < len(json_string) and linecount < numlines:
        try:
            i = json_string.index('\n', i+1)
        except:
            i = len(json_string)
        linecount += 1
    #print(i, len(json_string))
    print(json_string[:i])
    
def random_string(length=8):
    # using random.choices() 
    # generating random strings  
    res = ''.join(random.choices(string.ascii_uppercase +
                                 string.digits, k = length))
    return res

def attr_string(node):
    if node.tag == 'span' or node.tag == 'sup':
        return ' ...'
    s = ''
    for k, v in node.attrib.items():
        nextval = " {}='{}'".format(k, v)
        s += nextval
    return s

def print_leaf_node(node, level):
    indent = level*'  '
    tag_string = "<{}{}>".format(node.tag, attr_string(node))
    nodetext = str(node.text).strip()
    if node.text != None and nodetext != '':
        tag_string += nodetext + ''
    end_tag = "</{}>".format(node.tag)
    print(indent, tag_string, end_tag, sep='')

def traverse_leaf_node(node, level):
    indent = level*'  '
    tag_string = "<{}{}>".format(node.tag, attr_string(node))
    nodetext = str(node.text).strip()
    if node.text != None and nodetext != '':
        tag_string += nodetext + ''
    end_tag = "</{}>".format(node.tag)
    return indent + tag_string + end_tag + '\n'

def traverse_start_tag(node, level):
    indent = level*'  '
    tag_string = "<{}{}>".format(node.tag, attr_string(node))
    nodetext = str(node.text).strip()
    if node.text != None and nodetext != '':
        tag_string += nodetext + ''
    return indent + tag_string + '\n'
    
def print_start_tag(node, level):
    indent = level*'  '
    tag_string = "<{}{}>".format(node.tag, attr_string(node))
    nodetext = str(node.text).strip()
    if node.text != None and nodetext != '':
        tag_string += nodetext + ''
    print(indent, tag_string, sep='')

def print_end_tag(node, level):
    indent = level*'  '
    tag_string = "</{}>".format(node.tag)
    print(indent, tag_string, sep='')

def traverse_end_tag(node, level):
    indent = level*'  '
    tag_string = "</{}>".format(node.tag)
    return indent + tag_string + '\n'

def traverse_levels(node, level, maxlevel, maxchildren=30):
    if len(node) == 0:
        s = traverse_leaf_node(node, level)
        return s
    else:
        s1 = traverse_start_tag(node, level)
        s2 = ""
        if len(node) > 0 and level < maxlevel:
            for i, child in enumerate(node):
                if i < maxchildren:
                    s2 += traverse_levels(child, level+1, maxlevel, maxchildren)
                else:
                    s2 += (level+1)*'  ' + ' ...\n'
                    break
        s3 = traverse_end_tag(node, level)
        return s1 + s2 + s3

def print_levels(node, level, maxlevel, maxchildren=30):
    if len(node) == 0:
        print_leaf_node(node, level)
    else:
        print_start_tag(node, level)
        if len(node) > 0 and level < maxlevel:
            for i, child in enumerate(node):
                if i < maxchildren:
                    print_levels(child, level+1, maxlevel, maxchildren)
                else:
                    print((level+1)*'  ', '...')
                    break
        print_end_tag(node, level)
        
def print_tree(node, pretty_print=True, encoding='utf-8', limit=0):
    result = etree.tostring(node, pretty_print=pretty_print)
    if isinstance(result, bytes):
        result = result.decode(encoding)
    if limit > 0:
        print(result[:limit])
    else:
        print(result)

def print_results(nodeset, maxlevel=2, maxchildren=5):
    """
    This function iterates over all Elements in a given list
    of Elements, printing the tag, text, and attributes of each.
    
    Parameters:
    nodeset - a list of Elements
    """
    print("Length of nodeset result:", len(nodeset))
    for element in nodeset:
        print("Type:", type(element))
        if type(element) == etree._Element:
            print_levels(element, 0, maxlevel, maxchildren)
        else:
            print(element)
        print()

haschildren = lambda node: isinstance(node, list) or isinstance(node, dict)

def print_scalar(v):
    if isinstance(v, str):
        print('"' + v + '"', sep='',end="")
        return
    if isinstance(v, int) or isinstance(v, float):
        print(v, sep='',end="")
        return
    
def traverse_scalar(v):
    if isinstance(v, str):
        return '"' + v + '"'
    if isinstance(v, int) or isinstance(v, float):
        return str(v)
    else:
        return "??"
    
def text_head(s, nlines=10, json_string=False):
    if json_string:
        data = json.loads(s)
        s = json.dumps(data, indent=2)

    lines = s.split('\n')
    if nlines == None:
        nlines = len(lines)
    outlines = 0
    while outlines < len(lines) and outlines < nlines:
        print(lines[outlines].rstrip())
        outlines += 1


def print_json(node, level, maxlevel=5, maxchildren=5):
    if isinstance(node, str):
        print(level*'  ','"' + node + '"', sep='')
        return
    if isinstance(node, int) or isinstance(node, float):
        print(level*'  ',node, sep='')
        return
    
    assert isinstance(node, list) or isinstance(node, dict)
    
    if isinstance(node, list):
        print(level*'  ', '[')
        if level < maxlevel:
            for i, item in enumerate(node):
                if i < maxchildren:
                    print_json(item, level+1, maxlevel, maxchildren)
                else:
                    print((level+1)*'  ', '...')
                    break
        print(level*'  ', ']')
        return
    if isinstance(node, dict):
        print(level*'  ', '{')
        if level <= maxlevel:
            i = 0
            for k,v in node.items():
                if i < maxchildren:
                    print((level+1)*'  ','"',k,'": ',sep="",end="")
                    if haschildren(v):
                        print()
                        print_json(v, level+1, maxlevel, maxchildren)
                    else:
                        print_scalar(v)
                        print()
                    i += 1
                else:
                    print((level+1)*'  ', '...')
                    break
        else:
            print((level+1)*'  ', '...')
        print(level*'  ', '}')
        return

def traverse_json(node, level, maxlevel=5, maxchildren=5):
    if isinstance(node, str):
        return level*'  ' + '"' + node + '"' + '\n'
        
    if isinstance(node, int) or isinstance(node, float):
        return level*'  ' + str(node) + '\n'
    
    assert isinstance(node, list) or isinstance(node, dict)
    
    if isinstance(node, list):
        s1 = level*'  ' + '[' + '\n'
        s2 = ""
        if level < maxlevel:
            for i, item in enumerate(node):
                if i < maxchildren:
                    s2 += traverse_json(item, level+1, maxlevel, maxchildren)
                else:
                    s2 += (level+1)*'  ' + '...' + '\n'
                    break
        s3 = level*'  ' + ']' + '\n'
        return s1 + s2 + s3
    if isinstance(node, dict):
        s1 = level*'  ' + '{' + '\n'
        s2 = ""
        if level <= maxlevel:
            i = 0
            for k,v in node.items():
                if i < maxchildren:
                    s2 += (level+1)*'  ' + '"' + str(k) + '": '
                    if haschildren(v):
                        s2 += '\n'
                        s2 += traverse_json(v, level+1, maxlevel, maxchildren)
                    else:
                        s2 += traverse_scalar(v)
                        s2 += '\n'
                    i += 1
                else:
                    s2 += (level+1)*'  ' + '...' + '\n'
                    break
        else:
            s2 += (level+1)*'  ' + '...' + '\n'
        s3 = level*'  ' + '}' + '\n'
        return s1 + s2 + s3
