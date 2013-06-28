# coding: utf-8
import logging
import itertools
import ConfigParser
from functools import partial
from operator import contains

from werkzeug.serving import run_simple
from werkzeug.wrappers import Request, Response

from releasedate.repo import GitRepo
from releasedate.redmine import Redmine


log = logging.getLogger('redmine-releasedate')


class Releasedate(object):

    def __init__(self, config):
        self.message = config.get('releasedate', 'message', raw=True)
        self.tracker = Redmine(host=config.get('redmine', 'url'),
                               api_key=config.get('redmine', 'token'),
                               custom_field_id=config.get('redmine', 'released_at_id'))

    def dispatch_request(self, request):
        if not self.is_valid(request):
            return Response('Bad arguments', status=409)

        try:
            repo = GitRepo(request.form['repo'])
            messages = repo.commit_messages(request.form['previous_tag'], request.form['build_tag'])
            flatten = itertools.chain.from_iterable
            ticket_ids = set(flatten(itertools.imap(Redmine.get_ticket_id, messages)))
            release_date = repo.tag_date(request.form['build_tag'])

            message = self.message % {
                'instance': request.form.get('instance', 'server'),
                'date': release_date,
                'release_id': request.form['build_number'],
                'release_url': request.form['job_url']
            }

            for ticket_id in ticket_ids:
                self.tracker.issue(ticket_id).log_release_date(release_date, message=message)
                log.info('%s: %s', ticket_id, release_date)
                log.info(message)
            return Response('OK')

        except Exception as e:
            return Response(repr(e), status=500)

    def is_valid(self, request):
        if all(map(partial(contains, request.form), ('build_number', 'build_tag', 'previous_tag', 'job_url', 'repo'))):
            return True
        return False

    def wsgi_app(self, environ, start_response):
        request = Request(environ)
        response = self.dispatch_request(request)
        return response(environ, start_response)

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)


if __name__ == '__main__':
    log.addHandler(logging.StreamHandler())
    log.setLevel(logging.INFO)
    config = ConfigParser.ConfigParser()
    config.read('releasedate.cfg')
    run_simple('0.0.0.0', 3051, Releasedate(config))
