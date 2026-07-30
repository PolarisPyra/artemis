# Workspace Continuity

- Current branch: `artemis-konami`
- Latest published code/rules commit: `59e5b61`
- The Hi~Cheers item mask is module-scoped, and the native `uv` deployment and
  no-test repository policies are documented.
- The automap-backed Hi~Cheers implementation and relational `popn_playlog`
  persistence are published in commit `a90893c`.
- The `popn_profile.user → aime_user.id` foreign key is published in commit
  `59e5b61`; existing profiles are preserved and invalid orphan rows are not
  auto-reassigned.
- The workspace is synchronized with `origin/artemis-konami`.
- `origin/main` remains at `29213d2`.
- Repository workflow: commit and push directly to the requested branch; do
  not create or update pull requests.
