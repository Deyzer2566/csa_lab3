from enum import Enum


def crop(x, bits):
    return x & (2**bits - 1)


class ALU_Operation(Enum):
    AND = 0
    NOT = 1
    SUM = 2
    LS = 3
    RS = 4
    CROP = 5
    MUL = 6
    DIV = 7
    FIND_LOW_1 = 8
    OR = 9
    NEG = 10
    SUB = 11


class Registers_Memory_ALU_or_Flags_MUX(Enum):
    REGISTERS = 0
    ALU = 1
    MEMORY = 2
    FLAGS = 3


class RegisterEnum(Enum):
    R0 = 0
    R1 = 1
    R2 = 2
    R3 = 3
    R4 = 4
    R5 = 5
    R6 = 6
    R7 = 7
    R8 = 8
    R9 = 9
    R10 = 10
    LR = 11
    SP = 12
    PC = 13
    INTR = 14
    IR = 15


class ALU_or_flags_MUX(Enum):
    ALU = 0
    FLAGS = 1


class NZC_Flags(Enum):
    NEGATIVE = 0
    ZERO = 1
    CARRY = 2


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
    registers_memory_alu_or_flags_MUX: Registers_Memory_ALU_or_Flags_MUX
    interruption_num: int
    alu_or_flags: ALU_or_flags_MUX
    is_in_interruption: bool

    def __init__(self):
        self.mem_size = 0x100
        self.AR = 0
        self.DR = 0
        self.memory = [0 for i in range(self.mem_size)]
        self.registers = [0 for i in range(16)]
        self.selected_register = RegisterEnum.R0
        self.NZC = [False, False, False]
        self.ALU_out = [0, False, False, False]
        self.ALU_operation = ALU_Operation.AND
        self.first_ALU_input = 0
        self.data_from_memory = 0
        self.memory_mapped_registers = [0 for i in range(4)]
        self.memory_mapped_registers_address = 0xFFFFFC
        self.useCarry = False
        self.plus1 = False
        self.used_ALU_inputs = [False, False]
        self.registers_memory_alu_or_flags_MUX = (
            Registers_Memory_ALU_or_Flags_MUX.MEMORY
        )
        self.is_in_interruption = False
        self.alu_or_flags = ALU_or_flags_MUX.FLAGS
        self.interruption_num = 0

    def set_AR(self):
        match self.registers_memory_alu_or_flags_MUX:
            case Registers_Memory_ALU_or_Flags_MUX.REGISTERS:
                self.AR = self.registers[self.selected_register.value]
            case Registers_Memory_ALU_or_Flags_MUX.ALU:
                self.AR = self.ALU_out[0]
            case Registers_Memory_ALU_or_Flags_MUX.MEMORY:
                self.AR = self.data_from_memory
            case Registers_Memory_ALU_or_Flags_MUX.FLAGS:
                NZC = list(map(int, self.NZC))
                self.DR = (
                    self.interruption_num
                    | int(self.is_in_interruption) << 5
                    | int(NZC[NZC_Flags.CARRY.value]) << 6
                    | int(NZC[NZC_Flags.ZERO.value]) << 7
                    | int(NZC[NZC_Flags.NEGATIVE.value]) << 8
                )
        if (
            self.AR & self.memory_mapped_registers_address
            != self.memory_mapped_registers_address
        ):
            self.data_from_memory = (
                self.memory[self.AR] << 24
                | self.memory[self.AR + 1] << 16
                | self.memory[self.AR + 2] << 8
                | self.memory[self.AR + 3]
            )
        else:
            self.data_from_memory = self.memory_mapped_registers[self.AR % 4]

    def set_DR(self):
        match self.registers_memory_alu_or_flags_MUX:
            case Registers_Memory_ALU_or_Flags_MUX.REGISTERS:
                self.DR = self.registers[self.selected_register.value]
            case Registers_Memory_ALU_or_Flags_MUX.ALU:
                self.DR = self.ALU_out[0]
            case Registers_Memory_ALU_or_Flags_MUX.MEMORY:
                self.DR = self.data_from_memory
            case Registers_Memory_ALU_or_Flags_MUX.FLAGS:
                NZC = list(map(int, self.NZC))
                self.DR = (
                    self.interruption_num
                    | int(self.is_in_interruption) << 5
                    | int(NZC[NZC_Flags.CARRY.value]) << 6
                    | int(NZC[NZC_Flags.ZERO.value]) << 7
                    | int(NZC[NZC_Flags.NEGATIVE.value]) << 8
                )
        self.update_ALU_out()

    def reset_DR(self):
        self.DR = 0
        self.update_ALU_out()

    def select_registers_memory_or_alu(
        self, memory_or_alu: Registers_Memory_ALU_or_Flags_MUX
    ):
        self.registers_memory_alu_or_flags_MUX = memory_or_alu

    def write_to_memory(self):
        if self.AR & 0xFFFFFC != 0xFFFFFC:
            self.memory[self.AR] = (self.DR >> 24) & 0xFF
            self.memory[self.AR + 1] = (self.DR >> 16) & 0xFF
            self.memory[self.AR + 2] = (self.DR >> 8) & 0xFF
            self.memory[self.AR + 3] = self.DR & 0xFF
        else:
            self.memory_mapped_registers[self.AR % 4] = self.DR

    def set_first_ALU_input(self):
        match self.registers_memory_alu_or_flags_MUX:
            case Registers_Memory_ALU_or_Flags_MUX.REGISTERS:
                self.first_ALU_input = self.registers[self.selected_register.value]
            case Registers_Memory_ALU_or_Flags_MUX.ALU:
                self.first_ALU_input = self.ALU_out[0]
            case Registers_Memory_ALU_or_Flags_MUX.MEMORY:
                self.first_ALU_input = self.data_from_memory
            case Registers_Memory_ALU_or_Flags_MUX.FLAGS:
                NZC = list(map(int, self.NZC))
                self.DR = (
                    self.interruption_num
                    | int(self.is_in_interruption) << 5
                    | int(NZC[NZC_Flags.CARRY.value]) << 6
                    | int(NZC[NZC_Flags.ZERO.value]) << 7
                    | int(NZC[NZC_Flags.NEGATIVE.value]) << 8
                )
        self.update_ALU_out()

    def reset_first_ALU_input(self):
        self.first_ALU_input = 0
        self.update_ALU_out()

    def set_register(self):
        self.registers[self.selected_register.value] = self.ALU_out[0]

    def set_ALU_operation(self, operation: ALU_Operation):
        self.ALU_operation = operation
        self.update_ALU_out()

    def update_ALU_out(self):
        first = self.first_ALU_input if self.used_ALU_inputs[0] else 0
        second = self.DR if self.used_ALU_inputs[1] else 0
        match self.ALU_operation:
            case ALU_Operation.AND:
                out = first & second
                self.ALU_out = [out, out & (1 << 31) != 0, out == 0, False]
            case ALU_Operation.NOT:
                out = crop(~second, 32)
                self.ALU_out = [out, out & (1 << 31) != 0, out == 0, False]
            case ALU_Operation.SUM:
                out = first + second
                if (self.useCarry and self.NZC[2]) or self.plus1:
                    out += 1
                self.ALU_out = [
                    crop(out, 32),
                    out & (1 << 31) != 0,
                    crop(out, 32) == 0,
                    out > 2**32 - 1,
                ]
            case ALU_Operation.LS:
                out = first << second
                self.ALU_out = [
                    crop(out, 32),
                    out & (1 << 31) != 0,
                    crop(out, 32) == 0,
                    out & (2**32) != 0,
                ]
            case ALU_Operation.RS:
                out = first >> second
                self.ALU_out = [
                    crop(out, 32),
                    out & (1 << 31) != 0,
                    crop(out, 32) == 0,
                    (first >> (second - 1)) & 1 != 0,
                ]
            case ALU_Operation.CROP:
                out = second & 0xFFFF
                if second & 0x8000 != 0:
                    out |= 0xFFFF0000
                self.ALU_out = [out, out & (1 << 31) != 0, out == 0, False]
            case ALU_Operation.MUL:
                out = first * second
                self.ALU_out = [
                    crop(out, 32),
                    out & (1 << 31) != 0,
                    crop(out, 32) == 0,
                    False,
                ]
            case ALU_Operation.DIV:
                out = first // second
                self.ALU_out = [
                    crop(out, 32),
                    out & (1 << 31) != 0,
                    crop(out, 32) == 0,
                    False,
                ]
            case ALU_Operation.FIND_LOW_1:
                bit = 0
                while bit < 32:
                    if (second >> bit) & 1 != 0:
                        break
                    bit += 1
                self.ALU_out = [bit, False, bit == 0, False]
            case ALU_Operation.OR:
                out = first | second
                self.ALU_out = [
                    crop(out, 32),
                    out & (1 << 31) != 0,
                    crop(out, 32) == 0,
                    False,
                ]
            case ALU_Operation.NEG:
                out = (-second) & 0xFFFFFFFF
                self.ALU_out = [out, out & (1 << 31) != 0, out == 0, False]
            case ALU_Operation.SUB:
                out = first - second
                self.ALU_out = [
                    crop(out, 32),
                    out & (1 << 31) != 0,
                    crop(out, 32) == 0,
                    (first + second) > (1 << 32),
                ]

    def set_NZC(self):
        match self.alu_or_flags:
            case ALU_or_flags_MUX.ALU:
                self.NZC = [
                    self.ALU_out[0] & (1 << 8) != 0,
                    self.ALU_out[0] & (1 << 7) != 0,
                    self.ALU_out[0] & (1 << 6) != 0,
                ]
            case ALU_or_flags_MUX.FLAGS:
                self.NZC = self.ALU_out[1:]

    def select_register(self, register_num: RegisterEnum):
        self.selected_register = register_num

    def set_use_carry(self):
        self.useCarry = True
        self.update_ALU_out()

    def reset_use_carry(self):
        self.useCarry = False
        self.update_ALU_out()

    def set_plus_1(self):
        self.plus1 = True
        self.update_ALU_out()

    def reset_plus_1(self):
        self.plus1 = False
        self.update_ALU_out()

    def get_NZC(self):
        return self.NZC

    def get_ALU_flags(self):
        return self.ALU_out[1:]

    def get_IR(self):
        return self.registers[RegisterEnum.IR.value]

    def get_INTR(self):
        return self.registers[RegisterEnum.INTR.value]

    def set_use_first_ALU_input(self):
        self.used_ALU_inputs[0] = True
        self.update_ALU_out()

    def reset_use_first_ALU_input(self):
        self.used_ALU_inputs[0] = False
        self.update_ALU_out()

    def set_use_second_ALU_input(self):
        self.used_ALU_inputs[1] = True
        self.update_ALU_out()

    def reset_use_second_ALU_input(self):
        self.used_ALU_inputs[1] = False
        self.update_ALU_out()

    def select_ALU_out_for_flags(self):
        self.alu_or_flags = ALU_or_flags_MUX.ALU

    def select_ALU_flags_for_flags(self):
        self.alu_or_flags = ALU_or_flags_MUX.FLAGS

    def set_is_in_interruption(self):
        self.is_in_interruption = self.ALU_out[0] & (1 << 5) != 0

    def set_interuption_num(self):
        self.interruption_num = self.ALU_out[0] & 0x1F

    def add_interruption(self, int_num):
        self.registers[RegisterEnum.INTR.value] |= 1 << int_num

    def get_memory_mapped_register(self, reg: int):
        return self.memory_mapped_registers[reg]

    def set_memory_mapped_register(self, reg: int, value: int):
        self.memory_mapped_registers[reg] = value & (2**32 - 1)

    def get_int_num(self):
        return self.interruption_num
