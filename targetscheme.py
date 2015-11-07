from __future__ import absolute_import

import sys


def entry_point(argv):
    print 'hello, world'
    return 0


def target(driver, args):
    driver.exe_name = 'scheme-c'
    return entry_point, None


if __name__ == '__main__':
    entry_point(sys.argv)
