"""FleetCare backend test suite.

Unit tests (pure logic, no DB) live in ``test_projection_service.py``,
``test_fuel_service.py``, ``test_security.py`` and ``test_notification_dedup.py``.
Integration tests (real Postgres via ``conftest``) live in ``test_auth.py``,
``test_cars.py``, ``test_health.py`` and ``test_tires.py``.
"""
