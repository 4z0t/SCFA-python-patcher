

import re


sample = "int * __usercall Moho::UNIT_IssueCommand@<eax>(moho_set *a2@<edx>, int moho, Moho::SSTICommandIssueData *a4, char a5)"


REGISTERS_32 = {
    "eax": "a",
    "ebx": "b",
    "ecx": "c",
    "edx": "d",
    "esi": "S",
    "edi": "D",
}


FUNC_R = r"^([a-zA-Z0-9\:_]+\*?\s+\*?)\s+__user(call|purge)\s+([a-zA-Z0-9\:_]+)(@<([a-z0-9]+)>)?\((.+)\)$"

FUNC_ARGS = re.compile(
    r"((([a-zA-Z0-9\:_]+\*?\s+\*?)([a-zA-Z0-9_]+)(@<([a-z0-9]+)>)?)(\,\s+|\)))")


class Arg:

    def __init__(self) -> None:
        pass


class Function:

    def __init__(self) -> None:

        pass


def main(s: str):

    match = re.match(FUNC_R, s)
    if match is None:
        raise Exception("Invalid input string")
    # print(match)
    groups = match.groups()
    print(groups)
    return_type = groups[0]
    func_type = groups[1]
    func_name = groups[2]
    return_register = groups[4]
    func_args = groups[5]

    print(f"""
          Return type: {return_type}
          Func type: {func_type}
          Name: {func_name}
          Register: {return_register}
          Args: {func_args}
          """)

    for arg in FUNC_ARGS.findall(func_args):

        arg_type = arg[2]
        arg_name = arg[3]
        arg_register = arg[5]
        print(f"""
              Type: {arg_type}
              Name: {arg_name}
              Register: {arg_register}
              """)
    result = s

    # print(result)


if __name__ == "__main__":

    main(sample)
