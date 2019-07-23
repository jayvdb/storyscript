# -*- coding: utf-8 -*-
from click import unstyle

from pytest import raises

from storyscript.Features import Features
from storyscript.Story import Story
from storyscript.exceptions.StoryError import StoryError


def run_story(text):
    features = Features(None)
    return Story(text, features).process()


def test_exceptions_service_name(capsys):
    with raises(StoryError) as e:
        run_story('al.pine echo')

    message = e.value.message()
    # test with coloring once, but we representing ANSI color codes is tricky
    lines = unstyle(message).splitlines()
    assert lines[0] == 'Error: syntax error in story at line 1, column 1'
    assert lines[2] == '1|    al.pine echo'
    assert lines[5] == "E0002: A service name can't contain `.`"


def test_exceptions_arguments_noservice(capsys):
    with raises(StoryError) as e:
        run_story('length:10')
    e.value.with_color = False
    lines = e.value.message().splitlines()
    assert lines[0] == 'Error: syntax error in story at line 1, column 1'
    assert lines[2] == '1|    length:10'
    assert lines[5] == 'E0003: You have defined an argument, but not a service'


def test_exceptions_variables_backslash(capsys):
    with raises(StoryError) as e:
        run_story('a/b = 0')
    e.value.with_color = False
    lines = e.value.message().splitlines()
    assert lines[0] == 'Error: syntax error in story at line 1, column 1'
    assert lines[2] == '1|    a/b = 0'
    assert lines[5] == ('E0061: Invalid path name: `a/b`. '
                        "Path names can't contain `/`")


def test_exceptions_variables_dash(capsys):
    with raises(StoryError) as e:
        run_story('a-b = 0')
    e.value.with_color = False
    lines = e.value.message().splitlines()
    assert lines[0] == 'Error: syntax error in story at line 1, column 1'
    assert lines[2] == '1|    a-b = 0'
    assert lines[5] == ('E0061: Invalid path name: `a-b`. '
                        "Path names can't contain `-`")


def test_exceptions_return_outside(capsys):
    with raises(StoryError) as e:
        run_story('return 0')
    e.value.with_color = False
    lines = e.value.message().splitlines()
    assert lines[0] == 'Error: syntax error in story at line 1, column 1'
    assert lines[2] == '1|    return 0'
    assert lines[5] == 'E0004: `return` is allowed only inside functions'


def test_exceptions_missing_value(capsys):
    with raises(StoryError) as e:
        run_story('a = ')
    e.value.with_color = False
    lines = e.value.message().splitlines()
    assert lines[0] == 'Error: syntax error in story at line 1, column 5'
    assert lines[2] == '1|    a = '
    assert lines[5] == 'E0007: Missing value after `=`'


def test_exceptions_file_not_found(capsys):
    with raises(StoryError) as e:
        Story.from_file('this-file-does-not-exist', Features(None))
    message = e.value.message()
    assert 'File `this-file-does-not-exist` not found at' in message


def test_exceptions_dollar(capsys):
    with raises(StoryError) as e:
        run_story('x = $')
    e.value.with_color = False
    lines = e.value.message().splitlines()
    assert lines[0] == 'Error: syntax error in story at line 1, column 5'
    assert lines[2] == '1|    x = $'
    assert lines[5] == 'E0041: `$` is not allowed here'


def test_exceptions_function_redeclared(capsys):
    with raises(StoryError) as e:
        run_story('function f1 returns int\n    return 42\n'
                  'function f1 returns int\n    return 42\n')
    e.value.with_color = False
    lines = e.value.message().splitlines()
    assert lines[0] == 'Error: syntax error in story at line 3, column 1'
    assert lines[2] == '3|    function f1 returns int'
    assert lines[5] == 'E0111: Function `f1` has already been declared'


def test_exceptions_block_expected_before(capsys):
    with raises(StoryError) as e:
        run_story('while true')
    e.value.with_color = False
    lines = e.value.message().splitlines()
    assert lines[0] == 'Error: syntax error in story at line 1, column 11'
    assert lines[2] == '1|    while true'
    assert lines[5] == 'E0045: An indented block is required to follow here'


def test_exceptions_block_expected_after(capsys):
    with raises(StoryError) as e:
        run_story('while true\na = 2')
    e.value.with_color = False
    lines = e.value.message().splitlines()
    assert lines[0] == 'Error: syntax error in story at line 2, column 1'
    assert lines[2] == '2|    a = 2'
    assert lines[5] == 'E0041: `a` is not allowed here'
