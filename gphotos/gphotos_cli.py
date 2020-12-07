#!/usr/bin/env python3
"""
gphotos-cli.py - steve newbury, 2019

A basic command line tool to download your photos/videos from Google Photos to local storage.
"""

from gphotos import GooglePhotosService
import argparse
import os
import shelve
import sys
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
from oauth2client import tools

class GphotosCli(object):

    def __init__(self, flags, dest_dir=None, account=None):
        self.orig_flags = flags
        if os.environ.get('SNAP_USER_COMMON'):
            snap_conf = os.environ.get('SNAP_USER_COMMON')
            self.prog_dir = os.path.expanduser(snap_conf + '/config')
        else:
            self.prog_dir = os.path.expanduser('~/.config/gphotos-cli')
        if dest_dir:
            self.dest_dir = os.path.expanduser(dest_dir)
        else:
            self.dest_dir = os.path.expanduser('~/google-photos')

        if account:
            creds_file_name = '%s-creds.json' % account
            self.library_file_path = os.path.join(self.prog_dir, '%s-gphotos-cli_library_shelf' % account)
        else:
            creds_file_name = 'creds.json'
            self.library_file_path = os.path.join(self.prog_dir, 'gphotos-cli_library_shelf')
        self.overwrite = flags.overwrite
        self.no_dl = flags.nodl
        self.remove_deleted = flags.remove_deleted
        self.show_progress = flags.print_progress
        self.creds_file_path = os.path.join(self.prog_dir, creds_file_name)
        self.media_items = {}
        self.make_dirs() # do this first, will exit if dirs creation fails
        self.scopes = 'https://www.googleapis.com/auth/photoslibrary.readonly'
        self.setup_service()
        self.library = shelve.open(self.library_file_path)

    def __enter__(self):
        return self

    def __exit__(self, expt_type, expt_val, trace):
        self.library.sync()
        self.library.close()

    def close_library(self):
        print('Writing and closing down library')
        self.library.sync()
        self.library.close()

    def setup_service(self):
        self.gpservice = GooglePhotosService(self.creds_file_path, self.scopes, self.orig_flags)

    def make_dirs(self):
        for path in [self.prog_dir, self.dest_dir]:
            if not os.path.exists(path):
                try:
                    os.makedirs(path)
                except IOError as e:
                    print("Error creating %s dir: %s " % (path, e))
                    sys.exit(1)

    def populate_media_items(self):
        print('Loading GooglePhotos library...')
        npt = None
        while True:
            result = self.gpservice.get_media_items(next_token=npt)
            if 'mediaItems' in result:
                for i in result['mediaItems']:
                    self.media_items[i['id']] = i
            sys.stdout.flush()
            sys.stdout.write('\r%s items gathered' % len(self.media_items))
            if 'nextPageToken' in result:
                npt = result['nextPageToken']
            else:
                break

    def download_item(self, photo_obj):
        if self.no_dl:
            return True
        # Photos API object URL needs a flag to indicate download
        if 'video' in photo_obj['mimeType']:
            dl_flag = '=dv'
        else:
            dl_flag = '=d'
        base_url = photo_obj['baseUrl']
        download_url = base_url + dl_flag
        filename = photo_obj['filename']
        path = self.dest_dir + '/' + filename
        try:
            f = urlopen(download_url)
            photo_bytes = f.read()
            with open(path, 'wb') as f:
                f.write(photo_bytes)
        except HTTPError as herr:
            print('Http Error while downloading %s : %s' % (filename, herr))
            if herr.code == 403:
                # the URLs for the photos will expire after about an hour, at which point
                # the requests start failing with 403 errors
                return None
            return False
        except (URLError, IOError) as e:
            print('URL/IOError while writing %s : %s' % (filename, e))
            return False
        return True

    def print_progress(self, what):
        if self.show_progress:
            sys.stdout.flush()
            sys.stdout.write('\r%s' % what)

    def download_new_files(self):
        self.populate_media_items()
        self.downloaded = 0
        counter = 0
        for i in self.media_items:
            photo_obj = self.media_items[i]
            id = photo_obj['id']
            if id not in self.library or self.overwrite:
                result = self.download_item(photo_obj)
                if result == None:
                    # We got a 403 so urls have expired
                    print('\nMedia Urls have expired - requesting library re-populate')
                    i = 0
                    self.populate_media_items()
                if result:
                    self.library[id] = photo_obj
                    self.downloaded += 1
            counter += 1
            self.print_progress('%s / %s items processed' % (counter, len(self.media_items)))
        print('\nDownloaded %s new items' % self.downloaded)

    def remove_deleted_files(self):
        if not self.remove_deleted:
            return
        removed = counter = 0
        for i in self.library:
            photo_obj = self.library[i]
            id = photo_obj['id']
            path = self.dest_dir + '/' + photo_obj['filename']
            if id not in self.media_items:
                try:
                    os.remove(path)
                    removed += 1
                except OSError as e:
                    pass
                counter += 1
            self.print_progress('%s / %s items processed' % (counter, len(self.library)))
        print('\nRemoved %s deleted items' % removed)


def do_args():
    parser = argparse.ArgumentParser(description='gphotos-cli - Steve Newbury 2019 - version 0.1', parents=[tools.argparser])
    # Oauth has its own set of flags which it sets up itself (tools.argparser). Pass in the parent to catch them and add them to our flags
    parser.add_argument('-n', '--nodl', action='store_true', help="No Download - synchronises a list of existing files. Handy for initial sync of photo library.")
    parser.add_argument('-d', '--debug', action='store_true', help="Debug mode")
    parser.add_argument('-p', '--print_progress', action='store_true', help="Output progress while downloading media")
    parser.add_argument('-o', '--overwrite', action='store_true', help="Force overwrite of files that were already downloaded.")
    parser.add_argument('-a', '--account', action='store', help="Specify the Google account you are logging in with.")
    parser.add_argument('-D', '--destination_path', action='store', help="Specify the destination path for downloaded photos.") # doesnt affect cache of previously downloaded photos
    parser.add_argument('-R', '--remove_deleted', action='store_true', help="Remove files that have been removed from GooglePhotos. USE WITH CARE!")
    args = parser.parse_args()
    return args

def main():
    args = do_args()
    with GphotosCli(args, dest_dir=args.destination_path, account=args.account) as gpcli:
        try:
            gpcli.download_new_files()
            gpcli.remove_deleted_files()
        except KeyboardInterrupt:
            print('\nStop requested')
            print('\n%s new items downloaded ...' % gpcli.downloaded)
            gpcli.close_library()
            try:
                sys.exit(0)
            except SystemExit:
                os._exit(0)
        finally:
            gpcli.close_library()

if __name__ == '__main__':
    main()
