from google.appengine.api import users
from google.appengine.ext import db, webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

import os
import urllib

class MainPage(webapp.RequestHandler):
    def get(self):
        if self.request.get("name"):
            self.response.out.write(self.request.get("name"));
        else:
            self.response.out.write("hello, world");

application = webapp.WSGIApplication([
    ('/', MainPage),
  ])


def main():
    run_wsgi_app(application)


if __name__ == '__main__':
    main()
