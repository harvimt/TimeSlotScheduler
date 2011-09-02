#!/usr/bin/env python2
import sys
from flaskapp import app

if len(sys.argv) == 2 and sys.argv[1] == 'install':
	from flaskapp import install
	install()
elif len(sys.argv) == 2 and sys.argv[1] == 'schedule':
	from flaskapp.scheduler import run_scheduler
	run_scheduler()
else:
	app.run(debug=True)
