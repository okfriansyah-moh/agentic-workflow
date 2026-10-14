# Local note CLI — accepted revision 2

The chosen implementation language is Python. This command-line tool works entirely offline on UTF-8 files. There is no browser, service, network provider or database. Its input filename is supplied by the user.

- CLI-1: `note check FILE` leaves file bytes unchanged. A file with valid records exits 0; malformed records exit 2 with the first invalid line number on stderr. Revision 1's malformed-input exit code was 1; revision 2 changes it to 2.
- CLI-2: `note normalize FILE` atomically replaces a valid file with records serialized in the specified format in sorted key order, each ending in one newline. If replacement fails before commit, original bytes are retained and the command exits 3 with an error on stderr.
- CLI-3: `note normalize --dry-run FILE` reports the proposed records serialized in the specified format to stdout with exit 0 and never modifies file bytes or creates a replacement file.
- CLI-4: The legacy `note upload` command is removed and out of scope for new cases. Retire its old scenario; do not add a network dependency.

Record format is one `key=value` pair per line with a nonempty ASCII-letter key and a nonempty value. Unique keys are required. A valid example is `beta=2` then `alpha=1`, each newline-terminated. Empty files are valid. Unknown error wording beyond the required line number is not contractual.

Verification commitment: include isolated unit cases for record validation and specified ordering, plus complementary process/real-filesystem proof for command exits and atomic replacement. An injected in-memory write error does not establish that original file bytes survive a failed real replacement.
