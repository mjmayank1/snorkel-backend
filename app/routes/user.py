import os
from flask import Blueprint, request
from app.models import User, Review
from app import db, app, cache
import jwt
import json
import requests
from jwt.algorithms import RSAAlgorithm
from flask_jwt_extended import (
  jwt_required,
  get_current_user,
  create_access_token,
  create_refresh_token,
  set_access_cookies,
  set_refresh_cookies,
  unset_jwt_cookies
)
  
from app.helpers.create_account import create_account
from app.helpers.login import login
from sqlalchemy import or_, func
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import bcrypt
from flask.helpers import make_response

bp = Blueprint('user', __name__, url_prefix="")

"""
Auth data goes in a cookie
"""
@bp.route("/user/register", methods=["POST"])
def user_signup():
  """ Register
  ---
  post:
      summary: Register new user endpoint.
      description: Register a new user
      parameters:
          - name: first_name
            in: body
            description: First Name
            type: string
            required: true
          - name: last_name
            in: body
            description: Last Name
            type: string
            required: true
          - name: email
            in: body
            description: Email address
            type: string
            required: true
          - name: username
            in: body
            description: Username
            type: string
            required: false
          - name: profile_pic
            in: body
            description: Profile Pic
            type: string
            required: false
          - name: password
            in: body
            description: Password
            type: string
            required: false
      responses:
          200:
              description: Returns User object
              content:
                application/json:
                  schema: UserSchema
          400:
              content:
                application/json:
                  schema:
                    msg: string
              description: User couldn't be created.
  """
  first_name = request.json.get('first_name') or ''
  last_name = request.json.get('last_name') or ''
  email = request.json.get('email')
  username = request.json.get('username')
  profile_pic = request.json.get('profile_pic')
  unencrypted_password = request.json.get('password')
  display_name = first_name + ' ' + last_name

  resp = create_account(
    db,
    first_name=first_name,
    last_name=last_name,
    display_name=display_name,
    email=email,
    profile_pic=profile_pic,
    username=username,
    unencrypted_password=unencrypted_password,
  )
  return resp

@bp.route("/user/apple_register", methods=["POST"])
def user_apple_signup():
  """ Apple Register
  ---
  post:
      summary: Register new user with Apple auth endpoint.
      description: Register a new user with Apple auth
      requestBody:
        content:
          application/json:
            schema: AppleRegisterSchema
      responses:
          200:
              description: Returns User object
              content:
                application/json:
                  schema: UserSchema
          400:
              content:
                application/json:
                  schema:
                    msg: string
              description: User couldn't be created.
  """
  #https://developer.apple.com/documentation/sign_in_with_apple/sign_in_with_apple_js/configuring_your_webpage_for_sign_in_with_apple
  code = request.json.get('code')
  id_token = request.json.get('id_token')
  state = request.json.get('state')
  email = None
  

  #https://gist.github.com/davidhariri/b053787aabc9a8a9cc0893244e1549fe
  key_payload = requests.get('https://appleid.apple.com/auth/keys').json()
  token_headers = jwt.get_unverified_header(id_token)
  jwk = None
  for key in key_payload["keys"]:
    if key.get('kid') == token_headers.get('kid'):
      jwk = key
  if not jwk:
    return 'No matching key found', 500
  public_key = RSAAlgorithm.from_jwk(json.dumps(jwk))


  try:
      token = jwt.decode(id_token, public_key, audience=os.environ.get("APPLE_APP_ID"), algorithms=["RS256"])
  except jwt.exceptions.ExpiredSignatureError as e:
      raise Exception("That token has expired")
  except jwt.exceptions.InvalidAudienceError as e:
      raise Exception("That token's audience did not match")
  except Exception as e:
      print(e)
      raise Exception("An unexpected error occoured")
  if not email:
    email = token.get('email')

  user = User.query.filter(func.lower(User.email)==email.lower()).first()
  if user:
    return login(user)

  # renamed  to avoid confusion and possible name clashes
  user_body = request.json.get('user')
  if user_body:
    first_name = user_body.get('name').get('firstName')
    last_name = user_body.get('name').get('lastName')
    display_name = first_name + last_name
    email = user_body.get('email')

    return create_account(
      db,
      first_name,
      last_name,
      display_name,
      email,
    )

  return { "msg": "user doesn't exist and didn't get a user object"}, 422


@bp.route("/user/google_register", methods=["POST"])
def user_google_signup():
  """ Google Register
  ---
  post:
      summary: Register new user with Google auth endpoint.
      description: Register a new user with Google auth
      parameters:
          - name: credential
            in: body
            description: google oauth token credential returned from Google login button
            type: string
            required: true
      responses:
          200:
              description: Returns User object
              content:
                application/json:
                  schema: UserSchema
          400:
              content:
                application/json:
                  schema:
                    msg: string
              description: User couldn't be created.
  """
  token = request.json.get('credential')
  app.logger.error(request.json.get('credential'))
  userid = None
  try:
    # Specify the CLIENT_ID of the app that accesses the backend:
    idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), os.environ.get('GOOGLE_CLIENT_ID'))

    # Or, if multiple clients access the backend server:
    # idinfo = id_token.verify_oauth2_token(token, requests.Request())
    # if idinfo['aud'] not in [CLIENT_ID_1, CLIENT_ID_2, CLIENT_ID_3]:
    #     raise ValueError('Could not verify audience.')

    # If auth request is from a G Suite domain:
    # if idinfo['hd'] != GSUITE_DOMAIN_NAME:
    #     raise ValueError('Wrong hosted domain.')

    # ID token is valid. Get the user's Google Account ID from the decoded token.
    email = idinfo.get('email')
    user = User.query.filter(func.lower(User.email)==email.lower()).first()
    if user:
      return login(user)
    first_name = idinfo.get('given_name')
    last_name = idinfo.get('family_name')
    display_name = idinfo.get('name')
    profile_pic = idinfo.get('picture')
    resp = create_account(
      db,
      first_name,
      last_name,
      display_name,
      email,
      profile_pic,
    )
    return resp
  except ValueError:
    return { 'data': token }, 401
    # Invalid token
    pass
  return { 'data': userid, 'token': token }

@bp.route("/user/register/password", methods=["POST"])
def user_finish_signup():
  """ Add account password
  ---
  post:
      summary: Add password for a newly registered user. Can't be used to change password.
      description: Add password for a newly registered user. Can't be used to change password.
      parameters:
          - name: user_id
            in: body
            description: User ID (not username)
            type: string
            required: true
          - name: password
            in: body
            description: password
            type: string
            required: true
      responses:
          200:
              description: Returns User object
              content:
                application/json:
                  schema: UserSchema
          400:
              content:
                application/json:
                  schema:
                    Error:
                      properties:
                        msg:
                          type: string
              description: User couldn't be created.
  """
  user_id = request.json.get('user_id')
  user = User.query.filter_by(id=user_id).first()
  if user.password:
    return { 'msg': 'This user has already registered a password' }, 401
  unencrypted_password = request.json.get('password')
  password = bcrypt.hashpw(unencrypted_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
  user.password = password
  db.session.commit()
  auth_token = create_access_token(identity=user.id)
  refresh_token = create_refresh_token(identity=user.id)
  responseObject = {
    'status': 'success',
    'message': 'Successfully registered.',
    'auth_token': auth_token,
    'username': user.username,
  }
  resp = make_response(responseObject)
  set_access_cookies(resp, auth_token)
  set_refresh_cookies(resp, refresh_token)
  return resp

"""
Save the response token as an Authorization header with the format
Authorization: Bearer <token>
"""
@bp.route("/user/login", methods=["POST"])
def user_login():
  """ Login
  ---
  post:
      summary: login with username/email and password
      description: login with username/email and password
      parameters:
          - name: email
            in: body
            description: username or password
            type: string
            required: true
          - name: password
            in: body
            description: password
            type: string
            required: true
      responses:
          200:
              description: Returns User object
              content:
                application/json:
                  schema: UserSchema
          400:
              content:
                application/json:
                  schema:
                    Error:
                      properties:
                        msg:
                          type: string
              description: Wrong password.
  """
  email = request.json.get('email')
  password = request.json.get('password')
  
  user = User.query.filter(or_(func.lower(User.email)==email.lower(), User.username==email)).first()
  if not user:
    return { 'msg': 'Wrong password or user does not exist' }, 400
  if bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
    return login(user)
  else:
    return { 'msg': 'Wrong password or user does not exist' }, 400

@bp.route("/user/logout")
def logout():
  resp = make_response({'msg': 'Successfully logged out'})
  unset_jwt_cookies(resp)
  return resp

@bp.route("/user/patch", methods=["PATCH"])
@jwt_required()
def patch_user():
  """ Patch User
    ---
    patch:
        summary: patch user (admin only)
        description: patch user (admin only). also include the params of the user that you want to change in the body
        parameters:
          - name: id
            in: body
            description: user id
            type: int
            required: true
        responses:
            200:
                description: Returns User object
                content:
                  application/json:
                    schema: UserSchema
            400:
                content:
                  application/json:
                    schema:
                      Error:
                        properties:
                          msg:
                            type: string
                description: Not logged in.
  """
  user = get_current_user()
  user_id = request.json.get('id')
  if user.admin and user_id:
    user = User.query.filter_by(id=user_id).first_or_404()
  updates = request.json
  updates.pop('id', None)
  try:
    for key in updates.keys():
      if key == 'username':
        username = updates.get(key).lower()
        if not username.isalnum():
          return {
            'msg': 'Usernames can\'t have special characters'
          }, 422
        if User.query.filter_by(username=username).first():
          return {
            'msg': 'Someone already has that username'
          }, 401
        setattr(user, key, username.lower())
      else:
        setattr(user, key, updates.get(key))
  except ValueError as e:
    return e, 500
  db.session.commit()
  user.id
  return user.get_dict(), 200

@bp.route("/user/me")
@jwt_required(refresh=True)
def get_me():
    """ Fetch Current User
    ---
    get:
        summary: fetch current user (without reviews)
        description: fetch current user. Store auth token in header as Authorization: `Bearer ${token}`
        responses:
            200:
                description: Returns User object
                content:
                  application/json:
                    schema: UserSchema
            400:
                content:
                  application/json:
                    schema:
                      Error:
                        properties:
                          msg:
                            type: string
                description: Not logged in.
    """
    user = get_current_user()
    auth_token = create_access_token(identity=user.id)
    resp_data = user.get_dict()
    resp_data['access_token'] = auth_token
    resp = make_response(resp_data)
    set_access_cookies(resp, auth_token)
    return resp

@bp.route("/users/nearby")
def users_nearby():
  latitude = request.args.get('latitude')
  longitude = request.args.get('longitude')
  query = User.query.filter(User.latitude.is_not(None)).order_by(User.distance(latitude, longitude)).limit(10)
  results = query.all()
  return { 'data': [result.get_dict() for result in results] }

@bp.route("/user/get")
@cache.cached(query_string=True)
def get_user():
    """ Get User
    ---
    get:
        summary: Get User
        description: Get User (and their reviews)
        parameters:
            - name: username
              in: body
              description: username
              type: string
              required: true
        responses:
            200:
                description: Returns user object
                content:
                  application/json:
                    schema: UserSchema
    """
    username = request.args.get('username')
    if not username:
      return {
        'msg': 'Include a username in the request. If you are trying to get the logged in user, use /user/me'
      }, 422
    user = User.query \
      .filter(func.lower(User.username)==username.lower()).first()
    reviews = Review.query.filter_by(author_id=user.id).order_by(Review.date_dived.desc()).all()
    if not user:
      return { 'msg': 'User doesn\'t exist' }, 404
    user_data = user.get_dict()
    reviews_data = []
    for index, review in enumerate(reviews):
      review.spot
      review_data = review.get_dict()
      review_data['spot'] = review.spot.get_dict()
      if not review_data.get('title'):
        review_data['title'] = review.spot.name
      title = review_data['title']
      review_data['title'] = f'#{index+1} - {title}'
      reviews_data.append(review_data)
    user_data['reviews'] = reviews_data
    return { 'data': user_data }