#flask web-server
from flask import Flask, session, get_flashed_messages

#flask genshi templates
from flaskext.genshi import render_response
from flaskext.genshi import Genshi

#flatland form processing
from flatland import Form, String
from flatland.out.genshi import setup

#initialize server, templates and callbacks
app = Flask(__name__)
genshi = Genshi(app)

app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

@genshi.template_parsed
def callback(template):
	setup(template)

genshi.extensions['html'] = 'html5' #change default rendering mode to html5 instead of strict html4

#database/sqlalchemy setup
from database import db_session

@app.teardown_request
def shutdown_session(exception=None):
	db_session.remove()


def install():
	from datamodel import Base
	from database import engine
	Base.metadata.create_all(engine)

#setup static folder
from werkzeug import SharedDataMiddleware
import os
import inspect
filename = inspect.currentframe().f_code.co_filename

app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
  '/': os.path.join(os.path.dirname(filename), 'static')
})

#add csrf protection
from flaskext.csrf import csrf
csrf(app)

#import sub-modules

import admin
import user
import cas #auth module
import survey
