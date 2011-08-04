# CAS Authentication
# 
import os, string, random, urllib, re

from flask import session, request, url_for, redirect

from flaskext.genshi import render_response

#flatland form processing
from flatland import Form, String
from flatland.out.genshi import setup

from flaskapp import genshi, app, globals

cas_url = 'https://sso.pdx.edu:8443/cas/'
logout_url = cas_url + 'logout'

@app.route('/casauthenticate', methods=['GET','POST'])
def authenticate():
	global cas_url

	if '_cas_token' in session:
		netid = validate(session['_cas_token'])
		if netid != None:
				return render_response('message.html',context=dict(title='Already Logged In',message='Already Logged In'))

	if 'ticket' in request.args:
		netid = validate(request.args['ticket'])
		if netid != None:
				return render_response('message.html',context=dict(title='Success',message='Successfully Logged In'))

	login_url = cas_url + 'login' \
		+ '?service=' + urllib.quote(serviceURL())

	app.logger.debug('Redirecting to: %s' % login_url)

	return redirect(login_url)

def validate(ticket = None):
	global cas_url

	if ticket is None:
		if '_cask_token' in session:
			ticket = session['_cas_token']
		else:
			return None

	val_url = cas_url + "validate" + \
		'?service=' + urllib.quote(serviceURL()) + \
		'&ticket=' + urllib.quote(ticket)

	r = urllib.urlopen(val_url).readlines() # returns 2 lines
	if len(r) == 2 and re.match("yes", r[0]) != None:
		return r[1].strip()
	return None

def serviceURL():
	ret = request.url
	ret = re.sub(r'ticket=[^&]*&?', '', ret)
	ret = re.sub(r'\?&?$|&$', '', ret)
	return ret
