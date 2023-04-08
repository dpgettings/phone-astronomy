from pathlib import Path
import requests
import json
from astrometry.net import client as adn

repo_dir = Path('/home/dan/github-repos/phone-astronomy')
API_KEYFILE = repo_dir / 'api.key'
SESSION_KEYFILE = Path('session.key')

def _get_api_key(keyfile=None):
    if keyfile.is_file():
        with open(keyfile, 'r') as f:
            return f.read().strip()
    else:
        raise FileNotFoundError(f'API keyfile {keyfile} not found.')

def _dump_session_key(session_key, keyfile=None):
    if keyfile.is_file():
        raise FileExistsError(f'Session keyfile {keyfile} already exists.')
    else:
        with open(keyfile, 'w') as f:
            return f.write(session_key)

def _login(api_keyfile=None, session_keyfile=None):
    """
    >> u'{"status": "success", "message": "authenticated user: ", "session": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"}'
    """
    api_key = _get_api_key(api_keyfile)

    ## Create new session object
    session = adn.Client()
    session.login(api_key)

    ## Write session key
    session_key = session.session
    _dump_session_key(session_key, session_keyfile)

    return session

def _establish_session(session_keyfile=SESSION_KEYFILE, api_keyfile=API_KEYFILE):
    """
    TODO: Check if session key is stale. If so, establish new session.
    """
    ## Check if logged in
    if not session_keyfile.is_file():
        ## Log in and write session key
        session = _login(api_keyfile, session_keyfile)
    else:
        ## Create new session obj
        session_key = _get_api_key(session_keyfile)
        session = adn.Client()
        ## Add existing session key
        session.session = session_key

    return session

def submit_file(filename, **kwds):

    session = _establish_session(**kwds)

    return session.upload(filename)


if __name__ == "__main__":
    import sys

    filename = Path(sys.argv[1])
    print(f'Input File: {filename}')
    
    if filename.is_file():
        sub_info = submit_file(filename)

        ## submission id
        subid = sub_info['subid']

        ## query job status
        sub_url = f'http://nova.astrometry.net/api/submissions/{subid}'
        res = requests.get(sub_url)

        ## if submission has job number, get fits version
        sub_obj = res.json()
        jobid = sub_obj['jobs'][0]

        basename = filename.stem
        
