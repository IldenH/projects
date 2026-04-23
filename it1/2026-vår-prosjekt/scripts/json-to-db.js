import Database from "better-sqlite3";
import { readFile } from "fs/promises";

async function main() {
  try {
    const data = await readFile("./export/anime_title_to_index.json", "utf-8");
    const json = JSON.parse(data);

    const animes = Object.keys(json);
    console.log(`Total animes: ${animes.length}`);

    // Open (or create) the SQLite database
    const db = new Database("main.db");

    // Create Anime table if it doesn't exist
    db.exec(`
      CREATE TABLE IF NOT EXISTS Anime (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
      )
    `);

    // Prepare an insert statement
    const insert = db.prepare("INSERT OR IGNORE INTO Anime (name) VALUES (?)");

    // Use a transaction for better performance
    const insertMany = db.transaction((animes) => {
      for (const anime of animes) {
        insert.run(anime);
      }
    });

    insertMany(animes);

    console.log("All anime titles inserted successfully!");
    db.close();
  } catch (error) {
    console.error(error);
  }
}

main();
