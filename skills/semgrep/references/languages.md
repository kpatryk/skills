# Semgrep Supported Languages

Source: https://semgrep.dev/docs/writing-rules/rule-syntax#language-extensions-and-languages-key-values

Use these values in the `languages:` key of your rules.

| Language | `languages:` key values | File extensions |
|----------|------------------------|-----------------|
| Apex (Pro only) | `apex` | `.cls` |
| Bash | `bash`, `sh` | `.bash`, `.sh` |
| C | `c` | `.c`, `.h` |
| Cairo | `cairo` | `.cairo` |
| Circom | `circom` | `.circom` |
| Clojure | `clojure` | `.clj`, `.cljs`, `.cljc`, `.edn` |
| C++ | `cpp`, `c++` | `.cc`, `.cpp`, `.cxx`, `.c++`, `.h`, `.hpp` |
| C# | `csharp`, `c#` | `.cs` |
| Dart | `dart` | `.dart` |
| Dockerfile | `dockerfile`, `docker` | `Dockerfile`, `.dockerfile` |
| Elixir (Pro only) | `ex`, `elixir` | `.ex`, `.exs` |
| Generic (text) | `generic` | `.generic` |
| Go | `go`, `golang` | `.go` |
| Hack | `hack` | `.hack`, `.hck`, `.hh` |
| HTML | `html` | `.htm`, `.html` |
| Java | `java` | `.java` |
| JavaScript | `js`, `javascript` | `.js`, `.jsx`, `.cjs`, `.mjs` |
| JSON | `json` | `.json`, `.ipynb` |
| Jsonnet | `jsonnet` | `.jsonnet`, `.libsonnet` |
| Julia | `julia` | `.jl` |
| Kotlin | `kt`, `kotlin` | `.kt`, `.kts`, `.ktm` |
| Lisp | `lisp` | `.lisp`, `.cl`, `.el` |
| Lua | `lua` | `.lua` |
| OCaml | `ocaml` | `.ml`, `.mli` |
| PHP | `php` | `.php`, `.tpl`, `.phtml` |
| Protocol Buffers | `proto`, `protobuf`, `proto3` | `.proto` |
| Python | `python`, `python2`, `python3`, `py` | `.py`, `.pyi` |
| R | `r` | `.r`, `.R` |
| Ruby | `ruby` | `.rb` |
| Rust | `rust` | `.rs` |
| Scala | `scala` | `.scala` |
| Solidity | `solidity`, `sol` | `.sol` |
| Swift | `swift` | `.swift` |
| Terraform / HCL | `tf`, `hcl`, `terraform` | `.tf`, `.hcl`, `.tfvars` |
| TypeScript | `ts`, `typescript` | `.ts`, `.tsx` |
| Vue | `vue` | `.vue` |
| XML | `xml` | `.xml`, `.plist` |
| YAML | `yaml` | `.yml`, `.yaml` |

## Notes

- **`generic`**: Text-based matching (no AST). Useful for config files, comments, or languages without a parser.
- **Pro-only languages** (Apex, Elixir, Gosu, C# interfile): Require Semgrep Pro Engine (`--pro` flag and a license).
- **Multi-language rules**: List multiple values: `languages: [python, javascript]`. Semgrep will only apply the rule to matching files.
- **`auto` config**: Semgrep auto-detects language from file extension and applies appropriate rules.

## Language maturity levels

Community Edition (CE) supports most languages listed above at "GA" maturity. Some may be "beta" or "experimental":

- **GA**: Full AST support, metavariables work as expected
- **Beta**: Parser works but some patterns may not match
- **Experimental**: Limited support, possible false negatives

Check current maturity: https://semgrep.dev/docs/semgrep-ce-languages
