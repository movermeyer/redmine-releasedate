# coding: utf-8
import sys
from os import environ as env

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


def run(url=None, repo=None, instance_url=None):
    """ Send POST request to releasedate server after jenkins job is successfully finished"""
    url = url or sys.argv[1]
    repo = repo or sys.argv[2]
    instance_url = instance_url or sys.argv[3] if len(sys.argv) > 3 else instance_url
    try:
        context = get_build_context()
    except ImproperlyConfigured as e:
        return str(e)

    result = requests.post(url, data={
        'build_number': context['build_number'],
        'build_tag': context['build_tag'],
        'previous_tag': get_previous_tag(context['build_tag'], context['build_number']),
        'job_url': context['job_url'],
        'repo': repo,
        'instance': instance_url,
    })
    return result.text
