"""
Tests for j2lint.cli.py
"""
import logging
import os
import re
from unittest.mock import create_autospec, patch
from argparse import Namespace

import pytest

from j2lint.settings import settings
from j2lint.cli import sort_issues, sort_and_print_issues, create_parser, run, RULES_DIR
from j2lint.linter.error import LinterError

from .utils import does_not_raise, j2lint_default_rules_string


@pytest.fixture
def default_namespace():
    """
    Default ArgPase namespace for j2lint
    """
    return Namespace(
        files=[],
        ignore=[],
        warn=[],
        list=False,
        rules_dir=[RULES_DIR],
        verbose=False,
        debug=False,
        json=False,
        stdin=False,
        log=False,
        version=False,
        vv=False,
    )


@pytest.mark.parametrize(
    "argv, namespace_modifications",
    [
        (pytest.param([], {}, id="default")),
        pytest.param(
            ["--log", "-stdout", "-j", "-d", "-v", "--stdin", "--version"],
            {
                "debug": True,
                "vv": True,  # This is stdout
                "stdin": True,
                "version": True,
                "log": True,
                "json": True,
                "verbose": True,
            },
            id="set all debug flags",
        ),
    ],
)
def test_create_parser(default_namespace, argv, namespace_modifications):
    """
    Test j2lint.cli.create_parser

    the namespace_modifications is a dictionnary where key
    is one of the keys in the namespace and value is the value
    it should be overwritten to.

    This test only verifies that given a set of arguments on the
    cli, the parser returns the correct values in the Namespace
    """
    expected_namespace = default_namespace
    for key, value in namespace_modifications.items():
        setattr(expected_namespace, key, value)
    parser = create_parser()
    options = parser.parse_args(argv)
    assert options == expected_namespace


@pytest.mark.parametrize(
    "number_issues, issues_modifications, expected_sorted_issues_ids",
    [
        (0, {}, []),
        (1, {}, [("dummy.j2", "T0", 1, "test-rule-0")]),
        pytest.param(
            2,
            {},
            [
                ("dummy.j2", "T0", 1, "test-rule-0"),
                ("dummy.j2", "T1", 2, "test-rule-1"),
            ],
            id="sort-on-linenumber",
        ),
        pytest.param(
            2,
            {2: {"filename": "aaa.j2"}},
            [("aaa.j2", "T1", 2, "test-rule-1"), ("dummy.j2", "T0", 1, "test-rule-0")],
            id="sort-on-filename",
        ),
        pytest.param(
            2,
            {2: {"rule": {"id": "AA"}, "linenumber": 1}},
            [
                ("dummy.j2", "AA", 1, "test-rule-1"),
                ("dummy.j2", "T0", 1, "test-rule-0"),
            ],
            id="sort-on-rule-id",
        ),
    ],
)
def test_sort_issues(
    make_issues, number_issues, issues_modifications, expected_sorted_issues_ids
):
    """
    Test j2lint.cli.sort_issues

    the issues_modificartions is a dictionary that has the following
    structure:

      { <issue-index>: { <key>: <desired_value }

    the test will go over these modifications and apply them to the
    appropriate issues, apply the sort_issues method and verifies the
    ordering is correct
    """
    issues = make_issues(number_issues)
    # In the next step we apply modifications on the generated LinterErrors
    # if required
    for index, modification in issues_modifications.items():
        for key, value in modification.items():
            if isinstance(value, dict):
                nested_obj = getattr(issues[index - 1], key)
                for n_key, n_value in value.items():
                    setattr(nested_obj, n_key, n_value)
            else:
                setattr(issues[index - 1], key, value)
    sorted_issues = sort_issues(issues)
    sorted_issues_ids = [
        (issue.filename, issue.rule.id, issue.linenumber, issue.rule.short_description)
        for issue in sorted_issues
    ]
    assert sorted_issues_ids == expected_sorted_issues_ids


@pytest.mark.parametrize(
    "options, number_issues, issue_type, expected_output, expected_stdout",
    [
        pytest.param(
            Namespace(json=False), 0, "ERRORS", (0, {}), "", id="No issue - cli"
        ),
        pytest.param(
            Namespace(json=True), 0, "ERRORS", (0, {}), "", id="No issue - json"
        ),
        pytest.param(
            Namespace(json=False),
            1,
            "ERRORS",
            (1, {}),
            "\nJINJA2 LINT ERRORS\n************ File ERRORS\ndummy.j2:1 test rule 0 (test-rule-0)\n",
            id="One issue - cli",
        ),
        pytest.param(
            Namespace(json=True),
            1,
            "ERRORS",
            (
                1,
                {
                    "ERRORS": [
                        {
                            "filename": "dummy.j2",
                            "id": "T0",
                            "line": "dummy",
                            "linenumber": 1,
                            "message": "test rule 0",
                            "severity": "LOW",
                        }
                    ]
                },
            ),
            "",
            id="One issue - json",
        ),
    ],
)
def test_sort_and_print_issues(
    capsys,
    make_issues,
    options,
    number_issues,
    issue_type,
    expected_output,
    expected_stdout,
):
    """
    Test j2lint.cli.sort_and_print_issues

    The method is a bit of a mess to test as it relies heavily on the
    inputs being passed being correct (for instance if you pass the lint_warnings
    with an issue_type of ERROR, it will just print all teh warnings under error).

    This test hence just aims at verifying that the method prints correctly without
    any further checks.
    """
    # we need to make sure settings is correct to print the issues as JSON
    # TODO - this is bad practice to expect __repr__ to select the output
    # from settings.. to be fixed later..
    #
    # this is not reset between tests so need to reset it..
    if options.json:
        settings.output = "json"

    issues = {issue_type: make_issues(number_issues)}
    json_output = {}
    total_count, json_output = sort_and_print_issues(
        options, issues, issue_type, json_output
    )

    assert total_count == expected_output[0]
    assert json_output == expected_output[1]

    captured = capsys.readouterr()
    assert captured.out == expected_stdout


@pytest.mark.parametrize(
    "argv, expected_stdout, expected_stderr, expected_exit_code, expected_raise, number_errors, number_warnings",
    [
        pytest.param([], "", "HELP", 1, does_not_raise(), 0, 0, id="no input"),
        pytest.param(["-h"], "HELP", "", 0, pytest.raises(SystemExit), 0, 0, id="help"),
        pytest.param(
            ["-ver"],
            "Jinja2-Linter Version 0.1\n",
            "",
            0,
            does_not_raise(),
            0,
            0,
            id="version",
        ),
        pytest.param(
            ["--log", "tests/data/test.j2"],
            "Linting complete. No problems found.\n",
            "",
            0,
            does_not_raise(),
            0,
            0,
            id="log level INFO",
        ),
        pytest.param(
            ["-v", "tests/data/test.j2"],
            """
JINJA2 LINT ERRORS
************ File tests/data/test.j2
Linting rule: T0
Rule description: test rule 0
Error line: dummy.j2:1 dummy
Error message: test rule 0


JINJA2 LINT WARNINGS
************ File tests/data/test.j2
Linting rule: T0
Rule description: test rule 0
Error line: dummy.j2:1 dummy
Error message: test rule 0

Jinja2 linting finished with 1 issue(s) and 1 warning(s)
""",
            "",
            2,
            does_not_raise(),
            1,
            1,
            id="verbose, one error, one warning",
        ),
        pytest.param(
            ["-j", "tests/data/test.j2"],
            '{"ERRORS": [{"id": "T0", "message": "test rule 0", "filename": "dummy.j2", "linenumber": 1, "line": "dummy", "severity": "LOW"}], "WARNINGS": [{"id": "T0", "message": "test rule 0", "filename": "dummy.j2", "linenumber": 1, "line": "dummy", "severity": "LOW"}]}\n',
            "",
            2,
            does_not_raise(),
            1,
            1,
            id="json, one error, one warning",
        ),
        pytest.param(
            ["-l"],
            "DEFAULT_RULES",
            "",
            0,
            does_not_raise(),
            0,
            0,
            id="list rules",
        ),
        pytest.param(
            ["--vv", "--debug", "tests/data/test.j2"],
            "Linting complete. No problems found.\n",
            "",
            0,
            does_not_raise(),
            0,
            0,
            id="log level DEBUG",
        ),
        pytest.param(
            ["-stdout", "tests/data/test.j2"],
            "Linting complete. No problems found.\n",
            "",
            0,
            does_not_raise(),
            0,
            0,
            id="stdout / vv",
        ),
    ],
)
def test_run(
    capsys,
    caplog,
    j2lint_usage_string,
    make_issues,
    argv,
    expected_stdout,
    expected_stderr,
    expected_exit_code,
    expected_raise,
    number_errors,
    number_warnings,
):
    """
    Test the j2lint.cli.run method

    This test is a bit too complex and should probably be splitted out to test various
    functionalities

    the call is to test the various options of the main entry point, patching away inner
    methods when required. The id of the tests explains the intention.
    """
    if "-stdout" in argv or "--vv" in argv:
        caplog.set_level(logging.INFO)
    if "-d" in argv or "--debug" in argv:
        caplog.set_level(logging.DEBUG)
    # TODO this method needs to be split a bit as it has
    # too many responsability
    if expected_stdout == "HELP":
        expected_stdout = j2lint_usage_string
    if expected_stdout == "DEFAULT_RULES":
        expected_stdout = j2lint_default_rules_string()
    if expected_stderr == "HELP":
        expected_stderr = j2lint_usage_string
    with expected_raise:
        with patch("j2lint.cli.Runner.run") as mocked_runner_run, patch(
            "logging.disable"
        ) as mocked_logging_disable:
            errors = {"ERRORS": make_issues(number_errors)}
            warnings = {"WARNINGS": make_issues(number_warnings)}
            mocked_runner_run.return_value = (errors["ERRORS"], warnings["WARNINGS"])
            run_return_value = run(argv)
            captured = capsys.readouterr()
            if "-stdout" not in argv and "--vv" not in argv:
                assert captured.out == expected_stdout
                # Hmm - WHY - need to find why failing with stdout
                assert captured.err == expected_stderr
            else:
                assert expected_stdout in captured.out
            assert run_return_value == expected_exit_code
            if ("-stdout" in argv or "--vv" in argv) and (
                "-d" in argv or "--debug" in argv
            ):
                assert "DEBUG" in [record.levelname for record in caplog.records]


def test_run_stdin(capsys):
    """
    Test j2lint.cli.run when using stdin
    Note that the code is checking that this is not run from a tty

    A solution to run is something like:
    ```
    cat myfile.j2 | j2lint --stdin
    ```

    In this test, the isatty answer is mocked.
    """
    with patch("logging.disable") as mocked_logging_disable, patch(
        "sys.stdin"
    ) as patched_stdin, patch("os.unlink", side_effect=os.unlink) as mocked_os_unlink:
        patched_stdin.isatty.return_value = False
        patched_stdin.read.return_value = "{%set test=42 %}"
        run_return_value = run(["--log", "--stdin"])
        patched_stdin.isatty.assert_called_once()
        captured = capsys.readouterr()
        matches = re.match(
            r"\nJINJA2 LINT ERRORS\n\*\*\*\*\*\*\*\*\*\*\*\* File \/.*\n(\/.*.j2):1 Jinja statement should have a single space before and after: '{% statement %}' \(jinja-statements-single-space\)\nJinja2 linting finished with 1 issue\(s\) and 0 warning\(s\)\n",
            captured.out,
            re.MULTILINE,
        )
        assert matches is not None
        mocked_os_unlink.assert_called_with(matches.groups()[0])
        assert os.path.exists(matches.groups()[0]) == False
        assert run_return_value == 2
