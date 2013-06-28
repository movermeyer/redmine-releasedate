# coding: utf-8
import json
import os
import re
import tempfile
import ConfigParser
from unittest import TestCase
from urlparse import parse_qs

import mock
import sh
from httpretty import httpretty
from httpretty.compat import PY3

from werkzeug.test import Client
from werkzeug.wrappers import BaseResponse
from releasedate import jenkins
from releasedate.server import Releasedate


class HttprettyCase(TestCase):

    def setUp(self):
        httpretty.reset()
        httpretty.enable()

    def tearDown(self):
        httpretty.disable()

    def assertBodyQueryString(self, **kwargs):
        """ Hakish, but works %("""
        if PY3:
            qs = parse_qs(httpretty.last_request.body.decode('utf-8'))
        else:
            qs = dict((key, [values[0].decode('utf-8')]) for key, values in parse_qs(httpretty.last_request.body).items())
        assert kwargs == qs


class TestClient(HttprettyCase):

    @mock.patch.dict('os.environ', {
        'BUILD_NUMBER': '42',
        'BUILD_TAG': 'jenkins-myjob-42',
        'JOB_URL': 'http://jenkins_url/jobs/42/',
    })
    def test_client_sent_data(self):
        httpretty.register_uri(httpretty.POST, "http://releasedate-server/", body='OK')
        jenkins.run('http://releasedate-server/', '/path/to/my/repo/')

        self.assertBodyQueryString(**{'build_number': ['42'],
                                      'build_tag': ['jenkins-myjob-42'],
                                      'previous_tag': ['jenkins-myjob-41'],
                                      'job_url': ['http://jenkins_url/jobs/42/'],
                                      'repo': ['/path/to/my/repo/'],
                                      })


class TestServer(HttprettyCase):

    def setUp(self):
        super(TestServer, self).setUp()
        self.dir = tempfile.mkdtemp()
        sh.cd(self.dir)
        sh.git.init()
        sh.git('config', 'user.name', '"Guido"')
        sh.git('config', 'user.email', '"me@here.com"')
        sh.touch('README')
        sh.git.add('.')
        sh.git.commit('-am', 'first commit')
        sh.git.tag('-a', 'jenkins-release-1', '-m', 'Release 1')
        sh.touch('file1')
        sh.git.add('.')
        sh.git.commit('-am', 'second commit #777 #123')
        sh.git.tag('-a', 'jenkins-release-2', '-m', 'Release 2', _env={"GIT_COMMITTER_DATE": "2006-04-07T22:13:13"})
        sh.touch('file2')
        sh.git.add('.')
        sh.git.commit('-am', '#67 third commit')
        sh.git.tag('-a', 'jenkins-release-3', '-m', 'Release 3')

    def tearDown(self):
        super(TestServer, self).tearDown()
        sh.rm('-r', self.dir)

    def test_api_calls_to_redmine(self):
        httpretty.register_uri(httpretty.PUT, re.compile("http://example.com/issues/(\d+).json"), status=200)

        config = ConfigParser.ConfigParser()
        config.read(os.path.join(os.path.dirname(__file__), 'releasedate.cfg'))
        client = Client(Releasedate(config), response_wrapper=BaseResponse)
        response = client.post(data={
            'build_number': '42',
            'build_tag': 'jenkins-release-2',
            'previous_tag': 'jenkins-release-1',
            'job_url': 'http://jenkins_url/jobs/2/',
            'repo': self.dir,
            'instance': 'TestServer',
        })

        assert len(httpretty.latest_requests) == 2

        assert response.status_code == 200, response.data
        assert httpretty.last_request.path == '/issues/123.json'

        json_post = json.loads(httpretty.last_request.body)
        assert json_post['issue']['notes'] == 'Deployed on TestServer at 2006-04-07 22:13:13 in release \"42\":http://jenkins_url/jobs/2/'



# redmine-release-server
# test bad args
# test all ok
# test 500 exception
