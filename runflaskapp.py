#!./env/bin/python
import sys
from flaskapp import app

if len(sys.argv) == 2 and sys.argv[1] == 'install':
	from flaskapp import install
	install()
else:
	app.run(debug=True)
