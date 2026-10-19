---
name: export-chat-trajectory
description: Export an identified Codex chat's available local rollout messages, tool activity, and execution metadata to JSONL for analysis.
---

# Export chat trajectory

Produce a JSONL snapshot of the requested chat, preserving recorded content and provenance. Export conversation and tool activity; exclude hidden internal reasoning and private system/developer instructions, even when the user requests everything. State this scope briefly before exporting.

## Locate and inspect

1. Resolve the exact thread ID from trusted chat context or the user's selection. Do not select a session merely because it is newest or shares the working directory.
2. Use `CODEX_HOME` when set, otherwise `~/.codex`. Search `sessions/` and `archived_sessions/` for rollout JSONL files containing that thread ID. Include all matching parts; do not include related chats without authorization.
3. Inspect record types, field names, counts, and message roles/phases before processing content. Rollout schemas can vary. Do not print reasoning payloads or entire logs to discover their structure.

## Classify records

Use an explicit allowlist based on the observed schema:

| Record | Export treatment |
| --- | --- |
| `response_item/message` | Include user messages and assistant commentary/final messages. Exclude analysis/summary channels or phases and private internal metadata fields. |
| `response_item` tool calls/results | Include function/custom tool calls and outputs, plus observed search or shell call types. Preserve arguments, call IDs, outputs, and status. |
| `event_msg/item_completed` | Include user/agent messages, command execution, file changes, MCP tool calls, search activity, and image-view references. Apply the same message restrictions. |
| Execution and usage records | Include task start/completion, token usage/counts, goal/settings events, and compaction occurrence markers where present. |
| Reasoning records/items | Exclude raw reasoning, reasoning summaries, and encrypted reasoning content. |
| Private context records | Exclude system/developer messages, internal context snapshots, and compaction summaries. Do not copy session metadata wholesale. |
| Unknown types or nested extensions | Inspect their schema and classify before inclusion; count unresolved types as omitted. |

Classification applies to nested content as well as top-level types. A tool/event wrapper is not blanket permission to include private context. Retain ordinary tool output faithfully; document any necessary redaction instead of silently rewriting it.

## Write the export

- Honor the requested destination. Otherwise use `~/Downloads/Codex-exports/`, outside the repository, with a filename containing the thread ID and UTC timestamp. Create a new file without overwriting earlier exports.
- Read source files without modifying them. Parse JSONL directly with a small local script; let malformed records and filesystem failures surface. Do not repair or silently skip invalid JSON.
- Write UTF-8 JSONL with one complete JSON object per line. Preserve source order within each file and retain timestamps, IDs, roles, tool names, and payloads. For multiple parts, record their ordering explicitly.
- Add `export_source` containing the source filename and original one-based line number to each exported record.
- Write an initial `export_manifest` with schema version, thread ID, UTC snapshot time, source paths/order, included counts by type, omitted counts/reasons, and any redactions or coverage limits.
- Preserve repeated records rather than guessing at deduplication. Explain that response records and item-completed events may represent the same interaction.
- Do not fabricate absent turns or reconstruct missing logs from memory. The export covers available on-disk records at snapshot time; it cannot include subsequent tool outputs or the final handoff message.

## Verify and deliver

Reparse every output line, reconcile counts with the manifest, and confirm excluded record classes are absent, including nested reasoning items and private message roles. Report the absolute clickable file path, record count, size, and material exclusions. Do not claim the full conversation was recovered unless source coverage proves it.
