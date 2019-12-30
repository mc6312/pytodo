#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#@TODO simple TODO comment sample

""" pytodo.py

    Copyright 2019 MC-6312

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>."""


import tokenize
import os, os.path
import sys
from collections import namedtuple


TITLE = 'PyToDo'
VERSION = '1.02'
TITLE_VERSION = f'{TITLE} v{VERSION}'

CMT_PREFIXES = {None, tokenize.STRING, tokenize.COMMENT, tokenize.INDENT, tokenize.DEDENT, tokenize.NL, tokenize.NEWLINE}
TODO_PREFIX = '@TODO'
TODO_PREFIX_LEN = len(TODO_PREFIX)

"""@TODO long TODO sample
with multi-line text"""


todoinfo = namedtuple('todoinfo', 'lineno context content')


def filter_string(token):
    s = token.string

    if token.type == tokenize.COMMENT:
        # remove starting "#"
        return s[1:].strip()
    else:
        # STRING type, remove all starting/ending quotation marks

        qmark = s[0]
        start = 1
        end = len(s) - 1

        while start < end and s[start] == qmark: start += 1
        while end > start and s[end] == qmark: end -= 1

        return s[start:end + 1].strip()


def find_todo_strings(filename):
    """Search @TODO prefixes in comments and docstrings into filename.

    Returns two-tuple.
    1st element: boolean (True if no errors);
    2nd element:
        if 1st == True: list of todoinfo;
        if 1st == False: string with error message."""

    if not os.path.exists(filename):
        return (False, '%s is not found' % filename)

    if os.path.splitext(filename)[1].lower() != '.py':
        return (False, '%s is not Python script' % filename)

    todos = []
    stack = []

    #@TODO fix context stack

    with open(filename, 'rb') as f:
        tokens = tokenize.tokenize(f.readline)

        lasttype = None
        lastdef = False
        lastdeflevel = 0
        lastlevel = 0
        level = 0

        for tkn in tokens:
            if tkn.type == tokenize.NAME:
                if lastdef:
                    stack.append(tkn.string)
                    lastdef = False
                elif tkn.string in ('def', 'class'):
                    lastdef = True
                else:
                    lastdef = False
            elif tkn.type == tokenize.INDENT:
                lastlevel = level
                level += 1
            elif tkn.type == tokenize.DEDENT:
                lastlevel = level
                if level > 0:
                    level -= 1

                if level < lastdeflevel and stack:
                    del stack[-1]
            elif tkn.type in (tokenize.COMMENT, tokenize.STRING) and lasttype in CMT_PREFIXES:
                lastdeflevel = level
                s = filter_string(tkn)
                if s.startswith(TODO_PREFIX):
                    # cleaning
                    s = list(map(lambda v: v.strip(), s[TODO_PREFIX_LEN:].splitlines()))

                    todos.append(todoinfo(tkn.start[0], '.'.join(stack), s))

            lasttype = tkn.type

    return (True, todos)


class DemoClass():
    #@TODO todo string in class definition

    def demo_method():
        #@TODO todo string in class method

        def second_level_function():
            #@TODO todo string in second level function
            pass


def format_todo_strings(todos):
    maxlnw = 0
    linenumbers = []

    #@TODO fix TODO context formatting

    for nfo in todos:
        lnumstr = str(nfo.lineno)
        lnumstrl = len(lnumstr)
        if lnumstrl > maxlnw:
            maxlnw = lnumstrl

    maxlnw += 1

    tabfmt = '  %%%ds %%s' % maxlnw
    curctx = ''
    first = True

    for nfo in todos:
        if first:
            first = False
        else:
            print()

        if nfo.context != curctx:
            if nfo.context:
                print('  %s()' % nfo.context)

            curctx = nfo.context

        print(tabfmt % ('%d:' % nfo.lineno, nfo.content[0]))

        for cntstr in nfo.content[1:]:
            print(tabfmt % ('', cntstr))


def main(args):
    if len(args) < 2:
        print('%s\nUsage: %s filename.py [... filename.py]' %\
            (TITLE_VERSION, __file__),
            file=sys.stderr)
        return 1

    for arg in args[1:]:
        ok, r = find_todo_strings(arg)
        if ok:
            if r:
                print(os.path.split(arg)[1])
                format_todo_strings(r)
                print()
        else:
            print(r, file=sys.stderr)

    return 0


if __name__ == '__main__':
    sys.argv.append(__file__)
    sys.exit(main(sys.argv))
