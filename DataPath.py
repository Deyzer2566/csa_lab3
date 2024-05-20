undefined = 0
from enum import Enum
def crop(x, bits):
	if x < 0:
		return min(x, 2**bits-1)
	else:
		return max(x, -2**bits)
class Opcode(Enum):
	pass
class ALU_Operation(Enum):
	AND=0
	NOT=1
	SUM=2
	LS=3
	RS=4
	CROP=5
	MUL=6
	DIV=7
class DataPath:
	def __init__(self):
		self.mem_size = 0xffffff
		self.AR = 0
		self.DR = 0
		self.memory_selected = False
		self.memory = {}
		self.registers = [0 for i in range(16)]
		self.selected_register=0
		self.NZVC = [False,False,False, False]
		self.ALU_out = [0, False, False, False, False]
		self.ALU_out_register = 0
		self.ALU_operation = ALU_Operation.AND
		self.first_ALU_input = 0
		self.databus_from_DR_to_memory = undefined
		self.databus_from_ALU_and_memory = undefined
		self.data_from_memory = 0
		self.memory_mapped_registers=[0 for i in range(4)]
		self.useCarry = False
		self.plus1 = False
	def get_data_from_databus_from_ALU_and_memory(self):
		if any(self.databus_from_ALU_and_memory):
			data = 0
			if self.databus_from_ALU_and_memory[0]:
				data |= self.ALU_out_register
			if self.databus_from_ALU_and_memory[1]:
				data |= self.data_from_memory
			return data
		else:
			return undefined
	def setAR(self):
		self.AR = self.get_data_from_databus_from_ALU_and_memory()
		self.set_ALU_out()
	def setDR(self):
		self.DR = self.get_data_from_databus_from_ALU_and_memory()
		self.set_ALU_out()
	def resetDR(self):
		self.DR = 0
	def select_memory(self):
		self.memory_selected=True
	def deselect_memory(self):
		self.memory_selected=False
	def read_from_memory(self):
		if self.memory_selected:
			if self.AR & 0xfffffc != 0xfffffc:
				self.data_from_memory = self.memory[self.AR]
			else:
				self.data_from_memory = self.memory_mapped_registers[self.AR%4]
		else:
			self.data_from_memory = undefined
	def write_to_memory(self):
		if self.memory_selected:
			if self.AR & 0xfffffc != 0xfffffc:
				self.memory[self.AR] = self.databus_from_DR_to_memory
			else:
				self.memory_mapped_registers[self.AR%4]=self.databus_from_DR_to_memory
	def DR_to_databus_on(self):
		self.databus_from_DR_to_memory = self.DR
	def DR_to_databus_off(self):
		self.databus_from_DR_to_memory = undefined
	def set_First_ALU_input(self):
		self.first_ALU_input = self.registers[self.selected_register]
		self.set_ALU_out()
	def reset_First_ALU_input(self):
		self.first_ALU_input = 0
		self.set_ALU_out()
	def set_register(self):
		self.registers[self.selected_register] = self.get_data_from_databus_from_ALU_and_memory()
	def set_ALU_out(self):
		match self.ALU_operation:
			case ALU_Operation.AND:
				out = self.first_ALU_input & self.DR
				self.ALU_out = [out, out<0, out==0, False, False]
			case ALU_Operation.NOT:
				out = ~ self.DR
				self.ALU_out = [out, out<0, out==0, False, False]
			case ALU_Operation.SUM:
				out = self.first_ALU_input + self.DR
				if (self.useCarry and self.NZVC[3]) or self.plus1:
					out += 1
				self.ALU_out = [crop(out), out<0, out==0, abs(out)>2**32-1 , out > 2**32-1 or self.first_ALU_input>0 and self.DR < 0 and abs(self.first_ALU_input)<abs(self.DR)]
			case ALU_Operation.LS:
				out = self.first_ALU_input << self.DR
				self.ALU_out = [crop(out), out<0, out==0, False, out & (2**32) != 0]
			case ALU_Operation.RS:
				out = self.first_ALU_input >> self.DR
				self.ALU_out = [crop(out), out<0, out==0, False, out & (2**32) != 0]
			case ALU_Operation.CROP:
				out = self.DR&0xffff
				if self.DR < 0:
					out = -out
				self.ALU_out = out
			case ALU_Operation.MUL:
				out = self.first_ALU_input * self.DR
				self.ALU_out = [crop(out), out<0, out==0, False, False]
			case ALU_Operation.DIV:
				out = self.first_ALU_input // self.DR
				self.ALU_out = [crop(out), out<0, out==0, False, False]
	def set_NZVC(self):
		NZC = self.ALU_out[1:]