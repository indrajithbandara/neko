from unittest import TestCase
from nssm import tokens


class TestTokenMatch(TestCase):
    def aseq(self, tok: tokens.Token, v: str):
        self.assertIsNotNone(tok, 'Token was none.')
        self.assertIsNotNone(v, 'String value was none.')
        self.assertIsInstance(tok, tokens.Token, 'Token was not a Token.')
        self.assertEqual(tok.value, v)

    def test_logical_operators(self):
        self.aseq(tokens.gte, '>=')
        self.aseq(tokens.equal, '==')
        self.aseq(tokens.not_equal, '!=')
        self.aseq(tokens.lte, '<=')
        self.aseq(tokens.lt, '<')
        self.aseq(tokens.gt, '>')
        self.aseq(tokens.bang, '!')
        self.aseq(tokens.land, '&&')
        self.aseq(tokens.lor, '||')

    def test_bitwise_operators(self):
        self.aseq(tokens.bsr, '>>')
        self.aseq(tokens.bsl, '<<')
        self.aseq(tokens.tilde, '~')
        self.aseq(tokens.bor, '|')
        self.aseq(tokens.bxor, '^')
        self.aseq(tokens.band, '&')

    def test_mathematical_operators(self):
        self.aseq(tokens.plus, '+')
        self.aseq(tokens.minus, '-')
        self.aseq(tokens.times, '*')
        self.aseq(tokens.divide, '/')
        self.aseq(tokens.modulo, '%')
        self.aseq(tokens.power, '**')
        self.aseq(tokens.int_divide, '//')

    def test_assignment_bitwise_operators(self):
        self.aseq(tokens.bsr_ass, '>>=')
        self.aseq(tokens.bsl_ass, '<<=')
        self.aseq(tokens.bor_ass, '|=')
        self.aseq(tokens.bxor_ass, '^=')
        self.aseq(tokens.band_ass, '&=')

    def test_assignment_mathematical_operators(self):
        self.aseq(tokens.plus_ass, '+=')
        self.aseq(tokens.minus_ass, '-=')
        self.aseq(tokens.times_ass, '*=')
        self.aseq(tokens.divide_ass, '/=')
        self.aseq(tokens.modulo_ass, '%=')
        self.aseq(tokens.pow_ass, '**=')
        self.aseq(tokens.int_divide_ass, '//=')
        self.aseq(tokens.inc, '++')
        self.aseq(tokens.dec, '--')

    def test_misc_tokens(self):
        self.aseq(tokens.comma, ',')
        self.aseq(tokens.question, '?')
        self.aseq(tokens.colon, ':')
        self.aseq(tokens.lsquare, '[')
        self.aseq(tokens.rsquare, ']')
        self.aseq(tokens.lbrace, '{')
        self.aseq(tokens.rbrace, '}')
        self.aseq(tokens.lparen, '(')
        self.aseq(tokens.rparen, ')')









