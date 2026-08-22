# Estimation Guide

## Traffic

```text
daily operations = active entities × operations per entity
average QPS = daily operations / 86,400
peak QPS = busiest-window operations / window seconds
burst target = peak QPS × short-burst factor
```

Calculate reads and writes separately. A daily average is not a capacity target when activity is concentrated in working hours or events.

## Storage

```text
daily raw data = records per day × average record size
retained raw data = daily raw data × retention days
primary capacity = retained raw data + indexes + physical overhead + growth headroom
fleet capacity = primary + replicas + protected recovery copies
```

Estimate large attachments or media separately from structured database rows. State whether backups are full, incremental, deduplicated, or retained for a shorter period before summing copies.

## Availability and recovery

Translate availability targets into expected downtime, but also define failure scope and recovery:

- monthly or yearly availability window;
- RPO for committed data;
- RTO for the critical workflow;
- failover mechanism;
- restore testing;
- dependency failures that can still make the service unavailable.

## Cache and queues

Size cache from the hot working set, object size, TTL, hit-rate target, and redundancy. Size queues from arrival rate, worker throughput, maximum acceptable age, retry volume, and poison-message handling.

## Sanity checks

- Label every unit.
- Do not mix decimal and binary storage units silently.
- Separate source facts from assumptions.
- Keep calculated demand separate from rounded design and load-test targets.
- Check whether one normal server already exceeds the target before proposing distribution.
- Explain which decision changes if an assumption is wrong.
