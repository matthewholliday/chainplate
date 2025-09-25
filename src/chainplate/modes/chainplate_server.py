from json import JSONDecodeError
from ..message import Message
from flask import jsonify, request, Flask
import traceback
try:
    # Need to reconfigure cors settings
    from flask_cors import CORS
except ImportError:  # pragma: no cover
    CORS = None  # type: ignore
from ..services.data.data_service import DataService
import os
from time import sleep
from concurrent.futures import ThreadPoolExecutor
from ..services.logging.logging_service import LoggingService
# import jsonify, request

import logging

# configure logging once at startup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("[CHAINPLATE SERVER]")

app = Flask(__name__)

# ---------------- Basic & Health Endpoints ----------------

@app.route('/')
def root():  # pragma: no cover - trivial text response tested elsewhere
    return "Hello, World!", 200

@app.route('/health', methods=['GET'])
def health():
    from ..services.health.health_check import HealthCheckService
    try:
        health_service = HealthCheckService()
        health_check = health_service.check()
        body = health_check.to_dict()
        status = body.get('status', 'unknown')
    except Exception as e:  # pragma: no cover - defensive
        logger.exception("Health check failed")
        body = {'status': 'error', 'errors': [str(e)]}
        status = 'error'
    return jsonify(body), (200 if status == "ok" else 503)

@app.route('/workflow', methods=['POST'])
def workflow_legacy():
    """Legacy simplified workflow endpoint kept to satisfy existing tests.

    Accepts JSON: {"chainplate_code": str, "payload": any}
    Currently it validates presence of chainplate_code and returns 200.
    Real workflow execution is handled by /api/executions for async processing.
    """
    try:
        data = request.get_json(silent=True) or {}
        code = data.get("chainplate_code")
        if not code:
            return jsonify({"error": "chainplate_code required"}), 400
        # Echo minimal response (could be extended to call actual workflow runner)
        return jsonify({"status": "accepted", "payload": data.get("payload")}), 200
    except JSONDecodeError:
        return jsonify({'error': 'Invalid JSON'}), 400
    except Exception as e:  # pragma: no cover - defensive
        logger.exception("workflow_legacy failed")
        return jsonify({'error': str(e)}), 500

# --- CORS (Permissive: Allow All) ---
# NOTE: This configuration allows ALL origins, methods, and headers. It is convenient
# for local development or internal trusted environments but SHOULD NOT be used in
# production without tightening the allowed origins/headers/methods.
# To restrict later, replace origins='*' with a list, e.g. origins=['https://example.com'].
if CORS:  # Preferred path when flask_cors is available
    try:
        CORS(
            app,
            resources={r"/*": {"origins": "*"}},
            supports_credentials=True,
            allow_headers="*",
            methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            expose_headers=["Content-Type", "Authorization"],
        )
        logger.info("CORS enabled via flask_cors (allow-all).")
    except Exception:  # pragma: no cover
        logger.exception("Failed to initialize flask_cors; falling back to manual headers.")
        CORS = None  # force fallback

if not CORS:
    # Fallback manual header injection when flask_cors not installed
    @app.after_request  # type: ignore
    def add_cors_headers(response):  # pragma: no cover - trivial
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Headers'] = request.headers.get(
            'Access-Control-Request-Headers', 'Authorization, Content-Type')
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
        return response
    logger.info("CORS enabled manually (allow-all). Install flask-cors for full feature set.")

# NEW: initialize DataService (file or memory)
_DB_PATH = os.getenv("CHAINPLATE_DB", "chainplate.db")

# Ensure parent directory for DB exists (handles mounted volumes or custom paths)
try:
    db_dir = os.path.dirname(_DB_PATH) or '.'
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
except Exception as e:  # pragma: no cover - defensive
    logger.error(f"Failed to ensure DB directory '{_DB_PATH}': {e}")

data_service = DataService(_DB_PATH)

def run_workflow(execution_id: str, code: str, payload: str, my_logger=None):
    # Local import to avoid importing heavy dependencies (e.g., OpenAI) unless needed
    from .chainplate_workflow import ChainplateWorkflow  # type: ignore
    LoggingService.log_info(f"Starting workflow execution {execution_id} with payload: {payload}")
    result = {}
    try:
        data_service = DataService(_DB_PATH)
        message = Message()
        message.set_payload(payload)
        message = ChainplateWorkflow(code, mode="workflow",execution_id=execution_id).run(message)
        LoggingService.log_info(f"Workflow execution {execution_id} completed.")
        result = {  
        'payload': message.get_payload(),
        'logs': message.get_logs(),
        'vars': message.get_vars()
        }
    except Exception as e:
        readable_trace = traceback.format_tb(e.__traceback__)
        LoggingService.log_error(f"Workflow execution {execution_id} failed: {e} \n {readable_trace}")


        result = {
            'payload': None,
            'logs': [f"Error: {e}"],
            'vars': {}
        }


    data_service.set_execution_result(execution_id, result['payload'] or 'No Output')
    data_service.set_execution_status(execution_id, 'DONE')
    data_service.close()

@app.route('/api/executions', methods=['POST'])
def workflow():
    # Local import (see run_workflow)
    from .chainplate_workflow import ChainplateWorkflow  # type: ignore
    try:
        data_service = DataService(_DB_PATH)
        code = request.get_data(as_text=True)
        execution_id = data_service.create_execution(code=code)
        data_service.close()
        executor = ThreadPoolExecutor(max_workers=1)
        code = request.get_data(as_text=True)
        payload = request.headers.get('X-Payload', '')
        executor.submit(run_workflow, execution_id, code, payload)
        return jsonify({'exeuction_id' : execution_id}), 202
    except JSONDecodeError:
        return jsonify({'error': 'Invalid JSON'}), 400
    except Exception as e:
        logger.exception("Workflow error")
        return jsonify({'error': str(e)}), 500

@app.route('/execution', methods=['GET'])
def get_single_execution():
    try:
        execution_id = request.args.get('id')
        if not execution_id or not execution_id.isdigit():
            return jsonify({'error': 'Valid execution id required as integer'}), 400
        execution_id = int(execution_id)
        execution = data_service.get_execution(execution_id)
        return jsonify({'execution': execution}), 200
    except KeyError as ke:
        return jsonify({'error': str(ke)}), 404
    except Exception as e:
        logger.exception("get_execution failed")
        return jsonify({'error': str(e)}), 500

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

@app.route('/data/executions/<int:execution_id>/steps/<int:step_id>/user_response', methods=['POST'])
def add_user_response_step(execution_id: int, step_id: int):
    """
    Create a user response step for an execution step that requires input.

    Request JSON:
    {
      "content": "user provided text"
    }
    """
    ds = DataService(_DB_PATH)
    try:
        data = request.get_json()
        if data is None:
            return jsonify({'error': 'JSON body required'}), 400
        content = data.get('content')
        if not content or not isinstance(content, str):
            return jsonify({'error': 'content (string) required'}), 400

        new_step_id = ds.add_user_response_step(execution_id, step_id, content)
        step = ds.get_step(new_step_id)
        return jsonify({'step_id': new_step_id, 'step': step}), 201
    except JSONDecodeError:
        return jsonify({'error': 'Invalid JSON'}), 400
    except ValueError as ve:
        # DataService validation errors (missing step, not requires_input, already has response)
        return jsonify({'error': str(ve)}), 400
    except KeyError as ke:
        return jsonify({'error': str(ke)}), 404
    except Exception as e:
        logger.exception("add_user_response_step failed")
        return jsonify({'error': str(e)}), 500
    finally:
        ds.close()

@app.route('/data/executions/<int:execution_id>', methods=['GET'])
def get_execution(execution_id: int):
    data_service = DataService(_DB_PATH)
    try:
        execution, steps = data_service.get_execution_with_steps(execution_id)
        return jsonify({'execution': execution, 'steps': steps}), 200
    except KeyError as ke:
        return jsonify({'error': str(ke)}), 404
    except Exception as e:
        logger.exception("get_execution failed")
        return jsonify({'error': str(e)}), 500
    finally:
        data_service.close()

# ---------------- New GET endpoints for all data resources ----------------

@app.route('/data/logs', methods=['GET'])
def list_logs():
    data_service = DataService(_DB_PATH)
    try:
        limit = request.args.get('limit', default='100')
        offset = request.args.get('offset', default='0')
        if not limit.isdigit() or not offset.isdigit():
            return jsonify({'error': 'limit and offset must be integers'}), 400
        rows = data_service.list_logs(limit=int(limit), offset=int(offset))
        return jsonify({'logs': rows, 'count': len(rows)}), 200
    except Exception as e:
        logger.exception("list_logs failed")
        return jsonify({'error': str(e)}), 500
    finally:
        data_service.close()

@app.route('/data/logs/<int:log_id>', methods=['DELETE'])
def delete_log(log_id: int):
    data_service = DataService(_DB_PATH)
    try:
        data_service.delete_log(log_id)
        return jsonify({'status': 'deleted', 'log_id': log_id}), 200
    except KeyError as ke:
        return jsonify({'error': str(ke)}), 404
    except Exception as e:
        logger.exception("delete_log failed")
        return jsonify({'error': str(e)}), 500
    finally:
        data_service.close()

@app.route('/data/logs', methods=['DELETE'])
def delete_all_logs():
    data_service = DataService(_DB_PATH)
    try:
        count = data_service.delete_all_logs()
        return jsonify({'status': 'deleted', 'count': count}), 200
    except Exception as e:
        logger.exception("delete_all_logs failed")
        return jsonify({'error': str(e)}), 500
    finally:
        data_service.close()

@app.route('/data/logs/<int:log_id>', methods=['GET'])
def get_log(log_id: int):
    data_service = DataService(_DB_PATH)
    try:
        row = data_service.get_log(log_id)
        return jsonify({'log': row}), 200
    except KeyError as ke:
        return jsonify({'error': str(ke)}), 404
    except Exception as e:
        logger.exception("get_log failed")
        return jsonify({'error': str(e)}), 500
    finally:
        data_service.close()

@app.route('/data/executions', methods=['GET'])
def list_executions():
    data_service = DataService(_DB_PATH)
    try:
        limit = request.args.get('limit', default='100')
        offset = request.args.get('offset', default='0')
        if not limit.isdigit() or not offset.isdigit():
            return jsonify({'error': 'limit and offset must be integers'}), 400
        rows = data_service.list_executions(limit=int(limit), offset=int(offset))
        return jsonify({'executions': rows, 'count': len(rows)}), 200
    except Exception as e:
        logger.exception("list_executions failed")
        return jsonify({'error': str(e)}), 500
    finally:
        data_service.close()

@app.route('/data/executions/<int:execution_id>/steps', methods=['GET'])
def list_steps(execution_id: int):
    data_service = DataService(_DB_PATH)
    try:
        rows = data_service.list_execution_steps(execution_id)
        return jsonify({'execution_id': execution_id, 'steps': rows, 'count': len(rows)}), 200
    except Exception as e:
        logger.exception("list_steps failed")
        return jsonify({'error': str(e)}), 500
    finally:
        data_service.close()

@app.route('/data/steps/<int:step_id>', methods=['GET'])
def get_step(step_id: int):
    data_service = DataService(_DB_PATH)
    try:
        row = data_service.get_step(step_id)
        return jsonify({'step': row}), 200
    except KeyError as ke:
        return jsonify({'error': str(ke)}), 404
    except Exception as e:
        logger.exception("get_step failed")
        return jsonify({'error': str(e)}), 500
    finally:
        data_service.close()

@app.route('/data/executions/<int:execution_id>/bundle', methods=['GET'])
def get_execution_bundle(execution_id: int):
    data_service = DataService(_DB_PATH)
    try:
        bundle = data_service.get_execution_bundle(execution_id)
        return jsonify(bundle), 200
    except KeyError as ke:
        return jsonify({'error': str(ke)}), 404
    except Exception as e:
        logger.exception("get_execution_bundle failed")
        return jsonify({'error': str(e)}), 500
    finally:
        data_service.close()

@app.route('/data/executions/<int:execution_id>/agent/memory', methods=['GET'])
def get_agent_memory(execution_id: int):
    data_service = DataService(_DB_PATH)
    try:
        mem = data_service.get_agent_memory(execution_id)
        return jsonify({'execution_id': execution_id, 'agent_memory': mem, 'count': len(mem)}), 200
    except Exception as e:
        logger.exception("get_agent_memory failed")
        return jsonify({'error': str(e)}), 500
    finally:
        data_service.close()

@app.route('/data/executions/<int:execution_id>/agent/plan', methods=['GET'])
def get_agent_plan(execution_id: int):
    data_service = DataService(_DB_PATH)
    try:
        plan = data_service.get_agent_plan(execution_id)
        return jsonify({'execution_id': execution_id, 'agent_plan': plan, 'count': len(plan)}), 200
    except Exception as e:
        logger.exception("get_agent_plan failed")
        return jsonify({'error': str(e)}), 500
    finally:
        data_service.close()

@app.route('/data/executions/<int:execution_id>/agent/goal', methods=['GET'])
def get_agent_goal(execution_id: int):
    data_service = DataService(_DB_PATH)
    try:
        goal = data_service.get_agent_goal(execution_id)
        return jsonify({'execution_id': execution_id, 'agent_goal': goal, 'count': len(goal)}), 200
    except Exception as e:
        logger.exception("get_agent_goal failed")
        return jsonify({'error': str(e)}), 500
    finally:
        data_service.close()

# ---------------- MCP Services Endpoints ----------------

@app.route('/data/mcp/services', methods=['GET'])
def http_get_mcp_services():
    """Return all stored MCP services/tools."""
    ds = DataService(_DB_PATH)
    try:
        services = ds.get_mcp_services()
        return jsonify({'services': services, 'count': len(services)}), 200
    except Exception as e:
        logger.exception("http_get_mcp_services failed")
        return jsonify({'error': str(e)}), 500
    finally:
        ds.close()

@app.route('/data/mcp/services', methods=['PUT'])
def http_put_mcp_services():
    """Upsert a list of MCP services/tools.

    Expected JSON body: {"services": [ {"name": str, "type": str, "command": str, "args": [..], "env": [str,...]? , "description": str? }, ... ] }
    """
    ds = DataService(_DB_PATH)
    try:
        data = request.get_json()
        if data is None:
            return jsonify({'error': 'JSON body required'}), 400
        services = data.get('services')
        if services is None:
            return jsonify({'error': '"services" list required'}), 400
        if not isinstance(services, list):
            return jsonify({'error': '"services" must be a list'}), 400
        # Basic validation of each item
        for idx, svc in enumerate(services):
            if not isinstance(svc, dict):
                return jsonify({'error': f'services[{idx}] must be an object'}), 400
            if not svc.get('name'):
                return jsonify({'error': f'services[{idx}] missing required field name'}), 400
            if 'env' in svc and svc['env'] is not None:
                if not isinstance(svc['env'], list):
                    return jsonify({'error': f'services[{idx}].env must be a list of strings'}), 400
                for j, v in enumerate(svc['env']):
                    if not isinstance(v, str):
                        return jsonify({'error': f'services[{idx}].env[{j}] must be a string'}), 400
        ds.put_mcp_services(services)
        stored = ds.get_mcp_services()
        return jsonify({'status': 'upserted', 'count': len(services), 'services': stored}), 200
    except JSONDecodeError:
        return jsonify({'error': 'Invalid JSON'}), 400
    except (TypeError, ValueError) as ve:
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        logger.exception("http_put_mcp_services failed")
        return jsonify({'error': str(e)}), 500
    finally:
        ds.close()

@app.route('/data/mcp/services', methods=['DELETE'])
def http_delete_mcp_services():
    """Delete all MCP services/tools."""
    ds = DataService(_DB_PATH)
    try:
        deleted = ds.delete_mcp_services()
        return jsonify({'status': 'deleted', 'count': deleted}), 200
    except Exception as e:
        logger.exception("http_delete_mcp_services failed")
        return jsonify({'error': str(e)}), 500
    finally:
        ds.close()

def run_server(port: int = 5000):
    app.run(host='0.0.0.0', port=port) #TODO - move to config file or environment variable for flexibility

# If this module is executed directly (as it is in the Docker ENTRYPOINT: python -m chainplate.modes.chainplate_server)
# we must explicitly start the server. Previously this file only defined run_server without calling it, so the
# module exited immediately causing the container's main process to exit and Docker to restart it repeatedly
# under the chosen restart policy.
if __name__ == "__main__":  # pragma: no cover - startup glue
    # Allow port override via CHAINPLATE_PORT env var (falls back to 5000). Fail gracefully on bad values.
    _port_env = os.getenv("CHAINPLATE_PORT", "5000")
    try:
        _port = int(_port_env)
    except ValueError:
        logger.warning(f"Invalid CHAINPLATE_PORT value '{_port_env}', defaulting to 5000")
        _port = 5000
    logger.info(f"Starting Chainplate server on 0.0.0.0:{_port}")
    run_server(_port)