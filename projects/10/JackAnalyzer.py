#!/usr/bin/python3

import glob, io, os, re, sys

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
