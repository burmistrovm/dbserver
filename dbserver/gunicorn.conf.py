bind = "127.0.0.1:81"
workers = 5
app_name = "wsgi.py"
daemon = False
worker_class = 'sync'
worker_connections = 1000
timeout = 1000000
keepalive = 1000000
DEBUG = False
