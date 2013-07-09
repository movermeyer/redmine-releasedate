Redmine releasedate
===================

Track when your features are shipped to production in Redmine.
Currently supports git & jenkins.

.. image:: https://travis-ci.org/futurecolors/redmine-releasedate.png?branch=master
    :target: https://travis-ci.org/futurecolors/redmine-releasedate

.. image:: https://coveralls.io/repos/futurecolors/redmine-releasedate/badge.png?branch=master
    :target: https://coveralls.io/r/futurecolors/redmine-releasedate

.. image:: https://pypip.in/v/redmine-releasedate/badge.png
    :target: https://crate.io/packages/redmine-releasedate/

How it works
------------

Upon finishing deploy job, jenkins creates a git tag, so it can track commits that refer to the build.
We can use these tags to track which tickets were deployed.
Date of deploy is stored in custom field of each ticket that was mentioned in commit.
A comment is left for every ticket in release as well for readability.

.. image:: https://raw.github.com/futurecolors/redmine-releasedate/master/screenshots/releasedate.png


Installation
------------

Server
~~~~~~

Install it where your git repo resides. We only support local git repos,
so make sure you have enough permissions to access git repo files.

* ``pip install redmine-releasedate``
* Specify redmine access options in ``releasedate.cfg``
* run ``redmine-release-server`` and make it available via http
::

    # releasedate.cfg
    [redmine]
    url = http://example.com
    token = your_api_token_goes_here
    released_at_id = 42  ;custom field id goes here

    [releasedate]
    message = Deployed on %(instance)s at %(date)s in release "%(release_id)s":%(release_url)s
    address = 0.0.0.0  ; optional
    port = 8080  ; optional


Jenkins
~~~~~~~

* Pip install ``redmine-releasedate`` on your jenkins server. No configuration is needed.

* Add this to your Jenkins build step (preferably, in `post-build task`_)::

    git push --tags
    redmine-release http://releasedate_url/ /path/to/repo/ [instance_url]


.. _post-build task: https://wiki.jenkins-ci.org/display/JENKINS/Post+build+task


Redmine
~~~~~~~

Create a user with permissions to edit tickets and post notes in your project.
Obtain his API token and put it into ``releasedate.cfg``.
Add custom field to store releasedate information.


Serve as WSGI app
~~~~~~~~~~~~~~~~~

You can run server as usual wsgi app behind uwsgi or guicorn::

    # your/wsgi/module.py
    os.environ.setdefault("RELEASEDATE_CONFIG", "path/to/your/releasedate.cfg")
    from releasedate.wsgi import get_wsgi_application


Limitations
-----------
Second run of client command will make second comment and overwrite release date, 
so please make sure you run ``redmine-release`` only once per deploy.


See also
--------

* `Redmine hudson plugin`_
* `Jenkins redmine plugin`_

.. _Redmine hudson plugin: http://www.r-labs.org/projects/r-labs/wiki/Hudson_En
.. _Jenkins redmine plugin: https://wiki.jenkins-ci.org/display/JENKINS/Redmine+Plugin
