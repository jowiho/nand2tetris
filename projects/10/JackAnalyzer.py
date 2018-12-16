#!/usr/bin/python3

import glob, io, os, re, sys

class TokenType:
	NONE = 'none'
	KEYWORD = 'keyword'
	SYMBOL = 'symbol'
	INT_CONST = 'integerConstant'
	STR_CONST = 'stringConstant'
	IDENTIFIER = 'identifier'

class JackTokenizer:
	digits = '0123456789'
	symbols = r'{}()[].,;+-*/&|<>=~'
	keywords = ['class', 'constructor', 'function', 'method', 'field', 'static', 'var', 'int', 'char', 'boolean', 'void', 'true', 'false', 'null', 'this', 'let', 'do', 'if', 'else', 'while', 'return']

	def __init__(self, filename):
		with open(filename, "r") as input_file:
			self.input = input_file.read()
		self.pos = 0
		self.token_type = TokenType.NONE

	def have_token(self):
		return self.token_type != TokenType.NONE

	def get_token(self):
		return self.token

	def get_token_type(self):
		return self.token_type

	def advance(self):
		self._moveToNextToken()
		c = self._peek()
		if c == False:
			self.token = False
			self.token_type = TokenType.NONE
		elif c == '"':
			self._read_string_constant()
		elif self.symbols.find(c) >= 0:
			self._read_symbol()
		elif re.match('[0-9]', c):
			self._read_int_constant()
		elif re.match('[a-zA-Z]', c):
			self.token = self._read_up_to('[^a-zA-Z0-9_]')
			self.token_type = TokenType.KEYWORD if self.token in self.keywords else TokenType.IDENTIFIER
		else:
			raise Exception("Unexpected character: '" + c + "'")
		return self.token_type != TokenType.NONE

	def _moveToNextToken(self):
		while self.pos < len(self.input):
			c = self.input[self.pos]
			if c.isspace():
				self.pos += 1
			elif c == '/' and self._peek(1) == '/':
				# Single line // comment
				self._read_up_to('\n')
			elif c == '/' and self._peek(1) == '*':
				# Block /* comment */
				self._skip_block_comment()
			else:
				return

	def _read_string_constant(self):
		self._read_char() # Skip opening quotes
		self.token_type = TokenType.STR_CONST
		self.token = self._read_up_to('"')
		self._read_char() # Skip closing quotes

	def _read_int_constant(self):
		self.token_type = TokenType.INT_CONST
		self.token = int(self._read_up_to('[^0-9]'))

	def _read_symbol(self):
		self.token_type = TokenType.SYMBOL
		self.token = self._read_char()

	# Skip /* Block comment */
	def _skip_block_comment(self):
		self.pos += 2 # Skip /*
		self._read_up_to(r'\*')
		self.pos += 1 # Skip *
		while self._peek() != '/':
			self._read_up_to(r'\*')
			self.pos += 1
		self.pos += 1

	def _peek(self, ahead = 0):
		return self.input[self.pos + ahead] if self.pos < len(self.input) else False

	def _read_char(self):
		c = self.input[self.pos]
		self.pos += 1
		return c

	def _read_up_to(self, regex):
		text = ''
		while self.pos < len(self.input):
			if re.match(regex, self._peek()):
				break
			text += self._read_char()
		return text

def escapeXml(xml):
	return str(xml).replace('&', '&amp;').replace('>', '&gt;').replace('<', '&lt;')

class CompilationEngine:
	def __init__(self, tokenizer):
		self.tokenizer = tokenizer

	def compile(self):
		print('<tokens>')
		while self.tokenizer.advance():
			print('<{0}> {1} </{0}>'.format(self.tokenizer.get_token_type(), escapeXml(self.tokenizer.get_token())))
		print('</tokens>')


def analyze_file(jack_filename):
	jack_filename = os.path.splitext(jack_filename)[0] + ".jack"
	tokenizer = JackTokenizer(jack_filename)
	CompilationEngine(tokenizer).compile()

def main(argv):
	if len(argv) == 1 and os.path.isdir(argv[0]):
		for file in glob.glob(argv[0] + "/*.jack"):
			analyze_file(file)
	elif len(argv) == 1 and os.path.splitext(argv[0])[1] == ".jack":
		analyze_file(argv[0])
	else:
		print("Usage: JackAnalyzer.py <filename>.jack | <directory>")
		sys.exit(1)

if __name__ == '__main__':
    main(sys.argv[1:])
