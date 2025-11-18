import asyncio
import json
import os
from pathlib import Path

import implicit
import yaml
import scipy.sparse as sp
from rich.progress import track
from sqlalchemy import select

from core.config import CoreConfig
from titles.chuni.database import ChuniData
from titles.chuni.schema.cozynet import recommendations
from titles.chuni.schema.score import best_score


async def main():
    cfg_dir = Path(os.getenv("ARTEMIS_CFG_DIR", "config"))
    core_cfg = CoreConfig()

    if (cfg_dir / "core.yaml").exists():
        with (cfg_dir / "core.yaml").open(encoding="utf-8") as f:
            core_cfg.update(yaml.safe_load(f))

    print("Fetching playlogs...")
    chuni_data = ChuniData(core_cfg)
    query = (
        select(
            best_score.c.user,
            best_score.c.musicId,
            best_score.c.level,
            best_score.c.playCount,
        )
    )
    result = await chuni_data.score.execute(query)

    if result is None:
        print("[ERROR] Could not fetch playlog data")
        return

    # df = pd.DataFrame(result, columns=["user", "music_id", "level", "play_count"])
    # df["music_id_level"] = df["music_id"] * 100 + df["level"]
    user_set = set()
    users = []
    playcounts = []
    music_id_levels = []

    for row in result.fetchall():
        user_set.add(row["user"])
        users.append(row["user"])
        playcounts.append(row["playCount"])
        music_id_levels.append(row["musicId"] * 100 + row["level"])

    matrix = sp.csr_matrix((
        playcounts,
        (users, music_id_levels)
    ))

    print("Training model...")
    model = implicit.als.AlternatingLeastSquares(
        factors=50, regularization=0.01, iterations=15, use_native=True
    )
    model.fit(matrix)
    model.save("recommendation_weights")

    print("Generating recommendations...")
    inserted_rows = []

    for user_id in track(user_set):
        rec, prob = model.recommend(user_id, matrix[user_id], N=20, recalculate_user=True)
        inserted_rows.extend(
            [
                {
                    "user": int(user_id),
                    "game": "chuni",
                    "musicId": int(music_level_index) // 100,
                    "level": int(music_level_index) % 100,
                }
                for music_level_index in rec
            ]
        )

    Path("recommendations.json").write_text(json.dumps(inserted_rows))
    # query = delete(recommendations).where(recommendations.c.game == "chuni")
    # _ = await chuni_data.cozynet.execute(query)

    # query = insert(recommendations).values(inserted_rows)
    # _ = await chuni_data.cozynet.execute(query)


if __name__ == "__main__":
    asyncio.run(main())
