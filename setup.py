#!/usr/bin/env python
# -*- coding: utf-8 -*-
import inspect
import io
import sys
from os import getenv, path

from setuptools import find_packages, setup
from setuptools.command.bdist_egg import bdist_egg as _bdist_egg
from setuptools.command.install import install as _install
from setuptools.command.sdist import sdist as _sdist

root_dir = path.dirname(__file__)


# Read a file and return its as a string
def read(file_name):
    return io.open(path.join(root_dir, file_name)).read()


name = 'storyscript'
version = None
release_version = None
# try loading the current version
try:
    result = {'__file__': path.join(root_dir, name, 'Version.py')}
    exec(read(path.join(name, 'Version.py')), result)
    version = result['version']
    release_version = result['release_version']
except FileNotFoundError:
    pass

description = read('README.md')
short_description = ('StoryScript is an high-level language that can be used '
                     'to orchestrate microservices in an algorithmic way.')

classifiers = [
    'Development Status :: 4 - Beta',
    'Environment :: Console',
    'Environment :: Plugins',
    'Intended Audience :: Developers',
    'Intended Audience :: System Administrators',
    'License :: OSI Approved :: MIT License',
    'Natural Language :: English',
    'Programming Language :: Python',
    'Programming Language :: Other Scripting Engines',
    'Topic :: Office/Business',
    'Topic :: Software Development :: Build Tools',
    'Topic :: Software Development :: Compilers'
]

requirements = [
    'click==7.0',
    'lark-parser>=0.6.5',
    'click-alias==0.1.1a2',
    'story-hub==0.0.4'
]

extras = [
    'sphinx',
    'guzzle-sphinx-theme'
]

###############################################################################
# Custom build steps
###############################################################################


def prepare_release(cwd, use_release):
    version_file = path.join(cwd, name, 'VERSION')
    if use_release:
        version_text = release_version
    else:
        version_text = version
    if path.isdir(path.dirname(version_file)):
        print(f'writing version({version_text}) -> {version_file}')
        with open(version_file, 'w') as f:
            f.write(version_text)


class Install(_install):
    def run(self):
        if not _install._called_from_setup(inspect.currentframe()):
            # The run function from setuptools.command.install doesn't detect
            # install cmd properly in the current setting of sub classing
            # Install and therefore we detect it here and do the right thing
            # for install command otherwise fall back to super class run for
            # the other cases.
            _install.run(self)
        else:
            _install.do_egg_install(self)
        self.execute(prepare_release, (self.install_lib, False),
                     msg='Preparing the installation')


class Sdist(_sdist):
    def make_release_tree(self, basedir, files):
        _sdist.make_release_tree(self, basedir, files)
        self.execute(prepare_release, (basedir, True),
                     msg='Building the source release')


class BdistEgg(_bdist_egg):
    def copy_metadata_to(self, egg_info):
        _bdist_egg.copy_metadata_to(self, egg_info)
        self.execute(prepare_release, (self.bdist_dir, True),
                     msg='Building the binary release')


class VerifyVersionCommand(_install):
    """Custom command to verify that the git tag matches our version"""
    description = 'verify that the git tag matches our version'

    def run(self):
        tag = getenv('CIRCLE_TAG')

        if tag != release_version:
            info = ('Git tag: {0} does not match the '
                    'version of this app: {1}').format(tag, release_version)
            sys.exit(info)


setup(name=name,
      version=release_version,
      description=short_description,
      long_description=description,
      long_description_content_type='text/markdown',
      classifiers=classifiers,
      download_url=('https://github.com/asyncy/storyscript/archive/'
                    f'{version}.zip'),
      keywords='',
      author='Asyncy',
      author_email='support@asyncy.com',
      url='http://storyscript.org',
      license='MIT',
      packages=find_packages(exclude=('build.*', 'tests', 'tests.*')),
      include_package_data=True,
      zip_safe=True,
      install_requires=requirements,
      extras_require={
          'docs': extras
      },
      python_requires='>=3.5',
      entry_points={
          'console_scripts': ['storyscript=storyscript.Cli:Cli.main']
      },
      cmdclass={
        'install': Install,
        'sdist': Sdist,
        'bdist_egg': BdistEgg,
        'verify': VerifyVersionCommand,
      })
