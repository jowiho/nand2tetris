#!/usr/bin/python3

import os, re, sys

class CodeWriter:
	def __init__(self, file):
		self.file = file
		self.labelNo = 0

	def _get_next_label(self):
		self.labelNo += 1
		return 'LABEL' + str(self.labelNo)

	def write(self, line):
		self.file.write(line + '\n')

	def write_comment(self, text):
		self.write('// ' + text)

	def _pushd(self):
		self.write('@SP')
		self.write('M=M+1')
		self.write('A=M-1')
		self.write('M=D')

	def _popd(self):
		self.write('@SP')
		self.write('AM=M-1')
		self.write('D=M')

	def _push_constant(self, value):
		self.write('@' + str(value))
		self.write('D=A')
		self._pushd()

	def _push_register(self, register):
		self.write('@' + register)
		self.write('D=M')
		self._pushd()

	def _push_segment(self, segmentRegister, address):
		self.write('@' + segmentRegister)
		self.write('D=M')
		self.write('@' + address)
		self.write('A=D+A')
		self.write('D=M')
		self._pushd()

	def write_push(self, segment, address):
		if segment == 'constant':
			self._push_constant(address)
		elif segment == 'pointer':
			self._push_register('R' + str(3 + int(address)))
		elif segment == 'temp':
			self._push_register('R' + str(5 + int(address)))
		elif segment == 'static':
			self._push_register('S' + address)
		elif segment == 'local':
			self._push_segment('LCL', address)
		elif segment == 'argument':
			self._push_segment('ARG', address)
		elif segment == 'this':
			self._push_segment('THIS', address)
		elif segment == 'that':
			self._push_segment('THAT', address)
		else:
			raise Exception('Unknown push segment ' + segment)

	def _pop_register(self, register):
		self._popd()
		self.write('@' + register)
		self.write('M=D')

	def _pop_segment(self, segmentRegister, address):
		# R13 = segment + address
		self.write('@' + segmentRegister)
		self.write('D=M')
		self.write('@' + address)
		self.write('D=D+A')
		self.write('@R13')
		self.write('M=D')
		self._popd()
		# *R13 = D
		self.write('@R13')
		self.write('A=M')
		self.write('M=D')

	def write_pop(self, segment, address):
		if segment == 'pointer':
			self._pop_register('R' + str(3 + int(address)))
		elif segment == 'temp':
			self._pop_register('R' + str(5 + int(address)))
		elif segment == 'static':
			self._pop_register('S' + address)
		elif segment == 'local':
			self._pop_segment('LCL', address)
		elif segment == 'argument':
			self._pop_segment('ARG', address)
		elif segment == 'this':
			self._pop_segment('THIS', address)
		elif segment == 'that':
			self._pop_segment('THAT', address)
		else:
			raise Exception('Unknown pop segment ' + segment)

	def write_not(self):
		self.write('@SP')
		self.write('A=M-1')
		self.write('M=!M')

	def write_neg(self):
		self.write('@SP')
		self.write('A=M-1')
		self.write('M=-M')

	def write_and(self):
		self.write('@SP')
		self.write('AM=M-1')
		self.write('D=M')
		self.write('A=A-1')
		self.write('M=D&M')

	def write_or(self):
		self.write('@SP')
		self.write('AM=M-1')
		self.write('D=!M')
		self.write('A=A-1')
		self.write('M=!M')
		self.write('M=D&M')
		self.write('M=!M')

	def write_add(self):
		self.write('@SP')
		self.write('AM=M-1')
		self.write('D=M')
		self.write('A=A-1')
		self.write('M=D+M')

	def write_sub(self):
		self.write('@SP')
		self.write('AM=M-1')
		self.write('D=M')
		self.write('A=A-1')
		self.write('M=M-D')

	def write_eq(self):
		label1 = self._get_next_label()
		label2 = self._get_next_label()
		self.write('@SP')
		self.write('AM=M-1')
		self.write('D=M')
		self.write('A=A-1')
		self.write('D=M-D')
		self.write('@' + label1)
		self.write('D;JEQ')
		self.write('@SP')
		self.write('A=M-1')
		self.write('M=0')
		self.write('@' + label2)
		self.write('0;JMP')
		self.write('(' + label1 + ')')
		self.write('@SP')
		self.write('A=M-1')
		self.write('M=-1')
		self.write('(' + label2 + ')')

	def write_lt(self):
		label1 = self._get_next_label()
		label2 = self._get_next_label()
		self.write('@SP')
		self.write('M=M-1')
		self.write('A=M')
		self.write('D=M')
		self.write('A=A-1')
		self.write('D=M-D')
		self.write('@' + label1)
		self.write('D;JLT')
		self.write('@SP')
		self.write('A=M-1')
		self.write('M=0')
		self.write('@' + label2)
		self.write('0;JMP')
		self.write('(' + label1 + ')')
		self.write('@SP')
		self.write('A=M-1')
		self.write('M=-1')
		self.write('(' + label2 + ')')

	def write_gt(self):
		label1 = self._get_next_label()
		label2 = self._get_next_label()
		self.write('@SP')
		self.write('M=M-1')
		self.write('A=M')
		self.write('D=M')
		self.write('A=A-1')
		self.write('D=M-D')
		self.write('@' + label1)
		self.write('D;JGT')
		self.write('@SP')
		self.write('A=M-1')
		self.write('M=0')
		self.write('@' + label2)
		self.write('0;JMP')
		self.write('(' + label1 + ')')
		self.write('@SP')
		self.write('A=M-1')
		self.write('M=-1')
		self.write('(' + label2 + ')')


class Parser:
	def __init__(self, code_writer):
		self.writer = code_writer

	def parseFile(self, filename):
		with open(filename) as file:
			for line in file.readlines():
				line = self._strip(line)
				if len(line):
					self._parse_line(line)

	def _strip(self, line):
		line = re.sub('//.*', '', line)
		line = re.sub('(^\s|\s*$)', '', line)
		return line

	def _parse_line(self, line):
		self.writer.write_comment(line)
		tokens = line.split()
		cmd = tokens[0]
		args = tokens[1:]
		if cmd == 'push':
			self.writer.write_push(args[0], args[1])
		elif cmd == 'pop':
			self.writer.write_pop(args[0], args[1])
		elif cmd == 'add':
			self.writer.write_add()
		elif cmd == 'sub':
			self.writer.write_sub()
		elif cmd == 'eq':
			self.writer.write_eq()
		elif cmd == 'lt':
			self.writer.write_lt()
		elif cmd == 'gt':
			self.writer.write_gt()
		elif cmd == 'neg':
			self.writer.write_neg()
		elif cmd == 'and':
			self.writer.write_and()
		elif cmd == 'or':
			self.writer.write_or()
		elif cmd == 'not':
			self.writer.write_not()
		else:
			raise Exception('Unknown command ' + cmd)


def translate_file(vm_filename):
	asm_filename = os.path.splitext(vm_filename)[0] + ".asm"
	with open(asm_filename, "w") as asm_file:
		writer = CodeWriter(asm_file)
		parser = Parser(writer)
		parser.parseFile(vm_filename)

def main(argv):
	if len(argv) == 1 and os.path.splitext(argv[0])[1] == ".vm":
		translate_file(argv[0])
	else:
		print("Usage: VMTranslator.py <filename>.vm")
		sys.exit(1)

if __name__ == '__main__':
    main(sys.argv[1:])
