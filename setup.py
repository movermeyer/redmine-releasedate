from setuptools import setup
from setuptools.command.test import test as TestCommand
import sys


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest

        errno = pytest.main(self.test_args)
        sys.exit(errno)


setup(
    name='redmine-releasedate',
    version='0.1',
    packages=['releasedate'],
    url='https://github.com/futurecolors/redmine-releasedate',
    requires=['requests', 'GitPython', 'werkzeug'],
    tests_require=['pytest', 'httpretty', 'mock', 'sh'],
    cmdclass={'test': PyTest},
    license='MIT',
    author='Ilya Baryshev',
    author_email='baryhsev@gmail.com',
    description='Track when your features are shipped to production in Redmine.',
    entry_points={
        'console_scripts': [
            'redmine-release-server = releasedate.server:run',
            'redmine-release = releasedate.jenkins:run',
    ]}
)
