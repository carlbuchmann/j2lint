"""collection.py - Class to create a collection of linting rules.
"""
import os
import sys

from j2lint.utils import load_plugins, is_rule_disabled
from j2lint.logger import logger


class RulesCollection:
    """RulesCollection class which checks the linting rules against a file.
    """

    def __init__(self, verbose=False):
        self.rules = []
        self.verbose = verbose

    def __iter__(self):
        return iter(self.rules)

    def __len__(self):
        return len(self.rules)

    def extend(self, more):
        """Extends list of rules

        Args:
            more (list): list of rules classes
        """
        self.rules.extend(more)

    def run(self, file_dict):
        """Runs the linting rules for given file

        Args:
            file_dict (dict): file path and file type

        Returns:
            list: list of linting errors found
        """
        text = ""
        errors = []
        warnings = []

        try:
            with open(file_dict['path'], mode='r', encoding="utf-8") as file:
                text = file.read()
        except IOError as error:
            print(f"WARNING: Couldn't open {file_dict['path']} - {error.strerror}"
                  , file=sys.stderr)
            return errors

        for rule in self.rules:
            if rule.ignore:
                logger.debug("Ignoring rule %s:%s for file %s",
                    rule.id, rule.short_description, file_dict['path'])
                continue
            if is_rule_disabled(text, rule):
                logger.debug("Skipping linting rule %s on file %s",
                    rule, file_dict['path'])
                continue

            logger.debug("Running linting rule %s on file %s",
                rule, file_dict['path'])
            rule_obj = rule()
            if rule in rule_obj.warn:
                warnings.extend(rule_obj.checklines(file_dict, text))
                warnings.extend(rule_obj.checkfulltext(file_dict, text))

            else:
                errors.extend(rule_obj.checklines(file_dict, text))
                errors.extend(rule_obj.checkfulltext(file_dict, text))

        return errors, warnings

    def __repr__(self):
        return "\n".join([repr(rule)
                          for rule in sorted(self.rules, key=lambda x: x.id)])

    @classmethod
    def create_from_directory(cls, rules_dir, ignore_rules, warn_rules):
        """Creates a collection from all rule modules

        Args:
            cls (Object): object of a rule class
            rules_dir (string): rules directory
            ignore_rules (list): list of rule descriptions to ignore

        Returns:
            list: a collection of rule objects
        """
        result = cls()
        result.rules = load_plugins(os.path.expanduser(rules_dir))
        # pylint: disable=fixme
        # FIXME: once the first version of j2lint is tagged and publish,
        #        remove the deprecated_short_description
        for rule in result.rules:
            if (
                rule.short_description in ignore_rules
                or rule.id in ignore_rules
                or (
                    hasattr(rule, "deprecated_short_description")
                    and rule.deprecated_short_description in ignore_rules
                )
            ):
                rule.ignore = True
            if (
                rule.short_description in warn_rules
                or rule.id in warn_rules
                or (
                    hasattr(rule, "deprecated_short_description")
                    and rule.deprecated_short_description in warn_rules
                )
            ):
                rule.warn.append(rule)
        logger.info(
            "Created collection from rules directory %s", rules_dir)
        return result
