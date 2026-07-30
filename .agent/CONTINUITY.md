# Workspace Continuity

- Current branch: `artemis-konami`
- Latest published code/rules commit: `7a657e6`
- The Hi~Cheers item mask is module-scoped, and the native `uv` deployment and
  no-test repository policies are documented.
- Local unpublished changes: remove integer `__count` attributes from Hi~Cheers
  response nodes so the binary encoder can serialize `player.new` responses;
  match the automap popular-music/service data; and replace profile JSON score
  storage with the relational `popn_playlog` table and migration.
- The workspace has local unpublished changes relative to `origin/artemis-konami`.
- `origin/main` remains at `29213d2`.
- Repository workflow: commit and push directly to the requested branch; do
  not create or update pull requests.
