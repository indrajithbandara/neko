from unittest import TestCase
from nssm import tokens
from nssm import lex


class TestLexer(TestCase):
    def testValidWhitespace(self):
        """Ensures we skip over all whitespace."""
        test = '\t \t \t \t'

        lex_obj = lex.Lexer(test)
        output = [token for token in lex_obj]

        # We should have only one token
        self.assertEqual(1, len(output), 'Did not get exactly 1 token.')
        # This token should be EOF
        self.assertIs(tokens.eof, output[0], 'Did not get EOF')
        # Furthermore, the index should be at EOF.
        self.assertEqual(len(test), lex_obj.index, 'Did not leave index at EOF')

    def testEof(self):
        """Ensures we detect EOF."""
        test = ''

        lex_obj = lex.Lexer(test)
        output = [token for token in lex_obj]
        # We should have only one token
        self.assertEqual(1, len(output), 'Did not get exactly 1 token.')
        # This token should be EOF
        self.assertIs(tokens.eof, output[0], 'Did not get EOF')
        self.assertIsInstance(tokens.eof, tokens.MiscToken, 'EOF must be MiscToken type.')
        # Furthermore, the index should be at EOF.
        self.assertEqual(len(test), lex_obj.index, 'Did not leave index at EOF')

    def testIdentifierStartsWithAlpha(self):
        """
        Ensures we detect a single identifier when the string starts with an alpha.
        """
        test = 'hello_world?'
        lex_obj = lex.Lexer(test)
        output = [token for token in lex_obj]
        self.assertEqual(2, len(output), 'Did not get two tokens. ' + str(output))
        # First should be identifier token and read 'hello_world'
        self.assertIsInstance(output[0], tokens.IdentifierToken, 'Expected identifier token.')
        self.assertEqual(output[0].value, 'hello_world')
        # Last should be EOF
        self.assertIs(tokens.eof, output[1])

    def testIdentifierStartsWithUnderscore(self):
        """
        Ensures we detect a single identifier when the string starts with an underscore.
        """
        test = '_hello_world'
        lex_obj = lex.Lexer(test)
        output = [token for token in lex_obj]
        self.assertEqual(2, len(output), 'Did not get two tokens. ' + str(output))
        # First should be identifier token and read '_hello_world'
        self.assertIsInstance(output[0], tokens.IdentifierToken, 'Expected identifier token.')
        self.assertEqual(output[0].value, '_hello_world')
        # Last should be EOF
        self.assertIs(output[1], tokens.eof)

    def testIdentifierWholeString(self):
        """
        Tests specifically all characters allowed in an identifier.
        """
        test = '_1234567890$abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        lex_obj = lex.Lexer(test)
        output = [token for token in lex_obj]
        # Two tokens
        self.assertEqual(2, len(output), 'Did not get two tokens.')
        # First is identifier
        self.assertIsInstance(output[0], tokens.IdentifierToken, 'Expected identifier token.')
        # Second is eof
        self.assertIs(output[1], tokens.eof, 'Expected EOF.')
        # First matches test input
        self.assertEqual(test, output[0].value)

    def testTwoIdentifiersSeparatedBySpace(self):
        """Tests two identifiers separated by a space."""
        test = 'hel$0 _world'
        lex_obj = lex.Lexer(test)
        output = [token for token in lex_obj]
        self.assertEqual(3, len(output), 'Expected three tokens.')
        self.assertIsInstance(output[0], tokens.IdentifierToken, 'Expected first token to be identifier')
        self.assertEqual('hel$0', output[0].value)
        self.assertIsInstance(output[1], tokens.IdentifierToken, 'Expected second token to be identifier')
        self.assertEqual('_world', output[1].value)
        self.assertIs(output[2], tokens.eof)
