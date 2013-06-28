Redmine releasedate
===================

Track when your features are shipped to production in Redmine.
Currently supports git & jenkins.

How it works
------------

Upon finishing deploy job, jenkins creates a git tag, so it can track commits that refer to the build.
We can use these tags to track which tickets were deployed.

Installation
------------

Server
~~~~~~

Install it where your git repo resides. We only support local git repos, so make sure you have enough permissions.

* ``pip install redmine-releasedate``
* Specify redmine access options in config.py
* run ``redmine-release-server`` and make it available via http

    # releasedate.cfg



Jenkins
~~~~~~~

Add this to your Jenkins build step::

    redmine-release http://youserver/ /path/to/repo/


Redmine
~~~~~~~

Create a user with permissions to edit tickets and post notes in your project.
Obtain his API token and put it into ``config.py``.
Add custom field to store releasedate information.

See also
--------

* `Redmine hudson plugin`_
* `Jenkins redmine plugin`_

.. _Redmine hudson plugin: http://www.r-labs.org/projects/r-labs/wiki/Hudson_En
.. _Jenkins redmine plugin: https://wiki.jenkins-ci.org/display/JENKINS/Redmine+Plugin
