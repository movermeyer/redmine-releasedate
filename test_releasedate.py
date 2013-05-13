# coding: utf-8
import ConfigParser
import tempfile
from unittest import TestCase
from urlparse import parse_qs
from httpretty import HTTPretty
from httpretty.compat import PY3
import mock
import sh
from werkzeug.test import Client
from releasedate import jenkins
from releasedate.server import Releasedate


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

class TestServer(HttprettyCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        sh.cd(self.dir)
        sh.git.init()
        sh.git('config', 'user.name', '"Guido"')
        sh.git('config', 'user.email', '"me@here.com"')
        sh.touch('README')
        sh.git.commit('-am', 'first commit')
        sh.git.tag('jenkins-release-1')
        sh.touch('file1')
        sh.git.commit('-am', 'second commit #777 #123')
        sh.git.tag('jenkins-release-2')
        sh.touch('file2')
        sh.git.commit('-am', '#67 third commit')
        sh.git.tag('jenkins-release-3')

    def test_ok(self):
        HTTPretty.register_uri(HTTPretty.POST, "http://redmine/", status=200)

        config = ConfigParser.ConfigParser().read('release.cfg')
        client = Client(Releasedate(config))
        client.post(data={'build_number': '42',
                          'build_tag': 'jenkins-myjob-42',
                          'previous_tag': 'jenkins-myjob-41',
                          'job_url': 'http://jenkins_url/jobs/42/',
                          'repo': '/path/to/my/repo/',
        })


        #assert request per ticket to redmine issued



# redmine-release-server
# test bad args
# test all ok
# test 500 exception
