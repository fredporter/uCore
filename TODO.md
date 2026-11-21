# uCore status and sprint index

Updated: 2026-11-09

uCore is the user application/service host. Development happens in external IDEs. The active product goal is a curated, local workspace that requires no code from its users; uCode is optional learning and composition.

The current assessed cleanup sprint is [Curated applications: alignment and cleanup](docs/plans/CURATED_APPLICATIONS_CLEANUP_SPRINT_2026-11-09.md). It records working features, committed checkpoints, scaffolds, ticket dependencies, release acceptance and deferred work. Start there rather than resuming historical Dev Mode programmes.

The [Global Knowledge and User Vault completion sprint](docs/plans/KNOWLEDGE_COMPLETION_SPRINT.md) tracks the organised Core edition, seed layout, shared intake and release qualification.

Canonical tasks and run state remain owned by uFlow within the existing host contracts. This file is an index, not a competing task database. Sprint preparation does not seed maintainer tasks into personal user lists.

Historical implementation evidence remains available in [the September product refactor plan](docs/UDOS_PRODUCT_REFACTOR_PLAN_2026-09-12.md) and the archived plans it references. Internal IDE, development-agent teams and general repository coding are retired product priorities. Preserve useful runtime capabilities, user data and prior evidence while moving them to their proper owners.


The 2026-11-10 extension adds content-curation skills, reviewed seed-vault distribution, Wizard/Sorceror/Knight human authority, separate Crypt/Drone/Tomb device profiles and preservation of useful Advanced Google/engineering/surface recipes. Sonic Screwdriver belongs in normal navigation. Advanced visibility never grants authority; external IDE development and immutable installed canon remain the boundary. See K09–K14 in the current sprint plan.

The mission correction restores **Mission → tasks/research → Queue → Binder results**. Mission Control begins with the user's objective; Binders remain content collections. BitChat and Sonic are normal user surfaces. The archive reconciliation and F09–F11/K15 retain earlier product concepts without restoring old runtimes or task histories.

## Feed automation and scheduling

uCore hosts the automation UI and feed intake. uFlow owns workflow definitions, schedules, task execution, retries, and run history. Evaluate the four tools through the same recipe so each earns its place against a concrete need.

1. **Establish the uFlow scheduling baseline.** Trace a saved workflow schedule from the [workflow API](backend/app/flow/workflow_api.py) through to a recorded run. Exercise sleep, restart, overlap, and repeated delivery. Review the [maintenance scheduler](backend/app/services/maintenance_scheduler.py) for reusable lifecycle and status behavior. Evaluate [APScheduler 3.x](https://apscheduler.readthedocs.io/en/3.x/userguide.html) if that baseline exposes gaps in cron, intervals, or missed-run handling. The timer hands a due occurrence to uFlow with a stable occurrence ID. uFlow records the enqueue durably and deduplicates retries of that occurrence. Use the host timezone for local schedules.
2. **Pilot Huginn for feed intake.** Watch two RSS feeds, filter and deduplicate items, then deliver them through the [existing feed API](backend/app/api/feed_api.py). Carry a source ID, item ID, item timestamp, and URL through the handoff. uFlow produces a morning review digest and records its Binder result. Evaluate how much source setup, filtering, and troubleshooting [Huginn](https://github.com/huginn/huginn) saves. uCore maintainers own any pilot worker and database, measure idle resource and storage costs, and document how to disable the connector and remove the pilot state. Resolve that state under `UDOS_HOME` through uCore settings.
3. **Try Node-RED for visual composition.** Wire the same source, filter, and delivery steps in [Node-RED](https://nodered.org/docs/user-guide/concepts). Compare setup, editing, and diagnosis with the Huginn recipe and use the findings to design uCore blocks. Test one device event if physical computing is part of the pilot. Any Node-RED test instance is a disposable uCore maintainer tool. Record its idle costs and tear down its process and test state after comparison.
4. **Evaluate Tokio in uCodePlus when a Rust workload needs durable timers.** uCodePlus maintainers own the evaluation, resource budget, and teardown for [persistent-scheduler](https://docs.rs/persistent-scheduler). Test restart recovery and duplicate delivery for a standalone uCodePlus job. If that job needs to start work in uCore, deliver an event through the host contract and let uFlow record the run.

**First milestone.** Save the morning schedule, deliver a duplicate feed item, sleep the Mac through the scheduled time, and repeat the missed-run check with a host restart. Expect one catch-up digest, one Binder entry for the duplicate item, and run history that shows the scheduled time, actual start, and outcome. Use the results to decide whether the next sprint should focus on feed intake, block authoring, or scheduler reliability.
