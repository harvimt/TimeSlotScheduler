import string, random

from flask import session, request, url_for, redirect

from flaskext.genshi import render_response

#flatland form processing
from flatland import Form, String
from flatland.out.genshi import setup

from flaskapp import genshi, app
from flaskapp.globals import *

@app.route('/survey/<question_id>')
def survey(question_id):
	if question_id == 1:
		return render_response('survey_rank.html', context=dict(
			question='Preferred Times',
			numToRank=3,
			prefs=[
				{'id':0,'name':'MW 12:00 - 14:00'},
				{'id':1,'name':'TR 12:00 - 14:00'},
				{'id':2,'name':'MWF 12:00 - 13:30'},
				{'id':3,'name':'TR 14:00 - 16:00'},
			]
		))
	else:
		return render_response('survey_weight.html', context=dict(
			question='Preferred Times',
			numWeights=5,
			prefs=[
				{'id':0,'name':'Lockwood'},
				{'id':1,'name':'Harviston'},
				{'id':2,'name':'West'},
				{'id':3,'name':'Cha'},
			]
		))

