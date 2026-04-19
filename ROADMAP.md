# ash-cli Roadmap

## Project Status

- **Type**: Local AI CLI agent using Agno + Qwen3.5-4B via llama.cpp
- **Current**: Outputs bash commands with streaming TUI, execute/copy options
- **Files**: 6 modules (config, agent, tui, buffer, __main__, __init__)

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

    style Core fill:#1a365d,stroke:#63b3ed,color:#fff
    style Sessions fill:#2d3748,stroke:#a0aec0,color:#fff
    style Features fill:#22543d,stroke:#68d391,color:#fff
    style Observability fill:#1a365d,stroke:#63b3ed,color:#fff
    style Distribution fill:#2d3748,stroke:#a0aec0,color:#fff
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
    
    style A0 fill:#1a365d,stroke:#63b3ed,color:#fff
    style B0 fill:#1a365d,stroke:#63b3ed,color:#fff
    style C0 fill:#1a365d,stroke:#63b3ed,color:#fff
```

### Config System [M]

- [ ] .env file support
- [ ] CLI arguments (`--model`, `--temp`, etc.)
- [ ] Config file (YAML/JSON)

### Logging [S]

- [ ] Log levels (debug, info, warning, error)
- [ ] JSON structured output
- [ ] Log file rotation with size limit
- [ ] Configurable format

### Error Handling [M]

- [ ] Connection error handling
- [ ] Retry logic with backoff
- [ ] Graceful degradation
- [ ] Input validation

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
    
    style A0 fill:#2d3748,stroke:#a0aec0,color:#fff
    style B0 fill:#2d3748,stroke:#a0aec0,color:#fff
```

### Session Storage [M]

- [ ] Persist to file (JSON/SQLite)
- [ ] Load previous sessions
- [ ] Session naming
- [ ] Export/import

### Testing [L]

- [ ] Add pytest
- [ ] Unit tests (config, agent, buffer)
- [ ] Integration tests
- [ ] GitHub Actions CI

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
    
    style A0 fill:#2d3748,stroke:#a0aec0,color:#fff
    style B0 fill:#2d3748,stroke:#a0aec0,color:#fff
    style C0 fill:#2d3748,stroke:#a0aec0,color:#fff
    style D0 fill:#2d3748,stroke:#a0aec0,color:#fff
```

### Multi-Model [M]

- [ ] Multiple model support
- [ ] Model switching
- [ ] Model presets

### Enhanced TUI [L]

- [ ] Keyboard shortcuts (vim bindings)
- [ ] Command completions
- [ ] Better scroll
- [ ] Themes

### Tools Integration [M]

- [ ] Git operations
- [ ] File previews
- [ ] Custom tools registration

### Output Options [S]

- [ ] Multiple output modes
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
    
    style A0 fill:#1a365d,stroke:#63b3ed,color:#fff
    style B0 fill:#1a365d,stroke:#63b3ed,color:#fff
    style C0 fill:#1a365d,stroke:#63b3ed,color:#fff
```

### Tracing [M]

- [ ] Request/response tracing
- [ ] Token usage tracking
- [ ] Latency metrics
- [ ] Session telemetry

### Metrics [S]

- [ ] Total tokens used
- [ ] API call counts
- [ ] Average response time
- [ ] Session statistics

### Debug Mode [S]

- [ ] Verbose flag (`-v`, `--debug`)
- [ ] Dump payloads
- [ ] Export session data
- [ ] Connection diagnostics

---

## Phase 5: Distribution

```mermaid
flowchart LR
    A0["PyPI Package [M]"] --> A1[PyPI release]
    A1 --> A2[Versioning]
    
    B0["Shell Completions [S]"] --> B1[bash]
    B1 --> B2[zsh]
    B2 --> B3[fish]
    
    style A0 fill:#2d3748,stroke:#a0aec0,color:#fff
    style B0 fill:#2d3748,stroke:#a0aec0,color:#fff
```

### PyPI Package [M]

- [ ] Package to PyPI
- [ ] Release workflow
- [ ] Version management

### Shell Completions [S]

- [ ] Bash completion
- [ ] Zsh completion
- [ ] Fish completion

---

## Quick Wins

```mermaid
flowchart LR
    A["--version [S]"] --> B["--help"]
    B --> C["Colored output"]
    C --> D["Config reset"]
    
    style A fill:#1a365d,stroke:#63b3ed,color:#fff
```

- [ ] Add `--version` flag [S]
- [ ] Extended `--help` [S]
- [ ] Colored command output [S]
- [ ] Config reset command [S]

---

## Release Milestones

```mermaid
gantt
    title ash-cli Release Timeline
    dateFormat  YYYY-MM-DD
    
    section v0.2.0
    Core Config System       :active, 2025-04-01, 7d
    Logging                 :2025-04-05, 5d
    Error Handling          :2025-04-08, 7d
    
    section v0.3.0
    Session Storage         :2025-04-15, 7d
    Testing                 :2025-04-20, 8d
    
    section v1.0.0
    All Features            :2025-05-01, 15d
    PyPI Release            :2025-05-14, 7d
```
