# coding: utf-8
import sys
from os import environ as env

import requests


def get_previous_tag(tag, build_number):
    return tag.replace(build_number, str(int(build_number) - 1))


def run(url=None, repo=None):
    """ Send POST request to releasedate server after jenkins job is successfully finished"""
    url = url or sys.argv[1]
    repo = repo or sys.argv[2]

    result = requests.post(url, data={
        'build_number': env['BUILD_NUMBER'],
        'build_tag': env['BUILD_TAG'],
        'previous_tag': get_previous_tag(env['BUILD_TAG'], env['BUILD_NUMBER']),
        'job_url': env['JOB_URL'],
        'repo': repo,
    })
    return result