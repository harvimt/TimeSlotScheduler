import string, random

from flask import session, request, url_for, redirect

from flaskext.genshi import render_response

#flatland form processing
from flatland import Form, String
from flatland.out.genshi import setup

from flaskapp import genshi, app
from flaskapp.globals import *

import cas

@app.route('/')
def home():
	username = cas.validate()
	if username is None:
		#TODO
		pass
	return render_response('')

@app.route('/admin')
def admin():
	if not cas.validate(): abort(403)
