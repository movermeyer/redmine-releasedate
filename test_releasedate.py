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

from werkzeug.test import Client, run_wsgi_app, create_environ
from werkzeug.wrappers import BaseResponse
from releasedate import jenkins
from releasedate.server import Releasedate, main


class ReleasedateTestCase(TestCase):

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

    def prepare_client(self):
        config = ConfigParser.ConfigParser()
        config.read(os.path.join(os.path.dirname(__file__), 'releasedate.cfg'))
        self.client = Client(Releasedate(config), response_wrapper=BaseResponse)


class TestClient(ReleasedateTestCase):

    @mock.patch.dict('os.environ', {
        'BUILD_NUMBER': '42',
        'BUILD_TAG': 'jenkins-myjob-42',
        'JOB_URL': 'http://jenkins_url/jobs/42/',
    })
    def test_client_sent_data(self):
        httpretty.register_uri(httpretty.POST, "http://releasedate-server/", body='OK')
        jenkins.run('http://releasedate-server/', '/path/to/my/repo/')
        check_against = {
            'build_number': ['42'],
            'build_tag': ['jenkins-myjob-42'],
            'previous_tag': ['jenkins-myjob-41'],
            'job_url': ['http://jenkins_url/jobs/42/'],
            'repo': ['/path/to/my/repo/'],
        }

        self.assertBodyQueryString(**check_against)

        output = jenkins.run('http://releasedate-server/', '/path/to/my/repo/', 'myserver')
        assert 'OK' in output
        check_against['instance'] = ['myserver']
        self.assertBodyQueryString(**check_against)

    def test_not_in_env(self):
        output = jenkins.run('http://releasedate-server/', '/path/to/my/repo/')
        assert 'Missing "BUILD_NUMBER" env variable.' in output
        assert len(httpretty.latest_requests) == 0


class TestRunServer(TestCase):

    @mock.patch('releasedate.server.run_simple')
    def test_run(self, run_simple):
        main()
        run_simple.assert_called_with('0.0.0.0', 8080, mock.ANY)
        assert type(run_simple.call_args[0][2]) == Releasedate


class TestServerOk(ReleasedateTestCase):

    def setUp(self):
        super(TestServerOk, self).setUp()
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
        self.prepare_client()
        self.valid_data = {
            'build_number': '42',
            'build_tag': 'jenkins-release-2',
            'previous_tag': 'jenkins-release-1',
            'job_url': 'http://jenkins_url/jobs/2/',
            'repo': self.dir,
            'instance': 'TestServer',
        }

    def tearDown(self):
        super(TestServerOk, self).tearDown()
        sh.rm('-r', self.dir)

    def test_api_calls_to_redmine(self):
        httpretty.register_uri(httpretty.PUT, re.compile("http://example.com/issues/(\d+).json"), status=200)

        response = self.client.post(data=self.valid_data)

        assert response.status_code == 200, response.data
        assert response.data == 'OK', response.data
        assert len(httpretty.latest_requests) == 2

        assert httpretty.latest_requests[-2].path == '/issues/777.json'
        json_post = json.loads(httpretty.latest_requests[-2].body)
        assert json_post['issue']['notes'] == 'Deployed on TestServer at 2006-04-07 22:13:13 in release \"42\":http://jenkins_url/jobs/2/'

        assert httpretty.last_request.path == '/issues/123.json'
        json_post = json.loads(httpretty.last_request.body)
        assert json_post['issue']['notes'] == 'Deployed on TestServer at 2006-04-07 22:13:13 in release \"42\":http://jenkins_url/jobs/2/'

    @mock.patch('releasedate.redmine.log')
    def test_redmine_failure(self, logger_mock):
        httpretty.register_uri(httpretty.PUT, re.compile("http://example.com/issues/(\d+).json"),
                               status=500,
                               body='Sorry, we are unavailable')
        response = self.client.post(data=self.valid_data)

        assert response.status_code == 200, response.data
        assert response.data == 'ERROR', response.data
        logger_mock.error.assert_called_with('Redmine update failed: [500] Sorry, we are unavailable')


class TestWSGI(TestCase):

    def test_wsgi(self):
        os.environ['RELEASEDATE_CONFIG'] = os.path.join(os.path.dirname(__file__), 'releasedate.cfg')
        from releasedate.wsgi import application
        app_iter, status, header = run_wsgi_app(application, create_environ())
        assert status == 409


class TestServerErrors(ReleasedateTestCase):

    def setUp(self):
        super(TestServerErrors, self).setUp()
        config = ConfigParser.ConfigParser()
        config.read(os.path.join(os.path.dirname(__file__), 'releasedate.cfg'))
        self.client = Client(Releasedate(config), response_wrapper=BaseResponse)

    def test_bad_args_409(self):
        assert self.client.post(data={'build_number': 'xxx'}).status_code == 409

    def test_exception_500(self):
        garbage_data = {
            'build_number': '', 'build_tag': '', 'previous_tag': '', 'job_url': '', 'repo': ''
        }
        assert self.client.post(data=garbage_data).status_code == 500
