import json
from flask import Blueprint, Response, jsonify, request, stream_with_context

from backend.agent.activity_trace import build_activity_steps
from backend.agent.agent import Agent
from backend.agent.zep_memory import is_zep_enabled, save_turn


agent_bp = Blueprint("agent", __name__)
agent = Agent()


@agent_bp.route("/chat", methods=["POST"])
def chat():
    data = request.json or {}
    message = data.get("message")
    session_id = data.get("session_id")

    if not message:
        return jsonify({"error": "message_required"}), 400

    response = agent.handle_message(message, session_id)

    save_turn(
        session_id=session_id,
        user_message=message,
        assistant_reply=response.get("reply", ""),
    )

    response["activity_steps"] = build_activity_steps(
        user_message=message,
        tools_called=response.get("tools_called", []),
    )

    response["memory"] = {
        "zep_enabled": is_zep_enabled(),
    }

    return jsonify(response)


@agent_bp.route("/chat/stream", methods=["GET"])
def chat_stream():
    message = request.args.get("message")
    session_id = request.args.get("session_id")

    if not message:
        return jsonify({"error": "message_required"}), 400

    def generate():
        try:
            yield _sse_event(
                "activity",
                {
                    "label": "Received request",
                    "status": "running",
                    "detail": "The SSE stream was opened successfully.",
                },
            )

            yield _sse_event(
                "activity",
                {
                    "label": "Running Agent workflow",
                    "status": "running",
                    "detail": "The backend is processing the user message.",
                },
            )

            response = agent.handle_message(message, session_id)

            save_turn(
                session_id=session_id,
                user_message=message,
                assistant_reply=response.get("reply", ""),
            )

            activity_steps = build_activity_steps(
                user_message=message,
                tools_called=response.get("tools_called", []),
            )

            for step in activity_steps:
                yield _sse_event("activity", step)

            response["activity_steps"] = activity_steps
            response["memory"] = {
                "zep_enabled": is_zep_enabled(),
            }

            yield _sse_event("final", response)
            yield _sse_event("done", {"ok": True})

        except Exception as exc:
            yield _sse_event(
                "error",
                {
                    "message": f"SSE Agent stream failed: {exc}",
                },
            )

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@agent_bp.route("/history", methods=["GET"])
def history():
    session_id = request.args.get("session_id")
    return jsonify(agent.get_history(session_id))


def _sse_event(event_name: str, payload: dict) -> str:
    return (
        f"event: {event_name}\n"
        f"data: {json.dumps(payload, default=str)}\n\n"
    )