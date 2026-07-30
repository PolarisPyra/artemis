# Workspace Continuity

- Current branch: `artemis-konami`
- Latest published code/rules commit: `7a657e6`
- The Hi~Cheers item mask is module-scoped, and the native `uv` deployment and
  no-test repository policies are documented.
- The automap-backed Hi~Cheers implementation and relational `popn_playlog`
  persistence are published in commit `a90893c`.
- Local unpublished change: link `popn_profile.user` to `aime_user.id` with an
  idempotent migration; existing profiles are preserved and invalid orphan
  rows are not auto-reassigned.
- The workspace has local unpublished changes relative to `origin/artemis-konami`.
- `origin/main` remains at `29213d2`.
- Repository workflow: commit and push directly to the requested branch; do
  not create or update pull requests.
