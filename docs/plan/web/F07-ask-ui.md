# F07 Ask PyroScope chat UI

Depends: F01. Priority: P0. Window: EVENT. Read first: API_REFERENCE.md `/api/ask`; A05.

## Goal
A simple, trustworthy chat panel that shows the answer, the tools that produced it, and the sources, and labels replay mode honestly.

## Files (`apps/web/src/features/ask/`)
`components/{ask-panel.tsx,message-list.tsx,answer-card.tsx,tool-timeline.tsx,citation-chips.tsx,suggested-questions.tsx,mode-badge.tsx,style-toggle.tsx}`, `api/use-ask.ts`, `hooks/use-conversation.ts`, `types.ts`, `index.ts`.

## Specification
- Input up to 500 characters with a counter; optional `style` toggle (`standard` or `plain`); the current area (from the URL state) is sent as `area_id` when no area is named in the question.
- Suggested questions: "When does fire season usually start here?", "Was last year unusual?", "Compare 2019 and 2023".
- Response display: answer text rendered as plain text with line breaks (no HTML, no raw Markdown); a tool timeline listing each tool call (name, arguments collapsed, duration); citation chips ("Data v2026-11-14-ab12cd3, years 2019 to 2023, area CHT") that, when clicked, set the calendar year or area through the shared URL state; a mode badge: "Live model" or "Scripted replay (offline demo)".
- States: sending (skeleton), clarification question from the assistant (rendered like a normal answer with area candidates as buttons), rate limited (429, show retry time), upstream error with a retry button; long questions blocked client-side.
- The conversation lives in component state; no persistence.

## Tests
- [x] Replay-mode response from the mock renders the badge, the timeline with two tool calls and two citations
- [x] An answer containing `<script>` and `<img onerror=...>` renders as literal text
- [x] 429 and 502 states; character limit

## Tasks
- [x] Panel, timeline, citations, badge, states
- [x] Citation click updates the URL state (test with a mocked router)
- [x] Master plan row F07 set to `[x]`
