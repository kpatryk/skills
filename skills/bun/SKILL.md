---
name: bun
description: |
  Bun is an all-in-one JavaScript/TypeScript runtime, package manager, bundler, and test runner. Use this skill whenever the user needs to work with Bun — whether running TypeScript/JSX files, managing packages, bundling applications, or running tests. This includes questions about bun run, bun install, bun build, bun test, bunx, .env loading, or any Bun-specific features. Even if the user doesn't explicitly mention Bun, use this skill when they're working with JavaScript/TypeScript projects and Bun could be a suitable alternative to Node.js/npm/Webpack/Jest workflows.

  Key capabilities: Execute JS/TS/JSX natively (no build step), install packages with bun.lockb, bundle for browser/node/bun targets, run Jest-compatible tests, auto-load .env files, serve HTTP with Bun.serve(), access Bun-specific APIs (Bun.file, Bun.spawn, bun:sqlite, Bun.redis), and use bunx to run package binaries.
---

# Bun: All-in-One JavaScript/TypeScript Toolkit

Bun is a fast, modern replacement for Node.js + npm + Webpack + Jest. It's a single executable that ships with everything you need to develop JavaScript and TypeScript applications.

## What is Bun?

- **Runtime**: Execute JS/TS/JSX files with 4x faster startup than Node.js, built on JavaScriptCore
- **Package Manager**: Install packages with bun install (uses binary bun.lockb instead of package-lock.json)
- **Bundler**: Bundle JS/TS/JSX for browser, Node.js, or Bun targets with bun build
- **Test Runner**: Jest-compatible test runner with snapshot support, watch mode, and coverage
- **CLI**: Includes bunx (like npx) to run package binaries and bun shell for cross-platform scripts

## Runtime: Running Code

### Basic Execution

Use `bun run` to execute TypeScript, JSX, and JavaScript files directly without any build step:

```bash
bun run app.ts          # TypeScript support out of the box
bun run component.tsx   # JSX/TSX support out of the box
bun index.js            # Can omit "run" keyword
bun --watch server.ts   # Watch mode for development
```

**Key features:**
- Native TypeScript/JSX transpilation (no ts-node needed)
- Automatic `.env` loading (reads from `.env` file in project root or parent directories)
- ESM-first, CommonJS compatible
- 4x faster startup than Node.js
- Web-standard APIs: `fetch`, `WebSocket`, `ReadableStream`, `Headers`, `URL`
- Full Node.js compatibility for globals (`process`, `Buffer`, `__dirname`) and built-in modules (`path`, `fs`, `http`, etc.)

### Package Scripts

Run scripts from `package.json`:

```bash
bun run dev        # Runs "dev" script
bun run build      # Runs "build" script
bun run            # List all available scripts
```

Scripts respect lifecycle hooks (`pre<script>`, `post<script>`).

### Advanced Runtime Options

```bash
bun --watch run index.ts    # Watch mode, re-run on changes
bun --smol run app.ts       # Low-memory mode (more frequent GC)
bun run -                   # Read code from stdin
bun --eval "console.log(1)" # Evaluate inline code (-e also works)
```

## Package Manager: Installing Dependencies

### Basic Commands

```bash
bun install              # Install all dependencies from package.json
bun add react            # Add package to dependencies
bun add -d @types/node   # Add dev dependency (-d flag)
bun remove lodash        # Remove package
bun update               # Update all packages
bun update react         # Update specific package
```

### Key Features

- **Binary lockfile** (`bun.lockb`): Much smaller than package-lock.json, commits to git
- **Fast installs**: Significantly faster than npm/yarn/pnpm
- **Workspaces**: Monorepo support with `"workspaces"` in package.json
- **Overrides**: Pin specific versions of transitive dependencies
- **Frozen lockfile**: `bun install --frozen-lockfile` for CI/CD (fail if lock doesn't match package.json)
- **Link local packages**: `bun link` and `bun link <package>` for local development

### Workspace Example

```json
{
  "name": "my-monorepo",
  "workspaces": ["packages/*"]
}
```

```bash
bun install --workspaces           # Install all workspace packages
bun run --filter "package-a" test  # Run test script in specific package
bun run --filter "ba*" build       # Run build in all packages matching pattern
```

### .env Support

Bun automatically loads `.env` files when running code:

```bash
# .env
DATABASE_URL=postgres://localhost/mydb
API_KEY=secret123

# app.ts
console.log(process.env.DATABASE_URL)  // "postgres://localhost/mydb"
```

## Test Runner: Testing with Bun

### Running Tests

```bash
bun test                    # Run all test files
bun test --watch            # Watch mode, re-run on changes
bun test --coverage         # Generate coverage report
bun test --concurrent       # Run tests in parallel (default is sequential)
bun test --bail             # Stop on first failure
bun test --retry 3          # Retry failed tests up to 3 times
```

### Writing Tests

Bun's test runner is Jest-compatible. Import from `bun:test`:

```typescript
import { test, expect, describe, it, beforeEach, mock, spyOn } from "bun:test";

describe("Math operations", () => {
  test("addition works", () => {
    expect(2 + 2).toBe(4);
  });

  it("subtraction works", () => {
    expect(5 - 3).toBe(2);
  });

  test("runs concurrently", async () => {
    await fetch("/api/endpoint");
    expect(true).toBe(true);
  });

  test.serial("runs sequentially", () => {
    // Runs one at a time, useful for tests that share state
  });

  test("has snapshots", () => {
    expect({ a: 1, b: 2 }).toMatchSnapshot();
  });
});
```

### Test Files

Bun auto-discovers test files with these patterns:
- `*.test.{js,jsx,ts,tsx}`
- `*_test.{js,jsx,ts,tsx}`
- `*.spec.{js,jsx,ts,tsx}`
- `*_spec.{js,jsx,ts,tsx}`

### Mocking and Spying

```typescript
import { mock, spyOn } from "bun:test";

// Mock a function
const mockFn = mock(() => "mocked value");
mockFn();  // Call it
console.log(mockFn.mock.calls); // See all calls

// Spy on existing function
const obj = { method: () => "original" };
spyOn(obj, "method").mockReturnValue("spied");
```

### DOM Testing

Bun ships with DOM support for React/Vue component testing:

```typescript
import { test, expect } from "bun:test";
import { render } from "@testing-library/react";

test("renders component", () => {
  const { container } = render(<MyComponent />);
  expect(container.querySelector("button")).toBeTruthy();
});
```

## Bundler: Building for Production

### Basic Bundling

```bash
bun build ./src/index.tsx --outdir ./dist
```

### CLI Options

```bash
bun build ./app.ts \
  --outdir ./dist          # Output directory
  --target browser         # Target environment (browser|bun|node, default: browser)
  --format esm             # Module format (esm|cjs|iife, default: esm)
  --minify                 # Minify output
  --sourcemap              # Generate sourcemap
  --splitting              # Code splitting for entry points
  --external:react         # Don't bundle, treat as external
  --watch                  # Watch mode, rebuild on changes
```

### JavaScript API

```typescript
const result = await Bun.build({
  entrypoints: ["./src/index.ts", "./src/admin.ts"],
  outdir: "./dist",
  target: "browser",      // "browser" | "bun" | "node"
  format: "esm",          // "esm" | "cjs" | "iife"
  minify: true,
  sourcemap: "external",
  splitting: true,        // Code splitting
  external: ["react"],    // Don't bundle
});

if (!result.success) {
  console.error(result.logs);
}
```

### Supported File Types

- **JS/TS/JSX/TSX**: Automatically transpiled
- **JSON/JSONC/TOML/YAML**: Parsed and inlined as objects
- **CSS**: Bundled into `style.css`
- **HTML**: Assets referenced in HTML are bundled
- **TXT**: Read and inlined as strings
- **Images, fonts**: Treated as assets, copied to output

## Key Bun APIs

### Bun.serve() - HTTP Server

```typescript
const server = Bun.serve({
  port: 3000,
  fetch(req) {
    const url = new URL(req.url);
    if (url.pathname === "/") return new Response("Hello!");
    return new Response("Not found", { status: 404 });
  },
});

console.log(`Listening on http://localhost:${server.port}`);
```

### File Operations

```typescript
// Read file
const file = Bun.file("./data.txt");
const text = await file.text();
const buffer = await file.arrayBuffer();

// Write file
await Bun.write("./output.txt", "Hello, world!");
await Bun.write("./data.json", JSON.stringify(obj));

// Copy file
await Bun.write("./copy.txt", Bun.file("./original.txt"));
```

### Process Management

```typescript
// Run a subprocess
const proc = Bun.spawn(["ls", "-la"]);
const text = await new Response(proc.stdout).text();
console.log(text);

// With stdin
const result = Bun.spawnSync(["cat"], {
  stdin: "Hello from stdin",
});
```

### Bun-Specific APIs

```typescript
// Password hashing (bcrypt)
const hashed = await Bun.password.hash("my-password");
const isMatch = await Bun.password.verify("my-password", hashed);

// SQLite database (included)
import { Database } from "bun:sqlite";
const db = new Database("data.db");
db.query("SELECT * FROM users").all();

// Redis client (included)
import { redis } from "bun:redis";
const client = redis.createClient();
await client.set("key", "value");

// SHA hashing
import { hash } from "bun";
const digest = hash("input data");  // Returns Uint8Array
```

## bunx: Run Package Binaries

Like `npx`, run package binaries without installing globally:

```bash
bunx cowsay "Hello, world!"     # Run any npm binary
bunx vite build                  # Build with Vite
bunx next dev                    # Run Next.js dev server
bunx create-react-app my-app     # Create new projects
```

## Performance Advantages

- **4x faster startup** than Node.js
- **~3.5x faster package installation** than npm
- **Bundler speed**: Comparable to esbuild, faster than webpack
- **Lower memory usage** due to JavaScriptCore engine
- **Single binary**: No dependency management overhead

## Common Patterns

### Development Workflow

```bash
bun install
bun run dev              # Start dev server with bun --watch
bun test --watch        # Run tests in watch mode
bun build ./src/index.ts --outdir ./dist
```

### CI/CD Integration

```bash
bun install --frozen-lockfile  # Use exact versions from lock file
bun test --coverage            # Run tests with coverage
bun build                      # Build for production
```

### Monorepo Setup

```bash
# Root package.json
{
  "workspaces": ["packages/app", "packages/lib"]
}

bun install                    # Installs all workspaces
bun run --filter app dev      # Run dev in app package
```

## Caveats and Limitations

- **Binary lockfile**: `bun.lockb` is not human-readable, but much smaller and faster
- **Some Node native addons**: Not all native addons work; pure JavaScript/WASM packages are fully supported
- **Ongoing Node.js compatibility**: Most Node.js code works, but check [compatibility page](https://bun.com/docs/runtime/nodejs-compat) for edge cases
- **Bundler format support**: `cjs` and `iife` formats are experimental (esm is stable)

## Learn More

Full documentation: https://bun.com/docs

Key sections:
- [Runtime](https://bun.com/docs/runtime)
- [Test Runner](https://bun.com/docs/test)
- [Bundler](https://bun.com/docs/bundler)
- [API Reference](https://bun.com/docs/api)

## Requirements

- Requires Bun CLI (`bun`, `bunx`) installed on the system.
- Cross-platform support: Linux, macOS, and Windows.
