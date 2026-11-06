

# the whole-matrix checks in test_matrix share one full expansion (the "cells" fixture, about a minute): they are slow,
# run with -m slow, and stay out of CI
def pytest_collection_modifyitems(items):
    import pytest

    for item in items:
        if item.module.__name__.endswith("test_matrix") and "cells" in getattr(item, "fixturenames", ()):
            item.add_marker(pytest.mark.slow)
