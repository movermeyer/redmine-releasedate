# coding: utf-8
import logging
import datetime
import itertools

import git


log = logging.getLogger(__name__)


class GitRepo(object):
    def __init__(self, path):
        self._repo = git.Repo(path)

    def commits_log(self, obj1, obj2):
        """ Get commits between two tags/branches, etc"""
        return self._repo.iter_commits(rev='%(obj1)s..%(obj2)s' % {'obj1': obj1, 'obj2': obj2})

    def commit_messages(self, obj1, obj2):
        """ Get messages between two tags/branches, etc"""
        return itertools.imap(lambda commit: commit.message, self.commits_log(obj1, obj2))

    def tag_date(self, tag_name):
        tag = self._repo.tags[tag_name]
        return datetime.datetime.fromtimestamp(tag.tag.tagged_date)