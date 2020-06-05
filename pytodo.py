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

DEBUG = True


import tokenize
import os, os.path
import sys
import argparse
from collections import namedtuple
import re

if DEBUG:
    from traceback import print_exception


TITLE = 'PyToDo'
VERSION = '1.13.1%s' % ('-debug' if DEBUG else '')
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

#TODO комментарий после функции

"""TODO многострочный комментарий
после функции"""

def crazy_function(param=lambda a: a):#функция с лямбдой в параметрах
    try:
        return param
    except:
        return None


def multi_line_function():
    class DemoClass1():
        def single_line_method(self): return 0 #@TODO TODO-комментарий на одной строке с однострочным методом

        def double_line_method(self): #@TODO образец TODO-комментария
            '''@TODO образец TODO-комментария в docstring'''
            return 0

    #TODO комментарий в теле функции после вложенной функции

    return DemoClass1()


class ToDoParser():
    NAME_DEF = 'def'
    NAME_CLASS = 'class'
    DEF_OPERATOR_NAMES = {NAME_DEF, NAME_CLASS}
    OPERATOR_NAMES = DEF_OPERATOR_NAMES|{'if', 'elif', 'else',
        'with', 'try',
        'except', 'finally',
        'for', 'while'}

    DOCSTRING_PREFIXES = {None, tokenize.STRING, tokenize.COMMENT, tokenize.INDENT, tokenize.DEDENT, tokenize.NL, tokenize.NEWLINE}

    stackitem = namedtuple('stackitem', 'name isclass')
    """ name        - str, строка для отображения,
        isclass     - False для типа "def", True для типа "class"."""

    todoinfo = namedtuple('todoinfo', 'lineno contextid isfixme content')
    """ lineno      - номер строки (целое);
        contextid   - номер в списке ToDoParser.contexts;
        isfixme     - True для FIXME, False для TODO;
        content     - список строк."""

    PREFIX_TODO = 'TODO'
    PREFIX_FIXME = 'FIXME'
    PREFIXES = (PREFIX_TODO, PREFIX_FIXME)

    RX_TODO = re.compile('^\s*@?(%s):?\s+(.+)$' % ('|'.join(PREFIXES)),
                         re.UNICODE|re.MULTILINE|re.DOTALL)
    # т.е. TODO без текста будут игнорироваться, ибо нефиг

    def __init__(self, filepath):
        #TODO проверочный todo-комментарий

        self.filename = os.path.split(filepath)[1]

        # список экземпляров todoinfo
        self.todos = []

        # список строк для отображения контекстов
        self.contexts = []

    def stack_to_str(self, stack):
        """Преобразование stack (списка экземпляров stackitem) в строку."""

        #TODO stack_to_str: проверочный todo-комментарий в начале метода
        buf = []

        lastsitem = None
        for sitem in stack:
            if lastsitem:
                buf.append('.' if lastsitem.isclass else '/')

            buf.append('%s%s' % (sitem.name, '' if sitem.isclass else '()'))

            lastsitem = sitem

        return ''.join(buf)
        #TODO stack_to_str: проверочный todo-комментарий в конце метода

    def add_context(self, contextstr):
        if not contextstr:
            return None

        try:
            return self.contexts.index(contextstr)
        except ValueError:
            ix = len(self.contexts)
            self.contexts.append(contextstr)
            return ix

    def append_todo(self, token, contextid):
        """Если token.string содержит TODO/FIXME-комментарий,
        создаёт и помещает в список todos экземпляр todoinfo."""

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

            # убираем кавычки в начале, но не более трёх
            maxqmarks = 3
            while start < end and s[start] == qmark and maxqmarks > 0:
                start += 1
                maxqmarks -= 1

            # в конце удаляем кавычек не больше, чем удалили в начале
            maxqmarks = 4 - maxqmarks
            while end > start and s[end] == qmark and maxqmarks > 0:
                end -= 1
                maxqmarks -= 1

            s = s[start:end + 1].strip()

        if not s:
            return

        rxm = self.RX_TODO.match(s)
        if rxm:
            # окончательная чистка от лишних пробелов и переносов
            txt = list(map(lambda v: v.strip(), rxm.group(2).splitlines(False)))

            if txt:
                self.todos.append(self.todoinfo(token.start[0],
                                contextid,
                                rxm.group(1) == self.PREFIX_FIXME,
                                txt))

    def parse_tokens(self, tokens, stack):
        """Рекурсивный разбор токенов.

        tokens  - генератор, выдающий экземпляры tokenize.TokenInfo,
        stack   - список элементов stackitem (уровней вложенности классов,
                  методов и функций).

        В случае ошибок генерирует исключения."""

        lasttoken = None
        opbegin = False
        opname = None
        curstack = stack
        curcontextstr = self.stack_to_str(curstack)
        curcontext = self.add_context(curcontextstr)

        while True:
            token = next(tokens)

            if token.type == tokenize.NAME:
                if not opbegin:
                    opbegin = token.string in self.OPERATOR_NAMES
                elif opbegin:
                    if lasttoken.string in self.DEF_OPERATOR_NAMES:
                        curstack = stack + [self.stackitem(token.string, lasttoken.string == self.NAME_CLASS)]
                    else:
                        curstack = stack

                    curcontextstr = self.stack_to_str(curstack)
                    curcontext = self.add_context(curcontextstr)

                    opbegin = False
            elif token.type == tokenize.INDENT:
                self.parse_tokens(tokens, curstack)
            elif token.type == tokenize.DEDENT:
                break
            elif token.type == tokenize.COMMENT:
                self.append_todo(token, curcontext)
            elif token.type == tokenize.STRING and (lasttoken is None or lasttoken.type in self.DOCSTRING_PREFIXES):
                # дабы сюда попадали только document strings
                self.append_todo(token, curcontext)

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

        parser = cls(filename)

        try:
            with open(filename, 'rb') as f:
                try:
                    tokens = tokenize.tokenize(f.readline)

                    es = parser.parse_tokens(tokens, [])
                    if es:
                        return (False, es)
                except StopIteration:
                    # генератор выдохся!
                    pass
        except Exception as ex:
            return (False, 'error parsing file "%s" - %s' % (filename, str(ex)))

        return (True, parser)

    def print_todo_list(self, colors, ofile):
        """Вывод отформатированного списка TODO.

        colors  - словарь, где ключи - константы COLOR_,
                  а значения - строки с ansi escapes;
        ofile   - файловый объект, куда выводится таблица."""

        #TODO проверочный todo-комментарий

        maxlnw = 0
        linenumbers = []

        todos = sorted(self.todos, key=lambda n: n.lineno)

        for nfo in todos:
            lnumstr = str(nfo.lineno)
            lnumstrl = len(lnumstr)
            if lnumstrl > maxlnw:
                maxlnw = lnumstrl

        maxlnw += 1

        tabfmt = '    %%%ds %%s' % maxlnw
        curctxid = None
        first = True

        for nfo in todos:
            if nfo.contextid != curctxid:
                if not first:
                    print(file=ofile)
                else:
                    first = False

                if nfo.contextid is not None:
                    print(colors[COLOR_CONTEXT] % ('  %s' % self.contexts[nfo.contextid]), file=ofile)

                curctxid = nfo.contextid

            clr = COLOR_FIXME if nfo.isfixme else COLOR_TODO

            print(tabfmt % ('%d:' % nfo.lineno,
                            colors[clr] % ('%s%s' % ('' if not nfo.isfixme else 'FIXME: ',
                                                     nfo.content[0]))
                            ),
                  file=ofile)

            for cntstr in nfo.content[1:]:
                print(tabfmt % ('', colors[clr] % cntstr), file=ofile)


class DemoClass2():
    #@TODO todo-строка в описании класса

    class InnerDemoClass():
        "TODO docstring в заголовке класса"

        def inner_demo_class_method(self): #@TODO комментарий в заголовке inner_demo_class_method
            #@TODO комментарий в теле inner_demo_class_method
            pass

    def demo_method():
        '''@TODO todo-строка в описании метода класса'''

        def second_level_function():
            #@TODO todo-строка в описании функции в методе класса
            pass


COLOR_MESSAGE, COLOR_FILENAME, COLOR_ERROR, COLOR_CONTEXT, COLOR_TODO, COLOR_FIXME = range(6)

PALETTE_NO_COLORS = {
    COLOR_MESSAGE: '%s',
    COLOR_FILENAME: '%s',
    COLOR_ERROR: '%s',
    COLOR_CONTEXT: '%s',
    COLOR_TODO: '%s',
    COLOR_FIXME: '%s',
    }

PALETTE_ANSI_COLORS = {
    COLOR_MESSAGE: '\033[1m%s\033[0m',
    COLOR_FILENAME: '\033[1m%s\033[0m',
    COLOR_ERROR: '\033[31m%s\033[0m',
    COLOR_CONTEXT: '\033[32m%s\033[0m',
    COLOR_TODO: '\033[0m%s\033[0m',
    COLOR_FIXME: '\033[93m%s\033[0m',
    }


def process_command_line():
    aparser = argparse.ArgumentParser(description='Todo list generator for Python %d scripts.' % (sys.version_info.major))

    aparser.add_argument('file', help='python script filename',
        action='append', nargs='+')

    aparser.add_argument('-c', '--colors', help='colorize output',
        action='store_true', dest='colors', default=False)

    aparser.add_argument('-O', '--output-file', help='output file name',
        action='store', nargs=1, dest='output', default='-')

    args = aparser.parse_args()

    if args.output[0] != '-':
        args.colors = False

    # ArgumentParser может хранить список имён файлов как список списков!
    fnames = []

    def __expand_list(lst):
        for i in lst:
            if isinstance(i, list):
                __expand_list(i)
            else:
                fnames.append(i)

    __expand_list(args.file)

    args.file = fnames

    return args


def main():
    colors = PALETTE_NO_COLORS

    try:
        print(colors[COLOR_MESSAGE] % TITLE_VERSION, file=sys.stderr)

        args = process_command_line()

        if args.colors:
            colors = PALETTE_ANSI_COLORS

        if args.output[0] == '-':
            ofile = sys.stdout
        else:
            ofile = open(args.output[0], 'w+')

        todolists = []

        try:
            for fname in args.file:
                print('  parsing %s...' % (colors[COLOR_FILENAME] % os.path.split(fname)[1]), file=sys.stderr)

                ok, r = ToDoParser.parse_source_file(fname)
                if ok:
                    if r.todos:
                        todolists.append(r)
                else:
                    print(colors[COLOR_ERROR] % r, file=sys.stderr)

            print(file=sys.stderr)

            for todolist in todolists:
                print(colors[COLOR_FILENAME] % todolist.filename, file=ofile)
                todolist.print_todo_list(colors, ofile)
                print(file=ofile)

        finally:
            if not ofile is sys.stdout:
                ofile.close()

    except Exception as ex:
        print(colors[COLOR_ERROR] % '*** Exception %s ***' % ex.__class__.__name__, file=sys.stderr)

        if DEBUG:
            enfo = sys.exc_info()
            print_exception(*enfo, file=sys.stderr)

        return 1

    return 0


if __name__ == '__main__':
    sys.argv += [__file__]
    #sys.argv += ['-c', __file__]
    sys.exit(main())
