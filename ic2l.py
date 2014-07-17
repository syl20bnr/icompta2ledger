'''ic2l: iCompta to Ledger.

Generates a ledger file based on a CSV file exported by iCompta.
Tested with iCompta v4 and Ledger v3.

Usage:
  ic2l.py <input> [-o FILE] [-v | --verbose]
  ic2l.py (-h | --help)
  ic2l.py --version

Options:
  -h --help       Show this screen.
  --version       Show version.
  <input>         The relative path to the CSV intput file.
  -o FILE         Name of an output file (written in the working directory).
  -v, --verbose   Show version.
'''
from docopt import docopt
from schema import Schema, Use, And, SchemaError
import os


if __name__ == '__main__':
    args = docopt(__doc__, version='iCompta to Ledger (ic2l) v0.1')
    s = Schema({'<input>': And(os.path.exists,
                               Use(open, error='<input> should be readable'),
                               error='input file does not exist')})
    try:
        args = s.validate(args)
    except SchemaError as e:
        exit(e)
