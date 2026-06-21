from flask import Blueprint, request, jsonify
from backend.agent.agent import Agent

agent_bp = Blueprint('agent', __name__)
agent = Agent()


@agent_bp.route('/chat', methods=['POST'])
def chat():
    data = request.json or {}
    message = data.get('message')
    session_id = data.get('session_id')
    if not message:
        return jsonify({'error': 'message_required'}), 400
    response = agent.handle_message(message, session_id)
    return jsonify(response)


@agent_bp.route('/history', methods=['GET'])
def history():
    session_id = request.args.get('session_id')
    return jsonify(agent.get_history(session_id))

