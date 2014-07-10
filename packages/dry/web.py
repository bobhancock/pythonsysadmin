import httplib
import urlparse

def http_exists(url):
    """ Test to see if an HTTP URL exists by just getting the HEAD.
    We are only testing for two response codes here: 200 and 302.
    """
     #os.environ["http_proxy"] = "http://xxx.xxx.xxx.xxx:80"

    host, path = urlparse.urlsplit(url)[1:3]
    if ":" in host:
        # port specificed, try to use it
        host, port = host.split(":", 1)
        
        try:
            port = int(port)
        except ValueError:
            raise ValueError('Invalid port number %r' % port)
    else:
        # not port specified, used default port
        port = None
        
    try:
        connection = httplib.HTTPConnection(host, port=port)
        connection.request("HEAD", path)
        
        resp = connection.getresponse()
        if resp.status == 200:
            found = True
        elif resp.status == 302: 
            # temporary redirect
            found = http_exists(urlparse.urljoin(
                url,
                resp.getheader('location', '')))
        else:
            found = False
    except Exception, e:
        raise Exception('%s: e' % url)
    
    return found
            
        