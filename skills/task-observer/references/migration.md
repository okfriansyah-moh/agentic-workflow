# Legacy observation migration

This installation starts a fresh global log. No migration runs automatically.

If the user requests migration, inspect the exact legacy source and back it up. Read `scripts/migrate-log.py` before using it and test on a temporary copy; it preserves the upstream migration implementation. Check its input and output schema against the current observation helper. Do not merge different project logs or move private material into the global log without an explicit scope decision. Validate every migrated record, unique IDs, and preserved evidence before switching the live storage path.
