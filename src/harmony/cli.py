'''
A small command line interface using Python's cmd module. This is mostly a
prototype, but may be useful in the final product...
'''

from __future__ import print_function

import cmd
import shlex
import datetime

from pytz import timezone as pytz_timezone

import app
import lang


class HarmonyCmd(cmd.Cmd):
    def __init__(self, *args, **kwargs):
        cmd.Cmd.__init__(self, *args, **kwargs)
        self.prompt = 'harmony> '

    def precmd(self, line):
        if line == 'EOF':
            print('')
            return 'quit'
        return line

    def parseline(self, line):
        '''More or less an exact copy of cmd.Cmd's implementation of this
        method, except run the line through Harmony's lang module. The tuple
        returned by this implementation is (cmd, args, line), the same as
        super's, where cmd is the name of the command, args is the dictionary
        returned from lang.process_line, and line is a string representation of
        the line.'''
        line = line.strip()
        if not line:
            return None, None, line
        elif line[0] == '?':
            return 'help', line[1:], 'help ' + line[1:]
        elif line[0] == '!':
            if hasattr(self, 'do_shell'):
                return 'shell', line[1:], 'shell ' + line[1:]
            else:
                return None, None, line
        i, n = 0, len(line)
        while i < n and line[i] in self.identchars: i+= 1
        cmd, args = line[:i], lang.process_line(line)
        return cmd, args, line

    def do_create(self, args):
        '''Create a new calendar or event.'''
        typ = args['type']
        if typ == 'calendar':
            app.app.create_calendar(args['name'], args['timezone'])
        elif typ == 'event':
            print(args)

    def do_delete(self, args):
        '''Delete a calendar or event.'''
        pass

    def do_list(self, args):
        '''List calendars or events.'''
        typ = args['type']
        if typ == 'calendar':
            lens = [0, 0]
            for cal in app.app.calendars.values():
                lpk = len(str(cal.pk))
                ltz = len(str(cal.timezone))
                if lpk > lens[0]:
                    lens[0] = lpk
                if ltz > lens[1]:
                    lens[1] = ltz
            for cal in app.app.calendars.values():
                print('[{0.pk:-{1[0]}}] '
                      '({0.timezone!s:{1[1]}}) '
                      '{0.name}'.format(cal, lens))
        elif typ == 'event':
            pass
        else:
            pass

    def do_quit(self, arg):
        '''Quit the interpreter.'''
        return True

    # Completion commands

    def complete_create(self, text, line, begidx, endidx):
        if begidx == 7:
            return [arg for arg in HarmonyCmd.CREATE_ARGS
                    if arg.startswith(text.lower())]


def main():
    HarmonyCmd().cmdloop()


if __name__ == '__main__':
    main()
