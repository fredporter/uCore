# Gate C — closed-loop Matter pilot

Status: **queued.** Prepared 27 November 2026. Not startable until a real Home
Assistant instance and an explicitly approved Matter light exist.

Companion material: [automation gates](OK_ASSISTANCE_AND_LOCAL_RUNS.md#delivery-gates),
Gate B evidence, and the HomeNook ownership decision
(`HomeNook/docs/decisions/D1-HA-MATTER-OWNERSHIP.md`).

## What Gate C proves

One controlled observation transition schedules one approved workflow, which
issues one approved Matter action, and the resulting Home Assistant state is
observed and receipted — end to end, once, with every step traceable.

Gate C is the first gate that touches physical equipment. Everything before it
(Gate A runs, Gate B observation and timing) is simulated or fixture-driven.

## Owners

| Concern | Owner |
| --- | --- |
| Workflow bindings, grants, runs, receipts, schedule | uFlow through uCore |
| Home Assistant gateway, Matter bridge contracts, deployment guidance | HomeNook |
| Commissioning, fabric, entity state, service calls | Upstream Home Assistant and its Matter Server |
| Physical device, network, approvals | Owner (Wizard) |

## Prerequisites — none of these exist yet

1. A reachable Home Assistant instance with a verified version, on a network the
   Mac can reach.
2. Its Matter Server integration commissioned with **one** light the owner
   explicitly approves for automation.
3. `HOMENOOK_ENABLE_HA=1` in the HomeNook deployment, with the gateway reachable
   from uCore.
4. A uFlow binding (Gate B milestone 1) whose workflow contains the approved
   light action, and a schedule (Gate B milestone 2) for the test window.
5. Credentials in the owning service's secret store — never in a schedule,
   binding, prompt or repository.
6. A short test window agreed in advance, with the device idle.

If any prerequisite is missing, Gate C stays queued. Do not substitute a mock
device and report Gate C as passed.

## Pilot sequence

1. Open the test window and record the clock source (host clock, explicit IANA
   timezone).
2. Deliver one controlled source transition (fixture feed or Huginn observation)
   for the bound source and subject.
3. Let the maintenance cycle admit the transition through its binding.
4. Let the schedule issue the occurrence inside the window.
5. Observe Home Assistant state before and after the service call.
6. Collect the chain: observation → transition → binding → run → service call →
   reported entity state, with correlation IDs.

Command acceptance and observed state are recorded **separately**. A successful
call is not proof of physical change; only the state observation is.

## Acceptance matrix

| Case | Expected |
| --- | --- |
| Happy path | One admitted run, one service call, entity state matches the request, full trace present |
| Device unavailable | Bounded retries, unconfirmed outcome reported, no silent success |
| Stale event | Rejected at admission, receipted, no call |
| Disabled workflow or binding | No admission, receipt records the suppression |
| Revoked grant | New admission refused; cached records remain readable |
| Lost service response | State read before any retry; ambiguous outcome recorded |
| Clock-only trigger | Same adapter, same trace, no observation required |
| Duplicate delivery | One run, one call (transition and occurrence identity) |

## Evidence to record

- HA and Matter Server versions, device model, firmware, network path.
- The observation payload, transition id, binding id, run id, occurrence id.
- The service call, its response, and the observed entity state with timestamps.
- Due-to-admission latency and call-to-state-confirmation latency.
- Any deviation from the matrix and its disposition.

## Rollback

1. Disable the uFlow binding and the schedule.
2. Revoke the HomeNook gateway grant for the pilot workflow.
3. Stop the sidecar or timing adapter once pending deliveries are recorded.
4. Leave Home Assistant's native controls and uFlow history intact.
5. Remove managed adapter state only after export and retention rules are applied.

## Non-goals

Broader trigger types, additional devices, multi-room scenes, and voice control
enter Gate D only after this pilot passes. Live Huginn/UnlimitedPipe sidecars and
the Rust scheduler prototype remain deferred and are not required here.
