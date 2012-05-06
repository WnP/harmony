'''
A small command line interface using Python's cmd module. This is mostly a
prototype, but may be useful in the final product...
'''

from __future__ import print_function

import cmd


class HarmonyCommand(cmd.Cmd):
    CREATE_ARGS = ('calendar', 'event')
    DELETE_ARGS = ('calendar', 'event')

    def __init__(self, *args, **kwargs):
        cmd.Cmd.__init__(self, *args, **kwargs)
        self.prompt = 'harmony> '

    def precmd(self, line):
        if line == 'EOF':
            print('')
            return 'quit'
        return line

    # All the do_* methods take a single argument `arg` that contains any
    # arguments to the command as a single string.

    def do_create(self, arg):
        '''Create a new calendar or event.'''
        pass

    def do_delete(self, arg):
        '''Delete a calendar or event.'''
        pass

    def do_list(self, arg):
        '''List events between two dates.'''
        pass

    def do_quit(self, arg):
        '''Quit the interpreter.'''
        return True

    # Completion commands

    def complete_new(self, text, line, begidx, endidx):
        if begidx == 4:
            return [c for c in HarmonyCommand.NEW_ARGS if c.startswith(text)]


def main():
    HarmonyCommand().cmdloop()


if __name__ == '__main__':
    main()
