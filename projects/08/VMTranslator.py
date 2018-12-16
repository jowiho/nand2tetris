#!/usr/bin/python3

import glob, os, re, sys

class CodeWriter:
	def __init__(self, file):
		self.file = file
		self.labelNo = 0
		self.label_prefix = ''

	def set_filename(self, filename):
		self.static_prefix = os.path.splitext(os.path.basename(filename))[0] + '.'

	def _get_next_label(self):
		self.labelNo += 1
		return self.label_prefix + 'LABEL' + str(self.labelNo)

	def _get_function_label(self, function):
		return function

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
			self._push_register(self.static_prefix + address)
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
			self._pop_register(self.static_prefix + address)
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
		self.write_goto(label2)
		self.write_label(label1)
		self.write('@SP')
		self.write('A=M-1')
		self.write('M=-1')
		self.write_label(label2)

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
		self.write_goto(label2)
		self.write_label(label1)
		self.write('@SP')
		self.write('A=M-1')
		self.write('M=-1')
		self.write_label(label2)

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
		self.write_goto(label2)
		self.write_label(label1)
		self.write('@SP')
		self.write('A=M-1')
		self.write('M=-1')
		self.write_label(label2)

	def write_label(self, label):
		self.write('(' + label + ')')

	def write_goto(self, label):
		self.write('@' + label)
		self.write('0;JMP')

	def write_if(self, label):
		self._popd()
		self.write('@' + label)
		self.write('D;JNE')

	def _push_segment_address(self, segment):
		self.write('@' + segment)
		self.write('D=M')
		self._pushd()

	def write_call(self, function, arg_count):
		# Save return address
		return_addr = self._get_next_label()
		self.write('@' + return_addr)
		self.write('D=A')
		self._pushd()
		# Save segment addresses
		self._push_segment_address('LCL')
		self._push_segment_address('ARG')
		self._push_segment_address('THIS')
		self._push_segment_address('THAT')
		# ARG = SP-n-5
		self.write('@SP')
		self.write('D=M')
		self.write('@' + str(arg_count + 5))
		self.write('D=D-A')
		self.write('@ARG')
		self.write('M=D')
		# LCL = SP
		self.write('@SP')
		self.write('D=M')
		self.write('@LCL')
		self.write('M=D')
		self.write_goto(self._get_function_label(function))
		self.write_label(return_addr)

	def write_function(self, function, local_count):
		self.label_prefix = function + '$'
		self.write_label(self._get_function_label(function))
		self.write('D=0')
		for i in range(local_count):
			self._pushd()

	def write_return(self):
		# R13 = LCL
		self.write('@LCL')
		self.write('D=M')
		self.write('@R13')
		self.write('M=D')
		# R14 = *(R13 - 5) (save return address)
		self.write('@5')
		self.write('A=D-A')
		self.write('D=M')
		self.write('@R14')
		self.write('M=D')		
		# *ARG = pop()
		self._popd()
		self.write('@ARG')
		self.write('A=M')
		self.write('M=D')
		# SP = ARG + 1
		self.write('@ARG')
		self.write('D=M+1')
		self.write('@SP')
		self.write('M=D')
		# Restore THAT
		self.write('@R13')
		self.write('AM=M-1')
		self.write('D=M')
		self.write('@THAT')
		self.write('M=D')
		# Restore THIS
		self.write('@R13')
		self.write('AM=M-1')
		self.write('D=M')
		self.write('@THIS')
		self.write('M=D')
		# Restore ARG
		self.write('@R13')
		self.write('AM=M-1')
		self.write('D=M')
		self.write('@ARG')
		self.write('M=D')
		# Restore LCL
		self.write('@R13')
		self.write('AM=M-1')
		self.write('D=M')
		self.write('@LCL')
		self.write('M=D')
		# Return (goto R14)
		self.write('@R14')
		self.write('A=M')
		self.write('0;JMP')
		self.label_prefix = ''

	def write_init(self):
		self.write('@256')
		self.write('D=A')
		self.write('@SP')
		self.write('M=D')
		self.write_comment('call Sys.init')
		self.write_call('Sys.init', 0)

class Parser:
	def __init__(self, code_writer):
		self.writer = code_writer

	def parseFile(self, filename):
		self.writer.set_filename(filename)
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
		elif cmd == 'label':
			self.writer.write_label(args[0])
		elif cmd == 'goto':
			self.writer.write_goto(args[0])
		elif cmd == 'if-goto':
			self.writer.write_if(args[0])
		elif cmd == 'call':
			self.writer.write_call(args[0], int(args[1]))
		elif cmd == 'function':
			self.writer.write_function(args[0], int(args[1]))
		elif cmd == 'return':
			self.writer.write_return()
		else:
			raise Exception('Unknown command ' + cmd)


def translate_file(vm_filename):
	asm_filename = os.path.splitext(vm_filename)[0] + ".asm"
	with open(asm_filename, "w") as asm_file:
		writer = CodeWriter(asm_file)
		parser = Parser(writer)
		parser.parseFile(vm_filename)

def translate_directory(directory):
	asm_filename = directory + '/' + os.path.basename(directory) + '.asm'
	with open(asm_filename, "w") as asm_file:
		writer = CodeWriter(asm_file)
		writer.write_init()
		parser = Parser(writer)
		for file in glob.glob(directory + "/*.vm"):
			writer.write_comment('file ' + file)
			parser.parseFile(file)

def main(argv):
	if len(argv) == 1 and os.path.isdir(argv[0]):
		translate_directory(argv[0])
	elif len(argv) == 1 and os.path.splitext(argv[0])[1] == ".vm":
		translate_file(argv[0])
	else:
		print("Usage: VMTranslator.py <filename>.vm | <directory>")
		sys.exit(1)

if __name__ == '__main__':
    main(sys.argv[1:])
