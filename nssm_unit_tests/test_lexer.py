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
        self.assertIsInstance(tokens.eof, tokens.MiscToken,
                              'EOF must be MiscToken type.')
        # Furthermore, the index should be at EOF.
        self.assertEqual(len(test), lex_obj.index, 'Did not leave index at EOF')

    def testIdentifierActuallyReserveWord(self):
        """
        Ensures we parse reserve words correctly.
        """
        for rw in ('for', 'while', 'if', 'elif', 'else',
                   'continue', 'break', 'in', 'return'):
            output = [token for token in lex.Lexer(rw)]

            self.assertEqual(2, len(output), rw)
            self.assertIsInstance(output[0], tokens.ReserveWordToken, rw)
            self.assertEqual(rw, output[0].value, rw)
            self.assertIs(tokens.eof, output[1])

    def testIdentifierStartsWithAlpha(self):
        """
        Ensures we detect a single identifier when the string starts with an
        alpha.
        """
        test = 'hello_world'
        lex_obj = lex.Lexer(test)
        output = [token for token in lex_obj]
        self.assertEqual(2, len(output), f'Did not get two tokens. {output}')
        # First should be identifier token and read 'hello_world'
        self.assertIsInstance(output[0], tokens.IdentifierToken,
                              'Expected identifier token.')
        self.assertEqual(output[0].value, 'hello_world')
        # Last should be EOF
        self.assertIs(tokens.eof, output[1])

    def testIdentifierStartsWithUnderscore(self):
        """
        Ensures we detect a single identifier when the string starts with an
        underscore.
        """
        test = '_hello_world'
        lex_obj = lex.Lexer(test)
        output = [token for token in lex_obj]
        self.assertEqual(2, len(output), f'Did not get two tokens. {output}')
        # First should be identifier token and read '_hello_world'
        self.assertIsInstance(output[0], tokens.IdentifierToken,
                              'Expected identifier token.')
        self.assertEqual(output[0].value, '_hello_world')
        # Last should be EOF
        self.assertIs(output[1], tokens.eof)

    def testIdentifierWholeString(self):
        """
        Tests specifically all characters allowed in an identifier.
        """
        test = \
            '_1234567890$abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        lex_obj = lex.Lexer(test)
        output = [token for token in lex_obj]
        # Two tokens
        self.assertEqual(2, len(output), 'Did not get two tokens.')
        # First is identifier
        self.assertIsInstance(output[0], tokens.IdentifierToken,
                              'Expected identifier token.')
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
        self.assertIsInstance(output[0], tokens.IdentifierToken,
                              'Expected first token to be identifier')
        self.assertEqual('hel$0', output[0].value)
        self.assertIsInstance(output[1], tokens.IdentifierToken,
                              'Expected second token to be identifier')
        self.assertEqual('_world', output[1].value)
        self.assertIs(output[2], tokens.eof)

    def testIdentifierPrecededProceededBySpace(self):
        """Tests parsing a single identifier surrounded by spaces."""
        test = '  lorem_ip$um_dolor_$it_amet '
        lex_obj = lex.Lexer(test)
        output = [token for token in lex_obj]
        self.assertEqual(2, len(output))
        self.assertIsInstance(output[0], tokens.IdentifierToken)
        self.assertEqual('lorem_ip$um_dolor_$it_amet', output[0].value)
        self.assertIs(tokens.eof, output[1])

    def testEndOfStatement(self):
        """Tests detecting End Of Statement."""
        test = '\n\n;\n\n;'
        lex_obj = lex.Lexer(test)
        output = [token for token in lex_obj]

        self.assertEqual(7, len(output))
        for i, tok in enumerate(output):
            if i in range(0, 6):
                self.assertIs(tokens.eos, tok)
            else:
                self.assertIs(tokens.eof, tok)

    def testIdentifierThenEos(self):
        """
        Tests parsing an identifier and then an end-
        of-statement.
        """
        test = 'hello_world;'
        lex_obj = lex.Lexer(test)
        output = [token for token in lex_obj]

        self.assertEqual(3, len(output))
        self.assertIsInstance(output[0], tokens.IdentifierToken)
        self.assertIs(output[1], tokens.eos)
        self.assertIs(output[2], tokens.eof)

    def testBase2bInteger(self):
        """Tests parsing a base 2 integer"""
        test = '0b0010110100101'
        lex_obj = lex.Lexer(test)
        output = [token for token in lex_obj]

        self.assertEqual(2, len(output))
        self.assertIsInstance(output[0], tokens.DecimalToken)
        self.assertIsInstance(output[0].value, int)
        self.assertEqual(int(test, 2), output[0].value)
        self.assertIs(output[1], tokens.eof)

    def testBase2BInteger(self):
        """Tests parsing a base 2 integer"""
        test = '0B0010110100101'
        lex_obj = lex.Lexer(test)
        output = [token for token in lex_obj]

        self.assertEqual(2, len(output))
        self.assertIsInstance(output[0], tokens.DecimalToken)
        self.assertIsInstance(output[0].value, int)
        self.assertEqual(int(test, 2), output[0].value)
        self.assertIs(output[1], tokens.eof)

    def testBase2oInteger(self):
        """Tests parsing a base 8 integer"""
        test = '0o70062233'
        lex_obj = lex.Lexer(test)
        output = [token for token in lex_obj]

        self.assertEqual(2, len(output))
        self.assertIsInstance(output[0], tokens.DecimalToken)
        self.assertIsInstance(output[0].value, int)
        self.assertEqual(int(test, 8), output[0].value)
        self.assertIs(output[1], tokens.eof)

    def testBase8OInteger(self):
        """Tests parsing a base 8 integer"""
        test = '0O70062233'
        lex_obj = lex.Lexer(test)
        output = [token for token in lex_obj]

        self.assertEqual(2, len(output))
        self.assertIsInstance(output[0], tokens.DecimalToken)
        self.assertIsInstance(output[0].value, int)
        self.assertEqual(int(test, 8), output[0].value)
        self.assertIs(output[1], tokens.eof)

    def testBase10Integer(self):
        """Tests parsing a base 10 integer"""
        test = '1234'
        lex_obj = lex.Lexer(test)
        output = [token for token in lex_obj]

        self.assertEqual(2, len(output))
        self.assertIsInstance(output[0], tokens.DecimalToken)
        self.assertIsInstance(output[0].value, int)
        self.assertEqual(int(test), output[0].value)
        self.assertIs(output[1], tokens.eof)

    def testBase16xInteger(self):
        """Tests parsing a base 10 integer"""
        test = '0x1234FAABAAD99453'
        lex_obj = lex.Lexer(test)
        output = [token for token in lex_obj]

        self.assertEqual(2, len(output))
        self.assertIsInstance(output[0], tokens.DecimalToken)
        self.assertIsInstance(output[0].value, int)
        self.assertEqual(int(test, 16), output[0].value)
        self.assertIs(output[1], tokens.eof)

    def testBase16XInteger(self):
        """Tests parsing a base 16 integer"""
        test = '0X1234FAABAAD99453'
        lex_obj = lex.Lexer(test)
        output = [token for token in lex_obj]

        self.assertEqual(2, len(output))
        self.assertIsInstance(output[0], tokens.DecimalToken)
        self.assertIsInstance(output[0].value, int)
        self.assertEqual(int(test, 16), output[0].value)
        self.assertIs(output[1], tokens.eof)

    def testFloatPointValue(self):
        """Tests a float in format `.1234`"""
        test = '.12345'
        lex_obj = lex.Lexer(test)
        output = [token for token in lex_obj]

        self.assertEqual(2, len(output))
        self.assertIsInstance(output[0], tokens.RealToken)
        self.assertIsInstance(output[0].value, float)
        self.assertEqual(float(test), output[0].value)
        self.assertIs(output[1], tokens.eof)

    def testFloatNumPointValue(self):
        """Tests a float in format `0.1234`"""
        test = '1024.12345'
        lex_obj = lex.Lexer(test)
        output = [token for token in lex_obj]

        self.assertEqual(2, len(output))
        self.assertIsInstance(output[0], tokens.RealToken)
        self.assertIsInstance(output[0].value, float)
        self.assertEqual(float(test), output[0].value)
        self.assertIs(output[1], tokens.eof)

    def testFloatPointExpeValue(self):
        """Tests a float in format `.1234e123`"""
        test = '.12345e123'
        lex_obj = lex.Lexer(test)
        output = [token for token in lex_obj]

        self.assertEqual(2, len(output))
        self.assertIsInstance(output[0], tokens.RealToken)
        self.assertIsInstance(output[0].value, float)
        self.assertEqual(float(test), output[0].value)
        self.assertIs(output[1], tokens.eof)

    def testFloatPointExpEValue(self):
        """Tests a float in format `.1234E123`"""
        test = '.12345E123'
        lex_obj = lex.Lexer(test)
        output = [token for token in lex_obj]

        self.assertEqual(2, len(output))
        self.assertIsInstance(output[0], tokens.RealToken)
        self.assertIsInstance(output[0].value, float)
        self.assertEqual(float(test), output[0].value)
        self.assertIs(output[1], tokens.eof)

    def testFloatNumExpValue(self):
        """Tests a float in format `1234e123`"""
        test = '12345e123'
        lex_obj = lex.Lexer(test)
        output = [token for token in lex_obj]

        self.assertEqual(2, len(output))
        self.assertIsInstance(output[0], tokens.RealToken)
        self.assertIsInstance(output[0].value, float)
        self.assertEqual(float(test), output[0].value)
        self.assertIs(output[1], tokens.eof)

    def testFloatNumExpPlusValue(self):
        """Tests a float in format `1234E+123`"""
        test = '12345E+123'
        lex_obj = lex.Lexer(test)
        output = [token for token in lex_obj]

        self.assertEqual(2, len(output))
        self.assertIsInstance(output[0], tokens.RealToken)
        self.assertIsInstance(output[0].value, float)
        self.assertEqual(float(test), output[0].value)
        self.assertIs(output[1], tokens.eof)

    def testFloatNumExpMinusValue(self):
        """Tests a float in format `1234e-123`"""
        test = '12345e-123'
        lex_obj = lex.Lexer(test)
        output = [token for token in lex_obj]

        self.assertEqual(2, len(output))
        self.assertIsInstance(output[0], tokens.RealToken)
        self.assertIsInstance(output[0].value, float)
        self.assertEqual(float(test), output[0].value)
        self.assertIs(output[1], tokens.eof)

    def testFloatFullValue(self):
        """Tests a float in format `9876.1234E-123`"""
        test = '9876.1234e-567'
        lex_obj = lex.Lexer(test)
        output = [token for token in lex_obj]

        self.assertEqual(2, len(output))
        self.assertIsInstance(output[0], tokens.RealToken)
        self.assertIsInstance(output[0].value, float)
        self.assertEqual(float(test), output[0].value)
        self.assertIs(output[1], tokens.eof)

    def testOperators(self):
        """Tests correctly parsing all operators registered"""
        for op, tok in tokens.OperatorToken.operators.items():
            output = [token for token in lex.Lexer(op)]

            self.assertEqual(2, len(output), op)
            self.assertIsInstance(output[0], tokens.OperatorToken, op)
            self.assertIsInstance(output[0].value, str, op)
            self.assertIs(tok, output[0], op)
            self.assertIs(tokens.eof, output[1], op)
