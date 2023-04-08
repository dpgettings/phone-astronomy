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

def _dump_session_key(session_key, keyfile=None, refresh=False):
    if keyfile.is_file() and not refresh:
        raise FileExistsError(f'Session keyfile {keyfile} already exists.')
    else:
        with open(keyfile, 'w') as f:
            return f.write(session_key)

def _login(api_keyfile=None, session_keyfile=None, refresh=False):
    """
    >> u'{"status": "success", "message": "authenticated user: ", "session": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"}'
    """
    api_key = _get_api_key(api_keyfile)

    ## Create new session object
    session = adn.Client()
    session.login(api_key)

    ## Write session key
    session_key = session.session
    _dump_session_key(session_key, session_keyfile, refresh=refresh)

    return session

def _good_session(session_obj):
    try:
        ## Requires login (not all methods do)
        session_obj.myjobs()
    except Exception:
        return False
    else:
        return True
        

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

    ## Check if session is actually not working
    if not _good_session(session):    
        print('--'*80)
        print("*** Session Stale ***")
        ## Redo login
        session = _login(api_keyfile, session_keyfile, refresh=True)
        
    return session

def submit_file(filename, **kwds):

    print("-"*80)
    print("[Establishing Session]")
    session = _establish_session()

    print("-"*80)
    print("[Submitting Image]")
    try:
        upload_result = session.upload(filename)
    except adn.client.RequestError as e:
        print("<< Launching new session >>")
        session = _login(refresh=True, **kwds)
        upload_result = session.upload(filename)

    return upload_result

if __name__ == "__main__":
    import sys

    filename = Path(sys.argv[1])
    print('=='*80)
    print(f'Input File: {filename}')
    
    if filename.is_file():
        sub_info = submit_file(filename)

        ## submission id
        subid = sub_info['subid']

        ## query job status
        sub_url = f'http://nova.astrometry.net/api/submissions/{subid}'

        ## >>> Wait for results loop goes here <<<<
        res = requests.get(sub_url)

        ## if submission has job number, get fits version
        sub_obj = res.json()
        jobid = sub_obj['jobs'][0]

        basename = filename.stem
        
        ### NOT DONE #####
