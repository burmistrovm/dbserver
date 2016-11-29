from cgi import parse_qs, escape
def application(environ, start_response):
    status = '200 OK'
    response_headers = [('Content-type','text/plain')]
    start_response(status, response_headers)
    lines = []
    d = parse_qs(environ['QUERY_STRING'])
    for key, value in d.items():
        lines.append("%s: %s" % (key, value))
    d = ''.join(lines)
    return ['hello %s'%d]
