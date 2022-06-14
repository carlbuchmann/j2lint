"""rule.py - Base class for all the lint rules with functions for mathching
             line and text based rule.
"""

from j2lint.utils import is_valid_file_type
from j2lint.linter.error import LinterError
from j2lint.logger import logger


class Rule:
    """Rule class which acts as a base class for rules with regex match
       functions.
    """
    id = None
    description = None
    ignore = False
    warn = []

    def __repr__(self):
        return self.id + ": " + self.description

    @classmethod
    def checktext(cls, file, text):
        """ default checktext method for each rule """

    @classmethod
    def check(cls, line):
        """ default check method for each rule """

    @staticmethod
    def is_valid_language(file):
        """Check if the file is a valid Jinja file

        Args:
            file (string): file path

        Returns:
            boolean: True if file extension is correct
        """

        if is_valid_file_type(file["path"]):
            return True
        return False

    def checklines(self, file, text):
        """Checks each line of file against the error regex

        Args:
            file (string): file path of the file to be checked
            text (string): file text of the same file

        Returns:
            list: list of issues in the given file
        """
        errors = []

        if not self.is_valid_language(file):
            logger.debug(
                "Skipping file %s. Linter does not support linting this file type", file)
            return errors

        for (index, line) in enumerate(text.split("\n")):
            if line.lstrip().startswith('#'):
                continue

            result = self.check(line)
            if not result:
                continue
            errors.append(LinterError(index+1, line, file['path'], self))
        return errors


    def checkfulltext(self, file, text):
        """Checks the entire file text against a lint rule

        Args:
            file (string): file path of the file to be checked
            text (string): file text of the same file

        Returns:
            list: list of issues in the given file
        """
        errors = []

        if not self.is_valid_language(file):
            logger.debug(
                "Skipping file %s. Linter does not support linting this file type", file)
            return errors

        results = self.checktext(file, text)

        if results is not None:
            for line, section, message in results:
                errors.append(LinterError(
                    line, section, file['path'], self, message))

        return errors
