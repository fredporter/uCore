"""Extension adapters — backward-compatible bridges to external repos.

Each adapter tries to import the real implementation from an external
package (e.g. 'uflow', 'uknowledge'). If the package is not installed,
it falls back to the existing uCore implementation so nothing breaks
during the transition.
"""