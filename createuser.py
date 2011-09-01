#!./env/bin/python

from flaskapp.datamodel import User
from flaskapp.database import db_session as sess

import sys


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print "Usage: createuser.py [ODIN username]"
        sys.exit(1)

    username = sys.argv[1]
    user = User(**{'user_name':username,'user_type':'admin'})
    sess.add(user)
    sess.commit()
