import pytest
from fastapi.testclient import TestClient

# We assume api.main exists since it was scaffolded in Phase 2
from api.main import app

client = TestClient(app)

class TestApiEndpoints:
    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        
    def test_ask_endpoint_routing(self):
        # Arrange
        payload = {
            "question": "Como resuelvo el error 403?",
            "role": "helpdesk"
        }
        
        # Act
        response = client.post("/ask", json=payload)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "status" in data
        assert data["status"] == "success"
        
        # NOTE: At this stage (T011), since RAG graph is not fully implemented, 
        # the answer will be the stub text "Funcionalidad RAG en progreso."
        # Once T016 and T017 are done, this test might need adjusting or it 
        # implicitly serves as a routing structural test.

    def test_jira_cloud_api_contract(self):
        # T018: Contract test for Jira cloud APIs. 
        # This will fail until T020 (Mock Jira Cloud API) is implemented.
        try:
            from services.mock_jira_cloud_api.main import app as jira_mock_app
            mock_client = TestClient(jira_mock_app)
            
            # test search
            res = mock_client.get("/rest/api/3/search?jql=project=IT")
            assert res.status_code == 200
            data = res.json()
            assert "issues" in data
            
            # test get ticket
            res = mock_client.get("/rest/api/3/issue/IT-100")
            assert res.status_code in [200, 404]
        except ImportError:
            pytest.fail("Mock Jira Cloud API service (T020) is not implemented yet")
