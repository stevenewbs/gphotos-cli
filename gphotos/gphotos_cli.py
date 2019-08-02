#!/usr/bin/env python3
"""
gphotos-cli.py - steve newbury, 2019

A basic command line tool to download your photos/videos from Google Photos to local storage
"""

from .gphotos import *
import argparse
import os

def do_args():
    parser = argparse.ArgumentParser(description='gphotos-cli - Steve Newbury 2019 - version 0.1', parents=[tools.argparser])
    # Oauth has its own set of flags which it sets up itself (tools.argparser). Pass in the parent to catch them and add them to our flags
    parser.add_argument('-n', '--nodl', action='store_true', help="No Download - synchronises a list of existing files. Handy for initial sync of photo library.")
    parser.add_argument('-d', '--debug', action='store_true', help="Debug mode")
    parser.add_argument('-o', '--overwrite', action='store_true', help="Force overwrite of files that were already downloaded.")
    parser.add_argument('-a', '--account', action='store', help="Specify the Google account you are logging in with.")
    parser.add_argument('-D', '--destination_path', action='store', help="Specify the destination path for downloaded photos.") # doesnt affect cache of previously downloaded photos
    args = parser.parse_args()
    return args

def main():
    args = do_args()
    with GphotosCli(args, dest_dir=args.destination_path, account=args.account) as gpcli:
        try:
            gpcli.download_new_files()
        except KeyboardInterrupt:
            print('\nStop requested')
            print('\n%s new items downloaded - exiting...' % gpcli.downloaded)
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

if __name__ == '__main__':
    main()
