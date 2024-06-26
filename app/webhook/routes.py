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
    author = data['pusher']['name'] if 'pusher' in data else data['sender']['login']
    timestamp = datetime.now(timezone.utc)

    # Initialize payload
    payload = {
        'request_id': None,
        'author': author,
        'action': None,
        'from_branch': None,
        'to_branch': None,
        'timestamp': timestamp
    }

    # Determine the event type
    if 'after' in data and 'ref' in data:
        payload['action'] = 'PUSH'
        payload['request_id'] = data['after']
        payload['to_branch'] = data['ref'].split('/')[-1]
    elif 'pull_request' in data:
        payload['action'] = data['action'].upper()
        payload['request_id'] = data['pull_request']['id']
        payload['from_branch'] = data['pull_request']['head']['ref']
        payload['to_branch'] = data['pull_request']['base']['ref']
        if data['action'] == 'closed' and data['pull_request']['merged']:  # Check for merge event
         payload['action'] = 'MERGE'
    # elif 'ref' in data and 'action' in data:
    #     payload['action'] = data['action'].upper()
    #     payload['from_branch'] = data['ref']
    #     payload['to_branch'] = data['base']['ref']
    else:
        return jsonify({'message':'Unsupported event type'}), 400

    # Insert the payload into MongoDB
    if payload['action'] in ['PUSH','PULL_REQUEST','MERGE']:
        mongo.db.actions.insert_one(payload)
        return jsonify({'message': 'Action received'}), 200
    else:
        return jsonify({'message': 'Invalid payload'}), 400

@webhook.route('/actions', methods=["GET"])
def get_actions():
    actions = mongo.db.actions.find().sort("timestamp", -1).limit(10)  # Fetch the latest 10 actions
    print(f"Fetched actions: {mongo.db.actions}")
    print(f"Fetched actions: {actions}")
    result = []
    for action in actions:
        print(format_datetime(action.get('timestamp')))
        result.append({
            'author': action.get('author'),
            'action': action.get('action'),
            'from_branch': action.get('from_branch'),
            'to_branch': action.get('to_branch'),
            'timestamp': format_datetime(action.get('timestamp'))
        })
    print(f"Fetched actions: {result}")
    return jsonify(result), 200
