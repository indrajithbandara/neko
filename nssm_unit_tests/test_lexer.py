import math

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
        """Ensures we parse reserve words correctly.
        """
        for rw in ('for', 'while', 'if', 'elif', 'else',
                   'continue', 'break', 'in', 'return'):
            output = [token for token in lex.Lexer(rw)]

            self.assertEqual(2, len(output), rw)
            self.assertIsInstance(output[0], tokens.ReserveWordToken, rw)
            self.assertEqual(rw, output[0].name, rw)
            self.assertEqual(rw, output[0].value, rw)
            self.assertIs(tokens.eof, output[1], rw)

        for sp_n, sp_v in {
                              'INF': math.inf,
                              'NaN': math.nan,
                              'true': True,
                              'false': False,
                              'null': None
                          }.items():
            output = [token for token in lex.Lexer(sp_n)]

            # Edge cases where tests may fail.
            # IEEE floating point integer spec specifies that NaN != NaN, so
            # obviously this test is going to bork here.
            self.assertEqual(2, len(output), str(output))
            self.assertIsInstance(output[0], tokens.ReserveWordToken, sp_n)

            self.assertEqual(sp_n, output[0].name, sp_n)
            if sp_n.lower() == 'inf':
                self.assertTrue(math.isinf(output[0].value), 'Not INF.')
            elif sp_n.lower() == 'nan':
                self.assertTrue(math.isnan(output[0].value), 'Not NaN')
            else:
                self.assertEqual(sp_v, output[0].value, sp_n)

            self.assertIs(tokens.eof, output[1], sp_n)

    def testIdentifierStartsWithAlpha(self):
        """Ensures we detect a single identifier when the string starts with an
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
        """Ensures we detect a single identifier when the string starts with an
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
        """Tests specifically all characters allowed in an identifier.
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
        """Tests two identifiers separated by a space.
        """
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
        """Tests parsing a single identifier surrounded by spaces.
        """
        test = '  lorem_ip$um_dolor_$it_amet '
        lex_obj = lex.Lexer(test)
        output = [token for token in lex_obj]
        self.assertEqual(2, len(output))
        self.assertIsInstance(output[0], tokens.IdentifierToken)
        self.assertEqual('lorem_ip$um_dolor_$it_amet', output[0].value)
        self.assertIs(tokens.eof, output[1])

    def testEndOfStatement(self):
        """Tests detecting End Of Statement.
        """
        test = '\n\n;\n\n;'
        lex_obj = lex.Lexer(test)
        output = [token for token in lex_obj]

        self.assertEqual(2, len(output))
        self.assertIs(tokens.eos, output[0])
        self.assertIs(tokens.eof, output[1])

    def testIdentifierThenEos(self):
        """Tests parsing an identifier and then an end-of-statement.
        """
        test = 'hello_world;'
        lex_obj = lex.Lexer(test)
        output = [token for token in lex_obj]

        self.assertEqual(3, len(output))
        self.assertIsInstance(output[0], tokens.IdentifierToken)
        self.assertIs(output[1], tokens.eos)
        self.assertIs(output[2], tokens.eof)

    def testBase2bInteger(self):
        """Tests parsing a base 2 integer
        """
        test = '0b0010110100101'
        lex_obj = lex.Lexer(test)
        output = [token for token in lex_obj]

        self.assertEqual(2, len(output))
        self.assertIsInstance(output[0], tokens.IntToken)
        self.assertIsInstance(output[0].value, int)
        self.assertEqual(int(test, 2), output[0].value)
        self.assertIs(output[1], tokens.eof)

    def testBase2BInteger(self):
        """Tests parsing a base 2 integer
        """
        test = '0B0010110100101'
        lex_obj = lex.Lexer(test)
        output = [token for token in lex_obj]

        self.assertEqual(2, len(output))
        self.assertIsInstance(output[0], tokens.IntToken)
        self.assertIsInstance(output[0].value, int)
        self.assertEqual(int(test, 2), output[0].value)
        self.assertIs(output[1], tokens.eof)

    def testBase2oInteger(self):
        """Tests parsing a base 8 integer
        """
        test = '0o70062233'
        lex_obj = lex.Lexer(test)
        output = [token for token in lex_obj]

        self.assertEqual(2, len(output))
        self.assertIsInstance(output[0], tokens.IntToken)
        self.assertIsInstance(output[0].value, int)
        self.assertEqual(int(test, 8), output[0].value)
        self.assertIs(output[1], tokens.eof)

    def testBase8OInteger(self):
        """Tests parsing a base 8 integer
        """
        test = '0O70062233'
        lex_obj = lex.Lexer(test)
        output = [token for token in lex_obj]

        self.assertEqual(2, len(output))
        self.assertIsInstance(output[0], tokens.IntToken)
        self.assertIsInstance(output[0].value, int)
        self.assertEqual(int(test, 8), output[0].value)
        self.assertIs(output[1], tokens.eof)

    def testBase10Integer(self):
        """Tests parsing a base 10 integer
        """
        test = '1234'
        lex_obj = lex.Lexer(test)
        output = [token for token in lex_obj]

        self.assertEqual(2, len(output))
        self.assertIsInstance(output[0], tokens.IntToken)
        self.assertIsInstance(output[0].value, int)
        self.assertEqual(int(test), output[0].value)
        self.assertIs(output[1], tokens.eof)

    def testBase16xInteger(self):
        """Tests parsing a base 10 integer
        """
        test = '0x1234FAABAAD99453'
        lex_obj = lex.Lexer(test)
        output = [token for token in lex_obj]

        self.assertEqual(2, len(output))
        self.assertIsInstance(output[0], tokens.IntToken)
        self.assertIsInstance(output[0].value, int)
        self.assertEqual(int(test, 16), output[0].value)
        self.assertIs(output[1], tokens.eof)

    def testBase16XInteger(self):
        """Tests parsing a base 16 integer
        """
        test = '0X1234FAABAAD99453'
        lex_obj = lex.Lexer(test)
        output = [token for token in lex_obj]

        self.assertEqual(2, len(output))
        self.assertIsInstance(output[0], tokens.IntToken)
        self.assertIsInstance(output[0].value, int)
        self.assertEqual(int(test, 16), output[0].value)
        self.assertIs(output[1], tokens.eof)

    def testFloatPointValue(self):
        """Tests a float in format `.1234`
        """
        test = '.12345'
        lex_obj = lex.Lexer(test)
        output = [token for token in lex_obj]

        self.assertEqual(2, len(output))
        self.assertIsInstance(output[0], tokens.RealToken)
        self.assertIsInstance(output[0].value, float)
        self.assertEqual(float(test), output[0].value)
        self.assertIs(output[1], tokens.eof)

    def testFloatNumPointValue(self):
        """Tests a float in format `0.1234`
        """
        test = '1024.12345'
        lex_obj = lex.Lexer(test)
        output = [token for token in lex_obj]

        self.assertEqual(2, len(output))
        self.assertIsInstance(output[0], tokens.RealToken)
        self.assertIsInstance(output[0].value, float)
        self.assertEqual(float(test), output[0].value)
        self.assertIs(output[1], tokens.eof)

    def testFloatPointExpeValue(self):
        """Tests a float in format `.1234e123`
        """
        test = '.12345e123'
        lex_obj = lex.Lexer(test)
        output = [token for token in lex_obj]

        self.assertEqual(2, len(output))
        self.assertIsInstance(output[0], tokens.RealToken)
        self.assertIsInstance(output[0].value, float)
        self.assertEqual(float(test), output[0].value)
        self.assertIs(output[1], tokens.eof)

    def testFloatPointExpEValue(self):
        """Tests a float in format `.1234E123`
        """
        test = '.12345E123'
        lex_obj = lex.Lexer(test)
        output = [token for token in lex_obj]

        self.assertEqual(2, len(output))
        self.assertIsInstance(output[0], tokens.RealToken)
        self.assertIsInstance(output[0].value, float)
        self.assertEqual(float(test), output[0].value)
        self.assertIs(output[1], tokens.eof)

    def testFloatNumExpValue(self):
        """Tests a float in format `1234e123`
        """
        test = '12345e123'
        lex_obj = lex.Lexer(test)
        output = [token for token in lex_obj]

        self.assertEqual(2, len(output))
        self.assertIsInstance(output[0], tokens.RealToken)
        self.assertIsInstance(output[0].value, float)
        self.assertEqual(float(test), output[0].value)
        self.assertIs(output[1], tokens.eof)

    def testFloatNumExpPlusValue(self):
        """Tests a float in format `1234E+123`
        """
        test = '12345E+123'
        lex_obj = lex.Lexer(test)
        output = [token for token in lex_obj]

        self.assertEqual(2, len(output))
        self.assertIsInstance(output[0], tokens.RealToken)
        self.assertIsInstance(output[0].value, float)
        self.assertEqual(float(test), output[0].value)
        self.assertIs(output[1], tokens.eof)

    def testFloatNumExpMinusValue(self):
        """Tests a float in format `1234e-123`
        """
        test = '12345e-123'
        lex_obj = lex.Lexer(test)
        output = [token for token in lex_obj]

        self.assertEqual(2, len(output))
        self.assertIsInstance(output[0], tokens.RealToken)
        self.assertIsInstance(output[0].value, float)
        self.assertEqual(float(test), output[0].value)
        self.assertIs(output[1], tokens.eof)

    def testFloatFullValue(self):
        """Tests a float in format `9876.1234E-123`
        """
        test = '9876.1234e-567'
        lex_obj = lex.Lexer(test)
        output = [token for token in lex_obj]

        self.assertEqual(2, len(output))
        self.assertIsInstance(output[0], tokens.RealToken)
        self.assertIsInstance(output[0].value, float)
        self.assertEqual(float(test), output[0].value)
        self.assertIs(output[1], tokens.eof)

    def testOperators(self):
        """Tests correctly parsing all operators registered
        """
        for op, tok in tokens.OperatorToken.operators.items():
            output = [token for token in lex.Lexer(op)]

            self.assertEqual(2, len(output), op)
            self.assertIsInstance(output[0], tokens.OperatorToken, op)
            self.assertIsInstance(output[0].value, str, op)
            self.assertIs(tok, output[0], op)
            self.assertIs(tokens.eof, output[1], op)

    def testEmptyString(self):
        """Tests parsing an empty string
        """
        test1 = '""'
        test2 = '\'\''
        output1 = [token for token in lex.Lexer(test1)]
        output2 = [token for token in lex.Lexer(test2)]

        for o in (output1, output2):
            ostr = str(o)
            self.assertEqual(2, len(o), ostr)
            self.assertIsInstance(o[0], tokens.StringToken, ostr)
            self.assertIs(o[1], tokens.eof, ostr)
            self.assertIsInstance(o[0].value, str, ostr)
            self.assertEqual(0, len(o[0].value), ostr)

    def testQuoteInString(self):
        """Tests parsing a string that contains quotation marks that are escaped
        """
        # These strings should evaluate to the same thing. One uses
        # double quotes in the string, and the other uses single quotes.
        test1 = '"\\\'\'\\"hello\\", how\\\'s everyone feeling today?"'
        test2 = "'\\'\\'\"hello\\\", how\\'s everyone feeling today?'"
        output11, output12 = [token for token in lex.Lexer(test1)]
        output21, output22 = [token for token in lex.Lexer(test2)]

        self.assertEqual(output12, output22)
        self.assertIs(output12, tokens.eof)

        # Used a docstring so I don't have to escape anything.
        exp_str = '''   ''"hello", how's everyone feeling today?     '''.strip()

        self.assertEqual(output11, output21)
        self.assertEqual(output11.value, exp_str)
        # Thank fuck this test works...

    def testBasicString(self):
        """Tests parsing a string that contains some characters or something.
        Also ensures both quotation types work.
        """

        # Double-quote string.
        test = '"I like shorts! They are comfy, and easy to wear!"'
        output = [token for token in lex.Lexer(test)]
        self.assertEqual(2, len(output), str(output))
        self.assertIs(output[1], tokens.eof)
        self.assertEqual(
            'I like shorts! They are comfy, and easy to wear!',
            output[0].value)

        # Single-quote string.
        test = "'I like shorts! They are comfy, and easy to wear!'"
        output = [token for token in lex.Lexer(test)]
        self.assertEqual(2, len(output), str(output))
        self.assertIs(output[1], tokens.eof)
        self.assertEqual(
            'I like shorts! They are comfy, and easy to wear!',
            output[0].value)

    def testNewLineInString(self):
        """Tests what happens when a raw newline appears in the string.
        It should be parsed normally as a newline, as this grammar allows
        strings to cross line boundaries.
        """
        test = '"hello world\nhow are you?"'
        output = [token for token in lex.Lexer(test)][0]
        self.assertEqual(test[1:-1], output.value)

    def testEscapesInString(self):
        """Tests the basic escape characters
        """
        test = '"\\a\\b\\f\\n\\r\\v\\\\"'
        expected = '''\a\b\f\n\r\v\\'''
        output = [token for token in lex.Lexer(test)][0]
        self.assertEqual(expected, output.value)

    def testUtfLiteral(self):
        """Tests some valid UTF-8 literals.
        """
        expected_cs = ['@', '?', '\N{ANGRY FACE}', '\N{OK HAND SIGN}', '\f']

        for c in expected_cs:
            # Gets the hexadecimal part, appends it onto '\u'
            hex_value = '\\u' + hex(ord(c))[2:]

            code = f'"The character is: {hex_value}."'
            expected = f'The character is: {c}.'

            output = [token for token in lex.Lexer(code)][0]
            self.assertEqual(expected, output.value, c)

    def testUtfNTag(self):
        """Tests out the python-style \\N{ABCDEFG} tag syntax (without the
        first backslash, of course).
        """
        tests = {
            '"\\N{ANGRY FACE}"': '\N{ANGRY FACE}',
            '"\\N{HEAVY BLACK HEART}"': '\N{HEAVY BLACK HEART}',
            '"\\N{SPACE}"': ' ',
            '"\\N{EURO SIGN}"': '€',
            '"\\N{superscript three}\\N{superscript one}"': '³¹',
            '"\\N{LEFT CURLY BRACKET}"': '{',
            '"\\N{LEFT-POINTING DOUBLE ANGLE QUOTATION MARK}"': '«',
            '"\\N{RIGHTWARDS ARROW}"': '→',
        }

        for input_expr, output_expr in tests.items():
            output = [token for token in lex.Lexer(input_expr)][0]
            self.assertEqual(output_expr, output.value, output.value)

    def testExampleCode(self):
        """Tests some code that might be remotely similar to what we hope to
        parse once the system is complete.
        """

        code = '''\
            find_math_stuff = (list) {
                mean = .0e1;
                median = list[len(list)/2];
                max_val = -INF;
                min_val = INF;
                
                for el in list {
                    mean += el;
                    if el < min_val {
                        min_val = el;
                    };
                    if el > max_val {
                        max_val = el;
                    };
                };
                mean /= len(list);
                
                print(mean, median, max_val, min_val);
            };
            
            find_math_stuff(1,2,3,4,5,6,7,8,9,10);
        '''

        output = tuple(token for token in lex.Lexer(code))
        expected_output = (
            # find_math_stuff = (list) {
            tokens.IdentifierToken('find_math_stuff'),
            tokens.ass,
            tokens.lparen,
            tokens.IdentifierToken('list'),
            tokens.rparen,
            tokens.lbrace,
            # ....mean = 0;
            tokens.IdentifierToken('mean'),
            tokens.ass,
            tokens.RealToken(0.0),
            tokens.eos,
            # ....median = list[len(list)/2];
            tokens.IdentifierToken('median'),
            tokens.ass,
            tokens.IdentifierToken('list'),
            tokens.lsquare,
            tokens.IdentifierToken('len'),
            tokens.lparen,
            tokens.IdentifierToken('list'),
            tokens.rparen,
            tokens.divide,
            tokens.IntToken(2),
            tokens.rsquare,
            tokens.eos,
            # ....max_val = -INF;
            tokens.IdentifierToken('max_val'),
            tokens.ass,
            tokens.minus,
            tokens.inf_rw,
            tokens.eos,
            # ....min_val = INF;
            tokens.IdentifierToken('min_val'),
            tokens.ass,
            tokens.inf_rw,
            tokens.eos,
            # ....for el in list {
            tokens.for_rw,
            tokens.IdentifierToken('el'),
            tokens.in_rw,
            tokens.IdentifierToken('list'),
            tokens.lbrace,
            # ........mean += el;
            tokens.IdentifierToken('mean'),
            tokens.plus_ass,
            tokens.IdentifierToken('el'),
            tokens.eos,
            # ........if el < min_val {
            tokens.if_rw,
            tokens.IdentifierToken('el'),
            tokens.lt,
            tokens.IdentifierToken('min_val'),
            tokens.lbrace,
            # ............min_val = el;
            tokens.IdentifierToken('min_val'),
            tokens.ass,
            tokens.IdentifierToken('el'),
            tokens.eos,
            # ........}
            tokens.rbrace,
            tokens.eos,
            # ........if el > max_val {
            tokens.if_rw,
            tokens.IdentifierToken('el'),
            tokens.gt,
            tokens.IdentifierToken('max_val'),
            tokens.lbrace,
            # ............max_val = el;
            tokens.IdentifierToken('max_val'),
            tokens.ass,
            tokens.IdentifierToken('el'),
            tokens.eos,
            # ........}
            tokens.rbrace,
            tokens.eos,
            # ....}
            tokens.rbrace,
            tokens.eos,
            # ....mean /= len(list);
            tokens.IdentifierToken('mean'),
            tokens.divide_ass,
            tokens.IdentifierToken('len'),
            tokens.lparen,
            tokens.IdentifierToken('list'),
            tokens.rparen,
            tokens.eos,
            # ....print(mean, median, max_val, min_val);
            tokens.IdentifierToken('print'),
            tokens.lparen,
            tokens.IdentifierToken('mean'),
            tokens.comma,
            tokens.IdentifierToken('median'),
            tokens.comma,
            tokens.IdentifierToken('max_val'),
            tokens.comma,
            tokens.IdentifierToken('min_val'),
            tokens.rparen,
            tokens.eos,
            # }
            tokens.rbrace,
            tokens.eos,
            # find_math_stuff(1,2,3,4,5,6,7,8,9,10);
            tokens.IdentifierToken('find_math_stuff'),
            tokens.lparen,
            tokens.IntToken(1),
            tokens.comma,
            tokens.IntToken(2),
            tokens.comma,
            tokens.IntToken(3),
            tokens.comma,
            tokens.IntToken(4),
            tokens.comma,
            tokens.IntToken(5),
            tokens.comma,
            tokens.IntToken(6),
            tokens.comma,
            tokens.IntToken(7),
            tokens.comma,
            tokens.IntToken(8),
            tokens.comma,
            tokens.IntToken(9),
            tokens.comma,
            tokens.IntToken(10),
            tokens.rparen,
            tokens.eos,
            tokens.eof
        )

        print(*[repr(token) for token in output], sep='\n')
        self.assertEqual(len(expected_output), len(output))

        for i in range(0, len(output)):
            expected = expected_output[i]
            actual = output[i]
            self.assertEqual(expected, actual, f'Token {i}')
