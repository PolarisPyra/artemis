# Workspace Continuity

- Current branch: `main`
- Latest published code/rules commit: `81c7655`
- The Hi~Cheers item mask is module-scoped, and the native `uv` deployment and
  no-test repository policies are documented.
- The automap-backed Hi~Cheers implementation and relational `popn_playlog`
  persistence are published in commit `a90893c`.
- The `popn_profile.user → aime_user.id` foreign key is published in commit
  `59e5b61`; existing profiles are preserved and invalid orphan rows are not
  auto-reassigned.
- Pop'n playlog stage indexing, complete option persistence, and the default
  brightness of 50 are published in commit `81c7655`.
- The workspace is synchronized with `origin/main`.
- `origin/artemis-konami` remains at `da86fd9`.
- Repository workflow: commit and push directly to the requested branch; do
  not create or update pull requests.
