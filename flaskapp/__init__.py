# coding=UTF-8
"""
ARC Mentor Scheduler Web-App
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright © 2011 Mark Harviston <infinull@gmail.com>

This is the entry-point for the ARC Mentor Scheduler Web-App
Not much happens here, just boilerplate and setup

"""

#flask web-server
from flask import Flask, session, get_flashed_messages

#flask Genshi templates
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

#database/SQLAlchemy setup
from database import db_session as sess

@app.teardown_request
def shutdown_session(exception=None):
	sess.remove()

def install():
	from database import engine
	from datamodel import Base, User, PrefType, PrefWeight
	Base.metadata.create_all(engine)

	#Add initial admin user#
	user = User(user_name='harvimt',user_type='admin')
	sess.add(user)

	#add pref types
	sess.add_all((
		PrefType('Time','rank'),
		PrefType('Faculty','weight'),
		PrefType('Theme','weight')
	))
	sess.commit()


	#and pref weights
	sess.add_all((
		PrefWeight(1,-1,.4),
		PrefWeight(1,0,.1),
		PrefWeight(1,1,.1),
		PrefWeight(1,2,.3),
		PrefWeight(1,3,.4),
		PrefWeight(1,4,.5),
		PrefWeight(2,0,.1),
		PrefWeight(2,1,.2),
		PrefWeight(2,2,.3),
		PrefWeight(2,3,.4),
		PrefWeight(2,4,.5),
		PrefWeight(3,0,.1),
		PrefWeight(3,1,.2),
		PrefWeight(3,2,.3),
		PrefWeight(3,3,.4),
		PrefWeight(3,4,.5)
	))

	sess.commit()

	#add pref_weights

#setup static folder
from werkzeug import SharedDataMiddleware
import os
import inspect
filename = inspect.currentframe().f_code.co_filename

app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
  '/': os.path.join(os.path.dirname(filename), 'static')
})

#add CSRF protection
from flaskext.csrf import csrf
csrf(app)

#import sub-modules
import admin
import user
import cas #auth module
import survey
import courses
import weights
import mentors
