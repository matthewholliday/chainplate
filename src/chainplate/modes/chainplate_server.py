from json import JSONDecodeError
from .chainplate_workflow import ChainplateWorkflow
from ..message import Message
from flask import jsonify, request, Flask
# import jsonify, request
    

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

def run_server(port: int = 5000):
	app.run(host='0.0.0.0', port=port) #TODO - move to config file or environment variable for flexibility
