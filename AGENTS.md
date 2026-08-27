# AGENTS.md — Yllehs

## Project Overview

Yllehs is a software emulator of real Shelly devices.

The primary goal is to allow software and automation systems to interact with Yllehs as if they were communicating with real Shelly devices, while also allowing real Shelly JavaScript scripts to run inside a compatible JavaScript runtime.

Yllehs is **not** intended to be a generic mock server or a fictional "virtual Shelly" device with arbitrary capabilities.

The fundamental design principle is:

> Yllehs must emulate real Shelly device models and their documented behavior as faithfully as reasonably possible.

Examples of supported models may include:

- Shelly Plus 1
- Shelly Plus 1PM
- Shelly Plus 2PM
- Shelly Plus 4PM
- Shelly Plus i4
- Other real Shelly models added in the future

Model support must be based on the actual capabilities of the corresponding physical device.

---

## Core Requirements

### 1. Real Device Models

Yllehs must implement identifiable real Shelly models.

A virtual device instance must have at least:

- model
- firmware version/profile
- device identity
- component configuration
- component state
- network/API configuration
- JavaScript runtime
- scripts
- timers
- event handlers

For example:

```yaml
devices:
  - name: garage
    model: plus-1
    firmware: "TARGET_VERSION"
    port: 8080

  - name: lights
    model: plus-1pm
    firmware: "TARGET_VERSION"
    port: 8081

  - name: shutters
    model: plus-2pm
    firmware: "TARGET_VERSION"
    port: 8082
```

The model determines the available components.

Do not allow arbitrary capabilities to be added to a model if those capabilities do not exist on the corresponding physical device.

For example, a virtual Shelly Plus 1PM must not be configurable as an eight-input device merely because Yllehs can technically support eight inputs.

---

## 2. Multiple Devices in One Container

A single Yllehs container must be capable of running multiple independent virtual Shelly devices.

Each virtual device must have its own:

- model
- firmware profile
- configuration
- state
- components
- JavaScript runtime
- scripts
- timers
- event handlers

Virtual devices must be exposed through different HTTP ports.

Example:

```text
Yllehs container
│
├── :8080 → Shelly Plus 1
├── :8081 → Shelly Plus 1PM
├── :8082 → Shelly Plus 2PM
└── :8083 → Shelly Plus 4PM
```

Each endpoint must behave as an independent Shelly device.

The implementation must not require one container per virtual device.

---

## 3. Shelly RPC API Compatibility

Yllehs must implement the Shelly RPC API used by the target model and firmware profile.

Examples include:

```text
Shelly.GetStatus
Shelly.GetConfig
Shelly.ListMethods

Input.GetStatus
Input.GetConfig

Switch.GetStatus
Switch.Set
Switch.Toggle
```

The exact supported RPC surface must be determined by the selected model and firmware profile.

Do not invent Yllehs-specific RPC methods and expose them as if they were Shelly APIs.

Where possible, RPC responses, errors, parameters, callbacks, and state transitions must match the behavior of the corresponding physical device.

---

# Shelly JavaScript Runtime

## 4. JavaScript Compatibility Is a First-Class Requirement

Yllehs must provide a JavaScript runtime compatible with the Shelly scripting environment.

Scripts should be designed to run **unmodified** on both:

1. the corresponding physical Shelly device;
2. the corresponding Yllehs virtual device.

Yllehs must not require scripts to detect that they are running under emulation.

Do not introduce Yllehs-specific APIs into the normal Shelly scripting environment.

For example, scripts must not need to use:

```javascript
Yllehs.*
```

instead of:

```javascript
Shelly.*
```

---

## 5. Shelly Script APIs

Yllehs must implement the Shelly Script APIs that are available on the selected physical model/firmware.

Examples include:

```javascript
Shelly.call(...)
Shelly.addEventHandler(...)
Shelly.removeEventHandler(...)
Shelly.addStatusHandler(...)
Shelly.removeStatusHandler(...)
Shelly.getComponentStatus(...)
Shelly.getComponentConfig(...)
Shelly.getDeviceInfo(...)

Timer.set(...)
Timer.clear(...)

print(...)
```

HTTP functionality must be exposed through the same Shelly scripting mechanisms supported by the target firmware, for example:

```javascript
Shelly.call("HTTP.GET", ...)
Shelly.call("HTTP.POST", ...)
```

The implementation must not add convenience functions that do not exist on the corresponding physical Shelly.

---

## 6. Event Handlers

Event handlers are part of the real Shelly scripting environment and must be supported.

Yllehs must implement:

```javascript
Shelly.addEventHandler(...)
```

with semantics compatible with the corresponding physical Shelly.

The runtime must generate appropriate Shelly events when virtual components change state.

For example, a change involving:

```text
switch:0
```

or:

```text
input:0
```

must result in the appropriate Shelly event/status notification expected by the target firmware.

Do not replace the Shelly event system with a Yllehs-specific event API.

---

## 7. Status Handlers

Yllehs must distinguish between:

- event notifications;
- component status changes.

Where supported by the target firmware, both:

```javascript
Shelly.addEventHandler(...)
```

and:

```javascript
Shelly.addStatusHandler(...)
```

must be implemented according to their actual Shelly semantics.

Do not treat the two mechanisms as interchangeable.

---

## 8. Asynchronous Behavior

Shelly scripts are asynchronous.

Yllehs must preserve, as closely as possible:

- asynchronous RPC calls;
- callbacks;
- callback parameters;
- callback ordering;
- error codes;
- error messages;
- timeouts;
- timer behavior;
- event ordering.

For example:

```javascript
Shelly.call(
    "Input.GetStatus",
    { id: 0 },
    function (result, error_code, error_message) {
        // ...
    }
);
```

must behave like the corresponding call on a physical Shelly.

---

# Script Loading and Storage

## 9. Scripts Must Be Mountable

JavaScript files must be mountable into the Yllehs container using Docker volumes.

Example:

```yaml
services:
  yllehs:
    image: yllehs
    volumes:
      - ./scripts:/scripts:ro
```

A virtual device may reference a script:

```yaml
devices:
  - name: alarm-controller
    model: plus-1
    port: 8080
    script: /scripts/alarm.js
```

The script must execute inside the Shelly-compatible JavaScript runtime.

It must **not** simply be executed using Node.js.

---

## 10. One Runtime Per Virtual Device

Each virtual device must have an isolated scripting environment.

For example:

```text
Yllehs
│
├── Plus 1 :8080
│   └── JavaScript Runtime
│       └── alarm.js
│
├── Plus 1PM :8081
│   └── JavaScript Runtime
│       └── lights.js
│
└── Plus 2PM :8082
    └── JavaScript Runtime
        └── shutters.js
```

Scripts belonging to one virtual device must not directly access the state or runtime of another virtual device.

---

# Hardware Model

## 11. Component Model

The internal architecture should represent Shelly devices through components.

Examples:

```text
input:0
switch:0
switch:1
pm:0
pm:1
```

The component set must be derived from the real device model.

For example, if a real model exposes:

```text
switch:0
input:0
```

the corresponding Yllehs instance must expose those components.

If another model does not expose `input:0`, Yllehs must not expose it.

This capability model is critical for compatibility with third-party integrations.

---

## 12. Hardware Capabilities Must Be Model-Driven

Do not use a generic:

```yaml
inputs: 8
outputs: 8
```

configuration for arbitrary devices.

Instead:

```yaml
model: plus-1
```

must load the capability definition for the actual Plus 1.

Likewise:

```yaml
model: plus-2pm
```

must load the actual Plus 2PM component topology.

This allows integrations such as Konnecta to observe the same component/capability structure they would observe from a physical Shelly.

---

# Firmware Profiles

## 13. Firmware Matters

Yllehs must distinguish hardware model from firmware behavior.

A virtual device should therefore have:

```yaml
model: plus-1
firmware: "TARGET_VERSION"
```

The firmware profile may determine:

- available RPC methods;
- available Script APIs;
- component behavior;
- event behavior;
- configuration fields;
- error behavior.

Do not assume that all Shelly devices or firmware versions expose exactly the same API.

---

# Compatibility Philosophy

## 14. No Fictional APIs

Yllehs must not expose APIs merely because they are useful for the emulator.

For example, this is not acceptable as part of the Shelly scripting environment:

```javascript
VirtualShelly.setInput(...)
VirtualShelly.on(...)
Yllehs.getDevice(...)
```

If simulator-specific controls are required for testing, they must exist outside the emulated Shelly scripting API and must never become visible to normal Shelly scripts.

---

## 15. Simulator/Test Controls

Yllehs may provide external controls for simulation and testing.

For example, a test harness may need to force:

```text
input:0 = ON
input:0 = OFF
```

or simulate an external hardware event.

Such controls may be exposed through:

- a separate management interface;
- a test API;
- configuration;
- CLI commands;
- an internal testing interface.

These controls are implementation/testing facilities and are **not part of the emulated Shelly API**.

---

# Security

## 16. JavaScript Sandboxing

Shelly scripts must execute in a sandboxed JavaScript environment.

Do not execute scripts directly with:

```text
eval()
```

or expose the full host environment.

Scripts must not automatically have access to:

- host filesystem;
- host processes;
- arbitrary native APIs;
- container internals;
- other virtual devices.

Only APIs available to the corresponding physical Shelly should be exposed.

The JavaScript runtime should preferably use an embedded JavaScript engine suitable for sandboxing, such as QuickJS or another appropriate embedded engine.

---

# Testing

## 17. Physical Device Compatibility Tests

Compatibility with physical Shelly devices is a primary goal.

Where practical, the same operation or script should be executable against:

```text
Physical Shelly
```

and:

```text
Yllehs
```

and the results compared.

Tests should cover:

- RPC requests;
- RPC responses;
- component discovery;
- component status;
- component configuration;
- events;
- status notifications;
- timers;
- asynchronous callbacks;
- HTTP requests;
- JavaScript behavior;
- error handling.

---

## 18. Model-Specific Test Suites

Each supported model should have its own compatibility tests.

For example:

```text
tests/
├── plus-1/
├── plus-1pm/
├── plus-2pm/
└── plus-4pm/
```

Tests must verify that unsupported components are not exposed.

For example, if the physical device reports:

```text
input count = 0
```

Yllehs must not expose an artificial input component.

---

# Architecture Principles

The implementation should be structured around these concepts:

```text
Yllehs Server
│
├── Device Manager
│
├── Virtual Device
│   ├── Model Profile
│   ├── Firmware Profile
│   ├── Components
│   ├── State
│   ├── Configuration
│   └── Script Runtime
│
├── RPC Layer
│
├── Event System
│
└── Script Engine
    ├── Shelly API
    ├── Timer API
    ├── HTTP API
    └── Console/print
```

The RPC layer and JavaScript runtime should operate on the same underlying virtual device state.

For example:

```text
HTTP RPC
   │
   ▼
Component State
   │
   ├── Status notification
   │
   ├── Event notification
   │
   └── JavaScript callback
```

This prevents the REST implementation and scripting implementation from developing inconsistent state models.

---

# Example Use Case

A physical Shelly script such as:

```javascript
let inputIds = [0, 1, 2];

Shelly.addEventHandler(function (event) {
    if (event.component === "input:0") {
        print("Input 0 changed");
    }
});
```

should run on Yllehs without modification, provided that the selected model and firmware support the referenced API.

A virtual input state may be changed externally by the test environment.

The resulting state transition must pass through the same component/event mechanism used by the virtual device and ultimately trigger the Shelly-compatible JavaScript event handler.

---

# Development Rules

1. Prefer documented Shelly behavior over assumptions.
2. Never invent Shelly APIs.
3. Never expose Yllehs-specific APIs to normal Shelly scripts.
4. Model real hardware capabilities accurately.
5. Keep model and firmware behavior separate.
6. Preserve asynchronous semantics.
7. Treat event handling as part of the real Shelly Script API.
8. Keep each virtual device isolated.
9. Make scripts portable between physical Shelly devices and Yllehs.
10. Add compatibility tests whenever implementing a new API.
11. When behavior is uncertain, consult official Shelly documentation or test against physical hardware rather than guessing.
12. Do not implement a feature solely because it would be convenient for Yllehs if the corresponding physical Shelly does not provide that feature.

---

# Project Goal

The ultimate goal of Yllehs is:

> **To provide a faithful, software-defined implementation of real Shelly devices, including their RPC interfaces, component models, and JavaScript scripting environment, so that existing Shelly integrations and scripts can interact with Yllehs as they would with compatible physical Shelly hardware.**

Compatibility, fidelity, and reproducibility take precedence over adding convenient emulator-specific functionality.
