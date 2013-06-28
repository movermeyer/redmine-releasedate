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
            status = self.process_release(request.form)
            return Response(status)

        except Exception as e:
            return Response(repr(e), status=500)

    def is_valid(self, request):
        if all(map(partial(contains, request.form), ('build_number', 'build_tag', 'previous_tag', 'job_url', 'repo'))):
            return True
        return False

    def process_release(self, data):
        status = 'OK'
        repo = GitRepo(data['repo'])
        messages = repo.commit_messages(data['previous_tag'], data['build_tag'])
        flatten = itertools.chain.from_iterable
        ticket_ids = set(flatten(itertools.imap(Redmine.get_ticket_id, messages)))
        release_date = repo.tag_date(data['build_tag'])

        message = self.message % {
            'instance': data.get('instance', 'server'),
            'date': release_date,
            'release_id': data['build_number'],
            'release_url': data['job_url']
        }

        for ticket_id in ticket_ids:
            if not self.tracker.issue(ticket_id).log_release_date(release_date, message=message):
                status = 'ERROR'
            log.info('%s: %s', ticket_id, release_date)
            log.info(message)
        return status

    def wsgi_app(self, environ, start_response):
        request = Request(environ)
        response = self.dispatch_request(request)
        return response(environ, start_response)

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)


def main():
    log.addHandler(logging.StreamHandler())
    log.setLevel(logging.INFO)
    defaults = {
        'address': '0.0.0.0',
        'port': 8080,
    }
    config = ConfigParser.ConfigParser(defaults=defaults)
    config.read('releasedate.cfg')
    address = config.get('releasedate', 'address')
    port = int(config.get('releasedate', 'port'))
    run_simple(address, port, Releasedate(config))


if __name__ == '__main__':
    main()  # pragma: no cover
