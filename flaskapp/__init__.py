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
		PrefType('Time',    'rank',   5.0),
		PrefType('Faculty', 'weight', 2.0),
		PrefType('Theme',   'weight', 1.0)
	))
	sess.commit()


	#and pref weights
	sess.add_all((
		PrefWeight(1,0,0.00),
		PrefWeight(1,1,0.25),
		PrefWeight(1,2,0.50),
		PrefWeight(1,3,0.75),
		PrefWeight(1,4,1.00),
		PrefWeight(1,5,1.25),
		PrefWeight(1,6,1.50),

		PrefWeight(2,0,0.00),
		PrefWeight(2,1,0.33),
		PrefWeight(2,2,0.66),
		PrefWeight(2,3,1.00),
		PrefWeight(2,4,1.33),
		PrefWeight(2,5,1.67),
		PrefWeight(2,6,2.00),

		PrefWeight(3,0,0.00),
		PrefWeight(3,1,0.17),
		PrefWeight(3,2,0.33),
		PrefWeight(3,3,0.50),
		PrefWeight(3,4,0.67),
		PrefWeight(3,5,0.83),
		PrefWeight(3,6,1.00)
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
