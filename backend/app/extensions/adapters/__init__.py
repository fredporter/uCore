"""Extension adapters — hard-cut bridges to external repos.

Each adapter imports the implementation from an external package
(e.g. 'uflow', 'uknowledge', and runtime registrars). If an external
provider is unavailable, adapters either fail fast (required capability)
or run in explicitly configured compatibility mode.
"""