"""
gphotos.py - Steve Newbury, 2019

A library to interact with Google Photos - primarily downloading at this point.
"""
import shelve
import os
import sys
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
from apiclient.discovery import build
from apiclient.errors import HttpError
from httplib2 import Http
from oauth2client import file, client, tools
from tqdm import tqdm


class GooglePhotosService(object):

    def __init__(self, creds_file, scopes, flags):
        store = file.Storage(creds_file)
        creds = None
        if os.path.exists(creds_file):
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
        except HTTPError as httpe:
            print('HTTP error while downloading %s : %s' % (filename, httpe))
            if HTTPError.code == 403:
                # the token will expire after about an hour, at which point 
                # the requests start failing with 403 errors
                return None
        except IOError as e:
            print('IOError while writing %s : %s' % (filename, e))
            return False
        return True

    def download_new_files(self):
        self.populate_media_items()
        self.downloaded = 0
        for i in tqdm(self.media_items):
            photo_obj = self.media_items[i]
            id = photo_obj['id']
            if id in self.library:
                continue
            result = self.download_item(photo_obj)
            if result:
                self.library[photo_obj['id']] = photo_obj
                self.downloaded += 1
            if result == None:
                self.setup_service()
        print('Downloaded %s new photos' % self.downloaded)

