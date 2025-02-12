"""node.py - Class node for creating a parse tree for jinja statements and
             checking jinja statement indentation.
"""
from j2lint.linter.indenter.statement import JinjaStatement, JINJA_STATEMENT_TAG_NAMES
from j2lint.linter.error import JinjaLinterError, JinjaBadIndentationError
from j2lint.utils import flatten, get_tuple, delimit_jinja_statement
from j2lint.logger import logger

BEGIN_TAGS = [item[0] for item in JINJA_STATEMENT_TAG_NAMES]
END_TAGS = [item[-1] for item in JINJA_STATEMENT_TAG_NAMES]
MIDDLE_TAGS = list(flatten([[i[1:-1] for i in JINJA_STATEMENT_TAG_NAMES]]))

INDENT_SHIFT = 4
DEFAULT_WHITESPACES = 1
BLOCK_START_INDENT = 0
JINJA_START_DELIMITERS = ['{%-', '{%+']

jinja_node_stack = []
jinja_delimiter_stack = []


class Node:
    """Node class which represents a jinja file as a tree
    """

    statement = None
    tag = None
    node_start = 0
    node_end = 0
    children = []
    expected_indent = 0

    def create_node(self, line, line_no, indent_level=0):
        """Initializes a Node class object

        Args:
            line (string): line to create node for
            line_no (int): line number
            indent_level (int, optional): expected indentation level. Defaults to 0.

        Returns:
            Node: new Node class object
        """
        # pylint: disable = fixme
        # FIXME - this should just be an __init__
        node = Node()
        statement = JinjaStatement(line)
        node.statement = statement
        node.tag = statement.words[0]
        node.node_start = line_no
        node.node_end = line_no
        node.expected_indent = indent_level
        node.parent = self
        return node

    def create_indentation_error(self, node, message):
        """Creates indentation error tuple

        Args:
            node (Node): Node class object to create error for
            message (string): error message for the line

        Returns:
            tuple: tuple representing the indentation error
        """
        # pylint: disable = fixme
        # FIXME - why are we passing both self and node???
        return (node.statement.start_line_no,
                delimit_jinja_statement(node.statement.line,
                                        node.statement.start_delimiter,
                                        node.statement.end_delimiter),
                message)

    def check_indent_level(self, result, node):
        """check if the actual and expected indent level for a line match

        Args:
            result (list): list of tuples of indentation errors
            node (Node): Node object for which to check the level is correct
        """
        actual = node.statement.begin
        if len(jinja_node_stack) and jinja_node_stack[0].statement.start_delimiter in JINJA_START_DELIMITERS:
            BLOCK_START_INDENT = 1
        elif node.expected_indent == 0 and node.statement.start_delimiter in JINJA_START_DELIMITERS:
            BLOCK_START_INDENT = 1
        else:
            BLOCK_START_INDENT = 0

        if node.statement.start_delimiter in JINJA_START_DELIMITERS:
            expected = node.expected_indent + BLOCK_START_INDENT
        else:
            expected = node.expected_indent + DEFAULT_WHITESPACES + BLOCK_START_INDENT
        if actual != expected:
            message = "Bad Indentation, expected %d, got %d" % (
                expected, actual)
            error = self.create_indentation_error(node, message)
            result.append(error)
            logger.debug(error)

    def check_indentation(self, result, lines, line_no=0, indent_level=0):
        """Checks indentation for a list of lines

        Args:
            result (list): list of indentation error tuples
            lines (list): lines which are to be checked for indentation
            line_no (int, optional):  the current lines number being evaluated.
                                      Defaults to 0.
            indent_level (int, optional): the expected indent level for the
                                          current line. Defaults to 0.

        Raises:
            JinjaLinterError: Raises error if the text file has jinja tags
                              which are not supported by this indenter

        Returns:
            list: updates the 'result' list argument with indentation errors
        """
        while line_no < len(lines):
            line = lines[line_no]
            node = self.create_node(line, line_no, indent_level)
            if node.tag in BEGIN_TAGS:
                jinja_node_stack.append(node)
                self.children.append(node)
                line_no = node.check_indentation(
                    result, lines, line_no + 1, indent_level + INDENT_SHIFT)
                self.check_indent_level(result, node)
                continue
            elif node.tag in END_TAGS:
                if ('end' + jinja_node_stack[-1].tag) == node.tag:
                    if len(jinja_node_stack) and jinja_node_stack[-1] != self:
                        del node
                        return line_no
                    matchnode = jinja_node_stack[-1]
                    matchnode.node_end = line_no
                    node.node_end = line_no
                    node.expected_indent = matchnode.expected_indent
                    self.parent.children.append(node)
                    if matchnode == self:
                        line_no = line_no + 1
                        self.check_indent_level(result, node)
                        jinja_node_stack.pop()
                        return line_no
                message = "Tag is out of order '{}'".format(node.tag)
                error = self.create_indentation_error(node, message)
                result.append(error)
                raise JinjaLinterError(
                    "Tag is out of order '{}'".format(node.tag))
            elif node.tag in MIDDLE_TAGS:
                begin_tag_tuple = get_tuple(
                    JINJA_STATEMENT_TAG_NAMES, jinja_node_stack[-1].tag)
                if node.tag in begin_tag_tuple:
                    if jinja_node_stack[-1] != self:
                        del node
                        return line_no
                    matchnode = jinja_node_stack[-1]
                    node.node_end = line_no
                    node.expected_indent = matchnode.expected_indent
                    indent_level = node.expected_indent
                    matchnode.parent.children.append(node)
                    node.parent = matchnode.parent
                    line_no = node.check_indentation(
                        result, lines, line_no + 1, indent_level + INDENT_SHIFT)
                    self.check_indent_level(result, node)
                    continue
                else:
                    message = "Unsupported tag '%s' found" % (node.tag)
                    error = self.create_indentation_error(node, message)
                    result.append(error)
                    raise JinjaLinterError(
                        "Unsupported tag '%s' found" % (node.tag))
            else:
                self.children.append(node)
                line_no = line_no + 1
                self.check_indent_level(result, node)
                continue
