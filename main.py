from flask import Flask
from flask import request, Response
from flask import render_template
from flask import send_file
from flask import redirect
from flask import jsonify
from flask import make_response
from functools import wraps, update_wrapper
from datetime import datetime
import servers
import random
import json
import glob
import os
import sys
import socket

import re

from jinja2 import evalcontextfilter, Markup, escape
import jinja2
import simplepam

app = Flask(__name__)

_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')

@evalcontextfilter
def nl2br(eval_ctx, value):
    result = u'\n\n'.join(u'%s' % p.replace('\n', Markup('<br>\n'))
                          for p in _paragraph_re.split(escape(value)))
    if eval_ctx.autoescape:
        result = Markup(result)
    return result

jinja2.filters.FILTERS['nl2br'] = nl2br

def nocache(view):
    @wraps(view)
    def no_cache(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers['Last-Modified'] = datetime.now()
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response
    return update_wrapper(no_cache, view)

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """

    return  simplepam.authenticate(username, password)

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

app = Flask(__name__)

import subprocess
def check_monitor():
   o = subprocess.check_output(["ps -ax | grep monitor"],shell=True)
   
   if len(o.split("\n"))>3:
        return True
   else:
        return False


@app.route("/")
def main():
    servs,groups = servers.get_servers_and_groups()
    return render_template("./main.html",servers_dict=servs, groups_dict=groups, monitor_runned=check_monitor())


@app.route("/monitor/server/<id>")
def server_info(id):
    return render_template("./server.html",servid=id)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)
