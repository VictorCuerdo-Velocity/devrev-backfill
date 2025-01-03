import pytest
from unittest.mock import Mock, patch
from processors.issue_processor import IssueProcessor
from models import Issue, ProcessingResult

@pytest.fixture
def mock_client():
    return Mock()

@pytest.fixture
def processor(mock_client):
    return IssueProcessor(mock_client)

async def test_process_issues_success(processor, mock_client):
    # Setup test data
    issues = [
        Issue(issue_id="1", creator_user_id="user1", assigned_group="group1"),
        Issue(issue_id="2", creator_user_id="user2", assigned_group="group2")
    ]
    
    # Mock responses
    mock_client.get_groups.return_value = [
        {"id": "group1", "name": "Group 1"},
        {"id": "group2", "name": "Group 2"}
    ]
    mock_client.update_issue_creator_group.return_value = True
    
    # Process issues
    result = await processor.process_issues(issues)
    
    # Verify results
    assert result.total_processed == 2
    assert result.successful_updates == 2
    assert result.failed_updates == 0

async def test_process_issues_with_failures(processor, mock_client):
    issues = [
        Issue(issue_id="1", creator_user_id="user1", assigned_group="group1"),
        Issue(issue_id="2", creator_user_id="user2", assigned_group="invalid")
    ]
    
    mock_client.get_groups.return_value = [{"id": "group1"}]
    mock_client.update_issue_creator_group.return_value = True
    
    result = await processor.process_issues(issues)
    
    assert result.total_processed == 2
    assert result.successful_updates == 1
    assert result.failed_updates == 1