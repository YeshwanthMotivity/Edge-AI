import pytest

def test_list_policies(client, auth_headers):
    response = client.get("/api/v1/policies", headers=auth_headers)
    assert response.status_code == 200
    policies = response.json()
    assert isinstance(policies, list)
    assert "default_policy" in policies

def test_get_policy(client, auth_headers):
    response = client.get("/api/v1/policies/default_policy", headers=auth_headers)
    assert response.status_code == 200
    policy = response.json()
    assert policy["policy_name"] == "default_policy"
    assert "entities" in policy

def test_get_nonexistent_policy(client, auth_headers):
    response = client.get("/api/v1/policies/this_does_not_exist_123", headers=auth_headers)
    assert response.status_code == 404
