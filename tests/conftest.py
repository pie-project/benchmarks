def pytest_collection_modifyitems(items):
    import pytest

    for item in items:
        if item.module.__name__.endswith("test_matrix") and "cells" in getattr(item, "fixturenames", ()):
            item.add_marker(pytest.mark.slow)
