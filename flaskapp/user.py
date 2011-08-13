"""
Administer user info
list users, add new user, edit user info, etc.
"""

import ldap

import flask
from flask import session, request, url_for, redirect, abort, flash

from flaskext.genshi import render_response

#flatland form processing
from flatland import Form, String, Constrained, Enum
from flatland.validation import NoLongerThan
from flatland.out.genshi import setup

from flaskapp import genshi, app
from flaskapp.globals import *

from database import db_session as sess
from datamodel import User

import cas

## Forms & Validators ##
class UserForm(Form):
	"""Flatland Form for datamodel.User"""
	user_name = String.using(label="Username",validators=[NoLongerThan(32)])
	user_type = Enum.using(label="User Type",valid_values=['admin','user'])

def user_name_does_not_exist(el, state):
	return sess.query(User).get(el['user_name'].value) is None

def user_name_exists(el, state):
	return sess.query(User).get(el['user_name'].value) is None

def odin_name_exists(el,state):
	return get_odin(el['user_name'].value) is not None

class NewUserForm(UserForm):
	validators = [user_name_does_not_exist, odin_name_exists]

class EditUserForm(UserForm):
	validators = [user_name_exists, odin_name_exists]

## Odin/LDAP helpers ##

def get_odin(odin_name):
	""" get odin information from LDAP """
	l = ldap.open('localhost')
	l.simple_bind()

	s = l.search_s("ou=people,dc=pdx,dc=edu",ldap.SCOPE_SUBTREE,'uid=%s' % odin_name, ['gecos','mailLocalAddress'])

	if not s:
		return None

	full_name = s[0][1]['gecos'][0]
	email_address = s[0][1]['mailLocalAddress'][0]

	#app.logger.debug("full_name = %s" % full_name)

	r = dict(full_name=full_name, email=email_address)

	l.unbind()

	return r

## Pages ##

@app.route('/users')
def list_users():
	"""List Users"""
	require_auth('admin')

	users = sess.query(User).all()
	return render_response('list_users.html',dict(users=users))

@app.route('/user/new',methods=['POST','GET'])
def new_user():
	"""Display new user creation form or accept and process it"""
	require_auth('admin')

	form = NewUserForm()

	if request.method == 'POST':
		values = request.form.copy()
		del values['_csrf_token']
		form.set(values)

		if form.validate():
			user = User(**(form.value))
			sess.add(user)
			sess.commit()
			flash('Successfully added new user')
			return redirect(url_for('display_user',username=form['user_name'].value))
		else:
			flash('Form Validation Failed','error')

	return render_response('add_user.html', dict(form=form,submit_url=url_for('new_user')))

@app.route('/user/<username>')
def display_user(username):
	"""Display the user's info"""
	require_auth('admin')

	user = sess.query(User).get(username)
	if not user:
		abort(404)

	oinfo = get_odin(username)
	if oinfo is None:
		flash('User info not found in LDAP','error')
		user.email = 'unknown'
		user.full_name = 'unknown'
	else:
		user.email = oinfo['email']
		user.full_name = oinfo['full_name']

	return render_response('display_user.html', dict(user=user))

@app.route('/user/<username>/edit',methods=['GET','POST'])
def edit_user(username):
	"""Edit the user's info"""
	require_auth('admin')

	user = sess.query(User).get(username)
	if user is None: abort(404)

	form = EditUserForm.from_object(user)

	if request.method == 'POST':
		values = request.form.copy()
		del values['_csrf_token']

		if 'delete' in values:
			return render_response('del_confirm_user.html',dict(submit_url=url_form('del_confirm_user',username=username)))

		form.set(values)

		form.validate()

		if form['user_name'].value != username:
			form.add_error('username in url does not match that in form')

		if not form.valid:
			flash('Form Invalid','error')
		else:
			user.__dict__.update(form.value)
			sess.commit()
			flash('Successfully Updated User Info')

	user = sess.query(User).get(username)
	return render_response('edit_user.html',dict(form=form,submit_url=url_for('edit_user')))

@app.route('/user/<username>/confirm_delete', methods=['POST'])
def del_confirm_user(username):
	require_auth('admin')

	user = sess.query(User).get(username)
	if user is None: abort(404)

	if request.form['confirm'] == 'yes':
		sess.delete(user)
		sess.commit()

		flash('Successfully deleted %s' % username)
		return redirect(url_for('list_users'))
	else:
		return redirect(url_for('edit_user',username=username))

