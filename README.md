# Jinja2-Linter

AVD Ecosystem - Jinja2 Linter

## Project Goals

Build a Jinja2 linter that will provide the following capabilities:

- Validate syntax according to [AVD style guide](https://avd.sh/en/latest/docs/contribution/style-guide.html)
- Develop extension that works with VSCode and potentially other IDEs i.e PyCharm
  - if supporting multiple IDEs adds too much complexity, support for VSCode will take priority
- Capability to run as a GitHub Action and used to enforce style in our CI pipeline

## Syntax and code style issues

| Code | Short Description | Description |
|------|-------------------|-------------|
| S0   | `jinja-syntax-error`            | Jinja2 syntax should be correct |
| S1   | `single-space-decorator`        | A single space shall be added between Jinja2 curly brackets and a variable's name |
| S2   | `operator-enclosed-by-spaces`   | When variables are used in combination with an operator, the operator shall be enclosed by space |
| S3   | `jinja-statements-indentation`  | Nested jinja code block shall follow next rules:<br>- All J2 statements must be enclosed by 1 space<br>- All J2 statements must be indented by 4 more spaces within jinja delimiter<br>- To close a control, end tag must have same indentation level |
| S4   | `jinja-statements-single-space` | Jinja statement should have a single space before and after |
| S5   | `jinja-statements-no-tabs`      | Indentation are 4 spaces and NOT tabulation |
| S6*  | `jinja-statements-delimiter`    | Jinja statements should not have {%- or {%+ or -%} as delimiters |
| S7   | `single-statement-per-line`     | Jinja statements should be on separate lines |
| V1   | `jinja-variable-lower-case`     | All variables shall use lower case |
| V2   | `jinja-variable-format`         | If variable is multi-words, underscore _ shall be used as a separator |

_*Deprecation Warning_: There was a typo from day 1 in the j2lint repo on
delim**i**ter. It was written delim**e**ter. The current code version has fixed the
typo but to ensure backward compatibility the old syntax is still supported.
It will be deprecated when j2lint is officially released.

## Getting Started

### Install with pip

To get started, you can use Python pip to install j2lint:

```bash
pip install git+https://github.com/aristanetworks/j2lint.git
```

### Git approach

To get started with j2lint code, clone the Jinja2 Linter project on your system:

```
git clone https://github.com/aristanetworks/j2lint.git
```

### Prerequisites

Python version 3.6+


### Creating the environment

1. Create a virtual environment and activate it

    ```bash
    python3 -m venv myenv
    source myenv/bin/activate
    ```

2. Install pip, jinja2 and jinja2-linter

    ```bash
    sudo apt-get install python3-pip
    pip3 install jinja2
    git clone https://github.com/aristanetworks/j2lint
    cd j2lint
    python setup.py install
    ```

## Running the linter

```bash
j2lint <path-to-directory-of-templates>
```

### Running the linter on a specific file

```bash
j2lint <path-to-directory-of-templates>/template.j2
```

### Listing linting rules

```bash
j2lint --list
```

### Running the linter with verbose linter error output

```bash
j2lint <path-to-directory-of-templates> --verbose
```

### Running the linter with logs enabled. Logs saved in jinja2-linter.log in the current directory

```bash
j2lint <path-to-directory-of-templates> --log
```

To enable debug logs, use both options:

```bash
j2lint <path-to-directory-of-templates> --log --debug
```

### Running the linter with JSON format for linter error output

```bash
j2lint <path-to-directory-of-templates> --json
```

### Ignoring rules

1. The --ignore option can have one or more of these values: syntax-error, single-space-decorator, filter-enclosed-by-spaces, jinja-statement-single-space, jinja-statements-indentation, no-tabs, single-statement-per-line, jinja-delimiter, jinja-variable-lower-case, jinja-variable-format.

2. If multiple rules are to be ignored, use the --ignore option along with rule descriptions separated by space.

    ```bash
    j2lint <path-to-directory-of-templates> --ignore <rule_description1> <rule_desc>
    ```

3. If one or more linting rules are to be ignored only for a specific jinja template file, add a Jinja comment at the top of the file. The rule can be disabled using the short description of the rule or the id of the rule.


    ```jinja2
    {# j2lint: disable=S6}

    # OR
    {# j2lint: disable=jinja-delimiter #}
    ```
4. Disabling multiple rules

    ```jinja2
    {# j2lint: disable=jinja-delimiter j2lint: disable=S1 #}
    ```

### Adding custom rules

1. Create a new rules directory under j2lint folder.
2. Add custom rule classes that are similar to classes in j2lint/rules directory.
3. Run the jinja2 linter using --rules-dir option

    ```bash
    j2lint <path-to-directory-of-templates> --rules_dir <custom-rules-directory>
    ```

> Note: This runs the custom linting rules in addition to the default linting rules.

### Running jinja2 linter help command

```bash
j2lint --help
```

### Running jinja2 linter on STDIN template. This option can be used with VS Code.

```bash
j2lint --stdin
```

### Using j2lint as a pre-commit-hook

1. Add j2lint pre-commit hook inside your repository in .pre-commit-config.yaml.
```bash
   - repo: https://github.com/aristanetworks/j2lint.git
     rev: <release_tag/sha>
     hooks:
       - id: j2lint
```

2. Run pre-commit -> ```pre-commit run --all-files ```

## Acknowledgments

This project is based on [salt-lint](https://github.com/warpnet/salt-lint) and [jinjalint](https://github.com/motet-a/jinjalint)
