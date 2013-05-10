# coding: utf-8
import json
import logging
import re
import requests


log = logging.getLogger(__name__)


class Redmine(object):
    """ Redmine API class """

    def __init__(self, host, api_key=None, **options):
        """ Creates api client instance.

        :host: Full URL of redmine installation.
        :api_key: API key for Redmine. Can be obtained at http://<your_domain>/my/account
        """
        self.host = host.rstrip('/')
        self.api_key = api_key
        self.options = options

    @classmethod
    def get_ticket_id(cls, message):
        """ Returns list of ticket IDs, mentioned in a commit """
        return re.findall(r'#(?P<ticket_id>\d+)', message)

    def issue(self, issue_id):
        self.issue_id = issue_id
        return self

    def log_release_date(self, released_at, message=None):
        """ Log the date, when ticket was released

        :released_at: Date when this ticket was released into production.
        :message: Optional message to include as a note. Redmine likes Textile markup.
        """
        url = '%(host)s/issues/%(issue_id)s.json' % {'host': self.host, 'issue_id': self.issue_id}

        payload = {'issue': {
                    'custom_fields': [{
                         'id': self.options.get('custom_field_id'),
                         'value': released_at.strftime('%Y-%m-%d'),
                         'name': 'Released at'
                    }],
                  }}

        if message:
            payload['issue']['notes'] = message
        log.debug('Send message: %s', payload)
        response = requests.put(url, data=json.dumps(payload),
                                     headers={'X-Redmine-API-Key': self.api_key,
                                              'Content-Type': 'application/json'})

        if response.status_code == requests.codes.ok:
            return True
        else:
            log.error('Redmine update failed: [%s] %s' % (response.status_code, response.text))