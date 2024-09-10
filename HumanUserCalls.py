

import re
import pyperclip


"""
Converts x86 usercall/purge functions from IDA pseudo code into C ones made of GCC inline asm.
Still suggested to check generated code as well as performing additional changes for asm.
Example:
    input: char *__usercall Moho::DRAW_Rect@<eax>(
                            Vector3f *vec1@<eax>,
                            Vector3f *vec2@<ecx>,
                            int color@<edi>,
                            float thickness@<xmm0>,
                            CD3DPrimBatcher *batcher,
                            Vector3f *vec3,
                            CHeightField *heightField,
                            float a8)

    output:  char* Moho::DRAW_Rect (
                Vector3f* vec1,
                Vector3f* vec2,
                int color,
                float thickness,
                CD3DPrimBatcher* batcher,
                Vector3f* vec3,
                CHeightField* heightField,
                float a8)
            {
            char* __result;
            asm(
                "push %[a8];"       
                "push %[heightField];"
                "push %[vec3];"
                "push %[batcher];"
                "movss xmm0, %[thickness];"
                "call ADDRESS;"
                "add esp, 0x10;"
                : "=a" (__result)
                : [vec1] "a" (vec1), [vec2] "c" (vec2), [color] "D" (color), [thickness] "m" (thickness), [batcher] "g" (batcher), [vec3] "g" (vec3), [heightField] "g" (heightField), [a8] "g" (a8)
                :"xmm0"
            );
            return __result;
            }
"""


REGISTERS_32 = {
    "eax": "a",
    "ebx": "b",
    "ecx": "c",
    "edx": "d",
    "esi": "S",
    "edi": "D",

    "st0": "t",
}

XMM_REGISTERS = {f"xmm{i}" for i in range(16)}


FUNC_R = r"^([a-zA-Z0-9\:_]+\*?\s+\*?)\s*__user(call|purge)\s+([a-zA-Z0-9\:_]+)(@<([a-z0-9]+)>)?\((.+)\)$"

FUNC_ARGS = re.compile(
    r"((([a-zA-Z0-9\:_]+\*?\s+\*?)([a-zA-Z0-9_]+)(@<([a-z0-9]+)>)?)(\,\s+)?)")


def check_register(reg: str):
    if reg != "" and reg not in REGISTERS_32 and reg not in XMM_REGISTERS:
        raise Exception(f"unknown register {reg}")


class Arg:

    def __init__(self, arg_data) -> None:
        self.type: str = arg_data[2].replace(" ", "")
        self.name: str = arg_data[3]
        self.register: str = arg_data[5]

        check_register(self.register)

    def get_constraint(self):
        if self.register in REGISTERS_32:
            return REGISTERS_32[self.register]
        if self.register in XMM_REGISTERS:
            return "m"
        return "g"


class Function:

    def __init__(self, s) -> None:
        match = re.match(FUNC_R, s)
        if match is None:
            raise Exception("Invalid input string")
        groups = match.groups()
        self.type: str = groups[0].replace(" ", "")
        self.need_stack_clear: bool = groups[1] == "call"
        self.name: str = groups[2]
        self.register: str = groups[4]

        check_register(self.register)

        args = groups[5]
        self.args: list[Arg] = [Arg(arg) for arg in FUNC_ARGS.findall(args)]

    def convert_args(self) -> str:
        return ", ".join([f"{arg.type} {arg.name}" for arg in self.args])

    def make_output(self) -> str:
        if self.type == "void":
            return ""
        if self.register == "":
            raise Exception("Return register must be specified")
        return f"\"={REGISTERS_32[self.register]}\" (__result)"

    def make_input(self) -> str:
        return ", ".join([f"[{arg.name}] \"{arg.get_constraint()}\" ({arg.name})" for arg in self.args])

    def make_instructions(self) -> str:
        instructions = []
        for arg in self.args[::-1]:
            if arg.register == "":
                instructions.append(f"\"push %[{arg.name}];\"")
            elif arg.register in XMM_REGISTERS:
                instructions.append(
                    f"\"movss {arg.register}, %[{arg.name}];\"")

        instructions.append("\"call ADDRESS;\"")
        if self.need_stack_clear:
            stack_args = len([arg for arg in self.args if arg.register == ""])
            if stack_args != 0:
                instructions.append(f"\"add esp, 0x{stack_args*4:x};\"")

        return "\n".join(instructions)

    def make_changed_registers(self):
        return ", ". join([f"\"{arg.register}\"" for arg in self.args if arg.register in XMM_REGISTERS])

    def make_asm(self) -> str:
        return f"asm(\n{self.make_instructions()}\n: {self.make_output()}\n: {self.make_input()}\n: {self.make_changed_registers()}\n);"

    def make_header(self) -> str:
        return f"{self.type} {self.name} ({self.convert_args()})"

    def make_body(self) -> str:
        if self.type == "void":
            return f"{{\n{self.make_asm()}\n}}"

        return f"{{\n{self.type} __result;\n{self.make_asm()}\nreturn __result;\n}}"

    def convert(self) -> str:
        return f"{self.make_header()}\n{self.make_body()}"


def main(s: str):
    fn = Function(s)
    result = fn.convert()

    print(result)
    print("Result is copied to clipboard")
    pyperclip.copy(result)


if __name__ == "__main__":
    main(input().strip())
