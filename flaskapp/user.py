# coding=UTF-8
"""
Administer User Info
~~~~~~~~~~~~~~~~~~~~

:Copyright © 2011 Mark Harviston <infinull@gmail.com>


list users, add new user, edit user info, etc.

see `datamodel.User`
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
	valid = sess.query(User).get(el['user_name'].value) is None
	if not valid:
		el['user_name'].add_error('User Name already exists')
	return valid

def user_name_exists(el, state):
	valid = sess.query(User).get(el['user_name'].value) is not None
	if not valid:
		el['user_name'].add_error('Username does not exist')
	return valid

def odin_name_exists(el,state):
	valid = get_odin(el['user_name'].value) is not None
	if not valid:
		el['user_name'].add_error('odin name "%s" does not exist' % el['user_name'].value)
	return valid

class NewUserForm(UserForm):
	validators = [user_name_does_not_exist, odin_name_exists]

class EditUserForm(UserForm):
	validators = [user_name_exists, odin_name_exists]

## Odin/LDAP helpers ##

def ldap_up():
	r = False
	try:
		l = ldap.open('localhost')
		l.simple_bind()
		r = True
	except ldap.SERVER_DOWN:
		r = False
	finally:
		if l is not None: l.unbind()

	return r

def get_odin(odin_name):
	""" get odin information from LDAP """
	try:
		l = ldap.open('localhost')
		l.simple_bind()

		s = l.search_s("ou=people,dc=pdx,dc=edu",ldap.SCOPE_SUBTREE,'uid=%s' % odin_name, ['gecos','mailLocalAddress'])

		if not s: return None

		full_name = s[0][1]['gecos'][0]
		email_address = s[0][1]['mailLocalAddress'][0]

		r = dict(full_name=full_name, email=email_address)

	except ldap.SERVER_DOWN:
		return None
	finally:
		if l is not None:
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

	if not ldap_up():
		return render_response('message.html',dict(
			message_type='error',
			title="Add New User - LDAP Problem",
			message="Cannot add a new user since LDAP is not accessible"
		))

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
		user.update(**oinfo)

	return render_response('display_user.html', dict(user=user))

@app.route('/user/edit/<username>',methods=['GET','POST'])
def edit_user(username):
	"""Edit the user's info"""
	require_auth('admin')

	user = sess.query(User).get(username)
	if user is None: abort(404)

	form = EditUserForm()
	form.set_by_object(user)
	#app.logger.debug('(Post-Set) form=%r, valid=%r,errors=%r' % (form,form.valid,all_fl_errors(form.errors)))

	if request.method == 'POST':
		values = request.form.copy()
		del values['_csrf_token']

		if 'delete' in values:
			return render_response('del_confirm_user.html',dict(submit_url=url_for('del_confirm_user',username=username),name2del=username))

		form.set(values)

		if not form.validate():
			flash('Form Invalid','error')
			app.logger.debug('form=%r, valid=%r,errors=%r' % (form,form.valid,form.errors))

		elif form['user_name'].value != username:
			flash('Form Invalid','error')
			form.add_error('username in url does not match that in form')

		else:
			user.update(**form.value)
			#app.logger.debug('user=%r' % user)
			#app.logger.debug('dirty: %r' % sess.dirty)
			#app.logger.debug('id_modified=%r' % sess.is_modified(user))
			sess.commit()
			flash('Successfully Updated User Info')

	user = sess.query(User).get(username)
	return render_response('edit_user.html',dict(form=form,submit_url=url_for('edit_user',username=username)))

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

