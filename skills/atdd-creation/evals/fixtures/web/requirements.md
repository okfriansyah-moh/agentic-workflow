# Room reservation requirements — accepted revision 3

This accepted brief governs product behavior; design.md's draft proposals do not override it. The web client is Vue with TypeScript. The service exposes HTTP and stores reservations transactionally. No assistant, external provider, payments, uploads or catalog exists in this product.

- ROOM-1: Signed-in members may create their own room reservations; only coordinators may cancel another member's reservation. Denied operations return forbidden feedback and leave all reservations unchanged.
- ROOM-2: For one room, half-open intervals [start, end) must not overlap. Adjacent reservations are allowed. End must be later than start. Two simultaneous requests for the same free interval produce exactly one reservation; the other gets conflict feedback.
- ROOM-3: A recoverable save failure retains the entered room, start and end values. Retrying must allow a successful save when the cause is cleared. Field validation places focus on the first invalid field, with its error programmatically associated.
- ROOM-4: All reservation controls work with keyboard alone. At a 360 CSS-pixel viewport the form and error messages fit without horizontal scrolling. No specific wider breakpoint is mandated.
- ROOM-5: A member attempting cancellation of another member's reservation receives forbidden feedback and cannot change it. This restates the permission rule in ROOM-1 for the cancellation screen.
- ROOM-6: Successful creation shows the selected room and times, and remains visible after reload.

No execution results are supplied. Coverage should distinguish client interactions from actual server authorization and transaction behavior.

Verification commitment: include isolated unit cases for interval validity/overlap and permission decisions, component interaction checks, and complementary real server/persistence cases. A controlled unit clock or fake repository does not establish transaction contention or persistence after reload.
