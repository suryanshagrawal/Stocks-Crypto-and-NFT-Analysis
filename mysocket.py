import socket
import re

class _Proxy:
    proxyhost = "127.0.0.1"
    proxyport = 9999

    def __init__(self, host, port):
        self.host = host
        self.port = port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        retval = sock.connect_ex((_Proxy.proxyhost, _Proxy.proxyport))
        if retval == 0:
            self.socket = sock
        else:
            self.socket = None

    def close(self):
        self.socket.close()


def makeConnection(location, port=80, proxy=False):
    """ Description: Establish a TCP connection from the client machine and
        process running this function to a presumed server listening at the
        given port (80 by default) and located at Internet endpoint given by
        location.

        Returns an established socket connection, if successful, and None on
        failure.
    """
    if proxy:
        proxy_object = _Proxy(location, port)
        return proxy_object


    endsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    retval = endsocket.connect_ex((location, port))
    if retval == 0:
        return endsocket
    print("Error connecting to", str((location, port)))
    return None

def sendCRLF(connection):
    CRLF = '\r\n'
    sendString(connection, CRLF)

def sendString(connection, text, encoding="utf-8"):
    if isinstance(connection, _Proxy):
        conn = connection.socket
    else:
        conn = connection
    conn.sendall(text.encode(encoding))

def sendCRLFLines(connection, text, encoding="utf-8"):
    """ Description: given an established socket connection, take text, a string,
        and send it over the connection.  Before transmission over the network,
        a simple translation is done so that any LF characters in the string
        that do not have a preceeding CR are translated into CRLF, as expected
        by HTTP.  If text does not end in a LF or CRLF, one is appended.

        No return.
    """
    if isinstance(connection, _Proxy):
        conn = connection.socket
    else:
        conn = connection

    LF = '\n'
    CR = '\r'
    CRLF = '\r\n'

    offset = 0
    while offset < len(text):
        indexLF = text.find(LF, offset)
        if indexLF == -1:
            s = text[offset:]
            #print("Case 0: |{}| + CRLF".format(s))
            offset = len(text)
        elif indexLF == 0:          # starts with LF, no preceeding CR => CRLF
            s = ""
            #print("Case 1: || + CRLF")
            offset += 1
        elif text[indexLF - 1] == CR:
            s = text[offset:indexLF-1]
            #print("Case 2: |{}| + CRLF".format(s))
            offset = indexLF + 1
        else:
            s = text[offset:indexLF]
            #print("Case 3: |{}| + CRLF".format(s))
            offset = indexLF + 1

        s_crlf = s + CRLF
        conn.sendall(s_crlf.encode("utf-8"))


def receiveByLine(connection, eol=False):
    line = ""
    abyte = connection.recv(1)
    achar = abyte.decode("utf-8")
    #print(achar)
    while achar != '\n':
        line += achar
        abyte = connection.recv(1)
        achar = abyte.decode("utf-8")
        #print(achar)
    
    if not eol:
        return line + achar
    
    if line[-1] == '\r':
        return line[:-1]
    else:
        return line

def receiveBySize(connection, size, eol=True):
    LF = '\n'
    CR = '\r'
    CRLF = '\r\n'

    fragments = []
    remaining = size
    while remaining > 0:
        chunk = connection.recv(remaining)
        if not chunk:
            break
        bytesread = len(chunk)
        fragments.append(chunk.decode("utf-8"))
        remaining -= bytesread
    s = "".join(fragments)
    if eol:
        return s.replace(CRLF, LF)
    else:
        return s

def receiveTillClose(connection, encoding="utf-8", eol=False):
    LF = '\n'
    CR = '\r'
    CRLF = '\r\n'
    fragments = []
    chunk = connection.recv(1024)
    while chunk and chunk != '':
        bytesread = len(chunk)
        fragments.append(chunk.decode(encoding))
        chunk = connection.recv(1024)
    s = "".join(fragments)
    if eol:
        return s.replace(CRLF, LF)
    else:
        return s

def parseHeader(headerLine):
    pattern = r"^([\w\-_]+): (.*)$"
    match = re.search(pattern, headerLine)
    assert match
    return match.group(1), match.group(2)

def receiveStringResponse(connection, eol=True):
    if isinstance(connection, _Proxy):
        conn = connection.socket
    else:
        conn = connection
    LF = '\n'
    CR = '\r'
    CRLF = '\r\n'

    response = ""
    content_length = None
    connection_close = False
    startLine = receiveByLine(conn)
    response += startLine + LF
    endHeaders = False
    while not endHeaders:
        headerLine = receiveByLine(conn)
        if headerLine == "":
            endHeaders = True
        else:
            field, value = parseHeader(headerLine)
            #print(field, value)
            if field.lower() == "content-length":
                content_length = int(value)
            if field.lower() == "connection" and value.lower() == "close":
                connection_close = True
        response += headerLine + LF

    if content_length:
        response += receiveBySize(conn, content_length, eol)

    if connection_close:
        response += receiveTillClose(conn, eol)

    return response
