import sys
from setuptools import setup
from setuptools.command.test import test as TestCommand

import releasedate


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = ['test_releasedate.py']
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest

        errno = pytest.main(self.test_args)
        sys.exit(errno)


setup(
    name='redmine-releasedate',
    version=releasedate.__version__,
    packages=['releasedate'],
    url='https://github.com/futurecolors/redmine-releasedate',
    install_requires=['requests', 'GitPython', 'Werkzeug', 'docopt'],
    tests_require=['pytest', 'httpretty==0.6.2', 'mock', 'sh'],
    cmdclass={'test': PyTest},
    license='MIT',
    author='Ilya Baryshev',
    author_email='baryhsev@gmail.com',
    description='Track when your features are shipped to production in Redmine.',
    long_description=open('README.rst').read() + '\n\n' + open('CHANGELOG.rst').read(),
    entry_points={
        'console_scripts': [
            'redmine-release-server = releasedate.server:main',
            'redmine-release = releasedate.ci:cli',
        ]
    }
)
