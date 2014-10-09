import sys, os, re
import logging
from flask import Flask, g, url_for, render_template, request, abort, session, redirect
from pkg_resources import resource_stream
import lya
import pdb
import requests, http
import json
from flask_oauthlib.client import OAuth
from c9hubdashboard.forms import forms
from flask_wtf.csrf import CsrfProtect
from urllib.parse import urlparse


cfg = lya.AttrDict.from_yaml(resource_stream('c9hubdashboard.resources.etc', 'c9hubdashboard.default.yaml'))
print(' * Configuration ...')
cfg.dump(sys.stdout)

if os.getenv('C9HUB_API_PORT') is None:
    raise RuntimeError('Cannont locate the api')
C9HUB_API_PORT=re.sub('^tcp://', 'http://', os.getenv('C9HUB_API_PORT'))
print("Api endpoint: {}".format(C9HUB_API_PORT))


app = Flask(__name__, static_folder='../static', template_folder='../templates')
app.secret_key = 'secret_Rdflddos'
csrf = CsrfProtect(app)


oauth = OAuth(app)
logging.getLogger('flask_oauthlib').addHandler(logging.StreamHandler())
logging.getLogger('flask_oauthlib').setLevel(logging.DEBUG)
# remote = oauth.remote_app(
#     'doorkeeper-local',
#     consumer_key='a7af4b0df277e0fe7d14d80142ed67f80eb33a55bb77c7fe28614baa8a81c9c8',
#     consumer_secret='428345493f6d1a67f67733ee3a4bfa2ac424622fd6aca18b3c244ce647c30e62',
#     request_token_params={}, #{'scope': 'read'},
#     base_url='http://192.168.103.116:8080/authorize',
#     request_token_url=None,
#     access_token_url='https://127.0.0.1:3000/oauth/token',
#     access_token_method='POST',
#     authorize_url='https://192.168.103.116:3000/oauth/authorize'
# )
remote = oauth.remote_app(
    'doorkeeper-local',
    consumer_key='a7af4b0df277e0fe7d14d80142ed67f80eb33a55bb77c7fe28614baa8a81c9c8',
    consumer_secret='428345493f6d1a67f67733ee3a4bfa2ac424622fd6aca18b3c244ce647c30e62',
    request_token_params={},
    base_url='https://192.168.103.116:3000',
    request_token_url=None,
    access_token_url='https://172.17.42.1:3000/oauth/token',
    access_token_method='POST',
    authorize_url='oauth/authorize'
)

@app.before_request
def before_request():
    g.cfg = cfg

@app.after_request
def add_header(response):
    if request.path.startswith('/static/lib/'):
        return response
    if cfg.debug:
        response.cache_control.max_age = 0
        response.cache_control.no_store = True
        response.cache_control.no_cache = True
    return response

@app.teardown_request
def teardown_request(exception):
    pass

@csrf.error_handler
def csrf_error(reason):
    abort(400, {'error': 'Invalid csrf: {}'.format(reason)})

@app.route('/', methods=['GET', 'POST'])
def root():
    app.logger.info('root (method={}): {}'.format(request.method, dict(request.args)))
    host_ip = request.headers.get('X-Forwarded-Host', '0.0.0.0')
    if get_oauth_token() is None:
        app.logger.info('No token was found, redirecting to authorization server')
        #callback = url_for('authorize', next=None, _external=True)
        callback = "https://{}/authorize".format(host_ip)
        return remote.authorize(callback=callback)
    else:
        f = forms.CreateIdeForm()
        if request.method == 'POST':
            if f.validate_on_submit():
                target_endpoint_id = None
                r = requests.get('{}/v1/validationendpoint'.format(C9HUB_API_PORT))
                if r.status_code == 200:
                    versus = urlparse(remote.access_token_url)
                    for item in r.json():
                        pu = urlparse(item.get('url', ''))
                        app.logger.error('>>>>>>>>>> {}  VS  {}'.format(versus, pu))
                        if (versus.scheme == pu.scheme and versus.netloc == pu.netloc
                            and item.get('id')):
                            target_endpoint_id = item.get('id')
                            break
                else:
                    return redirect('/failure')
                if target_endpoint_id is None:
                    return redirect('/no_endpoint')
                payload = {
                    'display_name': f.display_name.data,
                    'credentials': {
                        'username': f.username.data,
                        'password': f.password.data
                        },
                    'git_clones': f.git_clones.data.split(' ')
                    }
                app.logger.info('root: making a rest request to the api')
                r = requests.post('{}/v1/ide'.format(C9HUB_API_PORT), data=json.dumps(payload), 
                                  headers={'Authorization': 'Bearer ' + get_oauth_token()[0], 'Content-Type': 'application/json', 'Validation-Endpoint': target_endpoint_id})
                if r.status_code != 200:
                    return redirect('/failure')
                r = requests.get('{}/v1/ide/{}'.format(C9HUB_API_PORT, r.json()['id']), allow_redirects=False)
                if r.status_code == 200:
                    target = r.json()['container_id']
                    return redirect("https://{}:8080/{}".format(host_ip, target))
                else:
                    return redirect('/failure')
            else:
                app.logger.info('root: invalid form')
        return render_template('index.html', form=f)
        #return app.send_static_file('index.html')
        #return url_for('static', filename='index.html')


@app.route('/authorize')
def authorize():
    app.logger.info('> GET /authorise: %s', dict(request.args))
    resp = remote.authorized_response()
    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']
        )
    print(resp)
    session['remote_oauth'] = (resp['access_token'], resp['refresh_token'])
    #return redirect(url_for('root', _scheme="https", _external=True))
    return redirect("https://{}{}".format(
            request.headers.get('X-Forwarded-Host', '0.0.0.0'), url_for('root')))

@remote.tokengetter
def get_oauth_token():
    app.logger.info("get_oauth_token: getting or regreshing bearer token")
    tmp = session.get('remote_oauth')
    if tmp is None:
        return None
    rf = tmp[1]
    payload = {
        'grant_type': 'refresh_token',
        'client_id': remote.consumer_key,
        'client_secret' : remote.consumer_secret,
        'refresh_token': rf
        }
    r = requests.post(remote.access_token_url, data=payload, verify=False)
    if r.status_code == 200:
        j = r.json()
        session['remote_oauth'] = (j['access_token'], j['refresh_token'])
        return session.get('remote_oauth')
    else:
        session.pop('remote_oauth', None)
        return None
# grant_type=authorization_code&client_id=a7af4b0df277e0fe7d14d80142ed67f80eb33a55bb77c7fe28614baa8a81c9c8&client_secret=428345493f6d1a67f67733ee3a4bfa2ac424622fd6aca18b3c244ce647c30e62&redirect_uri=http%3A%2F%2F192.168.103.116%3A8080%2Fauthorize&code=6dedc68e0f42b43027f6ea9cc204bbc80612139917774280caa6c6b55274542b



# @remote.tokengetter
# def get_oauth_token(access_token=None, refresh_token=None):
#     if access_token:
#         return session.get('remote_oauth')
#     elif refresh_token:
#         return session.get('refresh_token')
    
# @remote.tokensetter
# def save_token(token, request, *args, **kwargs):
#     session['remote_oauth'] = (token['access_token'], token['refresh_token'])
