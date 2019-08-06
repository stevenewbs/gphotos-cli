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
