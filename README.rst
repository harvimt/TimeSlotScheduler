UNST Mentor Scheduler
=====================

Description
~~~~~~~~~~~

Matches people to time slots based on a survey the people take.
Slots and people have multiple matching criteria one of which must be Time preference.
Time preference is a set of days of the week and a start and stop time

Originally built for the University Studies Department of Portland State University [1] where "time slots" represent
courses and the people being matched are "Mentors" (kind of like TAs) and the matching criteria are time, faculty and theme

Updates made for Google Summer of Code 2011 (GSoC):
    * Add a web interface
    * Improve algorithm to use state-based search instead of Monte-Carlo [2]

Dependencies
~~~~~~~~~~~~

* Tested with Python 2.6 and 2.7, would probably work with 2.5
* Flask
* Genshi
* Flask-Genshi
* Flask-CSRF
* Flatland
* SQLAlchemy


Installation
~~~~~~~~~~~~

Install using virtualenv::

    >>> git clone https://username@trac.research.pdx.edu/git/unst-scheduler.git
    >>> cd TimeSlotSchduler
    >>> ./bootstrap.sh

.. note:: Due to the nature of python-ldap, you'll need to ensure the proper system-level
          dependencies are install on the host. They include the following:

         * openssl development package(s)
         * sasl development package(s)

TODO
~~~~

* Implement a survey system
* Make entirely `PrefType` agnostic


Usage
~~~~~

.. note:: The backend systems have been setup to handle scheduling with arbitrary Preference Types,
          but the front-end system still assume 3 Preference Types, Time (must have id=1, Faculty and Theme).

          Eventually the only hard-coded Preference Type will be Time since it's special (it's a subclass),

          It will probably still be required to have TimePref's id == 1

1. Get a courses CSV from banweb
2. Go to the installation url (http://unst-scheduler.research.pdx.edu)
3. Login
4. Go to administer weights, and make sure the weights are all in order
5. Go to administer courses, then upload courses file. select the csv file, click upload file
6. After uploading the courses file, the site will redirect back to the administer coures page, make sure everything is in order
7. Go to Administer Mentors and then upload a mentors CSV file from the Qualtrics survey system, make sure to set the indexes
8. Open putty or otherwise ssh into research.pdx.edu
9. Enter in

   >>> cd /vol/www/unst-scheduler/htdocs
   >>> env/bin/python runscheduler.py

10. Open up results at schedule results in a browser
