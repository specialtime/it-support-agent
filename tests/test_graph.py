import pytest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import HumanMessage


# T024: Unit test for permission gating logic (check_permissions node)
# Tests MUST be written before implementation and initially FAIL.


def _make_state(role: str, intent: str = "action") -> dict:
    """Helper to build a minimal AgentState-compatible dict."""
    return {
        "messages": [HumanMessage(content="resetear contraseña de usuario jsmith")],
        "session_id": "test-session",
        "user_role": role,
        "intent": intent,
        "sharepoint_docs": [],
        "onprem_docs": [],
        "cloud_docs": [],
        "context": [],
        "action_taken": None,
        "answer": "",
        "sources": [],
        "confidence": 0.0,
        "has_expert_context": False,
        "permission_granted": False,
    }


class TestCheckPermissions:
    def test_user_role_is_denied(self):
        """role='user' must be blocked — permission_granted must be False."""
        from agent.nodes import check_permissions

        state = _make_state(role="user")
        result = check_permissions(state)

        assert result["permission_granted"] is False

    def test_helpdesk_role_is_allowed(self):
        """role='helpdesk' must be allowed — permission_granted must be True."""
        from agent.nodes import check_permissions

        state = _make_state(role="helpdesk")
        result = check_permissions(state)

        assert result["permission_granted"] is True

    def test_admin_role_is_allowed(self):
        """role='admin' must be allowed — permission_granted must be True."""
        from agent.nodes import check_permissions

        state = _make_state(role="admin")
        result = check_permissions(state)

        assert result["permission_granted"] is True

    def test_unknown_role_is_denied(self):
        """Any unrecognized role must be denied."""
        from agent.nodes import check_permissions

        state = _make_state(role="stranger")
        result = check_permissions(state)

        assert result["permission_granted"] is False


class TestResetPasswordTool:
    def test_reset_password_returns_confirmation(self):
        """The tool must return a non-empty confirmation string."""
        from agent.tools import reset_password

        result = reset_password.invoke({"username": "jsmith"})

        assert isinstance(result, str)
        assert len(result) > 0
        assert "jsmith" in result.lower() or "contraseña" in result.lower() or "reset" in result.lower()

    def test_reset_password_schema_requires_username(self):
        """Calling the tool without username must raise an error."""
        from agent.tools import reset_password
        import pydantic

        with pytest.raises((TypeError, pydantic.ValidationError, Exception)):
            # LangChain tools raise on missing required args
            reset_password.invoke({})


class TestGraphPermissionRouting:
    """Integration-level: verify the compiled graph enforces permissions end-to-end."""

    def test_graph_rejects_user_role_for_action(self):
        """A 'user' role asking for a password reset must receive a denial message."""
        from agent.graph import graph

        config = {"configurable": {"thread_id": "perm-test-user"}}
        initial_state = {
            "messages": [HumanMessage(content="resetea la contraseña del usuario jsmith")],
            "session_id": "perm-test-user",
            "user_role": "user",
        }

        result = graph.invoke(initial_state, config=config)

        answer = result.get("answer", "").lower()
        # Must contain a denial / permission keyword
        assert any(
            kw in answer
            for kw in ("permiso", "autorizado", "no puedes", "no tiene", "unauthorized", "denegado", "acceso")
        ), f"Expected denial message, got: {answer}"

    def test_graph_allows_helpdesk_role_for_action(self):
        """A 'helpdesk' role asking for a password reset must succeed (not deny)."""
        from agent.graph import graph

        config = {"configurable": {"thread_id": "perm-test-helpdesk"}}
        initial_state = {
            "messages": [HumanMessage(content="resetea la contraseña del usuario jsmith")],
            "session_id": "perm-test-helpdesk",
            "user_role": "helpdesk",
        }

        result = graph.invoke(initial_state, config=config)

        answer = result.get("answer", "").lower()
        # Must NOT be a flat denial
        denial_keywords = ["no tienes permiso", "no autorizado", "acceso denegado", "unauthorized"]
        assert not any(kw in answer for kw in denial_keywords), (
            f"Expected success confirmation, got denial: {answer}"
        )
