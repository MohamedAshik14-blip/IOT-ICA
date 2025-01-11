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


logging.basicConfig(level=logging.INFO)

pnconfig = PNConfiguration()
pnconfig.subscribe_key = os.getenv("PUBNUB_SUBSCRIBE_KEY", "sub-c-6963e588-282e-41ec-8194-9b6710e52ad3")
pnconfig.publish_key = os.getenv("PUBNUB_PUBLISH_KEY", "pub-c-45bab202-c191-4fbe-a1d0-2628df540689")
pnconfig.secret_key = os.getenv("PUBNUB_SECRET_KEY", "sec-c-MmM5ZTI3YjEtOGU5NC00YzY4LTk0NjYtZWI0MTUyYjlkMGY0")
pnconfig.user_id = os.getenv("PUBNUB_USER_ID", "temperature-subscriber")
pubnub = PubNub(pnconfig)


temperature_collection = mongo.db.temperatures
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


@app.route("/api/temperatures", methods=["GET"])
@token_required
def get_temperature(current_user):
    latest = temperature_collection.find_one(sort=[("timestamp", -1)])
    if latest:
        latest["_id"] = str(latest["_id"]) 
        return jsonify(latest), 200
    return jsonify({"message": "No data found"}), 404


@app.route("/api/history", methods=["GET"])
@token_required
def get_history(current_user):
    history = temperature_collection.find().sort("timestamp", -1).limit(50)
    result = [
        {key: (str(value) if isinstance(value, ObjectId) else value) for key, value in record.items()}
        for record in history
    ]
    return jsonify(result), 200


@app.route("/api/led", methods=["POST"])
@token_required
def control_led(current_user):
    data = request.get_json()
    action = data.get("action") 

    if action not in ["on", "off"]:
        return jsonify({"message": "Invalid action. Must be 'on' or 'off'."}), 400

  
    message = {"action": action}
    pubnub.publish().channel("Temperature-App").message(message).sync()

    return jsonify({"message": f"LED action '{action}' message sent to Raspberry Pi."}), 200


class MySubscribeCallback(SubscribeCallback):
    def message(self, pubnub, message):
        try:
            data = message.message
            if "temperature" in data and "humidity" in data:
                temperature_data = {
                    "temperature": data["temperature"],
                    "humidity": data["humidity"],
                    "timestamp": datetime.datetime.now(datetime.timezone.utc)
                }
                temperature_collection.insert_one(temperature_data)
                logging.info("Data saved to MongoDB")
        except Exception as e:
            logging.error(f"Error saving data from PubNub: {str(e)}")


pubnub.add_listener(MySubscribeCallback())
pubnub.subscribe().channels("Temperature-App").execute()


if __name__ == "__main__":
    try:
        
        mongo.cx.admin.command('ping')
        logging.info("Connected to MongoDB successfully.")
    except Exception as e:
        logging.error(f"Could not connect to MongoDB: {str(e)}")
        exit(1)

    app.run(debug=True, host="0.0.0.0", port=3001)
