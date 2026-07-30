# Workspace Continuity

- Current branch: `main`
- Latest published code/rules commit: `da86fd9`
- The Hi~Cheers item mask is module-scoped, and the native `uv` deployment and
  no-test repository policies are documented.
- The automap-backed Hi~Cheers implementation and relational `popn_playlog`
  persistence are published in commit `a90893c`.
- The `popn_profile.user → aime_user.id` foreign key is published in commit
  `59e5b61`; existing profiles are preserved and invalid orphan rows are not
  auto-reassigned.
- Local unpublished change: Pop'n playlog stage containers now use their
  numeric stage index, the full option set persists from both write paths, and
  the default brightness is 50.
- The workspace has local unpublished changes relative to `origin/main`.
- `origin/artemis-konami` remains at `da86fd9`.
- Repository workflow: commit and push directly to the requested branch; do
  not create or update pull requests.
