"""Extension adapters — hard-cut bridges to external repos.

Each adapter imports the implementation from an external package
(e.g. 'uflow', 'uknowledge'). If the package is unavailable, startup
fails fast for that capability so route ownership stays external.
"""