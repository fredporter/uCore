#!/usr/bin/env bash
set -euo pipefail

# Combined validation script for CI quick‑wins
# Runs all lightweight validation steps in sequence.
# This replaces the multiple individual validation steps.

echo "Running combined validation checks..."

# 1. Planning governance (already done earlier in workflow)
# 2. Capability requirements
python3 scripts/validate_capability_requirements.py

# 3. Docs non‑regression
python3 scripts/validate_docs_nonregression.py

# 4. Documentation route contract
PYTHONPATH=backend python3 scripts/check_documentation_route_contract.py

# 5. Extension manifests
python3 scripts/validate_extension_manifests.py

# 6. Duplicate API routes audit
python3 scripts/audit_duplicate_routes.py

# 7. Legacy settings cleanup validation
python3 scripts/validate_legacy_settings_cleanup.py

echo "All validation steps completed successfully."
