# -*- coding: utf-8 -*-
import os
import subprocess
from unittest.mock import ANY

from pytest import fixture

from storyscript.Bundle import Bundle
from storyscript.Features import Features
from storyscript.Story import Story
from storyscript.parser import Parser


@fixture
def bundle(patch):
    return Bundle()


def test_bundle_init(bundle):
    assert bundle.stories == {}
    assert bundle.story_files == {}


def test_bundle_init_files():
    bundle = Bundle(story_files={'one.story': 'hello'})
    assert bundle.story_files == {'one.story': 'hello'}


def test_bundle_gitignores(patch):
    """
    Ensures gitignores uses can produce the list of ignored files.
    """
    patch.object(subprocess, 'run')
    subprocess.run().returncode = 0
    result = Bundle.gitignores()
    command = ['git', 'ls-files', '--others', '--ignored',
               '--exclude-standard']
    subprocess.run.assert_called_with(command, encoding='utf8',
                                      stderr=subprocess.DEVNULL,
                                      stdout=subprocess.PIPE)
    subprocess.run().stdout.split.assert_called_with('\n')
    assert result == subprocess.run().stdout.split()


def test_bundle_gitignores_failed(patch):
    """
    Test what happens when the gitignore command fails
    """
    patch.object(subprocess, 'run')
    subprocess.run().returncode = 1
    result = Bundle.gitignores()
    subprocess.run().stdout.split.assert_not_called()
    assert result == []


def test_bundle_ignores(patch):
    patch.object(os.path, 'isdir')
    patch.object(os, 'walk', return_value=[('root', [], ['one.story', 'two'])])
    result = Bundle.ignores('path')
    os.walk.assert_called_with('path')
    assert result == [os.path.join('root', 'one.story')]


def test_bundle_ignores_not_dir(patch):
    patch.many(os.path, ['relpath', 'isdir'])
    os.path.isdir.return_value = False
    result = Bundle.ignores('path')
    os.path.relpath.assert_called_with('path')
    assert result == [os.path.relpath()]


def test_bundle_filter_path(patch):
    patch.object(os.path, 'relpath')
    result = Bundle.filter_path(os.path.join('.', 'root'), 'one.story', [])
    os.path.relpath.assert_called_with(os.path.join('.', 'root', 'one.story'))
    assert result == os.path.relpath()


def test_bundle_filter_path_ignores():
    result = Bundle.filter_path(os.path.join('.', 'root'), 'one.story',
                                [os.path.join('root', 'one.story')])
    assert result is None


def test_bundle_parse_directory(patch, bundle):
    """
    Ensures parse_directory can parse a directory
    """
    patch.object(os, 'walk', return_value=[('root', [], ['one.story', 'two'])])
    patch.object(Bundle, 'gitignores')
    result = Bundle.parse_directory('dir')
    assert Bundle.gitignores.call_count == 1
    os.walk.assert_called_with('dir')
    assert result == [os.path.join('root', 'one.story')]


def test_bundle_parse_directory_gitignored(patch, bundle):
    """
    Ensures parse_directory does not return gitignored files
    """
    patch.object(os, 'walk', return_value=[(os.path.join('.', 'root'),
                                           [], ['one.story'])])
    patch.object(Bundle, 'gitignores')
    Bundle.gitignores.return_value = [os.path.join('root', 'one.story')]
    assert Bundle.parse_directory('dir') == []


def test_bundle_parse_directory_ignored_path(patch, bundle):
    patch.object(os, 'walk', return_value=[(os.path.join('.', 'root'),
                                           [], ['one.story'])])
    patch.many(Bundle, ['gitignores', 'ignores'])
    Bundle.gitignores.return_value = []
    Bundle.parse_directory('dir', ignored_path='ignored')
    Bundle.ignores.assert_called_with('ignored')


def test_bundle_from_path(patch):
    """
    Ensures Bundle.from_path can create a Bundle from a filepath
    """
    patch.object(os.path, 'isdir', return_value=False)
    patch.init(Bundle)
    patch.object(Bundle, 'load_story')
    result = Bundle.from_path('path')
    Bundle.load_story.assert_called_with('path')
    assert isinstance(result, Bundle)


def test_bundle_from_path_directory(patch):
    """
    Ensures Bundle.from_path can create a Bundle from a directory path
    """
    patch.object(os.path, 'isdir')
    patch.init(Bundle)
    patch.many(Bundle, ['load_story', 'parse_directory'])
    Bundle.parse_directory.return_value = ['one.story']
    Bundle.from_path('path')
    Bundle.parse_directory.assert_called_with('path', ignored_path=None)
    Bundle.load_story.assert_called_with('one.story')


def test_bundle_from_path_directory_ignored(patch):
    """
    Ensures Bundle.from_path accepts an ignored_path keyword argument
    """
    patch.object(os.path, 'isdir')
    patch.init(Bundle)
    patch.many(Bundle, ['load_story', 'parse_directory'])
    Bundle.from_path('path', ignored_path='ignored')
    Bundle.parse_directory.assert_called_with('path', ignored_path='ignored')


def test_bundle_load_story(patch, bundle):
    """
    Ensures Bundle.load_story can load a story
    """
    patch.init(Story)
    patch.init(Features)
    bundle.story_files['one.story'] = 'hello'
    result = bundle.load_story('one.story')
    Story.__init__.assert_called_with('hello', features=ANY)
    assert isinstance(Story.__init__.call_args[1]['features'], Features)
    assert isinstance(result, Story)


def test_bundle_load_story_not_read(patch, bundle):
    """
    Ensures Bundle.load_story reads a story before loading it
    """
    patch.init(Story)
    patch.object(Story, 'read')
    bundle.story_files = {}
    bundle.load_story('one.story')
    Story.read.assert_called_with('one.story')
    assert bundle.story_files['one.story'] == Story.read()


def test_bundle_find_stories(patch, bundle):
    """
    Ensures Bundle.find_stories returns the list of loaded stories
    """
    bundle.story_files = {'one.story': 'hello'}
    assert bundle.find_stories() == ['one.story']


def test_bundle_services(bundle):
    bundle.stories = {'a': {'services': ['one']}, 'b': {'services': ['two']}}
    result = bundle.services()
    assert result == ['one', 'two']


def test_bundle_services_no_duplicates(bundle):
    bundle.stories = {'a': {'services': ['one']}, 'b': {'services': ['one']}}
    result = bundle.services()
    assert result == ['one']


def test_bundle_parse(patch, bundle):
    parse = bundle.parse
    patch.many(Bundle, ['parse', 'load_story'])
    parse(['one.story'], None, lower=False)
    Bundle.load_story.assert_called_with('one.story')
    story = Bundle.load_story()
    assert bundle.stories['one.story'] == story.tree


def test_bundle_compile(mocker, patch, bundle):
    compile = bundle.compile
    patch.many(Bundle, ['compile', 'load_story'])
    patch.many(Story, ['parse'])

    compile(['one.story'], parser=None)
    Bundle.load_story.assert_called_with('one.story')

    story = Bundle.load_story()
    story.compile.assert_called()
    assert bundle.stories['one.story'] == story.compiled


def test_bundle_bundle(patch, bundle):
    patch.many(Bundle, ['find_stories', 'services', 'compile', 'parser'])
    result = bundle.bundle()
    Bundle.parser.assert_called_with(None)
    Bundle.compile.assert_called_with(Bundle.find_stories(),
                                      parser=Bundle.parser())
    expected = {'stories': bundle.stories, 'services': Bundle.services(),
                'entrypoint': Bundle.find_stories()}
    assert result == expected


def test_bundle_bundle_ebnf(patch, bundle):
    patch.many(Bundle, ['find_stories', 'services', 'compile', 'parser'])
    bundle.bundle(ebnf='ebnf')
    Bundle.parser.assert_called_with('ebnf')
    Bundle.compile.assert_called_with(Bundle.find_stories(),
                                      parser=Bundle.parser())


def test_bundle_bundle_trees(patch, bundle):
    patch.many(Bundle, ['find_stories', 'parse', 'parser'])
    result = bundle.bundle_trees()
    Bundle.parser.assert_called_with(None)
    Bundle.parse.assert_called_with(Bundle.find_stories(),
                                    parser=Bundle.parser(),
                                    lower=False)
    assert result == bundle.stories


def test_bundle_bundle_trees_ebnf(patch, bundle):
    patch.many(Bundle, ['find_stories', 'parse', 'parser'])
    bundle.bundle_trees(ebnf='ebnf')
    Bundle.parser.assert_called_with('ebnf')
    Bundle.parse.assert_called_with(Bundle.find_stories(),
                                    parser=Bundle.parser(),
                                    lower=False)


def test_bundle_lex(patch, bundle):
    """
    Ensures Bundle.lex can lex a bundle
    """
    patch.object(Story, 'from_file')
    patch.object(Bundle, 'find_stories', return_value=['story'])
    patch.object(Bundle, 'parser')
    result = bundle.lex()
    Story.from_file.assert_called_with('story', features=bundle.features)
    Bundle.parser.assert_called_with(None)
    Story.from_file().lex.assert_called_with(parser=Bundle.parser())
    assert result['story'] == Story.from_file().lex()


def test_bundle_lex_ebnf(patch, bundle):
    """
    Ensures Bundle.lex supports specifying an ebnf file
    """
    patch.object(Story, 'from_file')
    patch.object(Bundle, 'find_stories', return_value=['story'])
    patch.object(Bundle, 'parser')
    bundle.lex(ebnf='ebnf')
    Bundle.parser.assert_called_with('ebnf')
    Story.from_file().lex.assert_called_with(parser=Bundle.parser())


def test_bundle_bundle_lower(patch, bundle, magic):
    patch.many(Bundle, ['find_stories', 'parse', 'parser'])
    a_story = magic()
    bundle.stories = {'foo': a_story}
    bundle.bundle_trees(ebnf='ebnf', lower=True)
    Bundle.parser.assert_called_with('ebnf')
    Bundle.parse.assert_called_with(Bundle.find_stories(),
                                    parser=Bundle.parser(),
                                    lower=True)


def test_bundle_parser_default(patch, bundle):
    """
    Ensures Bundle.parser creates no new instance of the parser by default
    """
    patch.init(Parser)
    assert bundle.parser(None) is None
    Parser.__init__.assert_not_called()


def test_bundle_parser_ebnf(patch, bundle):
    """
    Ensures Bundle.parser creates a new instance of a parser for custom
    EBNF files
    """
    patch.init(Parser)
    result = bundle.parser(ebnf='ebnf')
    Parser.__init__.assert_called_with(ebnf='ebnf')
    assert isinstance(result, Parser)
