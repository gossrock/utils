from typing import NamedTuple, List

class Command(NamedTuple):
    command_string: str

    def __str__(self) -> str:
        return self.command_string

    def to_list(self) -> List[str]:
        return self.command_string.split()

class CommandResult(NamedTuple):
    command:Command
    out:str
    error:str

    


    def __str__(self) -> str:
        return_val = '=============================================\n'
        return_val += f'COMMAND:{self.command}\n'
        if self.out != '':
            return_val += '=====STDOUT=====\n'
            return_val += self.out+'\n'
        if self.error != '':
            return_val += '=====STDERROR=====\n'
            return_val += self.error+'\n'
        return_val += '============================================='
        return return_val
