# coding: utf-8
from unittest import TestCase
from urlparse import parse_qs
from httpretty import HTTPretty
from httpretty.compat import PY3
import mock
from releasedate import jenkins


class HttprettyCase(TestCase):

    def setUp(self):
        HTTPretty.reset()
        HTTPretty.enable()

    def tearDown(self):
        HTTPretty.disable()

    def assertBodyQueryString(self, **kwargs):
        """ Hakish, but works %("""
        if PY3:
            qs = parse_qs(HTTPretty.last_request.body.decode('utf-8'))
        else:
            qs = dict((key, [values[0].decode('utf-8')]) for key, values in parse_qs(HTTPretty.last_request.body).items())
        assert kwargs == qs


class TestClient(HttprettyCase):

    @mock.patch.dict('os.environ', {
        'BUILD_NUMBER': '42',
        'BUILD_TAG': 'jenkins-myjob-42',
        'JOB_URL': 'http://jenkins_url/jobs/42/',
    })
    def test_client_sent_data(self):
        HTTPretty.register_uri(HTTPretty.POST, "http://testsever/", body='OK')
        jenkins.run('http://testsever/', '/path/to/my/repo/')

        self.assertBodyQueryString(**{'build_number': ['42'],
                                      'build_tag': ['jenkins-myjob-42'],
                                      'previous_tag': ['jenkins-myjob-41'],
                                      'job_url': ['http://jenkins_url/jobs/42/'],
                                      'repo': ['/path/to/my/repo/'],
                                      })

# redmine-release-server
# test bad args
# test all ok
# test 500 exception
