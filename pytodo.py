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
VERSION = '1.06'
TITLE_VERSION = '%s v%s' % (TITLE, VERSION)

CMT_PREFIXES = {None, tokenize.STRING, tokenize.COMMENT, tokenize.INDENT, tokenize.DEDENT, tokenize.NL, tokenize.NEWLINE}
TODO_PREFIX = '@TODO'
TODO_PREFIX_LEN = len(TODO_PREFIX)


"""@TODO длинный пример TODO
с многострочным текстом"""


todoinfo = namedtuple('todoinfo', 'lineno context content')
stackitem = namedtuple('stackitem', 'token isclass')


def single_line_function(): return 0 #@TODO комментарий к однострочной функции


def two_line_function():
    #@TODO комментарий к многострочной функции
    return 0


def multi_line_function():
    class DemoClass1():
        def single_line_method(self): return 0 #@TODO TODO-комментарий на одной строке с однострочным методом

        def double_line_method(self): #@TODO образец TODO-комментария
            '''@TODO образец TODO-комментария в docstring'''
            return 0

    return DemoClass1()


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

    def __flush_todo(lineno, s):
        if not s:
            return

        if s.startswith(TODO_PREFIX):
            #print('.'.join(map(lambda si: si.token.string if si else '@', filter(None, stack))))

            # окончательная чистка от лишних пробелов и переносов
            s = list(map(lambda v: v.strip(), s[TODO_PREFIX_LEN:].splitlines(False)))

            #@TODO допилить форматирование контекстов TODO
            todos.append(todoinfo(lineno,
                         '.'.join(map(lambda si: si.token.string, filter(None, stack))),
                         s))

    with open(filename, 'rb') as f:
        tokens = tokenize.tokenize(f.readline)

        lasttype = None

        ishead = False
        isclass = False
        isvisible = False
        isnewline = False
        nametoken = None

        # stack содержит экземпляры stackitem или None
        stack = []

        # "отложенные" комментарии
        # содержит кортежи из двух элементов - (номер строки, 'строка').
        # т.к. tokenize считает, что #-комментарий, расположенный после
        # заголовка класса/функции/метода, идет _перед_ INDENT и является
        # частью заголовка - стек в этот момент содержит на один элемент
        # меньше, чем мне надо
        comments = []

        # в стек добавляются записи в случае цепочки токенов:
        # NAME="def" NAME="<idname>" ... NEWLINE INDENT
        # "видимые": для idname in (def, class)
        # "невидимые": для idname in ('with', 'try', 'except', 'finally', 'for', 'while', 'if', 'elif')
        # аналогичные цепочки, НЕ заканчивающиеся токеном INDENT,
        # в стек НЕ добавляются (это м.б. однострочные функции и т.п.)

        for token in tokens:
            if token.type == tokenize.NAME:
                if token.string in ('def', 'class'):
                    ishead = True
                    isclass = token.string == 'class'
                    isvisible = True
                    nametoken = None
                elif token.string in ('with', 'try', 'except', 'finally', 'for', 'while', 'if', 'elif', 'else'):
                    ishead = False
                    isclass = False
                    isvisible = False
                    nametoken = None
                elif ishead:
                    if nametoken is None:
                        nametoken = token
            elif token.type == tokenize.NEWLINE:
                if ishead:
                    isnewline = True

                    # есть "отложенные" комментарии
                    if comments:
                        stack.append(stackitem(nametoken, isclass))

                        for lnum, cmts in comments:
                            __flush_todo(lnum, cmts)

                        del stack[-1]

                        comments.clear()

            elif token.type == tokenize.INDENT:
                if ishead and isnewline:
                    si = stackitem(nametoken, isclass) if isvisible else None
                    ishead = False
                else:
                    si = None
                    ishead = False

                stack.append(si)
            elif token.type == tokenize.DEDENT:
                if stack:
                    del stack[-1]
            elif token.type == tokenize.COMMENT:
                if ishead:
                    cmts = filter_token_string(token)
                    if cmts:
                        if isnewline:
                            __flush_todo(token.start[0], cmts)
                        else:
                            comments.append((token.start[0], cmts))
                else:
                    __flush_todo(token.start[0], filter_token_string(token))
            elif token.type == tokenize.STRING and lasttype in CMT_PREFIXES:
                # дабы сюда попадали только document strings
                __flush_todo(token.start[0], filter_token_string(token))

            lasttype = token.type

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


def format_todo_strings(todos):
    maxlnw = 0
    linenumbers = []

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
            print()

            if nfo.context:
                print('  %s()' % nfo.context)

            curctx = nfo.context

        print(tabfmt % ('%d:' % nfo.lineno, nfo.content[0]))

        for cntstr in nfo.content[1:]:
            print(tabfmt % ('', cntstr))


def main(args):
    if len(args) < 2:
        print('''%s
Todo list generator for Python %d scripts.

Usage: %s filename.py [... filename.py]''' % (TITLE_VERSION, sys.version_info.major, __file__),
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
