import pytest
from unittest.mock import MagicMock, patch
from etl.ingest import ingest_sharepoint, ingest_jira_onprem, ingest_jira_cloud, get_stats

def test_ingest_functions():
    """Prueba unitaria básica para verificar la correcta ingesta mockeada sin fallas de ejecución."""
    # Mocks para client y embedding_function
    mock_client = MagicMock()
    mock_ef = MagicMock()
    
    mock_collection = MagicMock()
    mock_client.get_or_create_collection.return_value = mock_collection
    
    # Pruebas para evitar errores de sintaxis y excepciones inesperadas en las funciones
    
    # 1. Sharepoint
    try:
        ingest_sharepoint(mock_client, mock_ef)
        mock_client.get_or_create_collection.assert_called_with(name="sharepoint", embedding_function=mock_ef)
    except Exception as e:
        pytest.fail(f"ingest_sharepoint falló inesperadamente: {e}")

    # 2. Jira OnPrem
    try:
        ingest_jira_onprem(mock_client, mock_ef)
        mock_client.get_or_create_collection.assert_called_with(name="jira_onprem", embedding_function=mock_ef)
    except Exception as e:
        pytest.fail(f"ingest_jira_onprem falló inesperadamente: {e}")
        
    # 3. Jira Cloud
    try:
        ingest_jira_cloud(mock_client, mock_ef)
        mock_client.get_or_create_collection.assert_called_with(name="jira_cloud", embedding_function=mock_ef)
    except Exception as e:
        pytest.fail(f"ingest_jira_cloud falló inesperadamente: {e}")

@patch("etl.embedding.get_chroma_client")
def test_get_stats(mock_get_client):
    """Test para get_stats"""
    mock_client = MagicMock()
    mock_collection = MagicMock()
    mock_collection.count.return_value = 5
    
    mock_client.get_collection.return_value = mock_collection
    mock_get_client.return_value = mock_client
    
    stats = get_stats()
    assert stats["sharepoint"] == 5
    assert stats["jira_onprem"] == 5
    assert stats["jira_cloud"] == 5
