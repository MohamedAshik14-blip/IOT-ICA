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

@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400

    if user_collection.find_one({"username": username}):
        return jsonify({"message": "User already exists"}), 400

    hashed_password = generate_password_hash(password, method="pbkdf2:sha256")
    user_collection.insert_one({"username": username, "password": hashed_password})

    return jsonify({"message": "User registered successfully"}), 201


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400

    user = user_collection.find_one({"username": username})
    if not user or not check_password_hash(user["password"], password):
        return jsonify({"message": "Invalid credentials"}), 401

    
    token = jwt.encode(
        {"user_id": str(user["_id"]), "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)},
        app.config["SECRET_KEY"],
        algorithm="HS256"
    )
    return jsonify({"token": token}), 200

if __name__ == "__main__":
    try:
        
        mongo.cx.admin.command('ping')
        logging.info("Connected to MongoDB successfully.")
    except Exception as e:
        logging.error(f"Could not connect to MongoDB: {str(e)}")
        exit(1)

    app.run(debug=True, host="0.0.0.0", port=3001)
