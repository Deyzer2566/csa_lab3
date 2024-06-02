from sys import argv
import re
from machine import Opcode, RegisterEnum, AddressType, Register_or_Immediate
from enum import Enum

opcodes = {i.name.lower(): i for i in Opcode}
registers = {i.name.lower(): i for i in RegisterEnum}


def get_integer(x):
    return int(x) if x[:2] != "0x" else int(x, 16)


spec_words = {
    "word": lambda x: (get_integer(x), None),
    "string": lambda x: ([ord(i) for i in list(x[1:-1])] + [0], None),
    "org": lambda x: (None, get_integer(x)),
    "words": lambda x: (list(map(get_integer, x.split(","))), None),
    "allocate": lambda x: ([0 for i in range(get_integer(x))], None),
}


def parse_opcode(s):
    opcode = re.search("(\w+?)(n?z)?(n?c)?(n?n)?$", s)
    n = opcode.group(4)
    c = opcode.group(3)
    z = opcode.group(2)
    opcode = opcode.group(1)
    return opcode, n, c, z


def parse_command_with_one_operand(operands):
    return [operands]


def parse_command_with_two_operands(operands):
    return list(map(str.strip, operands.split(",")))[:2]


class OperandType(Enum):
    IMMEDIATE = 0
    REGISTER = 1
    ADDRESS = 2


operands_parsers = [
    ["NOP", "HALT", "ExINT"],
    ["PUSH", "POP", "B", "BL", "BX", "BLX", "NOT", "NEG", "INT"],
    ["MOV", "LDR", "STR", "AND", "OR", "ADD", "SUB", "MUL", "DIV", "LS", "RS", "CMP"],
]
operands_parsers = (
    {i.lower(): str for i in operands_parsers[0]}
    | {i.lower(): parse_command_with_one_operand for i in operands_parsers[1]}
    | {i.lower(): parse_command_with_two_operands for i in operands_parsers[2]}
)
commands_operands_types = {
    "NOP": [],
    "HALT": [],
    "ExINT": [],
    "PUSH": [OperandType.REGISTER],
    "POP": [OperandType.REGISTER],
    "B": [OperandType.IMMEDIATE],
    "BL": [OperandType.IMMEDIATE],
    "BX": [OperandType.REGISTER],
    "BLX": [OperandType.REGISTER],
    "NOT": [OperandType.REGISTER],
    "NEG": [OperandType.REGISTER],
    "INT": [OperandType.IMMEDIATE],
    "MOV": [OperandType.REGISTER, [OperandType.REGISTER]],
    "LDR": [OperandType.REGISTER, [OperandType.ADDRESS, OperandType.REGISTER]],
    "STR": [OperandType.REGISTER, [OperandType.ADDRESS, OperandType.REGISTER]],
    "AND": [OperandType.REGISTER, [OperandType.REGISTER, OperandType.IMMEDIATE]],
    "OR": [OperandType.REGISTER, [OperandType.REGISTER, OperandType.IMMEDIATE]],
    "SUB": [OperandType.REGISTER, [OperandType.REGISTER, OperandType.IMMEDIATE]],
    "ADD": [OperandType.REGISTER, [OperandType.REGISTER, OperandType.IMMEDIATE]],
    "MUL": [OperandType.REGISTER, [OperandType.REGISTER, OperandType.IMMEDIATE]],
    "DIV": [OperandType.REGISTER, [OperandType.REGISTER, OperandType.IMMEDIATE]],
    "LS": [OperandType.REGISTER, [OperandType.REGISTER, OperandType.IMMEDIATE]],
    "RS": [OperandType.REGISTER, [OperandType.REGISTER, OperandType.IMMEDIATE]],
    "CMP": [OperandType.REGISTER, [OperandType.REGISTER, OperandType.IMMEDIATE]],
}


class Translator:
    def __init__(self):
        self.commands = {}
        self.labels = {}
        self.offset = 0
        self.commands_with_link = []

    def parse_command(self, opcode_num, operands, n, c, z):
        command = opcode_num.value << 27
        use_n = n is not None
        if n is not None:
            n = n == "n"
        else:
            n = False
        use_c = c is not None
        if c is not None:
            c = c == "c"
        else:
            c = False
        use_z = z is not None
        if z is not None:
            z = z == "z"
        else:
            z = False
        command |= (
            int(use_n) << 26
            | int(n) << 25
            | int(use_z) << 24
            | int(z) << 23
            | int(use_c) << 22
            | int(c) << 21
        )
        operands_types = commands_operands_types[opcode_num.name]
        if len(operands_types) == 0:
            return command
        match operands_types[0]:
            case OperandType.IMMEDIATE:
                try:
                    command |= get_integer(operands[0]) & 0xFFFF
                except ValueError:
                    self.commands_with_link += [
                        [self.offset, AddressType.RELATIVE_PC, operands[0][1:]]
                    ]
            case OperandType.REGISTER:
                try:
                    command |= registers[operands[0].lower()].value << 17
                except KeyError:
                    return "Неверное название регистра!"
        if len(operands_types) == 2:
            if operands[1][0] == "[" and operands[1][-1] == "]":
                if OperandType.ADDRESS in operands_types[1]:
                    if operands[1][1] == "=":
                        self.commands_with_link += [
                            [self.offset, AddressType.RELATIVE_PC, operands[1][2:-1]]
                        ]
                    elif operands[1][1:-1] in registers:
                        reg = registers[operands[1][1:-1].lower()]
                        command |= AddressType.REGISTER.value << 16 | reg.value << 12
                    else:
                        return "Неверный аргумент."
            elif (OperandType.REGISTER in operands_types[1]) and (
                operands[1].lower() in registers
            ):
                reg = registers[operands[1].lower()]
                command |= Register_or_Immediate.REGISTER.value << 16 | reg.value << 12
            elif OperandType.IMMEDIATE in operands_types[1]:
                if all([i in "-0123456789abcdefx" for i in list(operands[1])]):
                    command |= (
                        Register_or_Immediate.IMMEDIATE.value << 16
                        | get_integer(operands[1]) & 0xFFFF
                    )
                elif operands[1][0] == "=":
                    self.commands_with_link += [
                        [self.offset, AddressType.RELATIVE_PC, operands[1][1:]]
                    ]
                else:
                    self.commands_with_link += [
                        [self.offset, AddressType.ABSOLUTE, operands[1]]
                    ]
        return command

    def translation(self, fname):
        with open(fname) as f:
            for num_line, line in enumerate(f):
                line = line.strip()
                found = re.search("^(?:([^\s]+):)?\s*(?:(\w+)(?:\s+(.+))?)?$", line)
                if found:
                    label = found.group(1)
                    if label:
                        self.labels[label] = self.offset
                    command = found.group(2)
                    operands = found.group(3)
                    if command:
                        opcode, n, c, z = parse_opcode(command.lower())
                        try:
                            opcode_num = opcodes[opcode]
                            operands = operands_parsers[opcode](operands)
                            command = self.parse_command(opcode_num, operands, n, c, z)
                            if isinstance(command, str):
                                print(f"Ошибка в {num_line+1} строке. {command}")
                            if command:
                                self.commands[self.offset] = command
                            else:
                                self.commands[self.offset] = 0
                            self.offset += 4
                        except KeyError:
                            try:
                                command, new_addr = spec_words[opcode](operands)
                                if isinstance(command, list):
                                    for i in command:
                                        self.commands[self.offset] = i
                                        self.offset += 4
                                elif isinstance(command, int):
                                    self.commands[self.offset] = command
                                    self.offset += 4
                                if isinstance(new_addr, int):
                                    self.offset = new_addr
                            except KeyError:
                                print(
                                    f"Ошибка в {num_line+1} строке. Команды {opcode} не существует!"
                                )
                                break

    def linking(self):
        for i in self.commands_with_link:
            if i[1] == AddressType.RELATIVE_PC:
                self.commands[i[0]] |= (self.labels[i[2]] - (i[0] + 4)) & 0xFFFF
            elif i[1] == AddressType.ABSOLUTE:
                self.commands[i[0]] |= (self.labels[i[2]]) & 0xFFFF
            else:
                print("Ошибка во время подстановки адресов")


def main(source_in, out):
    t = Translator()
    t.translation(source_in)
    t.linking()
    with open(out, "wb") as f:
        for i, j in t.commands.items():
            f.seek(i)
            f.write(j.to_bytes(4, byteorder="big"))


if __name__ == "__main__":
    source_in = argv[1]
    out = argv[2]
    main(source_in, out)
