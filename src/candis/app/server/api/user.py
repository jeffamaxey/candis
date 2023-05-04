# imports - standard imports
import os
import gc
import json
import datetime

# imports - third-party imports
from flask import request, jsonify
from flask_mail import Message
import jwt
import addict
from jwt.exceptions import ExpiredSignatureError, InvalidSignatureError

# imports - module imports
from candis.app.server.app import app, redis, mail
from candis.app.server.models.user import User
from candis.config import CONFIG
from candis.app.server.response import Response
from candis.app.server.helpers import verify_password, modify_data_path
from candis.app.server.utils import login_required, logout_required, save_response_to_db, MailMessage

def generate_token(user_, key=app.config['SECRET_KEY'], delay=os.environ.get('EXPIRY_TIME_DELAY')):
    payload = addict.Dict(username=user_.username, email=user_.email)
    if delay:
        exp = datetime.datetime.utcnow() + datetime.timedelta(seconds=delay)
        payload.update({'exp': exp})
    return jwt.encode(payload=payload, key=key).decode('utf-8')

@app.route(CONFIG.App.Routes.API.User.SIGN_UP, methods=['POST'])
@logout_required
def sign_up():
    response = Response()
    form = addict.Dict(request.get_json())
    username, email, password = form['username'], form['email'], form['password']

    if User.get_user(username=username):
        response.set_error(
            Response.Error.UNPROCESSABLE_ENTITY,
            f"User with username '{username}'is already registered",
        )
    elif User.get_user(email=email):
        response.set_error(
            Response.Error.UNPROCESSABLE_ENTITY,
            f"User with email '{email}' is already registered",
        )
    else:
        new_user = User(username, email, password)
        new_user.add_user()

        encoded_token = generate_token(new_user)
        response.set_data({
            'token': encoded_token,
            'message': 'Registered successfully.'
        })
        new_user.close()

        try:
            path = CONFIG.App.DATADIR
            if not os.path.exists(path):
                os.mkdir(path)
            path = os.path.join(path, modify_data_path(username))
            if not os.path.exists(path):
                os.mkdir(path)
        except OSError as e:
            response.set_error(
                Response.Error.UNPROCESSABLE_ENTITY,
                f'could not setup data directory: {e}',
            )

    gc.collect()

    dict_      = response.to_dict()
    save_response_to_db(dict_)
    json_      = jsonify(dict_)
    code       = response.code

    return json_, code

@app.route(CONFIG.App.Routes.API.User.LOGIN, methods=['POST'])
@logout_required
def login():
    response = Response()
    form = addict.Dict(request.get_json())
    username, password = form['username'], form['password']

    user = User.get_user(username=username)
    if not user:
        response.set_error(
            Response.Error.UNPROCESSABLE_ENTITY,
            f'No User with username {username} found',
        )
    elif not verify_password(user.password, password):
        response.set_error(
            Response.Error.ACCESS_DENIED,
            'Password is incorrect.'
        )
    else:
        response.set_data({
            'token': generate_token(user),
            'message': 'Logged in successfully.'
        })
        redis.redis.hset('blacklist', user.username, 'False')

    dict_      = response.to_dict()
    save_response_to_db(dict_)
    json_      = jsonify(dict_)
    code       = response.code

    return json_, code

@app.route(CONFIG.App.Routes.API.User.SIGN_OUT, methods=['POST'])
@login_required
def logout(user):
    response = Response()
    
    username = user.username

    redis.redis.hset('blacklist', username, 'True')
    response.set_data({'message': 'Logged out successfully!'})
    
    dict_      = response.to_dict()
    save_response_to_db(dict_)
    json_      = jsonify(dict_)
    code       = response.code

    return json_, code

@app.route(CONFIG.App.Routes.API.User.FORGOT_PASSWORD, methods=['POST'])
@logout_required
def forgot():
    response = Response()
    form = addict.Dict(request.get_json())
    email = form['email']
    if user := User.get_user(email=email):
        delay = 900
        reset_token = generate_token(user, delay=delay)
        msg = Message(
            "Reset password!",
            recipients=[email]
        )
        # need to update url with prefix host name during runtime.
        url = request.host_url.rsplit('/', 1)[0] + CONFIG.App.Routes.RESET_PASSWORD
        msg.html = MailMessage.forgot_password_body(
            url=url, reset_token=reset_token, time=f'{delay / 60} minutes'
        )
        mail.send(msg)
        response.set_data({'message': 'Check your inbox for password reset link!'})
    else:
        response.set_error(
            Response.Error.UNPROCESSABLE_ENTITY,
            f"user with email '{email}' is not registered with us",
        )

    dict_      = response.to_dict()
    save_response_to_db(dict_)
    json_      = jsonify(dict_)
    code       = response.code

    return json_, code

@app.route(CONFIG.App.Routes.API.User.RESET_PASSWORD, methods=['POST'])
@logout_required
def reset():
    response = Response()
    form = addict.Dict(request.get_json())
    if 'reset_token' in form:
        # validate jwt token
        try:
            payload = jwt.decode(form.reset_token, app.config['SECRET_KEY'])
            username = payload['username']
            if 'new_password' in form:
                user = User.get_user(username=username)
                user.update_user(password=form.new_password)
                response.set_data({'message': 'Password updated successfully!'})
            else:
                response.set_data({'message': 'Enter your new password.'})
        except Exception as e:
            response.set_error(
                Response.Error.ACCESS_DENIED,
                "Invalid token."
            )
    else:
        response.set_error(
            Response.Error.ACCESS_DENIED,
            "Create a reset token first"
        )

    dict_      = response.to_dict()
    save_response_to_db(dict_)
    json_      = jsonify(dict_)
    code       = response.code

    return json_, code
