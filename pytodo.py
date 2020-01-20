#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#@TODO однострочный TODO-комментарий

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
VERSION = '1.04'
TITLE_VERSION = f'{TITLE} v{VERSION}'

CMT_PREFIXES = {None, tokenize.STRING, tokenize.COMMENT, tokenize.INDENT, tokenize.DEDENT, tokenize.NL, tokenize.NEWLINE}
TODO_PREFIX = '@TODO'
TODO_PREFIX_LEN = len(TODO_PREFIX)

DEBUG = False

"""@TODO длинный пример TODO
с многострочным текстом"""


todoinfo = namedtuple('todoinfo', 'lineno context content')


def filter_token_string(token):
    """Предварительная чистка комментария или документирующей строки
    от лишнего."""

    s = token.string

    if token.type == tokenize.COMMENT:
        # убираем начальный символ "#"
        return s[1:].strip()
    else:
        # элемент типа STRING, удаляем все лишние открывающие/закрывающие
        # кавычки

        qmark = s[0]
        start = 1
        end = len(s) - 1

        while start < end and s[start] == qmark: start += 1
        while end > start and s[end] == qmark: end -= 1

        return s[start:end + 1].strip()


def find_todo_strings(filename):
    """Поиск префиксов @TODO в комментариях и документирующих строках
    в файле с именем filename.

    Возвращает кортеж из двух элементов:
    1й: булевское значение (True, если нет ошибок);
    2й:
        если 1й == True: список экземпляров todoinfo;
        если 1й == False: строка с сообщением об ошибке."""

    if not os.path.exists(filename):
        return (False, '%s is not found' % filename)

    if os.path.splitext(filename)[1].lower() != '.py':
        return (False, '%s is not Python script' % filename)

    todos = []

    with open(filename, 'rb') as f:
        tokens = tokenize.tokenize(f.readline)

        lasttype = None
        lastdef = False
        lastdeflevel = 0
        lastlevel = 0
        lastline = 0
        level = 0
        stack = []

        def __stack_str():
            return '.'.join(filter(None, stack))

        def __dbg_stack(token):
            if lastline != token.start[0]:
                print('\033[1m%d %s ("%s"):\033[0m %s' % (
                    token.start[0],
                    tokenize.tok_name[token.type],
                    token.string,
                    __stack_str()))

        for token in tokens:
            if token.type == tokenize.NAME:
                if lastdef:
                    stack.append(token.string)
                    if DEBUG: __dbg_stack(token)
                    lastdef = False
                elif token.string in ('def', 'class'):
                    # начало описания - потом имя будет добавлено в стек
                    if DEBUG: __dbg_stack(token)
                    lastdef = True
                elif token.string in ('with', 'try', 'except', 'finally', 'for', 'while', 'if', 'elif'):
                    # потому что должны учитываться и эти уровни вложенности
                    # а вот "else" почему-то не должон...
                    if DEBUG: __dbg_stack(token)
                    stack.append(None)
                #else:
                #    __dbg_stack(token)
            elif token.type == tokenize.INDENT:
                lastlevel = level
                level += 1
                if DEBUG: __dbg_stack(token)
            elif token.type == tokenize.DEDENT:
                lastlevel = level
                if level > 0:
                    level -= 1

                if stack:
                    del stack[-1]
                if DEBUG: __dbg_stack(token)
            elif token.type in (tokenize.COMMENT, tokenize.STRING) and lasttype in CMT_PREFIXES:
                lastdeflevel = level
                s = filter_token_string(token)
                if s.startswith(TODO_PREFIX):
                    # окончательная чистка от лишних пробелов и переносов
                    s = list(map(lambda v: v.strip(), s[TODO_PREFIX_LEN:].splitlines(False)))

                    todos.append(todoinfo(token.start[0], __stack_str(), s))

            lasttype = token.type
            if token.start[0] != lastline:
                lastline = token.start[0]

    return (True, todos)


class DemoClass():
    #@TODO todo-строка в описании класса

    def demo_method():
        #@TODO todo-строка в описании метода класса

        def second_level_function():
            #@TODO todo-строка в описании функции в методе класса
            pass


def format_todo_strings(todos):
    maxlnw = 0
    linenumbers = []

    #@TODO допилить форматирование контекстов TODO

    for nfo in todos:
        lnumstr = str(nfo.lineno)
        lnumstrl = len(lnumstr)
        if lnumstrl > maxlnw:
            maxlnw = lnumstrl

    maxlnw += 1

    tabfmt = '    %%%ds %%s' % maxlnw
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
    sys.exit(main(sys.argv))
