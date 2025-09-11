from json import JSONDecodeError
from .chainplate_workflow import ChainplateWorkflow
from ..message import Message
from flask import jsonify, request, Flask
from ..services.data.database.rdb_service import RDBService
from ..services.ux.rdb_ux_service import RelationalDatabaseUXService
from .chainplate_chat_session import ChainplateChatSession
import asyncio
# import jsonify, request

import logging

# configure logging once at startup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("[CHAINPLATE SERVER]")
    

app = Flask(__name__)

@app.route('/')
def hello():
	return 'Hello, World!' # TODO - remove testing endpoint

@app.route('/workflow', methods=['POST'])
def workflow():
	# Example: get JSON from request and run workflow
	try:
		data = request.get_json()
		code = data.get('chainplate_code', '<pipeline name="no code provided"><debug>No code was provided to server.</debug></pipeline>')
		payload = data.get('payload', '')
		message = Message()
		message.set_payload(payload)
		message = ChainplateWorkflow(code, mode="workflow").run(message)
		result = {  
			'payload': message.get_payload(),
			'logs': message.get_logs(),
			'vars': message.get_vars()
		}
		return jsonify(result), 200
	except JSONDecodeError:
		return jsonify({'error': 'Invalid JSON'}), 400
	except Exception as e:
		return jsonify({'error': str(e)}), 500

async def run_chat_session(xml_body, ux_service):
	await asyncio.sleep(5)
	logger.info("Received ping request!") 
	#ChainplateChatSession(xml_body).run_interactive(ux_service)

# create a new conversation
@app.route('/conversation', methods=['POST'])
def post_conversation():
	logger.info("Received ping request!") 
	try:
		if request.method == 'POST':
			# get body of request (should be xml)
			xml_body = request.data.decode('utf-8')
			if not xml_body:
				return jsonify({'error': 'Request body (XML) is required'}), 400

			database = RDBService()

			# create a new conversation
			conversation_id = database.create_conversation()

			# initialize a ux service for this conversation
			ux_service = RelationalDatabaseUXService(conversation_id)

			# run the chat session (async)
			run_chat_session(xml_body, ux_service)

			result = {'conversation_id': conversation_id}
			return jsonify(result), 201
		else:
			return jsonify({'error': 'Invalid request method'}), 405
	except JSONDecodeError:
		return jsonify({'error': 'Invalid JSON'}), 400
	except Exception as e:
		return jsonify({'error': str(e)}), 500

# get a specific conversation by id
@app.route('/conversation/<conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
	try:
		if request.method == 'GET':
			database = RDBService()
			messages = database.get_messages(conversation_id)
			if messages is None:
				return jsonify({'error': 'Conversation not found'}), 404
			result = {'conversation_id': conversation_id, 'messages': []}
			for msg in messages:
				result['messages'].append({
					'id': msg[0],
					'content': msg[1],
					'order': msg[2],
					'created_at': msg[3]
				})
			return jsonify(result), 200
		else:
			return jsonify({'error': 'Invalid request method'}), 405
	except JSONDecodeError:
		return jsonify({'error': 'Invalid JSON'}), 400
	except Exception as e:
		return jsonify({'error': str(e)}), 500

# create a message in a specific conversation
@app.route('/conversation/<conversation_id>/message', methods=['POST'])
def post_message(conversation_id):
	try:
		if request.method == 'POST':
			data = request.get_json()
			role = data.get('role', 'user')
			content = data.get('content', '')
			if not content:
				return jsonify({'error': 'Message content is required'}), 400
			database = RDBService()
			message_id = database.create_message(conversation_id, role, content)
			result = {'message_id': message_id}
			return jsonify(result), 201
		else:
			return jsonify({'error': 'Invalid request method'}), 405
	except JSONDecodeError:
		return jsonify({'error': 'Invalid JSON'}), 400
	except Exception as e:
		return jsonify({'error': str(e)}), 500

# delete a specific conversation by id
@app.route('/conversation/<conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
	try:
		if request.method == 'DELETE':
			database = RDBService()
			database.delete_conversation(conversation_id)
			return jsonify({'message': 'Conversation deleted'}), 200
		else:
			return jsonify({'error': 'Invalid request method'}), 405
	except JSONDecodeError:
		return jsonify({'error': 'Invalid JSON'}), 400
	except Exception as e:
		return jsonify({'error': str(e)}), 500

# purge all conversations
@app.route('/conversations/purge', methods=['POST'])
def purge_conversations():
	try:
		if request.method == 'POST':
			database = RDBService()
			database.purge_conversations()
			return jsonify({'message': 'All conversations purged'}), 200
		else:
			return jsonify({'error': 'Invalid request method'}), 405
	except JSONDecodeError:
		return jsonify({'error': 'Invalid JSON'}), 400
	except Exception as e:
		return jsonify({'error': str(e)}), 500

# get all messages in a specific conversation
@app.route('/conversation/<conversation_id>/messages', methods=['GET'])
def get_messages(conversation_id):
	try:
		if request.method == 'GET':
			database = RDBService()
			messages = database.get_messages(conversation_id)
			if messages is None:
				return jsonify({'error': 'Conversation not found'}), 404
			result = {'conversation_id': conversation_id, 'messages': []}
			for msg in messages:
				result['messages'].append({
					'id': msg[0],
					'content': msg[1],
					'order': msg[2],
					'created_at': msg[3]
				})
			return jsonify(result), 200
		else:
			return jsonify({'error': 'Invalid request method'}), 405
	except JSONDecodeError:
		return jsonify({'error': 'Invalid JSON'}), 400
	except Exception as e:
		return jsonify({'error': str(e)}), 500
	

def run_server(port: int = 5000):
	app.run(host='0.0.0.0', port=port) #TODO - move to config file or environment variable for flexibility
