#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" pytodo.py

    Copyright 2019-2020 MC-6312

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
import argparse
from collections import namedtuple
import re


TITLE = 'PyToDo'
VERSION = '1.08'
TITLE_VERSION = '%s v%s' % (TITLE, VERSION)

CMT_PREFIXES = {None, tokenize.STRING, tokenize.COMMENT, tokenize.INDENT, tokenize.DEDENT, tokenize.NL, tokenize.NEWLINE}

PREFIX_TODO = 'TODO'
PREFIX_FIXME = 'FIXME'
PREFIXES = (PREFIX_TODO, PREFIX_FIXME)

RX_TODO = re.compile('^\s*@?(%s)\s+(.+)$' % ('|'.join(PREFIXES)),
                     re.UNICODE|re.MULTILINE|re.DOTALL)
# т.е. TODO без текста будут игнорироваться, ибо нефиг

""" Сей скрипт является проверочным файлом для самого себя, соответственно
    содержит демонстрационные TODO-комментарии и демонстрационные же
    классы с функциями, посему не стоит удивляться вкраплениям
    бессмысленного кода ниже."""

#@TODO однострочный TODO-комментарий
# TODO ещё один однострочный TODO-комментарий
# FIXME однострочный FIXME-комментарий
# ниже - "пустой TODO-комментарий" для проверки:
#TODO

"""@TODO длинный пример TODO
с многострочным текстом"""

"""FIXME длинный пример FIXME
с многострочным текстом"""


def single_line_function(): return 0 #@TODO комментарий к однострочной функции


def two_line_function(): #@TODO комментарий в заголовке многострочной функции
    #@TODO комментарий в начале многострочной функции
    a = 1
    #@TODO комментарий в теле многострочной функции
    return a


def crazy_function(param=lambda a: a):#функция с лямбдой в параметрах
    return param


def multi_line_function():
    class DemoClass1():
        def single_line_method(self): return 0 #@TODO TODO-комментарий на одной строке с однострочным методом

        def double_line_method(self): #@TODO образец TODO-комментария
            '''@TODO образец TODO-комментария в docstring'''
            return 0

    return DemoClass1()


class todoinfo():
    __slots__ = 'lineno', 'context', 'isfixme', 'content'

    def __init__(self, lineno, isfixme, content):
        self.lineno, self.isfixme, self.content = lineno, isfixme, content
        self.context = ''

    @classmethod
    def new_from_token(cls, token):
        """Если token.string содержит TODO/FIXME-комментарий, возвращает
        экземпляр todoinfo, иначе None."""

        s = token.string

        if token.type == tokenize.COMMENT:
            # убираем начальный символ "#"
            s = s[1:].strip()
        else:
            # элемент типа STRING, удаляем все лишние открывающие/закрывающие
            # кавычки

            qmark = s[0]
            start = 1
            end = len(s) - 1

            while start < end and s[start] == qmark: start += 1

            while end > start and s[end] == qmark: end -= 1

            s = s[start:end + 1].strip()

        if not s:
            return

        rxm = RX_TODO.match(s)
        if rxm:
            # окончательная чистка от лишних пробелов и переносов
            s = list(map(lambda v: v.strip(), rxm.group(2).splitlines(False)))

            return todoinfo(token.start[0],
                            rxm.group(1) == PREFIX_FIXME,
                            s)


class stackitem():
    __slots__ = 'token', 'itype', 'todos', 'multiline'

    DEF, CLASS, OTHER = range(3)

    def __init__(self, token, itype):
        self.token = token
        self.itype = itype
        self.todos = []
        self.multiline = False


NAME_DEF = 'def'
NAME_CLASS = 'class'
OPERATOR_NAMES = {NAME_DEF, NAME_CLASS,
    'if', 'elif', 'else',
    'with', 'try',
    'except', 'finally',
    'for', 'while'}


def find_todo_strings(filename):
    """Поиск префиксов @TODO в комментариях и документирующих строках
    в файле с именем filename.

    Возвращает кортеж из двух элементов:
    1й: булевское значение (True, если нет ошибок);
    2й:
        если 1й == True: список экземпляров todoinfo;
        если 1й == False: строка с сообщением об ошибке."""

    if not os.path.exists(filename):
        return (False, '"%s" is not found' % filename)

    if os.path.splitext(filename)[1].lower() != '.py':
        return (False, '"%s" is not Python script' % filename)

    #TODO проверочный todo-комментарий

    # список экземпляров todoinfo
    todos = []

    with open(filename, 'rb') as f:
        try:
            tokens = tokenize.tokenize(f.readline)

            # stack содержит экземпляры stackitem
            stack = []

            lasttoken = None
            ishead = False

            def append_todo(token):
                nfo = todoinfo.new_from_token(token)

                if not nfo:
                    return

                buf = []

                lastsitem = None
                for sitem in filter(lambda si: si.itype != si.OTHER, stack):
                    if lastsitem:
                        buf.append('.' if lastsitem.itype == sitem.CLASS else '/')

                    buf.append('%s%s' % (sitem.token.string, '' if sitem.itype == sitem.CLASS else '()'))

                    lastsitem = sitem

                nfo.context = ''.join(buf)

                if stack:
                    stack[-1].todos.append(nfo)
                else:
                    todos.append(nfo)

            for token in tokens:
                if token.type == tokenize.ERRORTOKEN:
                    return (False, 'syntax error at %d:%d of file "%s"' % (*token.start, filename))
                elif token.type == tokenize.NAME:
                    if token.string in OPERATOR_NAMES:
                        # начало функции, класса или метода
                        if stack and not stack[-1].multiline:
                            todos += stack[-1].todos
                            del stack[-1]

                        ishead = True
                    elif lasttoken is not None and lasttoken.type == tokenize.NAME and lasttoken.string in OPERATOR_NAMES:
                        # название функции, класса или метода
                        if lasttoken.string == NAME_CLASS:
                            itype = stackitem.CLASS
                        elif lasttoken.string == NAME_DEF:
                            itype = stackitem.DEF
                        else:
                            itype = stackitem.OTHER

                        stack.append(stackitem(token, itype))
                elif token.type == tokenize.NEWLINE:
                    if ishead:
                        ishead = False

                elif token.type == tokenize.INDENT:
                    if stack and stack[-1] is not None:
                        stack[-1].multiline = True

                elif token.type == tokenize.DEDENT:
                    if stack:
                        todos += stack[-1].todos
                        del stack[-1]
                elif token.type == tokenize.COMMENT:
                    append_todo(token)
                elif token.type == tokenize.STRING and lasttoken.type in CMT_PREFIXES:
                    # дабы сюда попадали только document strings
                    append_todo(token)

                lasttoken = token

        except tokenize.TokenError as ex:
            return (False, 'error parsing file "%s" - %s' % (filename, str(ex)))

    return (True, todos)


class DemoClass2():
    #@TODO todo-строка в описании класса

    class InnerDemoClass():
        def inner_demo_class_method(self): #@TODO комментарий в заголовке inner_demo_class_method
            #@TODO комментарий в теле inner_demo_class_method
            pass

    def demo_method():
        '''@TODO todo-строка в описании метода класса'''

        def second_level_function():
            #@TODO todo-строка в описании функции в методе класса
            pass


COLOR_FILENAME, COLOR_ERROR, COLOR_CONTEXT, COLOR_TODO, COLOR_FIXME = range(5)


def format_todo_strings(todos, colors, ofile):
    """Вывод отформатированного списка TODO.

    todos   - список экземпляров todoinfo;
    colors  - словарь, где ключи - константы COLOR_,
              а значения - строки с ansi escapes;
    ofile   - файловый объект, куда выводится таблица."""

    #TODO проверочный todo-комментарий

    maxlnw = 0
    linenumbers = []

    todos = sorted(todos, key=lambda n: n.lineno)

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
        if nfo.context != curctx:
            print(file=ofile)

            if nfo.context:
                print(colors[COLOR_CONTEXT] % ('  %s' % nfo.context), file=ofile)

            curctx = nfo.context

        clr = COLOR_FIXME if nfo.isfixme else COLOR_TODO

        print(tabfmt % ('%d:' % nfo.lineno,
                        colors[clr] % ('%s%s' % ('' if not nfo.isfixme else 'FIXME: ',
                                                 nfo.content[0]))
                        ),
              file=ofile)

        for cntstr in nfo.content[1:]:
            print(tabfmt % ('', colors[clr] % cntstr), file=ofile)


def main(args):
    #TODO проверочный todo-комментарий
    aparser = argparse.ArgumentParser(description='''%s
Todo list generator for Python %d scripts.''' % (TITLE_VERSION, sys.version_info.major))

    aparser.add_argument('-c', '--colors', help='colorize output',
        action='store_const', dest='colors', const=True, default=False)

    aparser.add_argument('file', help='python script filename',
        action='append', nargs='+')

    aparser.add_argument('-O', '--output-file', help='output file name',
        action='store', nargs=1, dest='output', default='-')

    args = aparser.parse_args()

    if args.output[0] != '-':
        args.colors = False

    if args.colors:
        colors = {COLOR_FILENAME: '\033[1m%s\033[0m',
            COLOR_ERROR: '\033[31m%s\033[0m',
            COLOR_CONTEXT: '\033[32m%s\033[0m',
            COLOR_TODO: '\033[0m%s\033[0m',
            COLOR_FIXME: '\033[93m%s\033[0m',
            }
    else:
        colors = {COLOR_FILENAME: '%s',
            COLOR_ERROR: '%s',
            COLOR_CONTEXT: '%s',
            COLOR_TODO: '%s',
            COLOR_FIXME: '%s',
            }

    def __fname_list(fnl, ofile):
        for fni in fnl:
            if isinstance(fni, list):
                __fname_list(fni, ofile)
            else:
                ok, r = find_todo_strings(fni)
                if ok:
                    if r:
                        print(colors[COLOR_FILENAME] % os.path.split(fni)[1], file=ofile)
                        format_todo_strings(r, colors, ofile)
                        print(file=ofile)
                else:
                    print(colors[COLOR_ERROR] % r, file=sys.stderr)

    if args.output[0] == '-':
        ofile = sys.stdout
    else:
        ofile = open(args.output[0], 'w+')

    try:
        __fname_list(args.file, ofile)
    finally:
        if not ofile is sys.stdout:
            ofile.close()

    return 0


if __name__ == '__main__':
    #sys.argv += ['badfile.py']
    #sys.argv += ['-c', __file__]#, '-O', 'TODO']
    sys.exit(main(sys.argv))
