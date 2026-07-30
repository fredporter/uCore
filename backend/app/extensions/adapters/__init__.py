"""Extension adapters — hard-cut bridges to external repos.

Each adapter imports the implementation from an external package
(e.g. 'uflow', 'uknowledge', and runtime registrars). If an external
provider is unavailable for a required capability, adapters fail fast.
"""