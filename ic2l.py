# -*- coding: utf-8 -*-
'''ic2l: iCompta to Ledger.

Generates a ledger file based on a CSV file exported by iCompta.
Tested with iCompta v4 and Ledger v3.

Usage:
  ic2l.py <input> <account> [-c CURRENCY] [-o FILE] [-v | --verbose]
  ic2l.py (-h | --help)
  ic2l.py --version

Options:
  -h --help       Show this screen.
  --version       Show version.
  <input>         The relative path to the CSV intput file.
  <account>       The balancing account name (i.e. Liabilities:MasterCard)
  -c CURRENCY     The currency [default: $]
  -o FILE         Name of an output file (written in the working directory).
  -v, --verbose   Show version.
'''
from docopt import docopt
import os
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

gverbose = False


def print_verbose(line):
    if gverbose:
        print line


class Entry(object):

    cat_regexps = {
        re.compile(u'Aménagement:.*'): u'Aménagement',
        re.compile(u'Équipements:.*'): u'Équipements',
        re.compile(u'Revenus:'): u'',
        re.compile(u'Carte de Crédit'): u'MasterCard',
        re.compile(u'Transfert:MasterCard'): u'Assets:Compte Joint'
    }

    def __init__(self, row, args):
        self._account = args['<account>']
        self._currency = args['-c']
        self._is_income = '-' not in row[ROW_AMOUNT]
        self._date = row[ROW_DATE]
        self._category = self._format_category(row[ROW_CATEGORY])
        self._payee = row[ROW_PAYEE]
        self._amount = self._format_amount(row[ROW_AMOUNT])
        self._status = row[ROW_STATUS]
        self._comment = self._format_comment(row[ROW_COMMENT])

    def write(self, f):
        print_verbose(u'{0} {1}'.format(self._date, self._payee))
        target = ''
        if self._is_income:
            target = self._account
        else:
            target = u'Expenses:{0}'.format(self._category)
        a = self._compute_amount_alignment(target)
        o = unicode(
            '\n'
            '{0} * {1}{2}\n'
            '{3}{4}{5}{6}\n').format(
                self._date, self._payee, self._comment,
                POST_ACCOUNT_ALIGNMENT, target, ' '*a, self._amount)
        if self._is_income:
            prefix = '' if self._category.startswith('Assets') else 'Income:'
            o += u'{0}{1}\n'.format(POST_ACCOUNT_ALIGNMENT,
                                    u'{0}{1}'.format(prefix, self._category))
        f.write(o.encode('utf8'))

    def _format_comment(self, c):
        if c:
            return u'\n{0}; {1}'.format(POST_ACCOUNT_ALIGNMENT, c)
        else:
            return u''

    def _format_category(self, c):
        fc = re.sub(r'.:.', ':', c)
        for regexp, repl in Entry.cat_regexps.items():
            fc = re.sub(regexp, repl, fc)
        return fc

    def _format_amount(self, a):
        fa = a.replace('-', '').replace(',', '.').replace(unichr(160), ',')
        if '.' not in fa:
            fa += '.00'
        if re.match(r'^[a-zA-Z]+$', self._currency):
            return '{0} {1}'.format(fa, self._currency)
        else:
            return '{0} {1}'.format(self._currency, fa)

    def _compute_amount_alignment(self, c):
        lacc = len(POST_ACCOUNT_ALIGNMENT + c)
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
    gverbose = args['--verbose']
    outputfile = args['-o']
    if not outputfile:
        outputfile = os.path.splitext(args['<input>'])[0] + '.ledger'
    entries = []
    with open(outputfile, 'w') as o:
        # write directives
        o.write('; -*- ledger -*-\n\n')
        o.write('bucket {0}\n'.format(args['<account>']))
        # write entries
        with open(args['<input>'], 'rb') as i:
            reader = unicode_csv_reader(i, delimiter=',', quotechar='"')
            # skip header
            reader.next()
            for row in reader:
                e = Entry(row, args)
                entries.append(e)
                e.write(o)
    print_verbose('Posts found: {0}'.format(len(entries)))
    print('Conversion has been successfully written to \"{0}\"'
          .format(outputfile))
