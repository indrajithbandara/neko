from unittest import TestCase
from nssm import tokens
from nssm import lex
from nssm import ex


class TestLexer(TestCase):
    def testValidWhitespace(self):
        """Ensures we skip over all whitespace."""
        test = '\t \t \t \t'

        lex_obj = lex.Lexer(test)
        output = [token for token in lex_obj]

        # We should have only one token
        self.assertEqual(len(output), 1, 'Did not get exactly 1 token.')
        # This token should be EOF
        self.assertIs(output[0], tokens.eof, 'Did not get EOF')
        # Furthermore, the index should be at EOF.
        self.assertEqual(len(test), lex_obj.index, 'Did not leave index at EOF')

    def testEof(self):
        """Ensures we detect EOF."""
        test = ''

        lex_obj = lex.Lexer(test)
        output = [token for token in lex_obj]
        # We should have only one token
        self.assertEqual(len(output), 1, 'Did not get exactly 1 token.')
        # This token should be EOF
        self.assertIs(output[0], tokens.eof, 'Did not get EOF')
        # Furthermore, the index should be at EOF.
        self.assertEqual(len(test), lex_obj.index, 'Did not leave index at EOF')

