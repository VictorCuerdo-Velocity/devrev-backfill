def test_issue_validation():
    validator = DataValidator()
    
    # Valid issue
    issue = Issue(
        issue_id="TEST-1",
        creator_user_id="USER-1",
        assigned_group="GROUP-1"
    )
    result = validator.validate_issue(issue)
    assert result.is_valid
    
    # Invalid issue
    issue = Issue(
        issue_id="",
        creator_user_id="USER-1",
        assigned_group="GROUP-1"
    )
    result = validator.validate_issue(issue)
    assert not result.is_valid
    assert "Issue ID is required" in result.errors