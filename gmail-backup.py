#!/usr/bin/env python3
# -*-  coding: utf-8 -*-
#
#   Gmail Backup CLI
#
#   Copyright © 2008, 2009, 2010 Jan Svec <honza.svec@gmail.com> and Filip Jurcicek <filip.jurcicek@gmail.com>
#
#   This file is part of Gmail Backup.
#
#   Gmail Backup is free software: you can redistribute it and/or modify it
#   under the terms of the GNU General Public License as published by the Free
#   Software Foundation, either version 3 of the License, or (at your option)
#   any later version.
#
#   Gmail Backup is distributed in the hope that it will be useful, but WITHOUT
#   ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
#   FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
#   more details.
#
#   You should have received a copy of the GNU General Public License along
#   with Gmail Backup.  If not, see <http://www.gnu.org/licenses/
#
#   See LICENSE file for license details

import argparse
import getpass
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gmb import ConsoleNotifier, _convertTime, GMailBackup, GMB_REVISION, GMB_DATE, imap_decode

PASSWORD_ENV = 'GMAIL_BACKUP_PASSWORD'

DESCRIPTION = \
'''Program for backup and restore of your GMail mailbox. You will need to activate
the IMAP access to your mailbox, to do so, please open your GMail settings and
under POP/IMAP tab activate this option.

Google no longer accepts your normal account password over IMAP. You have to
enable 2-Step Verification and create an App Password at
https://myaccount.google.com/apppasswords and use it as the password.'''

EPILOG = \
'''The messages are stored in the local directory in files which names follow the
format YYYY/MM/YYYYMMDD-hhmmss-from-subject-n.eml, where the date is the date
when the e-mail was SENT. Label assignment is stored in the file labels.txt.
The directory name can be followed by "#pattern" to change the naming pattern
and a name ending with .zip stores the backup into a ZIP archive.

The password can be passed as a command line argument, in the %(env)s
environment variable, or it is asked for interactively (recommended, so it
does not end up in your shell history).

Examples:

  Full backup of your GMail account into directory dir:
    gmail-backup backup dir user@gmail.com

  Backup of e-mails between two dates (YYYYMMDD, the second one is optional):
    gmail-backup backup dir user@gmail.com password 20070621 20080101

  Incremental backup since the date of the last backup ("stamp" file):
    gmail-backup backup dir user@gmail.com --stamp

  Restore your backup:
    gmail-backup restore dir user@gmail.com

  Permanently delete all messages from your mailbox:
    gmail-backup clear user@gmail.com

  List the IMAP mailboxes and number of messages:
    gmail-backup list user@gmail.com
''' % {'env': PASSWORD_ENV}


def getPassword(args):
    if args.password:
        return args.password
    password = os.environ.get(PASSWORD_ENV)
    if password:
        return password
    return getpass.getpass('Password (App Password) for %s: ' % args.username)


def cmdBackup(args, notifier):
    where = ['ALL']
    if args.since:
        where.append('SINCE')
        where.append(_convertTime(args.since))
    if args.before:
        where.append('BEFORE')
        where.append(_convertTime(args.before))

    b = GMailBackup(args.username, getPassword(args), notifier)
    b.backup(args.dirname, where, stamp=args.stamp)


def cmdRestore(args, notifier):
    b = GMailBackup(args.username, getPassword(args), notifier)
    b.restore(args.dirname, args.since, args.before)


def cmdClear(args, notifier):
    mailbox = input("Do you want to delete all messages from your mailbox (%s)?\nPlease, repeat the name of your mailbox: " % args.username)
    if mailbox != args.username:
        print("Mailbox names doesn't match")
        return
    b = GMailBackup(args.username, getPassword(args), notifier)
    b.clear()


def cmdList(args, notifier):
    b = GMailBackup(args.username, getPassword(args), notifier)
    for item, n_messages in b.list():
        print(item, imap_decode(item), n_messages)


def cmdVersion(args, notifier):
    print("GMail Backup revision %s (%s)" % (GMB_REVISION, GMB_DATE))


def buildParser():
    parser = argparse.ArgumentParser(prog='gmail-backup', description=DESCRIPTION, epilog=EPILOG,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--debug', action='store_true', help='print full traceback on errors')
    sub = parser.add_subparsers(dest='command', metavar='command')
    sub.required = True

    def addAccount(p):
        p.add_argument('username', help='your GMail account, eg. foo.bar@gmail.com')
        p.add_argument('password', nargs='?', help='your GMail App Password (asked for if omitted)')

    def addDates(p):
        p.add_argument('since', nargs='?', help='only e-mails since this date, in format YYYYMMDD')
        p.add_argument('before', nargs='?', help='only e-mails before this date, in format YYYYMMDD')

    p = sub.add_parser('backup', help='performs backup of your GMail mailbox')
    p.add_argument('dirname', help='directory (or .zip file) which will contain the backup of your mailbox')
    addAccount(p)
    addDates(p)
    p.add_argument('--stamp', action='store_true', help='backup only e-mails newer than the last backup')
    p.set_defaults(func=cmdBackup)

    p = sub.add_parser('restore', help='performs restore of your previously backed up GMail mailbox')
    p.add_argument('dirname', help='directory (or .zip file) which contains the backup of your mailbox')
    addAccount(p)
    addDates(p)
    p.set_defaults(func=cmdRestore)

    p = sub.add_parser('clear', help='clear this GMail mailbox (remove all messages and labels)')
    addAccount(p)
    p.set_defaults(func=cmdClear)

    p = sub.add_parser('list', help='list the names and number of messages of GMail IMAP mailboxes')
    addAccount(p)
    p.set_defaults(func=cmdList)

    p = sub.add_parser('version', help='print the version')
    p.set_defaults(func=cmdVersion)
    return parser


def main(argv=None):
    parser = buildParser()
    args = parser.parse_args(argv)
    notifier = ConsoleNotifier()
    try:
        args.func(args, notifier)
    except KeyboardInterrupt:
        notifier.nLog("Program interrupted by user")
        return 1
    except Exception:
        type, error, tb = sys.exc_info()
        if args.debug:
            notifier.nExceptionFull(type, error, tb)
        else:
            notifier.nException(type, error, tb)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
