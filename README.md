gphotos-cli
-----
A (very unofficial) Google Photos command line client to download your photos/videos to local storage.

Requirements
-----
* Python3
* google-api-python-client-py3 https://pypi.org/project/google-api-python-client-py3
* oauth2client https://pypi.org/project/oauth2client
* A Google Photos account

Usage
-----
    pip3 install google-api-python-client-py3 oauth2client
    git clone https://github.com/stevenewbs/gphotos-cli
    cd gphotos-cli
    ./gphotos-cli -a <google-account@gmail.com> -D <destination directory>

On first run, you will need to go through the authentication workflow to allow this script to access (readonly) your Google Photos library. 


Options
-----
* -n, --nodl             : Don't download, just synchronise the file lists. Effectively marks all media items as "downloaded".
* -o, --overwrite        : Force overwrite of media that already exist in the destination.
* -a, --account          : Add a second Google account to download music from (The "partner" solution - I got married!)
* -D, --destination_path : Specify the destination path for downloaded photos. *NOTE* This doesnt affect cache of previously downloaded photos - that is stored separately. 


ToDo
-----
Move to use google-auth-oauthlib 0.4.0 as oauth2client is deprecated
