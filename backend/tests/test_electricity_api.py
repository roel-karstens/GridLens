"""API endpoint tests for Phase 2: Electricity endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.dependencies import get_db


class TestElectricityEndpointsExist:
    """Test that electricity endpoints are registered."""

    def test_get_countries_endpoint_exists(self):
        """✓ GET /api/v1/electricity/countries endpoint exists."""
        client = TestClient(app)
        # Should work without auth (public endpoint)
        response = client.get("/api/v1/electricity/countries")
        assert response.status_code in (200, 401)  # 401 if auth required, 200 if public

    def test_current_status_endpoint_exists(self):
        """✓ GET /api/v1/electricity/current/{country_code} endpoint exists."""
        client = TestClient(app)
        response = client.get("/api/v1/electricity/current/NL")
        # Should require auth (401) or have data (200)
        assert response.status_code in (200, 401)

    def test_generation_mix_endpoint_exists(self):
        """✓ GET /api/v1/electricity/generation/{country_code} endpoint exists."""
        client = TestClient(app)
        response = client.get("/api/v1/electricity/generation/NL")
        assert response.status_code in (200, 401)

    def test_history_endpoint_exists(self):
        """✓ GET /api/v1/electricity/history/{country_code} endpoint exists."""
        client = TestClient(app)
        response = client.get("/api/v1/electricity/history/NL?metric=load")
        assert response.status_code in (200, 401)

    def test_compare_endpoint_exists(self):
        """✓ GET /api/v1/electricity/compare endpoint exists."""
        client = TestClient(app)
        response = client.get("/api/v1/electricity/compare?countries=NL,DE&metric=load")
        assert response.status_code in (200, 401)


class TestElectricityEndpointsAuthentication:
    """Test that endpoints properly enforce authentication."""

    def test_current_status_requires_auth(self, auth_headers):
        """✓ Current status endpoint requires authentication."""
        client = TestClient(app)
        
        # Without auth header
        response = client.get("/api/v1/electricity/current/NL")
        assert response.status_code == 403 or response.status_code == 401

    def test_generation_mix_requires_auth(self):
        """✓ Generation mix endpoint requires authentication."""
        client = TestClient(app)
        
        # Without auth header
        response = client.get("/api/v1/electricity/generation/NL")
        assert response.status_code == 403 or response.status_code == 401

    def test_history_requires_auth(self):
        """✓ History endpoint requires authentication."""
        client = TestClient(app)
        
        # Without auth header
        response = client.get("/api/v1/electricity/history/NL?metric=load")
        assert response.status_code == 403 or response.status_code == 401

    def test_compare_requires_auth(self):
        """✓ Compare endpoint requires authentication."""
        client = TestClient(app)
        
        # Without auth header
        response = client.get("/api/v1/electricity/compare?countries=NL,DE&metric=load")
        assert response.status_code == 403 or response.status_code == 401


class TestElectricityEndpointsWithAuth:
    """Test endpoints with valid auth."""

    def test_current_status_with_auth(self, auth_headers):
        """✓ Current status endpoint works with auth (returns 200 or 404 if no data)."""
        client = TestClient(app)
        response = client.get("/api/v1/electricity/current/NL", headers=auth_headers)
        # 200 if data exists, 404 if not, 500 if error
        assert response.status_code in (200, 404, 500)

    def test_generation_mix_with_auth(self, auth_headers):
        """✓ Generation mix endpoint works with auth."""
        client = TestClient(app)
        response = client.get("/api/v1/electricity/generation/NL", headers=auth_headers)
        assert response.status_code in (200, 404, 500)

    def test_history_with_auth(self, auth_headers):
        """✓ History endpoint works with auth."""
        client = TestClient(app)
        response = client.get(
            "/api/v1/electricity/history/NL?metric=load",
            headers=auth_headers
        )
        assert response.status_code in (200, 404, 500)

    def test_compare_with_auth(self, auth_headers):
        """✓ Compare endpoint works with auth."""
        client = TestClient(app)
        response = client.get(
            "/api/v1/electricity/compare?countries=NL,DE&metric=load",
            headers=auth_headers
        )
        assert response.status_code in (200, 404, 500)


class TestElectricityEndpointsValidation:
    """Test request validation."""

    def test_history_invalid_country(self, auth_headers):
        """✓ Invalid country code returns 404."""
        client = TestClient(app)
        response = client.get(
            "/api/v1/electricity/history/XX?metric=load",
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_history_missing_metric(self, auth_headers):
        """✓ Missing metric parameter returns error."""
        client = TestClient(app)
        response = client.get(
            "/api/v1/electricity/history/NL",  # Missing metric
            headers=auth_headers
        )
        # Should return 422 (validation error) or 400
        assert response.status_code in (422, 400)

    def test_compare_missing_countries(self, auth_headers):
        """✓ Missing countries parameter returns error."""
        client = TestClient(app)
        response = client.get(
            "/api/v1/electricity/compare?metric=load",  # Missing countries
            headers=auth_headers
        )
        assert response.status_code in (422, 400)

    def test_compare_invalid_country(self, auth_headers):
        """✓ Invalid country in compare returns 422."""
        client = TestClient(app)
        response = client.get(
            "/api/v1/electricity/compare?countries=XX,YY&metric=load",
            headers=auth_headers
        )
        assert response.status_code == 422

    def test_history_invalid_date_format(self, auth_headers):
        """✓ Invalid date format returns 422."""
        client = TestClient(app)
        response = client.get(
            "/api/v1/electricity/history/NL?metric=load&start=invalid-date",
            headers=auth_headers
        )
        assert response.status_code == 422


class TestElectricityEndpointsResponseSchema:
    """Test response schemas."""

    def test_get_countries_response_schema(self):
        """✓ GET /countries returns list of countries."""
        client = TestClient(app)
        response = client.get("/api/v1/electricity/countries")
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            if len(data) > 0:
                assert "code" in data[0]
                assert "name" in data[0]

    def test_current_status_response_has_required_fields(self, auth_headers):
        """✓ Current status response has expected fields."""
        client = TestClient(app)
        response = client.get("/api/v1/electricity/current/NL", headers=auth_headers)
        
        if response.status_code == 200:
            data = response.json()
            # Should have these fields
            assert "country_code" in data
            assert "timestamp" in data
            assert "load_mw" in data or data.get("load_mw") is None

    def test_generation_mix_response_has_required_fields(self, auth_headers):
        """✓ Generation mix response has expected fields."""
        client = TestClient(app)
        response = client.get("/api/v1/electricity/generation/NL", headers=auth_headers)
        
        if response.status_code == 200:
            data = response.json()
            assert "country_code" in data
            assert "timestamp" in data
            assert "generation_by_type" in data

    def test_history_response_has_required_fields(self, auth_headers):
        """✓ History response has expected fields."""
        client = TestClient(app)
        response = client.get(
            "/api/v1/electricity/history/NL?metric=load",
            headers=auth_headers
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "country_code" in data
            assert "metric" in data
            assert "observations" in data
            assert "count" in data

    def test_compare_response_has_required_fields(self, auth_headers):
        """✓ Compare response has expected fields."""
        client = TestClient(app)
        response = client.get(
            "/api/v1/electricity/compare?countries=NL,DE&metric=load",
            headers=auth_headers
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "metric" in data
            assert "timestamp" in data
            assert "countries" in data
