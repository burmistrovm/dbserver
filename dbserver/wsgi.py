"""
WSGI config for askme project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/howto/deployment/wsgi/
"""
import os
import sys

root_path = os.path.abspath(os.path.split(__file__)[0])
sys.path.insert(0, os.path.join(root_path, 'project_name'))
sys.path.insert(0, root_path)

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
