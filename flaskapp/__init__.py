#flask web-server
from flask import Flask

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


#setup static folder
from werkzeug import SharedDataMiddleware
import os
import inspect
filename = inspect.currentframe().f_code.co_filename

app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
  '/': os.path.join(os.path.dirname(filename), 'static')
})

import foo #test module
import cas #auth module
import survey
