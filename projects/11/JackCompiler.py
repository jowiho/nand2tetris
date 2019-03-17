#!/usr/bin/python3

# TODO: use string interpolation

import glob, os, re, sys

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

class Symbol:
	def __init__(self, typ, segment, seqno):
		self.typ = typ
		self.segment = segment
		self.seqno = seqno

class SymbolTable:
	def __init__(self):
		self.reset()

	def reset(self):
		self.symbols = {}
		self.count_per_segment = {}

	def add(self, name, typ, segment):
		seqno = self.count(segment)
		self.symbols[name] = Symbol(typ, segment, seqno)
		self.count_per_segment[segment] = seqno + 1

	def get(self, name):
		if name in self.symbols:
			return self.symbols[name]
		else:
			return False

	def length(self):
		return len(self.symbols)

	def count(self, segment):
		return self.count_per_segment[segment] if segment in self.count_per_segment else 0

class CompilationEngine:
	types = ['int', 'char', 'boolean']
	operators = ['+', '-', '*', '/', '&', '|', '<', '>', '=']

	def __init__(self, tokenizer, output_file):
		self.tokenizer = tokenizer
		self.output_file = output_file
		self.class_symbol_table = SymbolTable()
		self.function_symbol_table = SymbolTable()
		self.label_count = 0
		self.current_class = ''

	def emit(self, line):
		self.output_file.write('{}\n'.format(line))

	def comment(self, comment):
		self.output_file.write('// {}\n'.format(comment))

	def next_label(self):
		self.label_count += 1
		return 'L' + str(self.label_count)

	def compile(self):
		self.tokenizer.advance()
		self.compile_class()

	def compile_class(self):
		self.class_symbol_table.reset()
		self.eat(TokenType.KEYWORD, 'class')
		self.classname = self.eat(TokenType.IDENTIFIER)
		self.eat_symbol('{')
		while self.token() == 'static' or self.token() == 'field':
			self.compile_class_var_dec()
		while self.token() == 'constructor' or self.token() == 'function' or self.token() == 'method':
			self.compile_subroutine_dec()
		self.eat_symbol('}')

	def compile_class_var_dec(self):
		kind = self.eat(TokenType.KEYWORD)  # static|field
		typ = self.eat_type()
		name = self.eat(TokenType.IDENTIFIER)
		segment = 'static' if kind == 'static' else 'this'
		self.class_symbol_table.add(name, typ, segment)
		while self.try_eat_symbol(','):
			name = self.eat(TokenType.IDENTIFIER)
			self.class_symbol_table.add(name, typ, segment)
		self.eat_symbol(';')

	def compile_subroutine_dec(self):
		self.function_symbol_table.reset()
		kind = self.eat(TokenType.KEYWORD)  # constructor|function|method
		return_type = self.eat_type()
		name = self.eat(TokenType.IDENTIFIER)
		self.comment('{} {} {}'.format(kind, return_type, name))
		self.eat_symbol('(')
		self.compile_parameter_list(kind)
		self.eat_symbol(')')
		self.compile_subroutine_body(kind, name)
		if return_type == 'void':
			# Dummy return value
			self.emit('push constant 0')
		self.emit('return')

	def compile_parameter_list(self, kind):
		if kind == 'method':
			# First argument is "this"
			self.function_symbol_table.add('this', '', 'argument')
		if self.token() != ')':
			typ = self.eat_type()
			name = self.eat(TokenType.IDENTIFIER)
			self.function_symbol_table.add(name, typ, 'argument')
			while self.try_eat_symbol(','):
				typ = self.eat_type()
				name = self.eat(TokenType.IDENTIFIER) 
				self.function_symbol_table.add(name, typ, 'argument')

	def compile_subroutine_body(self, kind, name):
		self.eat_symbol('{')
		while self.token_type() == TokenType.KEYWORD and self.token() == 'var':
			self.compile_var_dec()
		self.emit('function {}.{} {}'.format(self.classname, name, self.function_symbol_table.count('local')))
		if kind == 'constructor':
			# Allocate "this"
			self.emit('push constant {}'.format(self.class_symbol_table.count('this')))
			self.emit('call Memory.alloc 1')
			self.emit('pop pointer 0')
		elif kind == 'method':
			# First argument is "this"
			self.emit('push argument 0')
			self.emit('pop pointer 0')
		self.compile_statements()
		self.eat_symbol('}')

	def compile_var_dec(self):
		self.eat(TokenType.KEYWORD) # var
		typ = self.eat_type()
		name = self.eat(TokenType.IDENTIFIER)
		self.function_symbol_table.add(name, typ, 'local')
		while self.try_eat_symbol(','):
			name = self.eat(TokenType.IDENTIFIER)
			self.function_symbol_table.add(name, typ, 'local')
		self.eat_symbol(';')

	def compile_statements(self):
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

	def compile_let_statement(self):
		self.comment('let')
		self.eat(TokenType.KEYWORD)  # let
		name = self.eat(TokenType.IDENTIFIER)
		if self.try_eat_symbol('['):
			is_array = True
			self.push_variable(name)
			self.compile_expression()
			self.eat_symbol(']')
			self.emit('add')  # Save array element address
		else:
			is_array = False
		self.eat_symbol('=')
		self.compile_expression()
		self.eat_symbol(';')
		if is_array:
			self.emit('pop temp 0')
			self.emit('pop pointer 1')  # Use saved array element address
			self.emit('push temp 0')
			self.emit('pop that 0')
		else:
			symbol = self.get_symbol(name)
			self.emit('pop {} {}'.format(symbol.segment, symbol.seqno))

	def compile_if_statement(self):
		label1 = self.next_label()
		label2 = self.next_label()
		self.eat(TokenType.KEYWORD) # if
		self.eat_symbol('(')
		self.compile_expression()
		self.eat_symbol(')')
		self.emit('not')
		self.emit('if-goto ' + label1)
		self.eat_symbol('{')
		self.compile_statements()
		self.eat_symbol('}')
		self.emit('goto ' + label2)
		self.emit('label ' + label1)
		if self.token_type() == TokenType.KEYWORD and self.token() == 'else':
			self.eat(TokenType.KEYWORD)  # else
			self.eat_symbol('{')
			self.compile_statements()
			self.eat_symbol('}')
		self.emit('label ' + label2)

	def compile_while_statement(self):
		label1 = self.next_label()
		label2 = self.next_label()
		self.emit('label ' + label1)
		self.eat(TokenType.KEYWORD)  # while
		self.eat_symbol('(')
		self.compile_expression()
		self.eat_symbol(')')
		self.emit('not')
		self.emit('if-goto ' + label2)
		self.eat_symbol('{')
		self.compile_statements()
		self.eat_symbol('}')
		self.emit('goto ' + label1)
		self.emit('label ' + label2)

	def compile_do_statement(self):
		self.eat(TokenType.KEYWORD)  # do
		name = self.eat(TokenType.IDENTIFIER)
		if self.try_eat_symbol('.'):
			symbol = self.try_get_symbol(name)
			if symbol:
				# Push object pointer (calling a method)
				self.emit('push {} {}'.format(symbol.segment, symbol.seqno))
				name = symbol.typ
				arg_count = 1
			else:
				# Don't push "this" (calling a function or constructor)
				arg_count = 0
			name += '.' + self.eat(TokenType.IDENTIFIER)
		else:
			# Push "this" (calling own method)
			self.emit('push pointer 0')
			name = self.classname + '.' + name
			arg_count = 1
		self.eat_symbol('(')
		arg_count += self.compile_expression_list()
		self.eat_symbol(')')
		self.eat_symbol(';')
		self.emit('call {} {}'.format(name, arg_count))
		# Discard return value
		self.emit('pop temp 0')

	def compile_return_statement(self):
		self.eat(TokenType.KEYWORD)  # return
		if self.token_type() != TokenType.SYMBOL or self.token() != ';':
			self.compile_expression()
		self.eat_symbol(';')

	# TODO: better name (argument_list?)
	def compile_expression_list(self):
		arg_count = 0
		if not (self.token_type() == TokenType.SYMBOL and self.token() == ')'):
			self.compile_expression()
			arg_count += 1
			while self.try_eat_symbol(','):
				arg_count += 1
				self.compile_expression()
		return arg_count

	def compile_expression(self):
		self.compile_term()
		if self.token_type() == TokenType.SYMBOL and self.token() in self.operators:
			operator = self.eat(TokenType.SYMBOL)
			self.compile_term()
			if operator == '&':
				self.emit('and')
			elif operator == '|':
				self.emit('or')
			elif operator == '>':
				self.emit('gt')
			elif operator == '<':
				self.emit('lt')
			elif operator == '=':
				self.emit('eq')
			elif operator == '+':
				self.emit('add')
			elif operator == '-':
				self.emit('sub')
			elif operator == '*':
				self.emit('call Math.multiply 2')
			elif operator == '/':
				self.emit('call Math.divide 2')
			else:
				raise Exception("Unexpected operator: " + operator)

	def compile_term(self):
		if self.token_type() == TokenType.INT_CONST:
			const = self.eat(TokenType.INT_CONST)
			self.emit('push constant {}'.format(const))
		elif self.token_type() == TokenType.STR_CONST:
			string = self.eat(TokenType.STR_CONST)
			self.emit('push constant {}'.format(len(string)))
			self.emit('call String.new 1')
			for c in string:
				self.emit('push constant {}'.format(ord(c)))
				self.emit('call String.appendChar 2')
		elif self.token_type() == TokenType.KEYWORD and self.token() == 'true':
			self.eat(TokenType.KEYWORD)
			self.emit('push constant 1')
			self.emit('neg')
		elif self.token_type() == TokenType.KEYWORD and self.token() == 'false':
			self.eat(TokenType.KEYWORD)
			self.emit('push constant 0')
		elif self.token_type() == TokenType.KEYWORD and self.token() == 'null':
			self.eat(TokenType.KEYWORD)
			self.emit('push constant 0')
		elif self.token_type() == TokenType.KEYWORD and self.token() == 'this':
			self.eat(TokenType.KEYWORD)
			self.emit('push pointer 0')
		elif self.try_eat_symbol('-'):
			self.compile_term()
			self.emit('neg')
		elif self.try_eat_symbol('~'):
			self.compile_term()
			self.emit('not')
		elif self.try_eat_symbol('('):
			self.compile_expression()
			self.eat_symbol(')')
		elif self.token_type() == TokenType.IDENTIFIER:
			name = self.eat(TokenType.IDENTIFIER)
			if self.try_eat_symbol('('):
				# Push "this" (calling own method)
				self.emit('push pointer 0')
				arg_count = 1 + self.compile_expression_list()
				self.eat_symbol(')')
				self.emit('call {}.{} {}'.format(self.classname, name, arg_count))
			elif self.try_eat_symbol('.'):
				# Subroutine call
				symbol = self.try_get_symbol(name)
				if symbol:
					# Push object pointer (calling a method)
					self.emit('push {} {}'.format(symbol.segment, symbol.seqno))
					name = symbol.typ
					arg_count = 1
				else:
					# Don't push "this" (calling a function or constructor)
					arg_count = 0
				name += '.' + self.eat(TokenType.IDENTIFIER)
				self.eat_symbol('(')
				arg_count += self.compile_expression_list()
				self.eat_symbol(')')
				self.emit('call {} {}'.format(name, arg_count))
			else:
				# Variable
				self.push_variable(name)
				if self.try_eat_symbol('['):
					# Array
					self.compile_expression()
					self.eat_symbol(']')
					self.emit('add')
					self.emit('pop pointer 1')
					self.emit('push that 0')

	def push_variable(self, name):
		symbol = self.get_symbol(name)
		self.emit('push {} {}'.format(symbol.segment, symbol.seqno))

	def get_symbol(self, name):
		symbol = self.try_get_symbol(name)
		if not symbol:
			raise Exception("Unknown symbol " + name)
		return symbol

	def try_get_symbol(self, name):
		symbol = self.function_symbol_table.get(name)
		if not symbol:
			symbol = self.class_symbol_table.get(name)
		return symbol

	def eat_type(self):
		if self.token_type() == TokenType.KEYWORD and (self.token() == 'void' or self.token() in self.types):
			return self.eat(TokenType.KEYWORD)
		else:
			return self.eat(TokenType.IDENTIFIER)

	def try_eat_symbol(self, symbol):
		if self.token_type() == TokenType.SYMBOL and self.token() == symbol:
			self.eat_symbol(symbol)
			return True
		else:
			return False

	def eat_symbol(self, symbol):
		self.eat(TokenType.SYMBOL, symbol)

	def eat(self, token_type, token = False):
		if self.token_type() != token_type:
			raise Exception("Unexpected token type: " + self.token())
		if token and self.token() != token:
			raise Exception("Unexpected token: " + self.token())
		token = self.token()
		self.tokenizer.advance()
		return token

	def token_type(self):
		return self.tokenizer.get_token_type()

	def token(self):
		return self.tokenizer.get_token()


def compile_file(jack_filename):
	xml_filename = os.path.splitext(jack_filename)[0] + ".vm"
	with open(xml_filename, "w") as xml_file:
		tokenizer = JackTokenizer(jack_filename)
		CompilationEngine(tokenizer, xml_file).compile()

def main(argv):
	if len(argv) == 1 and os.path.isdir(argv[0]):
		for file in glob.glob(argv[0] + "/*.jack"):
			compile_file(file)
	elif len(argv) == 1 and os.path.splitext(argv[0])[1] == ".jack":
		compile_file(argv[0])
	else:
		print("Usage: JackAnalyzer.py <filename>.jack | <directory>")
		sys.exit(1)

if __name__ == '__main__':
    main(sys.argv[1:])
