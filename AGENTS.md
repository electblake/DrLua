# Application execution

- DrLua is UI-only. Do not add CLI entry points, argument parsing, mode flags, or source-path startup arguments.
- Generate calls the generator directly inside the app's worker thread. Never launch another copy of DrLua or a Python CLI to perform generation.
- FFprobe is allowed for media metadata probing.
- Keep Tk widget access on the UI thread and show progress and output in the app.
- Test the actual Generate button with real media, not only a mocked generator.

# Fail-fast implementation

- Implement only the explicitly requested primary execution path.
- Do not add error handling, exception catches, retries, recovery logic, fallback values or providers, compatibility shims, silent substitution, or degraded modes.
- Do not add validation branches for custom error paths.
- Let failures surface naturally from the operation that fails.
