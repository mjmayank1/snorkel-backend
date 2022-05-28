import requests
import os
from flask import Blueprint, request
from app.models import DiveShop
from app import db
from flask_jwt_extended import jwt_required, get_current_user

bp = Blueprint('shop', __name__, url_prefix="/shop")
wally_api_base = os.environ.get('WALLY_API')
wally_auth_token = os.environ.get('WALLY_AUTH_TOKEN')

@bp.route('/get', methods=['GET'])
def fetch_dive_shops():
  dive_shops = DiveShop.query.all()
  data = [dive_shop.get_simple_dict() for dive_shop in dive_shops]
  return { 'data': data }

@bp.route('/get/<int:id>', methods=['GET'])
def fetch_dive_shop(id):
  dive_shop = DiveShop.query.get_or_404(id)
  data = dive_shop.get_dict()
  return { 'data': data }

@bp.route('/create', methods=['POST'])
@jwt_required()
def create_dive_shop():
  url = request.json.get('url')
  fareharbor_url = request.json.get('fareharbor_url')
  address1 = request.json.get('address1')
  address2 = request.json.get('address2')
  city = request.json.get('city')
  state = request.json.get('state')
  zip = request.json.get('zip')
  logo_img = request.json.get('logo_img')
  latitude = request.json.get('latitude')
  longitude = request.json.get('longitude')
  locality_id = request.json.get('locality_id')
  area_one_id = request.json.get('area_one_id')
  area_two_id  = request.json.get('area_two_id')
  country_id = request.json.get('country_id')

  dive_shop = DiveShop(
    url=url,
    fareharbor_url=fareharbor_url,
    address1=address1,
    address2=address2,
    city=city,
    state=state,
    zip=zip,
    logo_img=logo_img,
    latitude=latitude,
    longitude=longitude,
    locality_id=locality_id,
    area_one_id=area_one_id,
    area_two_id=area_two_id,
    country_id=country_id
  )

  db.session.add(dive_shop)
  db.session.commit()

  return { 'data': dive_shop.get_dict() }

@bp.route('/patch/<int:id>', methods=['PATCH'])
@jwt_required()
def update_dive_shop(id):
  dive_shop = dive_shop = DiveShop.query.get_or_404(id)
  user = get_current_user()

  # restrict access to patching a dive log
  if dive_shop.owner_user_id != user.id and not user.admin:
    return { "msg": "Only shop owner and admin can perform this action" }, 403

  updates = request.json
  try:
    for key in updates.keys():
      setattr(dive_shop, key, updates.get(key))
  except ValueError as e:
    return e, 500
  db.session.commit()
  data = dive_shop.get_dict()

  return { 'data': data }

@bp.route('/upload_stamp_image', methods=['POST'])
# @jwt_required()
def upload_stamp_image():
  if 'file' not in request.files:
    return { 'msg': 'No file included in request' }, 422
  request_url = wally_api_base + '/files/upload'
  headers = {
    "Authorization": "Bearer " + wally_auth_token
  }

  response = requests.post(request_url, headers=headers, data={}, files=request.files)
  response.raise_for_status()
  data = response.json()

  return { 'data':  data }