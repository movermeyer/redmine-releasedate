# coding: utf-8
"""Send POST request to releasedate server after jenkins job is successfully finished

Usage:
  redmine-release <url> <path_to_repo> [<instance_url>]
  redmine-release (-h | --help)
  redmine-release --version

<url> is a URL of your redmine instance.
<path_to_repo> is an absolute path to git repository (local to releasedate server)
<instance_url> is URL of a server where the code was deployed (optional)

Options:
  -h --help     Show this screen.
  --version     Show version.
"""

from os import environ as env
from docopt import docopt
from releasedate import __version__ as ver

import requests


class ImproperlyConfigured(Exception):
    pass


def get_previous_tag(tag, build_number):
    return tag.replace(build_number, str(int(build_number) - 1))


def get_build_context():
    """ Obtain info about current CI build for api request:

        * build number
        * git tag for the build
        * url of the CI job
    """
    try:
        return {
            'build_number': env['BUILD_NUMBER'],
            'build_tag': env['BUILD_TAG'],
            'job_url': env['JOB_URL']
        }
    except KeyError as e:
        raise ImproperlyConfigured('Missing "%s" env variable. '
                                   'Launch job via Jenkins, or provide evn variable manually.' % e.message)


def cli(*args):
    options = docopt(__doc__, args, version=ver)
    try:
        context = get_build_context()
    except ImproperlyConfigured as e:
        return str(e)

    result = requests.post(options['<url>'], data={
        'build_number': context['build_number'],
        'build_tag': context['build_tag'],
        'previous_tag': get_previous_tag(context['build_tag'], context['build_number']),
        'job_url': context['job_url'],
        'repo': options['<path_to_repo>'],
        'instance': options['<instance_url>'],
    })
    return result.text
