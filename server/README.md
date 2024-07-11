# Server

## Concepts

- **save**: the persisted state of a ReDel session on disk - source of truth is the data on disk
- **interactive session**: the state of a ReDel session in memory - source of truth is the ReDel instance

saves can be promoted to sessions by **load**ing them; sessions automatically save themselves every round (and
update the server's save list to make themselves known)

new sessions can be created from scratch; this also creates a save

an interactive session consumer (e.g., web viz) first gets the state and then works on event deltas sent over the
websocket