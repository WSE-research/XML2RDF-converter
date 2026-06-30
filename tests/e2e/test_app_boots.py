"""End-to-end smoke test: the FastAPI app imports and serves its OpenAPI schema."""
import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.e2e


def test_openapi_served():
    import app as app_module

    with TestClient(app_module.app) as client:
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        schema = resp.json()
        assert "XML to RDF converter" in schema["info"]["title"]
        # both documented endpoints are present
        assert "/xml2rdf" in schema["paths"]
        assert "/dtd2xslt" in schema["paths"]
