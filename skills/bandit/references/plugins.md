# Bandit Plugin Reference

Complete catalogue of Bandit test plugin IDs. Use with `-t` to select or `-s` to skip.

---

## B1xx — Miscellaneous

| ID | Name | Description | Severity | Confidence |
|----|------|-------------|----------|------------|
| B101 | assert_used | Use of `assert` detected — stripped with `python -O`; don't rely on assert for security checks | LOW | HIGH |
| B102 | exec_used | Use of `exec()` built-in | MEDIUM | HIGH |
| B103 | set_bad_file_permissions | Setting file permissions with `chmod` to overly permissive values (e.g. 0o777) | MEDIUM | HIGH |
| B104 | hardcoded_bind_all_interfaces | Binding to `0.0.0.0` exposes the service on all interfaces | MEDIUM | MEDIUM |
| B105 | hardcoded_password_string | Possible hardcoded password in a string assignment | LOW | LOW |
| B106 | hardcoded_password_funcarg | Possible hardcoded password passed as a function argument | LOW | LOW |
| B107 | hardcoded_password_default | Possible hardcoded password in a function default argument | LOW | LOW |
| B108 | hardcoded_tmp_directory | Probable use of `/tmp`, `/var/tmp`, or `/dev/shm` as a temp path | MEDIUM | MEDIUM |
| B109 | password_config_option_not_marked_secret | Password-like config options not marked secret | LOW | LOW |
| B110 | try_except_pass | `except: pass` silently swallows exceptions | LOW | HIGH |
| B111 | execute_with_run_as_root_equals_true | Running with `run_as_root=True` | LOW | HIGH |
| B112 | try_except_continue | `except: continue` silently swallows exceptions in a loop | LOW | HIGH |
| B113 | request_without_timeout | HTTP request made without a timeout — can hang forever | MEDIUM | LOW |

---

## B2xx — Application / Framework Misconfiguration

| ID | Name | Description | Severity | Confidence |
|----|------|-------------|----------|------------|
| B201 | flask_debug_true | `Flask.run(debug=True)` enables the interactive debugger — never in production | HIGH | HIGH |
| B202 | tarfile_unsafe_members | `tarfile.extractall()` called without filtering members — zip-slip risk | HIGH | HIGH |

---

## B3xx — Blacklisted Calls

| ID | Name | Dangerous calls | Severity |
|----|------|----------------|----------|
| B301 | pickle | `pickle.loads`, `pickle.load`, `pickle.Unpickler`, `dill.*`, `shelve.open`, `jsonpickle.decode`, `pandas.read_pickle` | MEDIUM |
| B302 | marshal | `marshal.load`, `marshal.loads` | MEDIUM |
| B303 | md5 | `hashlib.md5`, `hashlib.sha1`, `Crypto.Hash.MD*.new`, `Crypto.Hash.SHA.new` | MEDIUM |
| B304 | ciphers | Insecure ciphers: ARC2, ARC4, Blowfish, DES, XOR, IDEA, CAST5, SEED, TripleDES | HIGH |
| B305 | cipher_modes | ECB mode: `cryptography.hazmat.primitives.ciphers.modes.ECB` | MEDIUM |
| B306 | mktemp_q | `tempfile.mktemp()` — race condition, use `tempfile.mkstemp()` instead | MEDIUM |
| B307 | eval | `eval()` — use `ast.literal_eval()` for safe evaluation of literals | MEDIUM |
| B308 | mark_safe | `django.utils.safestring.mark_safe()` — possible XSS exposure | MEDIUM |
| B310 | urllib_urlopen | `urllib.urlopen` and related — audit for allowed schemes | MEDIUM |
| B311 | random | `random.random()`, `random.randint()`, etc. — not cryptographically secure | LOW |
| B312 | telnetlib | Any `telnetlib.*` call — telnet is unencrypted | HIGH |
| B313 | xml_bad_cElementTree | `xml.etree.cElementTree.parse/iterparse/fromstring/XMLParser` | MEDIUM |
| B314 | xml_bad_ElementTree | `xml.etree.ElementTree.parse/iterparse/fromstring/XMLParser` | MEDIUM |
| B315 | xml_bad_expatreader | `xml.sax.expatreader.create_parser` | MEDIUM |
| B316 | xml_bad_expatbuilder | `xml.dom.expatbuilder.parse/parseString` | MEDIUM |
| B317 | xml_bad_sax | `xml.sax.parse/parseString/make_parser` | MEDIUM |
| B318 | xml_bad_minidom | `xml.dom.minidom.parse/parseString` | MEDIUM |
| B319 | xml_bad_pulldom | `xml.dom.pulldom.parse/parseString` | MEDIUM |
| B321 | ftplib | Any `ftplib.*` call — FTP is unencrypted | HIGH |
| B323 | unverified_context | `ssl._create_unverified_context()` — disables certificate verification | MEDIUM |
| B324 | hashlib | `hashlib.new('md5', ...)`, `hashlib.new('sha1', ...)` etc. | MEDIUM |
| B325 | tempnam | `os.tempnam()`, `os.tmpnam()` — symlink-attack vulnerable (removed in Py3) | MEDIUM |

> **XML note:** Replace vulnerable XML parsers with the `defusedxml` equivalents to prevent XXE, entity expansion, and related attacks.

---

## B4xx — Blacklisted Imports

| ID | Name | Flagged imports | Severity |
|----|------|----------------|----------|
| B401 | import_telnetlib | `telnetlib` | HIGH |
| B402 | import_ftplib | `ftplib` | HIGH |
| B403 | import_pickle | `pickle`, `cPickle`, `dill`, `shelve` | LOW |
| B404 | import_subprocess | `subprocess` | LOW |
| B405 | import_xml_etree | `xml.etree.cElementTree`, `xml.etree.ElementTree` | LOW |
| B406 | import_xml_sax | `xml.sax` | LOW |
| B407 | import_xml_expat | `xml.dom.expatbuilder` | LOW |
| B408 | import_xml_minidom | `xml.dom.minidom` | LOW |
| B409 | import_xml_pulldom | `xml.dom.pulldom` | LOW |
| B411 | import_xmlrpclib | `xmlrpc` — monkey-patch with defusedxml | HIGH |
| B412 | import_httpoxy | `wsgiref.handlers.CGIHandler`, `twisted.web.twcgi.CGIScript` | HIGH |
| B413 | import_pycrypto | `Crypto.*` — pycrypto has CVEs; use `cryptography` or `pycryptodome` | HIGH |
| B415 | import_pyghmi | `pyghmi` — IPMI is insecure | HIGH |

---

## B5xx — Cryptography

| ID | Name | Description | Severity |
|----|------|-------------|----------|
| B501 | request_with_no_cert_validation | `requests.get(..., verify=False)` or similar — disables TLS cert verification | HIGH |
| B502 | ssl_with_bad_version | Explicitly using deprecated SSL/TLS versions (SSLv2, SSLv3, TLSv1, TLSv1.1) | HIGH |
| B503 | ssl_with_bad_defaults | Setting `ssl.PROTOCOL_SSLv23` as default — negotiates down to insecure versions | MEDIUM |
| B504 | ssl_with_no_version | `ssl.wrap_socket()` without `ssl_version` — allows insecure negotiation | LOW |
| B505 | weak_cryptographic_key | RSA/DSA key < 2048 bits, EC key < 224 bits | HIGH |
| B506 | yaml_load | `yaml.load()` without safe Loader — use `yaml.safe_load()` | MEDIUM |
| B507 | ssh_no_host_key_verification | `AutoAddPolicy` in Paramiko — MITM risk | HIGH |
| B508 | snmp_insecure_version | SNMP v1 or v2c — no authentication/encryption | HIGH |
| B509 | snmp_weak_cryptography | SNMP v3 with DES or MD5 — use AES/SHA | MEDIUM |

---

## B6xx — Injection

| ID | Name | Description | Severity |
|----|------|-------------|----------|
| B601 | paramiko_calls | Paramiko `exec_command` — possible shell injection if input unsanitized | MEDIUM |
| B602 | subprocess_popen_with_shell_true | `subprocess.Popen(..., shell=True)` — shell injection if args from user input | HIGH |
| B603 | subprocess_without_shell_true | `subprocess.Popen(...)` without shell=True — lower risk but still audit | LOW |
| B604 | any_other_function_with_shell_true | Other functions called with `shell=True` | MEDIUM |
| B605 | start_process_with_a_shell | `os.system()`, `os.popen()`, `commands.*` — implicit shell | HIGH |
| B606 | start_process_with_no_shell | `os.execl()`, `os.spawnl()` etc. without shell — lower risk | LOW |
| B607 | start_process_with_partial_path | Process started with relative/partial path — PATH hijacking risk | LOW |
| B608 | hardcoded_sql_expressions | String concatenation/formatting used to build SQL — SQLi risk | MEDIUM |
| B609 | linux_commands_wildcard_injection | Wildcard `*` in shell commands — argument injection risk | HIGH |
| B610 | django_extra_used | Django `.extra()` QuerySet method — raw SQL | MEDIUM |
| B611 | django_rawsql_used | Django `.RawSQL()` — raw SQL | MEDIUM |
| B612 | logging_config_insecure_listen | `logging.config.listen()` — executes arbitrary code received over network | HIGH |
| B613 | trojansource | Bidirectional control characters in source — Trojan Source attack | HIGH |
| B614 | pytorch_load | `torch.load()` without `weights_only=True` — arbitrary code execution | HIGH |
| B615 | huggingface_unsafe_download | HuggingFace `hf_hub_download()` with `local_files_only=False` in untrusted context | MEDIUM |

---

## B7xx — XSS / Template Injection

| ID | Name | Description | Severity |
|----|------|-------------|----------|
| B701 | jinja2_autoescape_false | Jinja2 `Environment(autoescape=False)` — XSS via template rendering | HIGH |
| B702 | use_of_mako_templates | Using Mako templates — no auto-escaping by default | MEDIUM |
| B703 | django_mark_safe | `mark_safe()` in Django views — XSS if content is user-controlled | MEDIUM |
| B704 | markupsafe_markup_xss | `markupsafe.Markup()` with user input — XSS risk | HIGH |

---

## Remediation quick-reference

| Finding | Recommended fix |
|---------|----------------|
| B301 pickle | Use JSON or another format; if you must use pickle, only unpickle trusted, signed data |
| B303/B324 MD5/SHA1 | Use `hashlib.sha256()` or stronger; for non-security checksums add `# nosec` |
| B306 mktemp | Use `tempfile.mkstemp()` (returns fd+path) or `tempfile.NamedTemporaryFile()` |
| B311 random | Use `secrets.token_hex()`, `secrets.randbelow()`, or `secrets.choice()` |
| B501 verify=False | Remove `verify=False`; if using self-signed cert, provide `verify='/path/to/ca.pem'` |
| B506 yaml.load | Replace with `yaml.safe_load(data)` |
| B507 AutoAddPolicy | Use `RejectPolicy` or `WarningPolicy`; validate host keys out-of-band |
| B602 shell=True | Use list form: `subprocess.run(["cmd", arg1, arg2])` |
| B608 SQL concat | Use parameterized queries: `cursor.execute("SELECT * FROM t WHERE id=%s", (uid,))` |
| B701 autoescape | `jinja2.Environment(autoescape=True)` or `select_autoescape(['html', 'xml'])` |
