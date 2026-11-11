"""Специфікація api/openapi.yaml має описувати всі маршрути API і лише їх."""
import re
from pathlib import Path

import yaml

SPEC_PATH = Path(__file__).resolve().parent.parent / "api" / "openapi.yaml"
HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


def _normalize(path):
    path = re.sub(r"<(?:\w+:)?\w+>", "{}", path)
    return re.sub(r"\{\w+\}", "{}", path)


def test_spec_is_openapi3():
    spec = yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))
    assert spec["openapi"].startswith("3.")
    assert "bearerAuth" in spec["components"]["securitySchemes"]


def test_spec_matches_routes(app):
    spec = yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))
    documented = {
        (method.upper(), _normalize(path))
        for path, item in spec["paths"].items()
        for method in item
        if method in HTTP_METHODS
    }
    implemented = {
        (method, _normalize(rule.rule))
        for rule in app.url_map.iter_rules()
        if rule.rule.startswith("/api/")
        for method in rule.methods - {"HEAD", "OPTIONS"}
    }
    assert implemented == documented
