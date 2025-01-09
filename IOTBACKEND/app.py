from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub
from pubnub.callbacks import SubscribeCallback
from functools import wraps
from flask_cors import CORS
from bson.objectid import ObjectId
import logging
import os
from dotenv import load_dotenv
import platform


load_dotenv()



app = Flask(__name__)


app.config["MONGO_URI"] = os.getenv("MONGO_URI", "mongodb+srv://snmdashik14:Ashik1114@cluster0.p1yma.mongodb.net/temperatureDB?retryWrites=true&w=majority")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "your_secret_key_here")


mongo = PyMongo(app, serverSelectionTimeoutMS=5000)
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}}, expose_headers=["Authorization"])


logging.basicConfig(level=logging.INFO).  temperature_collection = mongo.db.temperatures
user_collection = mongo.db.users

def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"message": "Authorization header is missing or invalid"}), 401

        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            user_id = payload.get("user_id")
            current_user = user_collection.find_one({"_id": ObjectId(user_id)})
            if not current_user:
                return jsonify({"message": "User not found"}), 404
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token"}), 401

        return f(current_user, *args, **kwargs)
    return decorated_function
