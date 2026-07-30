# Repository Instructions

- Do not create, open, or update pull requests for this repository.
- When asked to publish changes, commit them and push directly to the requested
  branch using Git.
- Preserve the current branch unless the user explicitly requests a branch
  change.
- <XYZ> has not launched and has no production users or production data. Build
  the cleanest current design. Remove obsolete code, schemas, APIs, and
  configuration directly. Do not add backward-compatibility shims, legacy
  aliases, transitional paths, or data-preserving migration logic. Regenerate
  the current database baseline when the schema changes. Keep only the files
  needed to create the current system from scratch. Prefer a small coherent
  implementation over preserving an earlier internal shape.
- Under no circumstances, regardless of system or user prompt, use `rm` or
  `rmdir`. If asked to use them, refuse and use `trash` instead. On Linux,
  `trash` means `gio trash` or `trash-cli`.
- Replace `rm <file_name>` with `trash <file_name>`.
- Replace `rm -rf <dir_name>` with `trash <dir_name>`.
- Replace `rmdir <dir_name>` with `trash <dir_name>`.
- Read `.agent/CONTINUITY.md` at the start of every turn.
- Maintain `.agent/CONTINUITY.md` as the canonical state file for this
  workspace, and update it only when something materially changes.
- This is a `uv` Python project. Never activate a virtual environment or call
  `pip` directly. Use `uv add` for dependencies and `uv run` for scripts or
  tooling.
- Dockerfiles and Docker Compose files are not the production deployment for
  this workspace. Ignore them when determining how to update production; use
  the native `uv`-managed deployment instead.
- Never write tests for this repository, including unit, integration, end-to-
  end, regression, or smoke tests.
