# -*- coding: utf-8 -*-
'''ic2l: iCompta to Ledger.

Generates a ledger file based on a CSV file exported by iCompta.
Tested with iCompta v4 and Ledger v3.

Usage:
  ic2l.py <input> <account> [-o FILE] [-v | --verbose]
  ic2l.py (-h | --help)
  ic2l.py --version

Options:
  -h --help       Show this screen.
  --version       Show version.
  <input>         The relative path to the CSV intput file.
  <account>       The account name (i.e. )
  -o FILE         Name of an output file (written in the working directory).
  -v, --verbose   Show version.
'''
from docopt import docopt
import re
import csv

ROW_DATE = 0
ROW_CATEGORY = 1
ROW_PAYEE = 5
ROW_AMOUNT = 6
ROW_STATUS = 8
ROW_COMMENT = 10
POST_ACCOUNT_ALIGNMENT = ' '*4
POST_AMOUNT_ALIGNMENT = 62

gaccount = ''


class Entry(object):

    cat_regexps = {
        re.compile(u'Aménagement.*'): u'Aménagement',
        re.compile(u'Équipements.*'): u'Équipements'
    }

    def __init__(self, row):
        self._date = row[ROW_DATE]
        self._category = self._format_category(row[ROW_CATEGORY])
        self._payee = row[ROW_PAYEE]
        self._amount = self._format_amount(row[ROW_AMOUNT])
        self._status = row[ROW_STATUS]
        self._comment = self._format_comment(row[ROW_COMMENT])

    def write(self, f):
        a = self._compute_amount_alignment()
        o = unicode(
            '\n'
            '{0} * {1}{2}\n'
            '{3}{4}{5}{6}\n'
            '{7}{8}\n').format(
                self._date, self._payee, self._comment,
                POST_ACCOUNT_ALIGNMENT, self._category, ' '*a, self._amount,
                POST_ACCOUNT_ALIGNMENT, gaccount)
        f.write(o.encode('utf8'))

    def _format_comment(self, c):
        if c:
            return u'\n{0}; {1}'.format(POST_ACCOUNT_ALIGNMENT, c)
        else:
            return u''

    def _format_category(self, c):
        cf = 'Assets:' + c.replace(' : ', ':').replace(' ', '.')
        for regexp, repl in Entry.cat_regexps.items():
            cf = re.sub(regexp, repl, cf)
        return cf

    def _format_amount(self, a):
        fa = a.replace('-', '').replace(',', '.').replace(unichr(160), ',')
        if '.' not in fa:
            fa += '.00'
        return '$CAD ' + fa

    def _compute_amount_alignment(self):
        lacc = len(POST_ACCOUNT_ALIGNMENT + self._category)
        lamount = len(self._amount)
        spacing = POST_AMOUNT_ALIGNMENT - (lacc + lamount)
        return spacing if spacing > 0 else 1


def unicode_csv_reader(unicode_csv_data, dialect=csv.excel, **kwargs):
    # csv.py doesn't do Unicode; encode temporarily as UTF-8:
    csv_reader = csv.reader(unicode_csv_data, dialect=dialect, **kwargs)
    for row in csv_reader:
        # decode UTF-8 back to Unicode, cell by cell:
        yield [unicode(cell, 'utf-8') for cell in row]


if __name__ == '__main__':
    args = docopt(__doc__, version='iCompta to Ledger (ic2l) v0.1')
    gaccount = args['<account>']
    entries = []
    with open(args['<input>'], 'rb') as f:
        reader = unicode_csv_reader(f, delimiter=',', quotechar='"')
        for row in reader:
            entries.append(Entry(row))
    with open('test.ledger', 'w') as f:
        for e in entries:
            e.write(f)
