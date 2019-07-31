"""
gphotos-cli.py - Steve Newbury, 2019

A basic photo manager to sync your photos from Google Photos to local storage
"""
import argparse
import datetime
import os
import shelve
import sys
from urllib.request import urlopen
from urllib.error import URLError
from apiclient.discovery import build
from apiclient.errors import HttpError
from httplib2 import Http
from oauth2client import file, client, tools
from tqdm import tqdm


class GooglePhotosService(object):

    def __init__(self, creds_file, scopes, flags):
        store = file.Storage(creds_file)
        creds = store.get()
        if not creds or creds.invalid:
            flow = client.OAuth2WebServerFlow(client_id='330748126588-jdcnokqu0qejifauaet2o7r0de55h1mp.apps.googleusercontent.com',
                client_secret='ufZwchZoRofvSN4pdAdbc-yy', scope=scopes)
            creds = tools.run_flow(flow, store, flags)
        self.service = build('photoslibrary', 'v1', http=creds.authorize(Http()))

    def get_media_items(self, size=99, next_token=None):
        try:
            result = self.service.mediaItems().list(pageSize=size, pageToken=next_token).execute()
        except HttpError as err:
            print('HttpError while requesting photo list : %s' % err)
            raise
        return result     

class GphotosCli(object):

    def __init__(self, flags, dest_dir=None, account=None):
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
        self.creds_file_path = os.path.join(self.prog_dir, creds_file_name)
        self.media_items = {}
        self.make_dirs() # do this first, will exit if dirs creation fails
        self.scopes = 'https://www.googleapis.com/auth/photoslibrary.readonly'
        self.gpservice = GooglePhotosService(self.creds_file_path, self.scopes, flags)
        self.library = shelve.open(self.library_file_path)

    def __enter__(self):
        return self

    def __exit__(self, expt_type, expt_val, trace):
        self.library.sync()
        self.library.close()

    def make_dirs(self):
        for path in [self.prog_dir, self.dest_dir]:
            if not os.path.exists(path):
                try:
                    os.mkdir(path)
                except IOError as e:
                    print("Error creating %s dir: %s " % (path, e))
                    sys.exit(1)

    def populate_media_items(self):
        print('Loading photo library...')
        npt = None
        while True:
            result = self.gpservice.get_media_items(next_token=npt)
            if 'mediaItems' in result:
                for i in result['mediaItems']:
                    self.media_items[i['id']] = i
            sys.stdout.flush()
            sys.stdout.write('\r%s photos gathered' % len(self.media_items))
            if 'nextPageToken' in result:
                npt = result['nextPageToken']
            else:
                break

    def download_item(self, photo_obj):
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
        except URLError as urle:
            print('Urlopen error while downloading %s : %s' % (filename, urle))
            return False
        except IOError as e:
            print('IOError while writing %s : %s' % (filename, e))
            return False
        return True

    def download_new_files(self):
        self.populate_media_items()
        downloads = counter = 0
        for i in tqdm(self.media_items):
            photo_obj = self.media_items[i]
            id = photo_obj['id']
            if id in self.library:
                continue
            if self.download_item(photo_obj):
                self.library[photo_obj['id']] = photo_obj
                downloads += 1
        print('Downloaded %s new photos' % downloads)

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
            print('\nStop requested - exiting...')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

if __name__ == '__main__':
    main()
