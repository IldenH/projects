import express from "express";
import Database from "better-sqlite3";
import cors from "cors";

const app = express();
const PORT = 3000;
const db = new Database("fjelltur.db");
app.use(cors());

app.get("/api/alle_fjell", (req, res) => {
  const rows = db.prepare("SELECT * FROM fjell").all();
  res.json(rows);
});

app.get("/api/bilder/:turId", (req, res) => {
  const turId = req.params.turId;
  const rows = db
    .prepare(
      `
select
    bilde.tittel,
    bilde.bildetekst,
    bilde.filnavn
 from bilde
join fjelltur on fjelltur.fjelltur_id = bilde.tur_id
where tur_id == ?
;
`,
    )
    .all(turId);
  res.json(rows);
});

app.get("/api/fjellturer", (req, res) => {
  const rows = db
    .prepare(
      `
select
    fjelltur_id,
    tidspunkt,
    varighet,
    brukernavn,
    fornavn,
    etternavn,
    epost,
    fjellnavn,
    hoyde,
    fjelltur.beskrivelse as tur_beskrivelse,
    fjell.beskrivelse as fjell_beskrivelse,
    omraade.navn as omraade_navn,
    omraade.beskrivelse as omraade_beskrivelse
from fjelltur
join person using (brukernavn)
join fjell using (fjell_id)
join omraade on fjell.omraade_id = omraade.id
;
      `,
    )
    .all();
  res.json(rows);
});

app.listen(PORT, () => {
  console.log(`Running on http://127:0.0.1:${PORT}`);
});
