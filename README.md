# Yllehs

Yllehs is a software emulator for physical Shelly IoT devices designed to expose **stateful virtual device states** and execute **Shelly JavaScript logic** via official, unmodified Shelly APIs (RPC and REST).

---

## Purpose

Many third-party home automation systems, IoT controllers, and integration clients can only execute custom logic or fetch external state by talking directly to real Shelly hardware interfaces. 

Yllehs bridges this gap by acting as a lightweight, software-defined Shelly fleet:
- Exposes **stateful variables** (switch outputs, input triggers, power metering, device statuses) backed by realistic Shelly hardware models.
- Executes **native Shelly JavaScript scripts** inside a sandboxed QuickJS runtime to handle logic, timers, and event-driven automation.
- Allows external clients and test harnesses limited to Shelly API interfaces to interact with external systems bridged by virtual Shelly devices.

---

## Features

- **Multi-Device Hosting**: Run multiple virtual Shelly devices with isolated state, ports, and JavaScript runtimes in a single process / container.
- **Generation-Aware APIs**:
  - **Gen 1** (`shelly1`, `shelly1pm`, `shelly25`): Traditional REST API endpoints (`/relay/0?turn=on`, `/settings`, `/status`, `/shelly`).
  - **Gen 2 / Gen 3** (`plus-1`, `plus-1pm`, `plus-2pm`, `plus-4pm`, `plus-i4`, `1-gen3`, `1pm-gen3`): Full Shelly RPC protocol (`/rpc`, `/rpc/<method>`, `/status`, `/shelly`).
- **Real Shelly JavaScript Runtime (QuickJS)**:
  - Native sandboxing (no host OS leakage or arbitrary `eval()`).
  - Implements `Shelly.call()`, `Shelly.addEventHandler()`, `Shelly.addStatusHandler()`, `Shelly.getComponentStatus()`, `Shelly.getComponentConfig()`, `Shelly.getDeviceInfo()`.
  - Implements `Timer.set()`, `Timer.clear()`, `print()`, `console.log()`.
- **Simulation Control**: Test trigger endpoints (`POST /_yllehs/simulate/input/{id}`) completely isolated from emulated Shelly device APIs.

---

## Supported Models

| Model | Gen | Components | API Type |
|---|---|---|---|
| `shelly1` | Gen 1 | `relay:0`, `input:0` | REST |
| `shelly1pm` | Gen 1 | `relay:0`, `input:0`, `pm:0` | REST |
| `shelly25` | Gen 1 | `relay:0`, `relay:1`, `input:0`, `input:1`, `pm:0`, `pm:1` | REST |
| `plus-1` | Gen 2 | `switch:0`, `input:0` | RPC + JS |
| `plus-1pm` | Gen 2 | `switch:0`, `input:0` | RPC + JS |
| `plus-2pm` | Gen 2 | `switch:0`, `switch:1`, `input:0`, `input:1` | RPC + JS |
| `plus-4pm` | Gen 2 | `switch:0..3`, `input:0..3` | RPC + JS |
| `plus-i4` | Gen 2 | `input:0..3` | RPC + JS |
| `1-gen3` | Gen 3 | `switch:0`, `input:0` | RPC + JS |
| `1pm-gen3` | Gen 3 | `switch:0`, `input:0` | RPC + JS |

---

## Configuration (`yllehs.yaml`)

```yaml
devices:
  - name: garage
    model: plus-1
    firmware: "1.4.0"
    port: 8080
    script: /scripts/alarm.js

  - name: lights
    model: plus-1pm
    firmware: "1.4.0"
    port: 8081

  - name: shutters
    model: plus-2pm
    firmware: "1.4.0"
    port: 8082

  - name: old-relay
    model: shelly1
    port: 8083
```

---

## Quickstart

### Local (with `uv`)

```bash
# Install dependencies
uv sync

# Run server
uv run python -m yllehs.main yllehs.yaml

# Run test suite
uv run pytest
```

### Docker

```bash
docker compose up --build
```
