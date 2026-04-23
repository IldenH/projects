import Database from "better-sqlite3";
import { readFile } from "fs/promises";

async function main() {
  try {
    const export_animes_data = await readFile(
      "./export/anime_title_to_index.json",
      "utf-8",
    );
    const export_animes_json = JSON.parse(export_animes_data);
    const export_animes = Object.keys(export_animes_json);
    console.log(`Total animes: ${export_animes.length}`);

    const meta_animes_data = await readFile(
      "./anime-offline-database.jsonl",
      "utf-8",
    );
    const seen = new Set();
    const meta_animes = meta_animes_data
      .split("\n")
      .filter(Boolean)
      .map((line) => JSON.parse(line))
      .filter((a) => export_animes.includes(a.title))
      .filter((a) => {
        if (seen.has(a.title)) return false;
        seen.add(a.title);
        return true;
      });

    console.log(`Total animes: ${meta_animes.length}`);
    console.log(meta_animes[0]);

    const db = new Database("main.db");

    db.prepare("DELETE FROM Anime").run();
    db.prepare("DELETE FROM sqlite_sequence WHERE name='Anime'").run();

    const insert = db.prepare(`
      INSERT OR IGNORE INTO Anime
      (name, picture, type, episodes, status, score, year, season)
      VALUES
      (@name, @picture, @type, @episodes, @status, @score, @year, @season)
    `);

    const insertMany = db.transaction((animes) => {
      for (const anime of animes) {
        insert.run({
          name: anime.title,
          picture: anime.picture ?? null,
          type: anime.type ?? null,
          episodes: anime.episodes ?? null,
          status: anime.status ?? null,
          score: anime.score?.median ?? null,
          year: anime.animeSeason.year ?? null,
          season: anime.animeSeason.season ?? null,
        });
      }
    });

    insertMany(meta_animes);

    console.log("All anime titles inserted successfully!");
    db.close();
  } catch (error) {
    console.error(error);
  }
}

main();
