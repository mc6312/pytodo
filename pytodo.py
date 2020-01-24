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
VERSION = '1.09'
TITLE_VERSION = '%s v%s' % (TITLE, VERSION)


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

    PREFIX_TODO = 'TODO'
    PREFIX_FIXME = 'FIXME'
    PREFIXES = (PREFIX_TODO, PREFIX_FIXME)

    RX_TODO = re.compile('^\s*@?(%s):?\s+(.+)$' % ('|'.join(PREFIXES)),
                         re.UNICODE|re.MULTILINE|re.DOTALL)
    # т.е. TODO без текста будут игнорироваться, ибо нефиг

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

        rxm = cls.RX_TODO.match(s)
        if rxm:
            # окончательная чистка от лишних пробелов и переносов
            s = list(map(lambda v: v.strip(), rxm.group(2).splitlines(False)))

            return todoinfo(token.start[0],
                            rxm.group(1) == cls.PREFIX_FIXME,
                            s)


class stackitem():
    __slots__ = 'token', 'itype', 'todos', 'multiline'

    DEF, CLASS, OTHER = range(3)

    def __init__(self, token, itype):
        self.token = token
        self.itype = itype
        self.todos = []
        self.multiline = False


class ToDoParser():
    NAME_DEF = 'def'
    NAME_CLASS = 'class'
    DEF_OPERATORS = {NAME_DEF, NAME_CLASS}
    OPERATOR_NAMES = {NAME_DEF, NAME_CLASS,
        'if', 'elif', 'else',
        'with', 'try',
        'except', 'finally',
        'for', 'while'}

    CMT_PREFIXES = {None, tokenize.STRING, tokenize.COMMENT, tokenize.INDENT, tokenize.DEDENT, tokenize.NL, tokenize.NEWLINE}
    OPERATOR_PREFIXES = {tokenize.NEWLINE, tokenize.NL, tokenize.INDENT, tokenize.DEDENT}

    def __init__(self):
        #TODO проверочный todo-комментарий

        # список экземпляров todoinfo
        self.todos = []

        # stack содержит экземпляры stackitem
        self.stack = []

    def format_stack(self, dofilter):
        #TODO format_stack: проверочный todo-комментарий в начале метода
        buf = []

        if dofilter:
            sitems = filter(lambda si: si.itype != si.OTHER, self.stack)
        else:
            sitems = self.stack

        lastsitem = None
        for sitem in sitems:
            if lastsitem:
                buf.append('.' if lastsitem.itype == sitem.CLASS else '/')

            buf.append('%s%s' % (sitem.token.string, '' if sitem.itype == sitem.CLASS else '()'))

            lastsitem = sitem

        return ''.join(buf)
        #TODO format_stack: проверочный todo-комментарий в конце метода

    def append_todo(self, token):
        #TODO append_todo: проверочный todo-комментарий в начале метода
        nfo = todoinfo.new_from_token(token)

        if not nfo:
            return

        nfo.context = self.format_stack(True)

        if self.stack:
            self.stack[-1].todos.append(nfo)
        else:
            self.todos.append(nfo)

        #TODO append_todo: проверочный todo-комментарий в конце метода

    def __print_stack(self, token):
        #TODO если будет нечем заняться - раскасить отладочный вывод
        print('%4d %10s: %s' % (
                    token.start[0],
                    ' '.join(filter(None, token.string.strip().split(None)))[:10],
                    self.format_stack(False)),
                file=sys.stderr)

    def parse_tokens(self, tokens):
        """Возвращает None в случае успеха, строку с сообщением в случае ошибки."""

        lasttoken = None
        blockop = False

        #FIXME: разобраться наконец с уровнями вложенности
        for token in tokens:
            if token.type == tokenize.ERRORTOKEN:
                return (False, 'syntax error at %d:%d of file "%s"' % (*token.start, filename))
            elif token.type == tokenize.NAME:
                if token.string in self.OPERATOR_NAMES:
                    # начало функции, класса или метода (а также if/else/...)

                    if lasttoken is None or lasttoken.type in self.OPERATOR_PREFIXES:
                        # откидываем случаи типа a = something if condition else other
                        blockop = False

                        # если на вершине стека однострочный оператор - выкидываем его
                        if self.stack and not self.stack[-1].multiline:
                            self.todos += self.stack[-1].todos
                            #self.stack[-1].todos.clear()
                            del self.stack[-1]
                    else:
                        blockop = True

                elif lasttoken is not None and lasttoken.type == tokenize.NAME and lasttoken.string in self.OPERATOR_NAMES:
                    if not blockop:
                        # название функции, класса или метода
                        if lasttoken.string == self.NAME_CLASS:
                            itype = stackitem.CLASS
                        elif lasttoken.string == self.NAME_DEF:
                            itype = stackitem.DEF
                        else:
                            itype = stackitem.OTHER

                        self.stack.append(stackitem(token, itype))
            elif token.type == tokenize.NEWLINE:
                # конец составного оператора
                pass
            elif token.type == tokenize.INDENT:
                if self.stack:
                    self.stack[-1].multiline = True

            elif token.type == tokenize.DEDENT:
                print('DEDENT after %s' % (tokenize.tok_name[lasttoken.type] if lasttoken else 'None'))
                if self.stack:
                    self.todos += self.stack[-1].todos
                    del self.stack[-1]
            elif token.type == tokenize.COMMENT:
                self.append_todo(token)
            elif token.type == tokenize.STRING and lasttoken.type in self.CMT_PREFIXES:
                # дабы сюда попадали только document strings
                self.append_todo(token)

            self.__print_stack(token)

            lasttoken = token

    @classmethod
    def parse_source_file(cls, filename):
        """Поиск префиксов @TODO в комментариях и документирующих строках
        в файле с именем filename.

        Возвращает кортеж из двух элементов:
        1й: булевское значение (True, если нет ошибок);
        2й:
            если 1й == True: экземпляр класса ToDoParser;
            если 1й == False: строка с сообщением об ошибке."""

        if not os.path.exists(filename):
            return (False, '"%s" is not found' % filename)

        if os.path.splitext(filename)[1].lower() != '.py':
            return (False, '"%s" is not Python script' % filename)

        parser = cls()

        with open(filename, 'rb') as f:
            try:
                tokens = tokenize.tokenize(f.readline)

                es = parser.parse_tokens(tokens)
                if es:
                    return (False, es)

            except tokenize.TokenError as ex:
                return (False, 'error parsing file "%s" - %s' % (filename, str(ex)))

        return (True, parser)


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
    curctx = None
    first = True

    for nfo in todos:
        if nfo.context != curctx:
            if not first:
                print(file=ofile)
            else:
                first = False

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
    aparser = argparse.ArgumentParser(description='''%s\n
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
                ok, r = ToDoParser.parse_source_file(fni)
                if ok:
                    if r:
                        print(colors[COLOR_FILENAME] % os.path.split(fni)[1], file=ofile)
                        format_todo_strings(r.todos, colors, ofile)
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
    sys.argv += ['-c', '../inkcdb/inkcdb.py']
    sys.exit(main(sys.argv))
