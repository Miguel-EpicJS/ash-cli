# ash-cli Roadmap

## Project Status

- **Type**: Local AI CLI agent using Agno + Qwen3.5-4B via llama.cpp
- **Current**: v1.0.0-rc1 - All core features, observability, and shell completions ready
- **Files**: 11 modules

## Legend

| Node Color | Status |
|-----------|--------|
| 🟢 Green | Complete |
| 🔵 Blue | In Progress / Current |
| ⚪ Gray | Planned / Not Started |

| Effort | Complexity |
|--------|------------|
| [S] Small | < 1 day |
| [M] Medium | 1-3 days |
| [L] Large | > 3 days |

---

## Dependency Graph

```mermaid
flowchart TD
    subgraph Core["Core Infrastructure"]
        config("Config System [M]")
        logging("Logging [S]")
        error("Error Handling [M]")
    end

    subgraph Sessions["Sessions & Testing"]
        sessions("Session Storage [M]")
        history("Command History [S]")
        testing("Testing [L]")
    end

    subgraph Features["Features"]
        multimodel("Multi-Model [M]")
        tui("Enhanced TUI [L]")
        tools("Tools Integration [M]")
        output("Output Options [S]")
    end

    subgraph Observability["Observability"]
        tracing("Tracing [M]")
        metrics("Metrics [S]")
        debug("Debug Mode [S]")
    end

    subgraph Distribution["Distribution"]
        pypi("PyPI Package [M]")
        completions("Shell Completions [S]")
    end

    logging --> tracing
    config --> logging
    config --> error
    config --> sessions
    logging --> sessions
    sessions --> history
    sessions --> testing
    history --> multimodel
    history --> tui
    tracing --> metrics
    tracing --> debug
    testing --> pypi

    style Core fill:#22543d,stroke:#68d391,color:#fff
    style Sessions fill:#22543d,stroke:#68d391,color:#fff
    style Features fill:#22543d,stroke:#68d391,color:#fff
    style Observability fill:#22543d,stroke:#68d391,color:#fff
    style Distribution fill:#1a365d,stroke:#63b3ed,color:#fff
```

---

## Phase 1: Core Infrastructure

```mermaid
flowchart LR
    A0["Config System [M]"] --> A1[".env support"]
    A1 --> A2[CLI Args]
    A2 --> A3[Config file]
    
    B0["Logging [S]"] --> B1[Log levels]
    B1 --> B2[JSON output]
    B2 --> B3[File rotation]
    
    C0["Error Handling [M]"] --> C1[Connection errors]
    C1 --> C2[Retry logic]
    C2 --> C3[Graceful degradation]
    
    style A0 fill:#22543d,stroke:#68d391,color:#fff
    style B0 fill:#22543d,stroke:#68d391,color:#fff
    style C0 fill:#22543d,stroke:#68d391,color:#fff
```

### Config System [M]

- [x] .env file support
- [x] CLI arguments (`--model`, `--temp`, etc.)
- [x] Config file (YAML/JSON)

### Logging [S]

- [x] Log levels (debug, info, warning, error)
- [x] JSON structured output
- [x] Log file rotation with size limit
- [x] Configurable format

### Error Handling [M]

- [x] Connection error handling
- [x] Retry logic with backoff
- [x] Graceful degradation
- [x] Input validation

---

## Phase 2: Sessions & Testing

```mermaid
flowchart LR
    A0["Session Storage [M]"] --> A1[History]
    A1 --> A2[Search]
    A0 --> A3[Export/Import]
    
    B0["Testing [L]"] --> B1[Unit Tests]
    B1 --> B2[Integration Tests]
    B2 --> B3[CI/CD]
    
    style A0 fill:#22543d,stroke:#68d391,color:#fff
    style B0 fill:#22543d,stroke:#68d391,color:#fff
```

### Session Storage [M]

- [x] Persist to file (JSON/SQLite)
- [x] Load previous sessions
- [x] Session naming
- [x] Export/import

### Testing [L]

- [x] Add pytest
- [x] Unit tests (config, agent, buffer, session, error, tui)
- [ ] Integration tests
- [x] GitHub Actions CI

---

## Phase 3: Features

```mermaid
flowchart LR
    A0["Multi-Model [M]"] --> A1[Model presets]
    
    B0["Enhanced TUI [L]"] --> B1[Shortcuts]
    B1 --> B2[Completions]
    
    C0["Tools [M]"] --> C1[Git tools]
    C1 --> C2[Custom tools]
    
    D0["Output Options [S]"] --> D1[Multiple modes]
    D1 --> D2[JSON output]
    
    style A0 fill:#22543d,stroke:#68d391,color:#fff
    style B0 fill:#22543d,stroke:#68d391,color:#fff
    style C0 fill:#22543d,stroke:#68d391,color:#fff
    style D0 fill:#22543d,stroke:#68d391,color:#fff
```

### Multi-Model [M]

- [x] Multiple model support
- [x] Model switching
- [x] Model presets (in config)

### Enhanced TUI [L]

- [x] Keyboard shortcuts (vim bindings for scroll: j, k)
- [x] History search (with /)
- [x] Command completions (Tab)
- [ ] Better scroll (smooth scroll/page up-down)
- [x] Themes (dark/light/system)

### Tools Integration [M]

- [x] Git operations (status, diff, commit, push, log)
- [x] File previews
- [x] Custom tools registration

### Output Options [S]

- [x] Execute/Copy/Skip interactive prompt
- [ ] JSON output mode
- [ ] Pipe to other commands

---

## Phase 4: Observability

```mermaid
flowchart LR
    A0["Tracing [M]"] --> A1[Token tracking]
    A1 --> A2[Latency metrics]
    A0 --> A3[Session telemetry]
    
    B0["Metrics [S]"] --> B1[Usage stats]
    B1 --> B2[API counts]
    
    C0["Debug Mode [S]"] --> C1[Verbose output]
    C1 --> C2[Payload dump]
    
    style A0 fill:#22543d,stroke:#68d391,color:#fff
    style B0 fill:#22543d,stroke:#68d391,color:#fff
    style C0 fill:#22543d,stroke:#68d391,color:#fff
```

### Tracing [M]

- [x] Request/reponse tracing (Done via logger)
- [x] Token usage tracking
- [x] Latency metrics
- [x] Session telemetry (Done via /stats)

### Metrics [S]

- [x] Total tokens used (per session)
- [x] API call counts
- [x] Average response time
- [x] Session statistics

### Debug Mode [S]

- [x] Verbose flag (`-v`, `--debug`)
- [x] Dump payloads
- [x] Export session data
- [x] Connection diagnostics

---

## Phase 5: Distribution

```mermaid
flowchart LR
    A0["PyPI Package [M]"] --> A1[PyPI release]
    A1 --> A2[Versioning]
    
    B0["Shell Completions [S]"] --> B1[bash]
    B1 --> B2[zsh]
    B2 --> B3[fish]
    
    style A0 fill:#1a365d,stroke:#63b3ed,color:#fff
    style B0 fill:#22543d,stroke:#68d391,color:#fff
```

### PyPI Package [M]

- [ ] Package to PyPI
- [ ] Release workflow
- [x] Version management

### Shell Completions [S]

- [x] Bash completion
- [x] Zsh completion
- [ ] Fish completion

---

## Quick Wins

```mermaid
flowchart LR
    A["--version [S]"] --> B["--help"]
    B --> C["Colored output"]
    C --> D["Config reset"]
    
    style A fill:#22543d,stroke:#68d391,color:#fff
```

- [x] Add `--version` flag [S]
- [x] Extended `--help` [S]
- [x] Colored command output [S]
- [x] Config reset command [S]

---

## Release Milestones

```mermaid
gantt
    title ash-cli Release Timeline
    dateFormat  YYYY-MM-DD
    
    section v0.2.0
    Core Infrastructure    :done, 2025-04-01, 14d
    
    section v0.3.0
    Sessions & Testing     :done, 2025-04-15, 10d
    Basic Features         :active, 2025-04-25, 10d
    
    section v1.0.0
    All Features            :2025-05-10, 15d
    PyPI Release            :2025-05-25, 7d
```
