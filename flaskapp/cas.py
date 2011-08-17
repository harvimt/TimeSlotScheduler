# coding=UTF-8
"""
CAS Authentication
~~~~~~~~~~~~~~~~~~

:Copyright © 2011 Mark Harviston <infinull@gmail.com>

Handle login/logout and authorization through PSU's CAS server

"""
# TODO: rework to use urlparse libs instead of regex and simple concat
#
import os, string, random, urllib, re

from flask import session, request, url_for, redirect

from flaskext.genshi import render_response

#flatland form processing
from flatland import Form, String
from flatland.out.genshi import setup

from flaskapp import genshi, app

cas_url = 'https://sso.pdx.edu:8443/cas/'
#logout_url = cas_url + 'logout'

@app.route('/login', methods=['GET','POST'])
def login():
	global cas_url

	if '_cas_token' in session:
		netid = validate()

		if netid is not None:
			flash('Already Logged In')
			return redirect('/')
		else:
			del session['_cas_token']

	if 'ticket' in request.args:
		session['_cas_token'] = request.args['ticket']
		netid = validate(request.args['ticket'])

		if netid != None:
			if 'redirect' in request.args:
				return redirect(request.args['redirect'])
			else:
				return redirect('/')

	login_url = cas_url + 'login' \
		+ '?service=' + urllib.quote(url_for('login',_external=True))

	app.logger.debug('Redirecting to: %s' % login_url)

	return redirect(login_url)

@app.route('/logout')
def logout():
	logout_url = cas_url + 'logout' \
		+ '?url=' + urllib.quote(url_for('login',_external=True))

	if validate():
		del session['username']
		return redirect(logout_url)
	else:
		flash('Already Logged Out')
		return redirect('/')

def validate(ticket = None):
	"""
	Checks for username session var if present returns it
	Checks for _cas_token session var, and attempts to validate it
	if valid set session['username'] to the username associated with the token and return that value
	otherwise return None
	"""

	global cas_url

	if ticket is None and 'username' in session:
		return session['username']

	if ticket is None:
		if '_cas_token' in session:
			ticket = session['_cas_token']
		else:
			app.logger.debug("token empty, valid= no")
			return None

	val_url = cas_url + "validate" + \
		'?service=' + urllib.quote(url_for('login',_external=True)) + \
		'&ticket=' + urllib.quote(ticket)

	r = urllib.urlopen(val_url).readlines() # returns 2 lines

	app.logger.debug("validating token %s" % ticket)

	if len(r) == 2 and re.match("yes", r[0]) is not None:
		app.logger.debug("valid")
		session['username'] = r[1].strip()
		return session['username']
	else:
		app.logger.debug("invalid")
		return None

@app.errorhandler(401)
def error_401_not_authorized(error):
	return render_response('message.html',context=dict(title="You Are Not Authorized",message=u'You must be logged in to view this page<br/><a href="/login">Log in</a>'))

