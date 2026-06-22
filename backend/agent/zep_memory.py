import os
from datetime import datetime, timezone
from importlib import import_module
from typing import Any, Optional


ZEP_API_KEY = os.getenv("ZEP_API_KEY")
ZEP_USER_ID = os.getenv("ZEP_USER_ID", "healthcare-demo-user")
ZEP_USER_EMAIL = os.getenv("ZEP_USER_EMAIL", "healthcare.demo@example.com")
ZEP_USER_FIRST_NAME = os.getenv("ZEP_USER_FIRST_NAME", "Healthcare")
ZEP_USER_LAST_NAME = os.getenv("ZEP_USER_LAST_NAME", "Demo")

_client_cache: Any = None


def is_zep_enabled() -> bool:
    return bool(ZEP_API_KEY)


def _get_client() -> Any:
    """
    Load the optional Zep client dynamically.

    Dynamic loading avoids PyCharm unresolved-reference warnings when
    zep-cloud is not installed in the local interpreter.
    """
    global _client_cache

    if not ZEP_API_KEY:
        return None

    if _client_cache is not None:
        return _client_cache

    try:
        client_module = import_module("zep_cloud.client")
        zep_class = getattr(client_module, "Zep")
        _client_cache = zep_class(api_key=ZEP_API_KEY)
        return _client_cache
    except (ImportError, AttributeError, TypeError, ValueError, RuntimeError):
        return None


def _build_message(role: str, role_type: str, content: str) -> Any:
    types_module = import_module("zep_cloud.types")
    message_class = getattr(types_module, "Message")

    return message_class(
        role=role,
        role_type=role_type,
        content=content,
        created_at=datetime.now(timezone.utc).isoformat(),
    )


def ensure_zep_session(session_id: Optional[str]) -> bool:
    sid = session_id or "default"
    client = _get_client()

    if client is None:
        return False

    try:
        client.user.add(
            user_id=ZEP_USER_ID,
            email=ZEP_USER_EMAIL,
            first_name=ZEP_USER_FIRST_NAME,
            last_name=ZEP_USER_LAST_NAME,
        )
    except Exception:  # noinspection PyBroadException
        pass

    try:
        if hasattr(client, "thread") and hasattr(client.thread, "create"):
            client.thread.create(
                thread_id=sid,
                user_id=ZEP_USER_ID,
            )
        elif hasattr(client, "memory") and hasattr(client.memory, "add_session"):
            client.memory.add_session(
                session_id=sid,
                user_id=ZEP_USER_ID,
            )
        else:
            return False
    except Exception:  # noinspection PyBroadException
        pass

    return True


def get_memory_context(session_id: Optional[str]) -> str:
    sid = session_id or "default"
    client = _get_client()

    if client is None:
        return ""

    try:
        ensure_zep_session(sid)

        if hasattr(client, "memory") and hasattr(client.memory, "get"):
            memory = client.memory.get(session_id=sid)
            return getattr(memory, "context", "") or ""

        if hasattr(client, "thread") and hasattr(client.thread, "get_user_context"):
            context = client.thread.get_user_context(thread_id=sid)
            return str(context or "")

        return ""
    except Exception:  # noinspection PyBroadException
        return ""


def save_turn(
    session_id: Optional[str],
    user_message: str,
    assistant_reply: str,
) -> bool:
    sid = session_id or "default"
    client = _get_client()

    if client is None:
        return False

    try:
        ensure_zep_session(sid)

        messages = [
            _build_message(
                role="User",
                role_type="user",
                content=user_message,
            ),
            _build_message(
                role="Healthcare AI Agent",
                role_type="assistant",
                content=assistant_reply,
            ),
        ]

        if hasattr(client, "thread") and hasattr(client.thread, "add_messages"):
            client.thread.add_messages(sid, messages=messages)
            return True

        if hasattr(client, "memory") and hasattr(client.memory, "add"):
            client.memory.add(sid, messages=messages)
            return True

        return False
    except Exception:  # noinspection PyBroadException
        return False