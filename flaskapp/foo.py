import string, random

from flask import session, request, url_for, redirect

from flaskext.genshi import render_response

#flatland form processing
from flatland import Form, String
from flatland.out.genshi import setup

from flaskapp import genshi, app
from flaskapp.globals import *

#declare flatland forms
class FooForm(Form):
	foo = String.using(label="Foo Bar")
	bar = String.using(label="Bar Foo")
	csrf_token = String #hidden

@app.route('/bar')
def bar():
	return render_response('survey_rank.html',context=dict(question='foo'))

@app.route("/foo")
def foo():
	form = FooForm()

	form.set(dict(csrf_token=generate_csrf_token()))
	submit_url = url_for('foo_submit')

	return render_response('FooForm.html',context=dict(form=form,submit_url=submit_url))

@app.route("/foo/submit", methods=['POST'])
def foo_submit():
	return redirect(url_for('foo'))
