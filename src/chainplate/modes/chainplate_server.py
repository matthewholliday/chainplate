from json import JSONDecodeError
from .chainplate_workflow import ChainplateWorkflow
from ..message import Message
from flask import jsonify, request, Flask
from ..services.data.data_service import DataService
import os
# import jsonify, request

import logging

# configure logging once at startup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("[CHAINPLATE SERVER]")

app = Flask(__name__)

# NEW: initialize DataService (file or memory)
_DB_PATH = os.getenv("CHAINPLATE_DB", "chainplate.db")
data_service = DataService(_DB_PATH)

@app.route('/')
def hello():
    return 'Hello, World!' # TODO - remove testing endpoint

@app.route('/workflow', methods=['POST'])
def workflow():
    # Example: get JSON from request and run workflow
    try:
        code = request.get_data(as_text=True)
        payload = request.headers.get('X-Payload')
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
        logger.exception("Workflow error")
        return jsonify({'error': str(e)}), 500

@app.route('/chat', methods=['POST'])

# ---------------- DataService REST Endpoints ----------------

@app.route('/data/logs', methods=['POST'])
def create_log():
    try:
        data = request.get_json()
        level = (data.get('level') or 'INFO').upper()
        message = data.get('message')
        if not message:
            return jsonify({'error': 'message required'}), 400
        if level not in ('INFO','WARNING','ERROR'):
            return jsonify({'error': 'invalid level'}), 400
        log_id = data_service.insert_log(level, message)
        return jsonify({'id': log_id, 'level': level, 'message': message}), 201
    except JSONDecodeError:
        return jsonify({'error': 'Invalid JSON'}), 400
    except Exception as e:
        logger.exception("create_log failed")
        return jsonify({'error': str(e)}), 500

@app.route('/data/executions', methods=['POST'])
def create_execution():
    try:
        data = request.get_json()
        code = data.get('code')
        if not code:
            return jsonify({'error': 'code required'}), 400
        exec_id = data_service.create_execution(code)
        return jsonify({'execution_id': exec_id}), 201
    except JSONDecodeError:
        return jsonify({'error': 'Invalid JSON'}), 400
    except Exception as e:
        logger.exception("create_execution failed")
        return jsonify({'error': str(e)}), 500

@app.route('/data/executions/<int:execution_id>/steps', methods=['POST'])
def add_execution_step(execution_id: int):
    try:
        data = request.get_json()
        content = data.get('content')
        role = data.get('role')
        channel = data.get('channel')
        requires_input = data.get('requires_input', False)
        # Normalize types
        if isinstance(channel, str) and channel.isdigit():
            channel = int(channel)
        requires_input = bool(requires_input in (True, 1, '1', 'true', 'True'))
        step_id = data_service.add_execution_step(
            execution_id,
            content=content,
            role=role,
            channel=channel,
            requires_input=requires_input
        )
        return jsonify({'step_id': step_id}), 201
    except JSONDecodeError:
        return jsonify({'error': 'Invalid JSON'}), 400
    except KeyError as ke:
        return jsonify({'error': str(ke)}), 404
    except Exception as e:
        logger.exception("add_execution_step failed")
        return jsonify({'error': str(e)}), 500

@app.route('/data/executions/<int:execution_id>', methods=['GET'])
def get_execution(execution_id: int):
    try:
        execution, steps = data_service.get_execution_with_steps(execution_id)
        return jsonify({'execution': execution, 'steps': steps}), 200
    except KeyError as ke:
        return jsonify({'error': str(ke)}), 404
    except Exception as e:
        logger.exception("get_execution failed")
        return jsonify({'error': str(e)}), 500

def run_server(port: int = 5000):
    app.run(host='0.0.0.0', port=port) #TODO - move to config file or environment variable for flexibility