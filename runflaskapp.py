#!./env/bin/python

from flaskapp import app
import sys


if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == 'install':
        from flaskapp import install
	install()
    else:
        app.run(debug=True)
