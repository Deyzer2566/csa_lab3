from enum import Enum
def crop(x, bits):
	if x > 0:
		return min(x, 2**bits-1)
	else:
		return max(x, -2**bits)
class ALU_Operation(Enum):
	AND=0
	NOT=1
	SUM=2
	LS=3
	RS=4
	CROP=5
	MUL=6
	DIV=7
class Memory_or_ALU_MUX(Enum):
	Memory=0
	ALU=1
class RegisterEnum(Enum):
	R0=0
	R1=1
	R2=2
	R3=3
	R4=4
	R5=5
	R6=6
	R7=7
	R8=8
	R9=9
	R10=10
	R11=11
	SP=12
	PC=13
	INTR=14
	IR=15
class DataPath:
	mem_size: int
	AR: int
	DR: int
	memory: set
	registers: list
	selected_register: RegisterEnum
	NZC: list
	ALU_out: list
	ALU_operation: ALU_Operation
	first_ALU_input: int
	data_from_memory: int
	memory_mapped_registers: list
	useCarry: bool
	plus1: bool
	memory_or_alu_mux: Memory_or_ALU_MUX
	def __init__(self):
		self.mem_size = 0xffffff
		self.AR = 0
		self.DR = 0
		self.memory = {}
		self.registers = [0 for i in range(16)]
		self.selected_register=RegisterEnum.R0
		self.NZC = [False,False, False]
		self.ALU_out = [0, False, False, False]
		self.ALU_operation = ALU_Operation.AND
		self.first_ALU_input = 0
		self.data_from_memory = 0
		self.memory_mapped_registers=[0 for i in range(4)]
		self.useCarry = False
		self.plus1 = False
		self.memory_or_alu_mux = Memory_or_ALU_MUX.Memory
	def set_AR(self):
		match self.memory_or_alu_mux:
			case Memory_or_ALU_MUX.ALU:
				self.AR = self.ALU_out[0]
			case Memory_or_ALU_MUX.Memory:
				self.AR = self.data_from_memory
		if self.AR & 0xfffffc != 0xfffffc:
			self.data_from_memory = self.memory[self.AR]
		else:
			self.data_from_memory = self.memory_mapped_registers[self.AR%4]
	def set_DR(self):
		match self.memory_or_alu_mux:
			case Memory_or_ALU_MUX.ALU:
				self.DR = self.ALU_out
			case Memory_or_ALU_MUX.Memory:
				self.DR = self.data_from_memory
		self.update_ALU_out()
	def reset_DR(self):
		self.DR = 0
		self.update_ALU_out()
	def select_memory_or_alu(self, memory_or_alu:Memory_or_ALU_MUX):
		self.memory_or_alu_mux = memory_or_alu
	def write_to_memory(self):
		if self.AR & 0xfffffc != 0xfffffc:
			self.memory[self.AR] = self.DR
		else:
			self.memory_mapped_registers[self.AR%4]=self.DR
	def set_First_ALU_input(self):
		self.first_ALU_input = self.registers[self.selected_register.value]
		self.update_ALU_out()
	def reset_First_ALU_input(self):
		self.first_ALU_input = 0
		self.update_ALU_out()
	def set_register(self):
		self.registers[self.selected_register.value] = self.ALU_out[0]
	def set_ALU_operation(self, operation: ALU_Operation):
		self.ALU_operation = operation
	def update_ALU_out(self):
		match self.ALU_operation:
			case ALU_Operation.AND:
				out = self.first_ALU_input & self.DR
				self.ALU_out = [out, out<0, out==0, False]
			case ALU_Operation.NOT:
				out = ~ self.DR
				self.ALU_out = [out, out<0, out==0, False]
			case ALU_Operation.SUM:
				out = self.first_ALU_input + self.DR
				if (self.useCarry and self.NZC[2]) or self.plus1:
					out += 1
				self.ALU_out = [crop(out,32), out<0, out==0, out > 2**32-1 or self.first_ALU_input>0 and self.DR < 0 and abs(self.first_ALU_input)<abs(self.DR)]
			case ALU_Operation.LS:
				out = self.first_ALU_input << self.DR
				self.ALU_out = [crop(out,32), out<0, out==0, out & (2**32) != 0]
			case ALU_Operation.RS:
				out = self.first_ALU_input >> self.DR
				self.ALU_out = [crop(out,32), out<0, out==0, out & (2**32) != 0]
			case ALU_Operation.CROP:
				out = self.DR&0xffff
				if self.DR < 0:
					out = -out
				self.ALU_out = [out, out<0, out==0, False]
			case ALU_Operation.MUL:
				out = self.first_ALU_input * self.DR
				self.ALU_out = [crop(out), out<0, out==0, False]
			case ALU_Operation.DIV:
				out = self.first_ALU_input // self.DR
				self.ALU_out = [crop(out), out<0, out==0, False]
	def update_NZC(self):
		self.NZC = self.ALU_out[1:]
	def select_register(self,register_num):
		self.selected_register = register_num
	def set_use_carry(self):
		self.useCarry=True
		self.update_ALU_out()
	def reset_use_carry(self):
		self.useCarry=False
		self.update_ALU_out()
	def set_plus_1(self):
		self.plus1=True
		self.update_ALU_out()
	def reset_plus_1(self):
		self.plus1=False
		self.update_ALU_out()
	def get_NZC(self):
		return self.NZC
	def get_IR(self):
		return self.registers[RegisterEnum.IR.value]
	def get_INTR(self):
		return self.registers[RegisterEnum.INTR.value]