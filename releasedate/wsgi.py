# coding: utf-8
import os

from releasedate.server import get_wsgi_application

os.environ.setdefault("RELEASEDATE_CONFIG", "releasedate.cfg")
application = get_wsgi_application()
