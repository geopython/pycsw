import StringIO
import os, sys

app_path = os.path.dirname(__file__)
sys.path.append(app_path)

from server import server

#os.chdir("/home/vagrant/src/opengeo/pycsw/pycsw")

def csw_application(env, start_response):
    config = 'default.cfg'

    if os.environ.has_key('PYCSW_CONFIG'):
        config = os.environ['PYCSW_CONFIG']

    if env['QUERY_STRING'].lower().find('config') != -1:
        for kvp in env['QUERY_STRING'].split('&'):
            if kvp.lower().find('config') != -1:
                config = kvp.split('=')[1]
    
    if os.path.isabs(config) is False:
        config = os.path.join(app_path, config)

    if "HTTP_HOST" in env and ":" in env["HTTP_HOST"]:
        env["HTTP_HOST"] = env["HTTP_HOST"].split(":")[0]

    env["local.app_root"] = app_path

    csw = server.Csw(config, env)

    gzip = False
    if (env.has_key('HTTP_ACCEPT_ENCODING') and
        env['HTTP_ACCEPT_ENCODING'].find('gzip') != -1):
        # set for gzip compressed response 
        gzip = True

    # set compression level
    if csw.config.has_option('server', 'gzip_compresslevel'):
        gzip_compresslevel = \
            int(csw.config.get('server', 'gzip_compresslevel'))
    else:
        gzip_compresslevel = 0

    contents = csw.dispatch_wsgi()

    headers = {}

    if gzip and gzip_compresslevel > 0:
        import gzip

        buf = StringIO()
        gzipfile = gzip.GzipFile(mode='wb', fileobj=buf,
                                 compresslevel=self.gzip_compresslevel)
        gzipfile.write(contents)
        gzipfile.close()
        
        contents = buf.getvalue()

        headers['Content-Encoding'] = 'gzip'

    headers['Content-Length'] = str(len(contents))
    headers['Content-Type'] = csw.contenttype

    status = '200 OK'
    start_response(status, headers.items())

    return [contents]

application = csw_application
