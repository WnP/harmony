'''
A small command line interface using Python's cmd module. This is mostly a
prototype, but may be useful in the final product...
'''

from __future__ import print_function

import cmd
import re


WS = re.compile('\s+')


class HarmonyCommand(cmd.Cmd):
    NEW_ARGS = ('calendar', 'event')

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

    def do_new(self, arg):
        '''Create a new calendar or event.'''
        pass

    def do_list(self, arg):
        '''List events between two dates.'''
        args = WS.split(arg)
        print('hello {0}!'.format(args))

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
