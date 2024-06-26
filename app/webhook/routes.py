from flask import Blueprint, request, jsonify
from app.extensions import mongo
from datetime import datetime, timezone

webhook = Blueprint('webhook', __name__, url_prefix='/webhook')

def format_datetime(dt):
    day = dt.day
    suffix = "th" if 11 <= day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    formatted_date = dt.strftime(f"%B {day}{suffix} %Y - %I:%M %p UTC")
    return formatted_date

@webhook.route('/receiver', methods=["POST"])
def receiver():
    data = request.json
    print(f"Received webhook data: {data}")

    # Extract common information
    # author = data['pusher']['name'] if 'pusher' in data else data['sender']['login']
    timestamp_str = data['timestamp']
    timestamp_dt = datetime.fromisoformat(timestamp_str)

    # Convert the timestamp to UTC
    timestamp_utc = timestamp_dt.astimezone(timezone.utc)


    # Initialize payload
    payload = {
        'request_id':data['request_id'],
        'author': data['author'],
        'action': data['action'],
        'from_branch': data['from_branch'],
        'to_branch': data['to_branch'],
        'timestamp': timestamp_utc
    }

    # Insert the payload into MongoDB
    if payload['action'] in ['PUSH','PULL_REQUEST','MERGE']:
        mongo.db.actions.insert_one(payload)
        return jsonify({'message': 'Action received'}), 200
    else:
        return jsonify({'message': 'Invalid payload'}), 400

@webhook.route('/actions', methods=["GET"])
def get_actions():
    actions = mongo.db.actions.find().sort("timestamp", -1).limit(10)  # Fetch the latest 10 actions
    result = []
    for action in actions:
        result.append({
            'author': action.get('author'),
            'action': action.get('action'),
            'from_branch': action.get('from_branch'),
            'to_branch': action.get('to_branch'),
            'timestamp': format_datetime(action.get('timestamp'))
        })
    print(f"Fetched actions: {result}")
    return jsonify(result), 200
