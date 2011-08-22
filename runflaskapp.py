#!/usr/bin/env python2
import sys
from flaskapp import app

if len(sys.argv) == 2 and sys.argv[1] == 'install':
	from flaskapp import install
	install()
else:
	app.run(host='131.252.208.85',port=9999,debug=True)
