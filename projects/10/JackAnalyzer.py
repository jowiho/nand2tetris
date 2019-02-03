#!/usr/bin/python3

import glob, os, re, sys

# Set to True to only output tokens (project 10 stage 1)
# Set to False to output parse tree (project 10 stage 2)
tokenize_only = False

class TokenType:
	KEYWORD = 'keyword'
	SYMBOL = 'symbol'
	INT_CONST = 'integerConstant'
	STR_CONST = 'stringConstant'
	IDENTIFIER = 'identifier'

class JackTokenizer:
	tokens = [
		{
			'type': TokenType.STR_CONST,
			're': r'"(.*?)"'
		},
		{
			'type': TokenType.INT_CONST,
			're': r'([0-9]+)'
		},
		{
			'type': TokenType.SYMBOL,
			're': r'([{}()[\]\.,;+\-\*/&|<>=~])'
		},
		{
			'type': TokenType.KEYWORD,
			're': r'\b(class|constructor|function|method|field|static|var|int|char|boolean|void|true|false|null|this|let|do|if|else|while|return)\b'
		},
		{
			'type': TokenType.IDENTIFIER,
			're': r'([a-zA-Z_][a-zA-Z_0-9]*)'
		}
	]

	def __init__(self, filename):
		with open(filename, "r") as input_file:
			self.input = input_file.read()
		self.pos = 0

	def get_token(self):
		return self.token

	def get_token_type(self):
		return self.token_type

	def advance(self):
		whitespace_or_comments = re.match(r'(\s+|//.*?\n|/\*.*?\*/)+', self.input[self.pos:], re.DOTALL)
		if whitespace_or_comments:
			self.pos += len(whitespace_or_comments.group(0))

		if self.pos >= len(self.input):
			return False
		else:
			for token in self.tokens:
				m = re.match(token['re'], self.input[self.pos:])
				if m:
					self.token_type = token['type']
					self.token = m.group(1)
					self.pos += len(m.group(0))
					return True
			raise Exception("Unexpected token: " + self.input[self.pos:])

def escapeXml(xml):
	return str(xml).replace('&', '&amp;').replace('>', '&gt;').replace('<', '&lt;')

class CompilationEngine:
	types = ['int', 'char', 'boolean']
	keyword_constants = ['true', 'false', 'null', 'this']
	operators = ['+', '-', '*', '/', '&', '|', '<', '>', '=']
	unary_ops = ['-', '~']

	def __init__(self, tokenizer):
		self.tokenizer = tokenizer

	def compile(self):
		if tokenize_only:
			print('<tokens>')
			while self.tokenizer.advance():
					print('<{0}> {1} </{0}>'.format(self.tokenizer.get_token_type(), escapeXml(self.tokenizer.get_token())))
			print('</tokens>')
		else:
			self.tokenizer.advance()
			self.compile_class()

	def compile_class(self):
		print('<class>')
		self.eat(TokenType.KEYWORD, 'class')
		self.eat(TokenType.IDENTIFIER)
		self.eat(TokenType.SYMBOL, '{')
		while self.token() == 'static' or self.token() == 'field':
			self.compile_class_var_dec()
		while self.token() == 'constructor' or self.token() == 'function' or self.token() == 'method':
			self.compile_subroutine_dec()
		self.eat(TokenType.SYMBOL, '}')
		print('</class>')

	def compile_class_var_dec(self):
		print('<classVarDec>')
		self.eat(TokenType.KEYWORD)        # static|field
		self.eat_type()
		self.eat(TokenType.IDENTIFIER)     # name
		while self.token_type() == TokenType.SYMBOL and self.token() == ',':
			self.eat(TokenType.SYMBOL, ',')
			self.eat(TokenType.IDENTIFIER) # name
		self.eat(TokenType.SYMBOL, ';')
		print('</classVarDec>')

	def compile_subroutine_dec(self):
		print('<subroutineDec>')
		self.eat(TokenType.KEYWORD)        # constructor|function|method
		self.eat_type()
		self.eat(TokenType.IDENTIFIER)     # name
		self.eat(TokenType.SYMBOL, '(')
		self.compile_parameter_list()
		self.eat(TokenType.SYMBOL, ')')
		self.compile_subroutine_body()
		print('</subroutineDec>')

	def compile_parameter_list(self):
		print('<parameterList>')
		if self.token_type() == TokenType.KEYWORD:
			self.eat(TokenType.KEYWORD)    # type
			self.eat(TokenType.IDENTIFIER) # name
			while self.token_type() == TokenType.SYMBOL and self.token() == ',':
				self.eat(TokenType.SYMBOL, ',')
				self.eat_type()
				self.eat(TokenType.IDENTIFIER) # name
		print('</parameterList>')

	def compile_subroutine_body(self):
		print('<subroutineBody>')
		self.eat(TokenType.SYMBOL, '{')
		while self.token_type() == TokenType.KEYWORD and self.token() == 'var':
			self.compile_var_dec()
		self.compile_statements()
		self.eat(TokenType.SYMBOL, '}')
		print('</subroutineBody>')

	def compile_var_dec(self):
		print('<varDec>')
		self.eat(TokenType.KEYWORD)        # var
		self.eat_type()
		self.eat(TokenType.IDENTIFIER)     # name
		while self.token_type() == TokenType.SYMBOL and self.token() == ',':
			self.eat(TokenType.SYMBOL, ',')
			self.eat(TokenType.IDENTIFIER) # name
		self.eat(TokenType.SYMBOL, ';')
		print('</varDec>')

	def compile_statements(self):
		print('<statements>')
		while self.token_type() == TokenType.KEYWORD:
			if self.token() == 'let':
				self.compile_let_statement()
			elif self.token() == 'if':
				self.compile_if_statement()
			elif self.token() == 'while':
				self.compile_while_statement()
			elif self.token() == 'do':
				self.compile_do_statement()
			elif self.token() == 'return':
				self.compile_return_statement()
			else:
				break
		print('</statements>')

	def compile_let_statement(self):
		print('<letStatement>')
		self.eat(TokenType.KEYWORD)      # let
		self.eat(TokenType.IDENTIFIER)   # name
		if self.token_type() == TokenType.SYMBOL and self.token() == '[':
			self.eat(TokenType.SYMBOL, '[')
			self.compile_expression()
			self.eat(TokenType.SYMBOL, ']')
		self.eat(TokenType.SYMBOL, '=')
		self.compile_expression()        # value
		self.eat(TokenType.SYMBOL, ';')
		print('</letStatement>')

	def compile_if_statement(self):
		print('<ifStatement>')
		self.eat(TokenType.KEYWORD)      # if
		self.eat(TokenType.SYMBOL, '(')
		self.compile_expression()        # condition
		self.eat(TokenType.SYMBOL, ')')
		self.eat(TokenType.SYMBOL, '{')
		self.compile_statements()
		self.eat(TokenType.SYMBOL, '}')
		if self.token_type() == TokenType.KEYWORD and self.token() == 'else':
			self.eat(TokenType.KEYWORD)  # else
			self.eat(TokenType.SYMBOL, '{')
			self.compile_statements()
			self.eat(TokenType.SYMBOL, '}')
		print('</ifStatement>')

	def compile_while_statement(self):
		print('<whileStatement>')
		self.eat(TokenType.KEYWORD)      # while
		self.eat(TokenType.SYMBOL, '(')
		self.compile_expression()        # condition
		self.eat(TokenType.SYMBOL, ')')
		self.eat(TokenType.SYMBOL, '{')
		self.compile_statements()
		self.eat(TokenType.SYMBOL, '}')
		print('</whileStatement>')

	def compile_do_statement(self):
		print('<doStatement>')
		self.eat(TokenType.KEYWORD)      # do
		self.eat(TokenType.IDENTIFIER)   # subroutineName or classname/varname
		if self.token_type() == TokenType.SYMBOL and self.token() == '.':
			self.eat(TokenType.SYMBOL, '.')
			self.eat(TokenType.IDENTIFIER)   # subroutineName
		self.eat(TokenType.SYMBOL, '(')
		self.compile_expression_list()
		self.eat(TokenType.SYMBOL, ')')
		self.eat(TokenType.SYMBOL, ';')
		print('</doStatement>')

	def compile_return_statement(self):
		print('<returnStatement>')
		self.eat(TokenType.KEYWORD)      # return
		if self.token_type() != TokenType.SYMBOL or self.token() != ';':
			self.compile_expression()
		self.eat(TokenType.SYMBOL, ';')
		print('</returnStatement>')

	def compile_expression_list(self):
		print('<expressionList>')
		if not (self.token_type() == TokenType.SYMBOL and self.token() == ')'):
			self.compile_expression()
			while self.token_type() == TokenType.SYMBOL and self.token() == ',':
				self.eat(TokenType.SYMBOL, ',')
				self.compile_expression()
		print('</expressionList>')

	def compile_expression(self):
		print('<expression>')
		self.compile_term()
		if self.token_type() == TokenType.SYMBOL and self.token() in self.operators:
			self.eat(TokenType.SYMBOL)
			self.compile_term()
		print('</expression>')

	def compile_term(self):
		print('<term>')
		if self.token_type() == TokenType.INT_CONST:
			self.eat(TokenType.INT_CONST)
		elif self.token_type() == TokenType.STR_CONST:
			self.eat(TokenType.STR_CONST)
		elif self.token_type() == TokenType.KEYWORD and self.token() in self.keyword_constants:
			self.eat(TokenType.KEYWORD)
		elif self.token_type() == TokenType.SYMBOL and self.token() in self.unary_ops:
			self.eat(TokenType.SYMBOL)
			self.compile_term()
		elif self.token_type() == TokenType.SYMBOL and self.token() == '(':
			self.eat(TokenType.SYMBOL, '(')
			self.compile_expression()
			self.eat(TokenType.SYMBOL, ')')
		elif self.token_type() == TokenType.IDENTIFIER:
			self.eat(TokenType.IDENTIFIER)
			if self.token_type() == TokenType.SYMBOL and self.token() == '[':
				self.eat(TokenType.SYMBOL, '[')
				self.compile_expression()
				self.eat(TokenType.SYMBOL, ']')
			elif self.token_type() == TokenType.SYMBOL and self.token() == '(':
				# Subroutine call
				self.eat(TokenType.SYMBOL, '(')
				self.compile_expression_list()
				self.eat(TokenType.SYMBOL, ')')
			elif self.token_type() == TokenType.SYMBOL and self.token() == '.':
				# Subroutine call
				self.eat(TokenType.SYMBOL, '.')
				self.eat(TokenType.IDENTIFIER)
				self.eat(TokenType.SYMBOL, '(')
				self.compile_expression_list()
				self.eat(TokenType.SYMBOL, ')')
		print('</term>')

	def compile_subroutine_call(self):
		print('<subroutineCall>')
		self.eat(TokenType.IDENTIFIER)      # subroutineName or className
		if self.token() == '.':
			self.eat(TokenType.SYMBOL, '.')
			self.eat(TokenType.IDENTIFIER)  # varName
		self.eat(TokenType.SYMBOL, '(')
		self.compile_expression_list()
		self.eat(TokenType.SYMBOL, ')')
		print('</subroutineCall>')

	def eat_type(self):
		if self.token_type() == TokenType.KEYWORD and (self.token() == 'void' or self.token() in self.types):
			self.eat(TokenType.KEYWORD)
		else:
			self.eat(TokenType.IDENTIFIER)

	def eat(self, token_type, token = False):
		if self.token_type() != token_type:
			raise Exception("Unexpected token type: " + self.token())
		if token and self.token() != token:
			raise Exception("Unexpected token: " + self.token())
		print('<{0}> {1} </{0}>'.format(self.token_type(), escapeXml(self.token())))
		self.tokenizer.advance()

	def token_type(self):
		return self.tokenizer.get_token_type()

	def token(self):
		return self.tokenizer.get_token()


def analyze_file(jack_filename):
	xml_filename = os.path.splitext(jack_filename)[0] + ".xml"
	with open(xml_filename, "w") as xml_file:
		tokenizer = JackTokenizer(jack_filename)
		CompilationEngine(tokenizer, xml_file).compile()

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
