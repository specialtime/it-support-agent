import pytest
from pydantic import BaseModel, ValidationError
import sys
import os

# Adds support if testing individually without root setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# T019: Tool schema validation test
# We anticipate the schemas needed for our tools in agent/tools.py

class SearchJiraTicketInput(BaseModel):
    query: str

class GetJiraTicketInput(BaseModel):
    ticket_key: str

class TestToolsSchemas:
    def test_search_jira_schema(self):
        # valid
        valid = SearchJiraTicketInput(query="project = IT AND status = 'In Progress'")
        assert valid.query == "project = IT AND status = 'In Progress'"
        
        # invalid
        with pytest.raises(ValidationError):
            SearchJiraTicketInput() # missing query

    def test_get_jira_schema(self):
        # valid
        valid = GetJiraTicketInput(ticket_key="SUPPORT-123")
        assert valid.ticket_key == "SUPPORT-123"
        
        # invalid
        with pytest.raises(ValidationError):
            GetJiraTicketInput() # missing key
