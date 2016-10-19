# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# =================================================================

# WSGI wrapper for pycsw
#
# Apache mod_wsgi configuration
#
# ServerName host1
# WSGIDaemonProcess host1 home=/var/www/pycsw processes=2
# WSGIProcessGroup host1
#
# WSGIScriptAlias /pycsw-wsgi /var/www/pycsw/wsgi.py
#
# <Directory /var/www/pycsw>
#  Order deny,allow
#  Allow from all
# </Directory>
#
# or invoke this script from the command line:
#
# $ python ./pycsw/wsgi.py
#
# which will publish pycsw to:
#
# http://localhost:8000/
#

import os
import sys
import six
import re
import ConfigParser
from six.moves.urllib.parse import unquote

from pycsw import server


PYCSW_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def dynUpdateConfigurationURLs(new_url):
    '''
    Update dynamically PyCSW configuration to match public IP:port of this server.

    The PyCSW server can be deployed in a VM or a container in different environment (dev, prod...). Its IP:port is therefore not deterministic.
    The values of 'serveraddress' in default.cfg can't be forecasted in advance.

    This function is meant to be called the client emit a request.
    The base URL requested by the client is retrieved and reinjected in PyCSW configuration.
    '''
    confFile = os.environ.get('PYCSW_CONFIG', '/etc/pycsw/default.cfg')
    configpar = ConfigParser.ConfigParser()
    configpar.read(confFile)
    # Old values
    oldServerURL = configpar.get('server', 'url')

    # New values
    new_url = re.sub('^https?://', '', new_url)  # Remove http[s] if present
    newServerURL = 'http://' + new_url + '/pycsw/csw.py'

    # Update the config is URLs are not the same as the one used for this HTTP requet.
    if oldServerURL != newServerURL:
        configpar.set('server', 'url', newServerURL)

        with open(confFile, 'wb') as configfilePtr:
            configpar.write(configfilePtr)

        print('--------------------------------------------------------------------------------------------------------------------------')
        print('Dynamically update PyCSW config \'serverURL\' to \'%s\'' % (newServerURL))



def application(env, start_response):
    """WSGI wrapper"""
    config = 'default.cfg'

    dynUpdateConfigurationURLs(env['HTTP_HOST'])   # Ex: 'HTTP_HOST': '172.16.10.21',

    if 'PYCSW_CONFIG' in env:
        config = env['PYCSW_CONFIG']

    root = PYCSW_ROOT

    if 'PYCSW_ROOT' in env:
        root = env['PYCSW_ROOT']

    if env['QUERY_STRING'].lower().find('config') != -1:
        for kvp in env['QUERY_STRING'].split('&'):
            if kvp.lower().find('config') != -1:
                config = unquote(kvp.split('=')[1])

    if not os.path.isabs(config):
        config = os.path.join(root, config)

    if 'HTTP_HOST' in env and ':' in env['HTTP_HOST']:
        env['HTTP_HOST'] = env['HTTP_HOST'].split(':')[0]

    env['local.app_root'] = root

    csw = server.Csw(config, env)

    gzip = False
    if ('HTTP_ACCEPT_ENCODING' in env and
            env['HTTP_ACCEPT_ENCODING'].find('gzip') != -1):
        # set for gzip compressed response
        gzip = True

    # set compression level
    if csw.config.has_option('server', 'gzip_compresslevel'):
        gzip_compresslevel = \
            int(csw.config.get('server', 'gzip_compresslevel'))
    else:
        gzip_compresslevel = 0

    status, contents = csw.dispatch_wsgi()

    headers = {}

    if gzip and gzip_compresslevel > 0:
        import gzip

        buf = six.BytesIO()
        gzipfile = gzip.GzipFile(mode='wb', fileobj=buf,
                                 compresslevel=gzip_compresslevel)
        gzipfile.write(contents)
        gzipfile.close()

        contents = buf.getvalue()

        headers['Content-Encoding'] = 'gzip'

    headers['Content-Length'] = str(len(contents))
    headers['Content-Type'] = str(csw.contenttype)
    start_response(status, list(headers.items()))

    return [contents]

if __name__ == '__main__':  # run inline using WSGI reference implementation
    from wsgiref.simple_server import make_server
    port = 8000
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    httpd = make_server('', port, application)
    print('Serving on port %d...' % port)
    httpd.serve_forever()
