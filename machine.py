from DataPath import DataPath, Registers_Memory_ALU_or_Flags_MUX, RegisterEnum, ALU_Operation, ALU_or_flags_MUX
from enum import Enum
from sys import argv
import pandas as pd
class Opcode(Enum):
    NOP=0 # Заглушка
    MOV=1 # Скопировать содержимое регистра в другой
    LDR=2 # Загрузить в регистр содержимое памяти
    STR=3 # Сохранить в память содержимое регистра
    PUSH=4
    POP=5
    B=6 # Переход на метку (относительно регистра PC)
    BL=7 # Переход метку с ссылкой
    BX=8 # Переход на адрес из регистра
    BLX=9 # Переход на адрес из регистра с ссылкой
    AND=10
    OR=11
    NOT=12
    NEG=13
    ADD=14
    SUB=15
    MUL=16
    DIV=17
    LS=18 # Сдвиг влево
    RS=19 # Сдвиг вправо
    HALT=20 # Останов
    INT=21 # Вызвать прерывание
    CMP=22
    ExINT=23 # Выйти из прерывания
class AddressType(Enum):
    RELATIVE_PC = 0
    REGISTER = 1
    ABSOLUTE = 2
class Register_or_Immediate(Enum):
    IMMEDIATE=0
    REGISTER=1
class ControlUnit:
    def __init__(self):
        self.datapath = DataPath()
        self._tick = 0
        self._is_working=True
    def tick(self):
        self._tick += 1
    def instruction_fetch(self):
        # PC -> AR
        self.datapath.select_register(RegisterEnum.PC)
        self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.REGISTERS)
        self.datapath.set_ALU_operation(ALU_Operation.SUM)
        self.datapath.reset_plus_1()
        self.datapath.reset_use_carry()
        self.tick()

        self.datapath.set_first_ALU_input()
        self.datapath.set_use_first_ALU_input()
        self.datapath.reset_use_second_ALU_input()
        self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.ALU)
        self.tick()

        self.datapath.set_AR()
        self.tick()

        #PC+1 -> PC
        self.datapath.set_plus_1()
        self.tick()

        self.datapath.set_first_ALU_input()
        self.tick()

        self.datapath.set_first_ALU_input()
        self.tick()

        self.datapath.set_first_ALU_input()
        self.tick()

        self.datapath.set_register()
        self.tick()

        #[AR] -> DR
        self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.MEMORY)
        self.tick()

        #DR -> IR
        self.datapath.set_DR()
        self.datapath.reset_first_ALU_input()
        self.datapath.reset_plus_1()
        self.datapath.set_use_second_ALU_input()
        self.datapath.reset_use_first_ALU_input()
        self.tick()

        self.datapath.select_register(RegisterEnum.IR)
        self.tick()

        self.datapath.set_register()
        self.tick()
    def get_opcode_from_IR(self):
        return Opcode((self.datapath.get_IR()>>27)&0b11111)
    def get_conditions_from_IR(self):
        flags = (self.datapath.get_IR()>>21)&0b111111
        return ([(flags & 1<<i) > 0 for i in reversed(range(6))])
    def get_first_register_from_IR(self):
        return RegisterEnum((self.datapath.get_IR()>>17)&0xf)
    def get_second_register_from_IR(self):
        return RegisterEnum((self.datapath.get_IR()>>12)&0xf)
    def get_third_register_from_IR(self):
        return RegisterEnum((self.datapath.get_IR()>>8)&0xf)
    def get_relative_type_from_IR(self):
        return AddressType((self.datapath.get_IR()>>16)&1)
    def conditions_check(self):
        conds = self.get_conditions_from_IR()
        flags = self.datapath.get_NZC()
        return all([(not conds[2*i]) or (flags[i] == conds[2*i+1]) for i in range(3)])
    def get_address_for_LDR_and_STR(self):
        match self.get_relative_type_from_IR():
            case AddressType.REGISTER:
                self.datapath.select_register(self.get_second_register_from_IR())
                self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.REGISTERS)
                self.tick()

                self.datapath.set_AR()
                self.tick()
            case AddressType.RELATIVE_PC:
                self.datapath.select_register(RegisterEnum.IR)
                self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.REGISTERS)
                self.tick()

                self.datapath.set_DR()
                self.tick()

                self.datapath.select_register(RegisterEnum.PC)
                self.tick()

                self.datapath.set_first_ALU_input()
                self.tick()

                self.datapath.reset_use_carry()
                self.datapath.set_ALU_operation(ALU_Operation.CROP)
                self.datapath.reset_plus_1()
                self.datapath.set_use_second_ALU_input()
                self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.ALU)
                self.tick()

                self.datapath.set_DR()
                self.tick()

                self.datapath.set_ALU_operation(ALU_Operation.SUM)
                self.datapath.set_use_first_ALU_input()
                self.tick()

                self.datapath.set_AR()
                self.tick()
    def branch(self):
        self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.REGISTERS)
        self.datapath.select_register(RegisterEnum.IR)
        self.tick()

        self.datapath.set_DR()
        self.datapath.set_ALU_operation(ALU_Operation.CROP)
        self.datapath.reset_use_first_ALU_input()
        self.datapath.set_use_second_ALU_input()
        self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.ALU)
        self.tick()

        self.datapath.set_DR()
        self.tick()

        self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.REGISTERS)
        self.datapath.select_register(RegisterEnum.PC)
        self.tick()

        self.datapath.set_first_ALU_input()
        self.datapath.set_use_first_ALU_input()
        self.datapath.set_ALU_operation(ALU_Operation.SUM)
        self.tick()

        self.datapath.set_register()
        self.tick()
    def save_link(self):
        self.datapath.reset_use_carry()
        self.datapath.reset_plus_1()
        self.datapath.select_register(RegisterEnum.PC)
        self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.REGISTERS)
        self.tick()

        self.datapath.reset_use_second_ALU_input()
        self.datapath.set_first_ALU_input()
        self.datapath.set_use_first_ALU_input()
        self.datapath.set_ALU_operation(ALU_Operation.SUM)
        self.tick()

        self.datapath.select_register(RegisterEnum.LR)
        self.tick()

        self.datapath.set_register()
        self.tick()
    def branch_from_register(self):
        self.datapath.reset_use_carry()
        self.datapath.reset_plus_1()
        self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.REGISTERS)
        self.datapath.select_register(self.get_first_register_from_IR())
        self.tick()

        self.datapath.reset_use_second_ALU_input()
        self.datapath.set_first_ALU_input()
        self.datapath.set_use_first_ALU_input()
        self.datapath.set_ALU_operation(ALU_Operation.SUM)
        self.tick()

        self.datapath.select_register(RegisterEnum.PC)
        self.tick()
        
        self.datapath.set_register()
        self.tick()
    def get_register_or_immediately_flag_from_IR(self):
        return Register_or_Immediate((self.datapath.get_IR()>>16)&1)
    def execute_fetch(self):
        opcode = self.get_opcode_from_IR()
        match opcode:
            case Opcode.NOP:
                pass
            case Opcode.MOV:
                self.datapath.reset_DR()
                self.datapath.select_register(self.get_second_register_from_IR())
                self.datapath.reset_plus_1()
                self.datapath.reset_use_carry()
                self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.REGISTERS)
                self.tick()

                self.datapath.set_first_ALU_input()
                self.datapath.set_use_first_ALU_input()
                self.datapath.reset_use_second_ALU_input()
                self.datapath.set_ALU_operation(ALU_Operation.SUM)
                self.tick()

                self.datapath.select_register(self.get_first_register_from_IR())
                self.tick()

                self.datapath.set_register()
                self.tick()
            case Opcode.LDR:
                self.get_address_for_LDR_and_STR()
                self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.MEMORY)
                self.tick()

                self.datapath.set_DR()
                self.tick()

                self.datapath.reset_use_carry()
                self.datapath.reset_plus_1()
                self.datapath.set_use_second_ALU_input()
                self.datapath.reset_first_ALU_input()
                self.datapath.set_ALU_operation(ALU_Operation.SUM)
                self.datapath.select_register(self.get_first_register_from_IR())
                self.tick()

                self.datapath.set_register()
                self.tick()
            case Opcode.STR:
                self.get_address_for_LDR_and_STR()
                self.datapath.select_register(self.get_first_register_from_IR())
                self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.REGISTERS)
                self.tick()

                self.datapath.set_first_ALU_input()
                self.tick()

                self.datapath.set_use_first_ALU_input()
                self.datapath.reset_use_second_ALU_input()
                self.datapath.set_ALU_operation(ALU_Operation.SUM)
                self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.ALU)
                self.tick()

                self.datapath.set_DR()
                self.tick()

                self.datapath.write_to_memory()
                self.tick()
            case Opcode.PUSH:
                self.datapath.reset_DR()
                self.datapath.set_ALU_operation(ALU_Operation.SUM)
                self.datapath.set_plus_1()
                self.datapath.reset_use_carry()
                self.datapath.set_use_second_ALU_input()
                self.datapath.reset_use_first_ALU_input()
                self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.ALU)
                self.tick()
                
                self.datapath.set_DR()
                self.tick()

                self.datapath.set_DR()
                self.tick()

                self.datapath.set_DR()
                self.tick()

                self.datapath.set_ALU_operation(ALU_Operation.NOT)
                self.tick()

                self.datapath.set_DR()
                self.tick()

                self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.REGISTERS)
                self.datapath.select_register(RegisterEnum.SP)
                self.datapath.reset_plus_1()
                self.tick()

                self.datapath.set_first_ALU_input()
                self.datapath.set_use_first_ALU_input()
                self.datapath.set_ALU_operation(ALU_Operation.SUM)
                self.tick()

                self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.ALU)
                self.tick()

                self.datapath.set_register()
                self.datapath.set_AR()
                self.tick()

                self.datapath.select_register(self.get_first_register_from_IR())
                self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.REGISTERS)
                self.tick()

                self.datapath.set_first_ALU_input()
                self.datapath.reset_use_second_ALU_input()
                self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.ALU)
                self.tick()

                self.datapath.set_DR()
                self.tick()

                self.datapath.write_to_memory()
                self.tick()
            case Opcode.POP:
                self.datapath.reset_DR()
                self.datapath.set_ALU_operation(ALU_Operation.SUM)
                self.datapath.set_plus_1()
                self.datapath.reset_use_carry()
                self.datapath.set_use_second_ALU_input()
                self.datapath.reset_use_first_ALU_input()
                self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.ALU)
                self.tick()
                
                self.datapath.set_DR()
                self.tick()

                self.datapath.set_DR()
                self.tick()

                self.datapath.set_DR()
                self.tick()

                self.datapath.set_DR()
                self.tick()

                self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.REGISTERS)
                self.datapath.select_register(RegisterEnum.SP)
                self.datapath.reset_plus_1()
                self.tick()

                self.datapath.set_first_ALU_input()
                self.datapath.set_use_first_ALU_input()
                self.datapath.set_ALU_operation(ALU_Operation.SUM)
                self.datapath.reset_use_second_ALU_input()
                self.tick()

                self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.ALU)
                self.tick()

                self.datapath.set_AR()
                self.tick()

                self.datapath.set_use_second_ALU_input()
                self.tick()

                self.datapath.set_register()
                self.tick()

                self.datapath.select_register(self.get_first_register_from_IR())
                self.tick()

                self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.MEMORY)
                self.tick()

                self.datapath.reset_use_first_ALU_input()
                self.datapath.set_DR()
                self.tick()

                self.datapath.select_register(self.get_first_register_from_IR())
                self.tick()

                self.datapath.set_register()
                self.tick()
            case Opcode.B:
                self.branch()
            case Opcode.BL:
                self.save_link()

                self.branch()
            case Opcode.BX:
                self.branch_from_register()
            case Opcode.BLX:
                self.save_link()

                self.branch_from_register()
            case Opcode.AND:
                self.datapath.reset_use_carry()
                self.datapath.reset_plus_1()
                self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.REGISTERS)
                self.datapath.select_register(self.get_first_register_from_IR())
                self.tick()

                self.datapath.set_first_ALU_input()
                self.datapath.reset_use_first_ALU_input()
                self.tick()
                match self.get_register_or_immediately_flag_from_IR():
                    case Register_or_Immediate.REGISTER:
                        self.datapath.select_register(self.get_second_register_from_IR())
                        self.tick()
                    case Register_or_Immediate.IMMEDIATE:
                        self.datapath.select_register(RegisterEnum.IR)
                        self.tick()

                        self.datapath.set_DR()
                        self.tick()

                        self.datapath.set_use_second_ALU_input()
                        self.datapath.set_ALU_operation(ALU_Operation.CROP)
                        self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.ALU)
                        self.tick()
                self.datapath.set_DR()
                self.tick()
                        
                self.datapath.set_use_first_ALU_input()
                self.datapath.set_use_second_ALU_input()
                self.datapath.set_ALU_operation(ALU_Operation.AND)
                self.tick()

                self.datapath.select_register(self.get_first_register_from_IR())
                self.datapath.select_ALU_flags_for_flags()
                self.tick()

                self.datapath.set_register()
                self.datapath.set_NZC()
                self.tick()
            case Opcode.OR:
                self.datapath.reset_use_carry()
                self.datapath.reset_plus_1()
                self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.REGISTERS)
                self.datapath.select_register(self.get_first_register_from_IR())
                self.tick()

                self.datapath.set_first_ALU_input()
                self.datapath.reset_use_first_ALU_input()
                self.tick()
                match self.get_register_or_immediately_flag_from_IR():
                    case Register_or_Immediate.REGISTER:
                        self.datapath.select_register(self.get_second_register_from_IR())
                        self.tick()
                    case Register_or_Immediate.IMMEDIATE:
                        self.datapath.select_register(RegisterEnum.IR)
                        self.tick()

                        self.datapath.set_DR()
                        self.tick()

                        self.datapath.set_use_second_ALU_input()
                        self.datapath.set_ALU_operation(ALU_Operation.CROP)
                        self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.ALU)
                        self.tick()
                self.datapath.set_DR()
                self.tick()
                        
                self.datapath.set_use_first_ALU_input()
                self.datapath.set_use_second_ALU_input()
                self.datapath.set_ALU_operation(ALU_Operation.OR)
                self.tick()

                self.datapath.select_register(self.get_first_register_from_IR())
                self.datapath.select_ALU_flags_for_flags()
                self.tick()

                self.datapath.set_register()
                self.datapath.set_NZC()
                self.tick()
            case Opcode.NOT:
                self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.REGISTERS)
                self.datapath.select_register(self.get_first_register_from_IR())
                self.tick()

                self.datapath.set_DR()
                self.datapath.reset_plus_1()
                self.datapath.reset_use_carry()
                self.datapath.set_use_second_ALU_input()
                self.datapath.reset_use_first_ALU_input()
                self.datapath.set_ALU_operation(ALU_Operation.NOT)
                self.datapath.select_ALU_flags_for_flags()
                self.tick()

                self.datapath.set_register()
                self.datapath.set_NZC()
                self.tick()
            case Opcode.NEG:
                self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.REGISTERS)
                self.datapath.select_register(self.get_first_register_from_IR())
                self.tick()

                self.datapath.set_DR()
                self.tick()

                self.datapath.reset_plus_1()
                self.datapath.reset_use_carry()
                self.datapath.set_use_second_ALU_input()
                self.datapath.reset_use_first_ALU_input()
                self.datapath.set_ALU_operation(ALU_Operation.NEG)
                self.datapath.select_ALU_flags_for_flags()
                self.tick()

                self.datapath.set_register()
                self.datapath.set_NZC()
                self.tick()
            case Opcode.ADD:
                self.datapath.reset_use_carry()
                self.datapath.reset_plus_1()
                self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.REGISTERS)
                self.datapath.select_register(self.get_first_register_from_IR())
                self.tick()

                self.datapath.set_first_ALU_input()
                self.datapath.reset_use_first_ALU_input()
                self.tick()
                match self.get_register_or_immediately_flag_from_IR():
                    case Register_or_Immediate.REGISTER:
                        self.datapath.select_register(self.get_second_register_from_IR())
                        self.tick()
                    case Register_or_Immediate.IMMEDIATE:
                        self.datapath.select_register(RegisterEnum.IR)
                        self.tick()

                        self.datapath.set_DR()
                        self.datapath.set_use_second_ALU_input()
                        self.datapath.set_ALU_operation(ALU_Operation.CROP)
                        self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.ALU)
                        self.tick()
                self.datapath.set_DR()
                self.tick()

                self.datapath.set_use_first_ALU_input()
                self.datapath.set_use_second_ALU_input()
                self.datapath.set_ALU_operation(ALU_Operation.SUM)
                self.tick()

                self.datapath.select_register(self.get_first_register_from_IR())
                self.datapath.select_ALU_flags_for_flags()
                self.tick()

                self.datapath.set_register()
                self.datapath.set_NZC()
                self.tick()
            case Opcode.SUB:
                self.datapath.reset_use_carry()
                self.datapath.reset_plus_1()
                self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.REGISTERS)
                self.datapath.select_register(self.get_first_register_from_IR())
                self.tick()

                self.datapath.set_first_ALU_input()
                self.datapath.reset_use_first_ALU_input()
                self.tick()
                match self.get_register_or_immediately_flag_from_IR():
                    case Register_or_Immediate.REGISTER:
                        self.datapath.select_register(self.get_second_register_from_IR())
                        self.tick()
                    case Register_or_Immediate.IMMEDIATE:
                        self.datapath.select_register(RegisterEnum.IR)
                        self.tick()

                        self.datapath.set_DR()
                        self.datapath.set_use_second_ALU_input()
                        self.datapath.set_ALU_operation(ALU_Operation.CROP)
                        self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.ALU)
                        self.tick()
                self.datapath.set_DR()
                self.tick()

                self.datapath.set_ALU_operation(ALU_Operation.NOT)
                self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.ALU)
                self.tick()

                self.datapath.set_DR()
                self.tick()

                self.datapath.set_plus_1()
                self.datapath.set_use_first_ALU_input()
                self.datapath.set_use_second_ALU_input()
                self.datapath.set_ALU_operation(ALU_Operation.SUM)
                self.tick()

                self.datapath.select_register(self.get_first_register_from_IR())
                self.datapath.select_ALU_flags_for_flags()
                self.tick()

                self.datapath.set_register()
                self.datapath.set_NZC()
                self.tick()
            case Opcode.MUL:
                self.datapath.reset_use_carry()
                self.datapath.reset_plus_1()
                self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.REGISTERS)
                self.datapath.select_register(self.get_first_register_from_IR())
                self.tick()

                self.datapath.set_first_ALU_input()
                self.datapath.reset_use_first_ALU_input()
                self.tick()
                match self.get_register_or_immediately_flag_from_IR():
                    case Register_or_Immediate.REGISTER:
                        self.datapath.select_register(self.get_second_register_from_IR())
                        self.tick()
                    case Register_or_Immediate.IMMEDIATE:
                        self.datapath.select_register(RegisterEnum.IR)
                        self.tick()

                        self.datapath.set_DR()
                        self.datapath.set_use_second_ALU_input()
                        self.datapath.set_ALU_operation(ALU_Operation.CROP)
                        self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.ALU)
                        self.tick()
                self.datapath.set_DR()
                self.tick()

                self.datapath.set_use_first_ALU_input()
                self.datapath.set_use_second_ALU_input()
                self.datapath.set_ALU_operation(ALU_Operation.MUL)
                self.tick()

                self.datapath.select_register(self.get_first_register_from_IR())
                self.datapath.select_ALU_flags_for_flags()
                self.tick()

                self.datapath.set_register()
                self.datapath.set_NZC()
                self.tick()
            case Opcode.DIV:
                self.datapath.reset_use_carry()
                self.datapath.reset_plus_1()
                self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.REGISTERS)
                self.datapath.select_register(self.get_first_register_from_IR())
                self.tick()

                self.datapath.set_first_ALU_input()
                self.datapath.reset_use_first_ALU_input()
                self.tick()
                match self.get_register_or_immediately_flag_from_IR():
                    case Register_or_Immediate.REGISTER:
                        self.datapath.select_register(self.get_second_register_from_IR())
                        self.tick()
                    case Register_or_Immediate.IMMEDIATE:
                        self.datapath.select_register(RegisterEnum.IR)
                        self.tick()

                        self.datapath.set_DR()
                        self.datapath.set_use_second_ALU_input()
                        self.datapath.set_ALU_operation(ALU_Operation.CROP)
                        self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.ALU)
                        self.tick()
                self.datapath.set_DR()
                self.tick()

                self.datapath.set_use_first_ALU_input()
                self.datapath.set_use_second_ALU_input()
                self.datapath.set_ALU_operation(ALU_Operation.DIV)
                self.tick()

                self.datapath.select_register(self.get_first_register_from_IR())
                self.datapath.select_ALU_flags_for_flags()
                self.tick()

                self.datapath.set_register()
                self.datapath.set_NZC()
                self.tick()
            case Opcode.LS:
                self.datapath.reset_use_carry()
                self.datapath.reset_plus_1()
                self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.REGISTERS)
                self.datapath.select_register(self.get_first_register_from_IR())
                self.tick()

                self.datapath.set_first_ALU_input()
                self.datapath.reset_use_first_ALU_input()
                self.tick()
                match self.get_register_or_immediately_flag_from_IR():
                    case Register_or_Immediate.REGISTER:
                        self.datapath.select_register(self.get_second_register_from_IR())
                        self.tick()
                    case Register_or_Immediate.IMMEDIATE:
                        self.datapath.select_register(RegisterEnum.IR)
                        self.tick()

                        self.datapath.set_DR()
                        self.datapath.set_use_second_ALU_input()
                        self.datapath.set_ALU_operation(ALU_Operation.CROP)
                        self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.ALU)
                        self.tick()
                self.datapath.set_DR()
                self.tick()

                self.datapath.set_use_first_ALU_input()
                self.datapath.set_use_second_ALU_input()
                self.datapath.set_ALU_operation(ALU_Operation.LS)
                self.tick()

                self.datapath.select_register(self.get_first_register_from_IR())
                self.datapath.select_ALU_flags_for_flags()
                self.tick()

                self.datapath.set_register()
                self.datapath.set_NZC()
                self.tick()
            case Opcode.RS:
                self.datapath.reset_use_carry()
                self.datapath.reset_plus_1()
                self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.REGISTERS)
                self.datapath.select_register(self.get_first_register_from_IR())
                self.tick()

                self.datapath.set_first_ALU_input()
                self.datapath.reset_use_first_ALU_input()
                self.tick()
                match self.get_register_or_immediately_flag_from_IR():
                    case Register_or_Immediate.REGISTER:
                        self.datapath.select_register(self.get_second_register_from_IR())
                        self.tick()
                    case Register_or_Immediate.IMMEDIATE:
                        self.datapath.select_register(RegisterEnum.IR)
                        self.tick()

                        self.datapath.set_DR()
                        self.datapath.set_use_second_ALU_input()
                        self.datapath.set_ALU_operation(ALU_Operation.CROP)
                        self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.ALU)
                        self.tick()
                self.datapath.set_DR()
                self.tick()

                self.datapath.set_use_first_ALU_input()
                self.datapath.set_use_second_ALU_input()
                self.datapath.set_ALU_operation(ALU_Operation.RS)
                self.tick()

                self.datapath.select_register(self.get_first_register_from_IR())
                self.datapath.select_ALU_flags_for_flags()
                self.tick()

                self.datapath.set_register()
                self.datapath.set_NZC()
                self.tick()
            case Opcode.HALT:
                self._is_working=False
            case Opcode.INT:
                self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.REGISTERS)
                self.datapath.select_register(RegisterEnum.IR)
                self.tick()

                self.datapath.set_DR()
                self.tick()

                self.datapath.set_ALU_operation(ALU_Operation.CROP)
                self.datapath.set_use_second_ALU_input()
                self.datapath.reset_use_first_ALU_input()
                self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.ALU)
                self.tick()

                self.datapath.set_DR()
                self.tick()

                self.datapath.reset_use_second_ALU_input()
                self.datapath.set_plus_1()
                self.datapath.reset_use_carry()
                self.datapath.set_ALU_operation(ALU_Operation.SUM)
                self.tick()

                self.datapath.set_first_ALU_input()
                self.tick()

                self.datapath.set_ALU_operation(ALU_Operation.LS)
                self.datapath.reset_plus_1()
                self.datapath.set_use_first_ALU_input()
                self.datapath.set_use_second_ALU_input()
                self.tick()

                self.datapath.set_first_ALU_input()
                self.tick()

                self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.REGISTERS)
                self.datapath.select_register(RegisterEnum.INTR)
                self.tick()
                
                self.datapath.set_DR()
                self.tick()

                self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.ALU)
                self.datapath.set_ALU_operation(ALU_Operation.OR)
                self.datapath.set_use_first_ALU_input()
                self.tick()

                self.datapath.set_register()
                self.tick()
            case Opcode.CMP:
                self.datapath.reset_use_carry()
                self.datapath.reset_plus_1()
                self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.REGISTERS)
                self.datapath.select_register(self.get_first_register_from_IR())
                self.tick()

                self.datapath.set_first_ALU_input()
                self.datapath.reset_use_first_ALU_input()
                self.tick()
                match self.get_register_or_immediately_flag_from_IR():
                    case Register_or_Immediate.REGISTER:
                        self.datapath.select_register(self.get_second_register_from_IR())
                        self.tick()
                    case Register_or_Immediate.IMMEDIATE:
                        self.datapath.select_register(RegisterEnum.IR)
                        self.tick()

                        self.datapath.set_DR()
                        self.datapath.set_use_second_ALU_input()
                        self.datapath.set_ALU_operation(ALU_Operation.CROP)
                        self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.ALU)
                        self.tick()
                self.datapath.set_DR()
                self.tick()

                self.datapath.set_ALU_operation(ALU_Operation.NOT)
                self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.ALU)
                self.tick()

                self.datapath.set_DR()
                self.tick()

                self.datapath.set_plus_1()
                self.datapath.set_use_first_ALU_input()
                self.datapath.set_use_second_ALU_input()
                self.datapath.set_ALU_operation(ALU_Operation.SUM)
                self.tick()

                self.datapath.select_ALU_flags_for_flags()
                self.tick()

                self.datapath.set_NZC()
                self.tick()
            case Opcode.ExINT:
                self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.REGISTERS)
                self.datapath.select_register(RegisterEnum.SP)
                self.tick()

                self.datapath.set_AR()
                self.datapath.set_first_ALU_input()
                self.tick()

                self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.MEMORY)
                self.tick()

                self.datapath.set_DR()
                self.tick()

                self.datapath.set_ALU_operation(ALU_Operation.SUM)
                self.datapath.reset_use_first_ALU_input()
                self.datapath.set_use_second_ALU_input()
                self.datapath.reset_plus_1()
                self.datapath.reset_use_carry()
                self.datapath.select_ALU_out_for_flags()
                self.tick()

                self.datapath.set_NZC()
                self.datapath.set_is_in_interruption()
                self.datapath.set_interuption_num()
                self.tick()

                self.datapath.set_use_first_ALU_input()
                self.datapath.reset_use_second_ALU_input()
                self.datapath.set_plus_1()
                self.datapath.set_ALU_operation(ALU_Operation.SUM)
                self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.ALU)
                self.tick()

                self.datapath.set_first_ALU_input()
                self.tick()

                self.datapath.set_first_ALU_input()
                self.tick()

                self.datapath.set_first_ALU_input()
                self.tick()

                self.datapath.set_AR()
                self.datapath.set_register()
                self.tick()

                self.datapath.set_first_ALU_input()
                self.tick()

                self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.MEMORY)
                self.tick()

                self.datapath.set_DR()
                self.datapath.set_use_second_ALU_input()
                self.datapath.reset_use_first_ALU_input()
                self.datapath.reset_plus_1()
                self.datapath.select_register(RegisterEnum.PC)
                self.tick()

                self.datapath.set_register()
                self.tick()

                self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.ALU)
                self.datapath.set_plus_1()
                self.datapath.set_use_first_ALU_input()
                self.datapath.reset_use_second_ALU_input()
                self.datapath.select_register(RegisterEnum.SP)
                self.tick()

                self.datapath.set_first_ALU_input()
                self.tick()

                self.datapath.set_first_ALU_input()
                self.tick()

                self.datapath.set_first_ALU_input()
                self.tick()

                self.datapath.set_register()
                self.tick()

    def check_interruptions(self):
        if self.datapath.get_INTR() != 0 and not self.datapath.is_in_interruption:
            # SP -= 4
            self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.REGISTERS)
            self.datapath.select_register(RegisterEnum.SP)
            self.tick()

            self.datapath.set_first_ALU_input()
            self.tick()

            self.datapath.reset_DR()
            self.datapath.set_plus_1()
            self.datapath.set_use_second_ALU_input()
            self.datapath.reset_use_first_ALU_input()
            self.datapath.set_ALU_operation(ALU_Operation.SUM)
            self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.ALU)
            self.tick()

            self.datapath.set_DR()
            self.tick()

            self.datapath.set_DR()
            self.tick()

            self.datapath.set_DR()
            self.tick()

            self.datapath.set_DR()
            self.tick()
            
            self.datapath.reset_plus_1()
            self.datapath.set_ALU_operation(ALU_Operation.SUB)
            self.datapath.set_use_first_ALU_input()
            self.tick()

            self.datapath.set_AR()
            self.datapath.set_register()
            self.tick()

            self.datapath.set_first_ALU_input()
            self.tick()

            #PC -> [SP]
            self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.REGISTERS)
            self.datapath.select_register(RegisterEnum.PC)
            self.tick()

            self.datapath.set_DR()
            self.tick()

            self.datapath.write_to_memory()
            self.tick()

            #SP -= 4

            self.datapath.reset_DR()
            self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.ALU)
            self.datapath.set_plus_1()
            self.datapath.reset_use_first_ALU_input()
            self.datapath.set_use_second_ALU_input()
            self.datapath.set_ALU_operation(ALU_Operation.SUM)
            self.tick()

            self.datapath.set_DR()
            self.tick()

            self.datapath.set_DR()
            self.tick()

            self.datapath.set_DR()
            self.tick()

            self.datapath.set_DR()
            self.tick()

            self.datapath.set_ALU_operation(ALU_Operation.SUB)
            self.datapath.set_use_first_ALU_input()
            self.datapath.reset_plus_1()
            self.datapath.select_register(RegisterEnum.SP)
            self.tick()

            self.datapath.set_AR()
            self.datapath.set_register()
            self.tick()

            #FLAGS -> [SP]
            self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.FLAGS)
            self.tick()

            self.datapath.set_DR()
            self.tick()
            
            self.datapath.write_to_memory()
            self.tick()

            #first bit of INTR -> FLAGS[INT_NUM]

            self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.REGISTERS)
            self.datapath.select_register(RegisterEnum.INTR)
            self.tick()

            self.datapath.set_DR()
            self.datapath.reset_use_first_ALU_input()
            self.datapath.set_use_second_ALU_input()
            self.datapath.set_ALU_operation(ALU_Operation.FIND_LOW_1)
            self.datapath.select_register(RegisterEnum.PC)
            self.tick()

            self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.ALU)
            self.tick()

            self.datapath.set_first_ALU_input()
            self.datapath.set_interuption_num()
            self.tick()

            #(first bit of INTR) + 1 -> PC

            self.datapath.set_ALU_operation(ALU_Operation.SUM)
            self.datapath.set_plus_1()
            self.datapath.set_use_first_ALU_input()
            self.datapath.reset_use_second_ALU_input()
            self.tick()

            self.datapath.set_first_ALU_input()
            self.tick()

            self.datapath.reset_use_first_ALU_input()
            self.datapath.set_use_second_ALU_input()
            self.datapath.reset_DR()
            self.datapath.set_plus_1()
            self.tick()

            self.datapath.set_DR()
            self.tick()

            self.datapath.set_DR()
            self.tick()

            self.datapath.set_ALU_operation(ALU_Operation.LS)
            self.datapath.reset_plus_1()
            self.datapath.set_use_first_ALU_input()
            self.tick()

            self.datapath.set_register()
            self.tick()

            # INTR &= ~(1<<INT_NUM)

            self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.REGISTERS)
            self.datapath.select_register(RegisterEnum.INTR)
            self.tick()

            self.datapath.set_DR()
            self.tick()

            self.datapath.set_ALU_operation(ALU_Operation.FIND_LOW_1)
            self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.ALU)
            self.datapath.set_use_second_ALU_input()
            self.tick()

            self.datapath.set_DR()
            self.tick()

            self.datapath.set_ALU_operation(ALU_Operation.SUM)
            self.datapath.reset_use_first_ALU_input()
            self.datapath.reset_use_second_ALU_input()
            self.datapath.set_plus_1()
            self.tick()

            self.datapath.set_first_ALU_input()
            self.tick()

            self.datapath.reset_plus_1()
            self.datapath.set_use_first_ALU_input()
            self.datapath.set_use_second_ALU_input()
            self.datapath.set_ALU_operation(ALU_Operation.LS)
            self.tick()

            self.datapath.set_DR()
            self.tick()

            self.datapath.set_ALU_operation(ALU_Operation.NOT)
            self.tick()

            self.datapath.set_first_ALU_input()
            self.tick()

            self.datapath.select_register(RegisterEnum.INTR)
            self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.REGISTERS)
            self.tick()
            
            self.datapath.set_DR()
            self.tick()

            self.datapath.set_ALU_operation(ALU_Operation.AND)
            self.tick()

            self.datapath.set_register()
            self.tick()
            
            #1 -> FLAGS[IS_IN_INT]
            
            self.datapath.select_registers_memory_or_alu(Registers_Memory_ALU_or_Flags_MUX.ALU)
            self.datapath.reset_use_first_ALU_input()
            self.datapath.reset_use_second_ALU_input()
            self.datapath.set_plus_1()
            self.datapath.set_ALU_operation(ALU_Operation.SUM)
            self.tick()

            self.datapath.set_first_ALU_input()
            self.datapath.set_DR()
            self.tick()

            self.datapath.set_use_second_ALU_input()
            self.datapath.set_use_first_ALU_input()
            self.tick()

            self.datapath.set_DR()
            self.tick()

            self.datapath.set_DR()
            self.tick()

            self.datapath.reset_plus_1()
            self.datapath.set_ALU_operation(ALU_Operation.LS)
            self.tick()

            self.datapath.set_is_in_interruption()
            self.tick()
            
    def execute_one_instruction(self):
        self.instruction_fetch()
        if(self.conditions_check()):
            self.execute_fetch()
        self.check_interruptions()

    def interrupt(self, int_num):
        self.datapath.add_interruption(int_num)
if __name__ == '__main__':
    c = ControlUnit()
    c.datapath.mem_size = 0x1000
    c.datapath.memory = [0 for i in range(c.datapath.mem_size)]
    with open(argv[1], 'rb') as f:
        programm = f.read()
        programm = [int.from_bytes(programm[i:i+1], byteorder='big') for i in range(len(programm))]
        c.datapath.memory[:len(programm)] = programm
    input_data = '\0'
    if len (argv) == 4:
        with open(argv[3], 'r') as f:
            input_data = f.read() + '\0'
    c.datapath.registers[RegisterEnum.SP.value]=0x1000-4
    c.datapath.registers[RegisterEnum.PC.value] = 0
    c.datapath.set_memory_mapped_register(1, -1)
    journal = pd.DataFrame(columns = [f'R{i}' for i in range(11)]+['LR','SP','PC','INTR','IR','N','Z','C'])
    while c._is_working:
        c.execute_one_instruction()
        if c.datapath.get_memory_mapped_register(0) != 0:
            print(chr(c.datapath.get_memory_mapped_register(0)), end='')
            c.datapath.set_memory_mapped_register(0,0)
        if c.datapath.get_memory_mapped_register(1) == 0xffffffff:
            if len(input_data) != 0:
                c.datapath.set_memory_mapped_register(1, ord(input_data[0]))
                input_data=input_data[1:]
                c.datapath.add_interruption(0)
        journal.loc[len(journal)] = [hex(i) for i in c.datapath.registers] + c.datapath.get_NZC()
    journal.to_csv(argv[2])
    print('Выполнено тактов:',c._tick)