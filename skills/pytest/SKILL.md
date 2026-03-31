---
name: pytest
description: >
  Expert guidance for writing, organizing, debugging, and running Python tests with pytest.
  Covers fixtures, parametrize, marks, mocking (monkeypatch + pytest-mock), async tests,
  output capture, conftest.py patterns, and plugins (pytest-cov, pytest-asyncio, pytest-xdist).
  Use this skill whenever the user is writing Python tests, setting up test infrastructure,
  debugging failing tests, adding pytest configuration in pyproject.toml, working with
  conftest.py, or using any pytest plugin. Invoke it even when the user just says
  "write me a test" or "my test is failing" or "add coverage" — if it involves Python testing,
  this skill applies.
---

# pytest

Python's most popular testing framework. Plain `assert` statements with rich failure diffs,
powerful fixtures, parametrization, and a vast plugin ecosystem.

## Test Discovery

pytest auto-discovers tests without any registration:
- Files: `test_*.py` or `*_test.py`
- Functions/methods: names starting with `test_`
- Classes: names starting with `Test` (no `__init__` method)

## CLI Quick Reference

```bash
pytest                        # run all tests
pytest tests/test_foo.py      # specific file
pytest tests/test_foo.py::test_bar  # specific test
pytest -v / -vv               # verbose output
pytest -q                     # quiet (dot per test)
pytest -k "auth and not slow" # filter by name expression
pytest -m slow                # filter by mark
pytest -x                     # stop on first failure
pytest --maxfail=3            # stop after N failures
pytest --lf                   # rerun last-failed only
pytest --ff                   # run failed-first
pytest -s                     # disable output capture (show prints)
pytest --tb=short             # traceback style: short/long/no/line/native/auto
pytest --co                   # collect only (list tests, don't run)
pytest --durations=10         # show 10 slowest tests
pytest -r a                   # show extra summary (a=all, f=failed, s=skipped)
pytest -p no:warnings         # disable warnings plugin
pytest -n auto                # parallel execution (pytest-xdist)
pytest --cov=src --cov-report=term-missing  # coverage (pytest-cov)
pytest --asyncio-mode=auto    # auto async mode (pytest-asyncio)
```

## Writing Tests

Use plain `assert` — pytest rewrites assertions to show rich diffs on failure:

```python
def test_addition():
    assert 1 + 1 == 2

def test_raises():
    with pytest.raises(ValueError, match="invalid"):
        raise ValueError("invalid input")

def test_approx():
    assert 0.1 + 0.2 == pytest.approx(0.3)
```

**Never** use `assertEqual`, `assertTrue`, etc. — pytest's `assert` rewrites give better output.

## Fixtures

Fixtures provide reusable setup. Request them by adding as function parameters:

```python
import pytest

@pytest.fixture
def db_conn():
    conn = create_connection(":memory:")
    yield conn          # everything after yield is teardown
    conn.close()

def test_query(db_conn):
    result = db_conn.execute("SELECT 1").fetchone()
    assert result == (1,)
```

### Fixture Scope

Controls how often a fixture is instantiated:

```python
@pytest.fixture(scope="function")  # default: new instance per test
@pytest.fixture(scope="class")     # shared across a test class
@pytest.fixture(scope="module")    # shared across a test file
@pytest.fixture(scope="package")   # shared across a package
@pytest.fixture(scope="session")   # shared across the entire test run
```

### Fixture Parameters

```python
@pytest.fixture(
    scope="module",
    autouse=False,      # True = applied automatically to all tests in scope
    name="client",      # alias — lets you use a different name than the function
    params=["a", "b"],  # parametrize the fixture itself
)
def http_client(request):
    return make_client(base_url=request.param)
```

### Built-in Fixtures

| Fixture | Purpose |
|---|---|
| `tmp_path` | `pathlib.Path` to a per-test temp dir — prefer over `/tmp` |
| `tmp_path_factory` | Session-scoped temp dirs |
| `capsys` | Capture/assert on stdout/stderr: `capsys.readouterr()` |
| `capfd` | Like capsys but at file-descriptor level |
| `caplog` | Capture log records: `caplog.records`, `caplog.text` |
| `monkeypatch` | Safe attribute/env/dict patching with auto-undo |
| `request` | Introspect the current test (param, node, config) |
| `pytestconfig` | Access pytest config / CLI options |
| `mocker` | pytest-mock: `mocker.patch(...)`, `mocker.MagicMock()` |

### conftest.py

Place fixtures (and hooks) shared across multiple test files in `conftest.py`. pytest discovers it automatically — no imports needed:

```
tests/
  conftest.py        ← fixtures available to all tests/
  unit/
    conftest.py      ← fixtures available to unit/ only
    test_foo.py
  integration/
    test_bar.py
```

## Marks

### Built-in Marks

```python
@pytest.mark.skip(reason="not implemented yet")
def test_future(): ...

@pytest.mark.skipif(sys.version_info < (3, 11), reason="requires 3.11+")
def test_new_feature(): ...

@pytest.mark.xfail(strict=False, raises=NotImplementedError, reason="known bug")
def test_buggy(): ...

@pytest.mark.usefixtures("db_conn", "clean_cache")
class TestUserFlow:
    def test_login(self): ...
```

### Custom Marks

Register in `pyproject.toml` to avoid warnings (and optionally enforce with `--strict-markers`):

```toml
[tool.pytest.ini_options]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: requires external services",
    "smoke: critical path tests only",
]
addopts = ["--strict-markers"]
```

Then use: `@pytest.mark.slow`, `@pytest.mark.integration`, etc.

## Parametrize

Run the same test with multiple inputs — each combination becomes a separate test case:

```python
@pytest.mark.parametrize("x, expected", [
    (1, 2),
    (5, 6),
    (-1, 0),
], ids=["one", "five", "negative"])
def test_increment(x, expected):
    assert x + 1 == expected

# Stack decorators for cartesian product
@pytest.mark.parametrize("base", [2, 10])
@pytest.mark.parametrize("exp", [0, 1, 2])
def test_power(base, exp):
    assert base ** exp >= 0

# Mark individual cases
@pytest.mark.parametrize("val", [
    1,
    pytest.param(-1, marks=pytest.mark.xfail(reason="negative not supported")),
])
def test_sqrt(val):
    assert math.sqrt(val) >= 0
```

## Mocking

### monkeypatch (built-in, no extra install)

```python
def test_env_var(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-key")
    monkeypatch.delenv("SECRET", raising=False)
    assert os.environ["API_KEY"] == "test-key"

def test_patch_function(monkeypatch):
    monkeypatch.setattr("myapp.utils.fetch_data", lambda url: {"ok": True})
    result = myapp.utils.fetch_data("http://example.com")
    assert result == {"ok": True}

def test_patch_dict(monkeypatch):
    monkeypatch.setitem(config, "timeout", 0)
```

All patches are automatically reverted after each test — no cleanup needed.

### pytest-mock (install: `pip install pytest-mock`)

Wraps `unittest.mock` with a pytest-idiomatic API via the `mocker` fixture:

```python
def test_api_call(mocker):
    mock_get = mocker.patch("requests.get")
    mock_get.return_value.json.return_value = {"id": 1, "name": "Alice"}

    result = fetch_user(1)
    assert result["name"] == "Alice"
    mock_get.assert_called_once_with("https://api.example.com/users/1")

def test_with_spy(mocker):
    spy = mocker.spy(my_module, "expensive_function")
    do_work()
    assert spy.call_count == 1
```

Prefer `mocker.patch` over `unittest.mock.patch` as a decorator/context manager — it integrates with pytest's fixture lifecycle.

## Async Tests

With `pytest-asyncio` (`pip install pytest-asyncio`):

```python
# pyproject.toml
# [tool.pytest.ini_options]
# asyncio_mode = "auto"

import pytest

@pytest.mark.asyncio   # not needed when asyncio_mode = "auto"
async def test_async_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200

@pytest.fixture
async def async_db():
    db = await create_async_db()
    yield db
    await db.close()
```

## Output Capture

```python
def test_stdout(capsys):
    print("hello world")
    captured = capsys.readouterr()
    assert captured.out == "hello world\n"
    assert captured.err == ""

def test_logging(caplog):
    import logging
    with caplog.at_level(logging.WARNING):
        logging.warning("watch out")
    assert "watch out" in caplog.text
```

Use `-s` / `--capture=no` on the CLI to see live output during debugging.

## Configuration (pyproject.toml)

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = [
    "--strict-markers",
    "-v",
    "--tb=short",
]
markers = [
    "slow: deselect with '-m \"not slow\"'",
    "integration: needs external services",
]
asyncio_mode = "auto"
filterwarnings = [
    "error",
    "ignore::DeprecationWarning:third_party_lib",
]
log_cli = true
log_cli_level = "INFO"
```

## Key Plugins

| Plugin | Install | Purpose |
|---|---|---|
| `pytest-cov` | `pip install pytest-cov` | Coverage reports |
| `pytest-mock` | `pip install pytest-mock` | `mocker` fixture wrapping unittest.mock |
| `pytest-asyncio` | `pip install pytest-asyncio` | async/await test support |
| `pytest-xdist` | `pip install pytest-xdist` | Parallel execution with `-n auto` |
| `pytest-httpx` | `pip install pytest-httpx` | Mock httpx requests |
| `pytest-freezegun` | `pip install pytest-freezegun` | Freeze time in tests |
| `pytest-django` | `pip install pytest-django` | Django database + client fixtures |

### Coverage

```bash
pytest --cov=src --cov-report=term-missing       # console with missing lines
pytest --cov=src --cov-report=html:htmlcov        # HTML report
pytest --cov=src --cov-report=xml                 # XML for CI
pytest --cov=src --cov-fail-under=90              # fail if coverage < 90%
```

## Common Patterns

### Fixture with Teardown (yield)

```python
@pytest.fixture
def temp_file(tmp_path):
    f = tmp_path / "data.txt"
    f.write_text("initial content")
    yield f
    # teardown: tmp_path cleaned up automatically, but you can do more here
```

### Parametrized Fixture

```python
@pytest.fixture(params=["sqlite", "postgres"])
def database(request):
    db = connect(request.param)
    yield db
    db.disconnect()

def test_insert(database):  # runs twice, once per db engine
    database.insert({"key": "value"})
    assert database.count() == 1
```

### Class-based Tests (no `__init__`)

```python
class TestUserAuth:
    def test_login_valid(self, client, valid_user):
        resp = client.post("/login", json=valid_user)
        assert resp.status_code == 200

    def test_login_invalid(self, client):
        resp = client.post("/login", json={"user": "x", "pass": "wrong"})
        assert resp.status_code == 401
```

## Common Pitfalls

| Pitfall | Fix |
|---|---|
| `PytestUnknownMarkWarning` | Register marks in `pyproject.toml` `markers` list |
| Fixture scope mismatch | A `function`-scoped fixture can't request a `session`-scoped fixture's state safely — match or widen scope |
| `ScopeMismatch` error | A wider-scope fixture (e.g. `session`) can't request a narrower-scope fixture (e.g. `function`) |
| `asyncio_mode` not set | Add `asyncio_mode = "auto"` to `[tool.pytest.ini_options]` or use `@pytest.mark.asyncio` |
| Importing conftest | Never `import conftest` — pytest injects fixtures automatically |
| Writing to `/tmp` directly | Use `tmp_path` fixture — it's isolated, cleaned up, and shows in test output |
| Using `unittest.mock.patch` as decorator | Use `mocker.patch(...)` from pytest-mock so patches respect fixture lifecycle |
| Missing `pytest.raises` context | If testing that code raises, use `with pytest.raises(ExcType):` not a bare `try/except` |
