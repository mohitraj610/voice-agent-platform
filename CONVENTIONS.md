# Coding Conventions

Standards discovered/agreed on while building this project. Add to this as new lessons come up — don't let it go stale.

## Error handling

- **Match the exception type to the failure, don't guess by library convention.** Only catch exceptions actually raised by the code in the `try` block (e.g. `openai.*` errors for OpenAI SDK calls, not `requests.exceptions` — the SDK doesn't use `requests`).
- **A tool-call failure is a conversational event, not an HTTP failure.** If parsing a tool's arguments fails (bad JSON, missing required field), don't `return` early with a raw error string. Build a `function_call_output` with an error-shaped `output` and let the model see it, so it can recover gracefully (ask for clarification, apologize) instead of the whole request dying.
- **Keep exception categories separate.** API-level failures (timeout, connection, rate limit) and tool-argument-level failures (bad JSON, missing keys) are different problems needing different responses — don't handle them in the same `try/except` block.
- **Use narrow `except` clauses.** Catch `json.JSONDecodeError, KeyError` specifically for argument parsing, not a bare `except Exception`, so unrelated bugs aren't silently swallowed.
- **Every response needs a status code that matches reality.** Don't return an error message with an implicit 200 OK — set `response.status_code` (or raise `HTTPException`) so callers/evals can tell success from failure without parsing message text.
- **Don't repeat the same exception-handling block across routes.** If multiple endpoints need identical `except` handling, use FastAPI's `@app.exception_handler(...)` instead of copy-pasting the same clauses into every route.

## Code hygiene

- No leftover `print()` debug statements in code you're calling done — remove them or convert to real logging.
- No dead imports — if a function/exception type isn't used anymore, delete the import along with it.
- Fix typos in identifiers when you notice them (e.g. schema/class names) rather than carrying them forward.

## Testing before calling something "done"

- Test with input that specifically tries to break the thing you just built (bad arguments, unrelated questions, edge cases) — not just the happy path.
- If a tool's stub return value could plausibly match what the LLM already "knows" on its own (e.g. real arithmetic), the test doesn't prove the tool pipeline works. Use a stub value the model has no way of independently verifying, so a correct final answer actually proves the tool's output was used.
