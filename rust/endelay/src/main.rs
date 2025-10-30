use quick_xml::de::from_str;
use reqwest::blocking::{Client, get};
use rusqlite::{Connection, params};
use serde::{Deserialize, Deserializer};
use serde_json::Value;
use std::io;
use std::io::Write;
use std::path::PathBuf;
use std::sync::Arc;
use std::sync::atomic::{AtomicBool, Ordering};
use std::thread;
use std::thread::sleep;
use std::time::Duration;
use time::OffsetDateTime;

#[derive(Debug, Deserialize)]
struct TimestampText {
    #[serde(rename = "$text")]
    text: String,
}

fn deserialize_xml_timestamp<'de, D>(deserializer: D) -> Result<Option<OffsetDateTime>, D::Error>
where
    D: Deserializer<'de>,
{
    Option::<TimestampText>::deserialize(deserializer)?.map_or(Ok(None), |wrapper| {
        OffsetDateTime::parse(
            &wrapper.text,
            &time::format_description::well_known::Rfc3339,
        )
        .map(Some)
        .map_err(|e| serde::de::Error::custom(format!("Failed to parse OffsetDateTime: {e}")))
    })
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "PascalCase")]
struct Call {
    #[serde(default, deserialize_with = "deserialize_xml_timestamp")]
    aimed_departure_time: Option<OffsetDateTime>,
    #[serde(default, deserialize_with = "deserialize_xml_timestamp")]
    actual_departure_time: Option<OffsetDateTime>,
    stop_point_ref: String,
}

impl Call {
    fn delay(&self) -> Option<time::Duration> {
        Some(self.actual_departure_time? - self.aimed_departure_time?)
    }
}

#[derive(Debug, Deserialize)]
struct JourneyCalls {
    #[serde(rename = "RecordedCall")]
    calls: Vec<Call>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "PascalCase")]
struct Journey {
    #[serde(rename = "RecordedCalls")]
    calls: Option<JourneyCalls>,
    line_ref: String,
}

#[derive(Debug, Deserialize)]
struct Frame {
    #[serde(rename = "EstimatedVehicleJourney")]
    journeys: Option<Vec<Journey>>,
}

#[derive(Debug, Deserialize)]
struct TimetableDelivery {
    #[serde(rename = "EstimatedJourneyVersionFrame")]
    frame: Frame,
}

#[derive(Debug, Deserialize)]
struct ServiceDelivery {
    #[serde(rename = "EstimatedTimetableDelivery")]
    delivery: TimetableDelivery,
}

#[derive(Debug, Deserialize)]
struct Data {
    #[serde(rename = "ServiceDelivery")]
    delivery: ServiceDelivery,
}

fn get_stop_name(stop_ref: String) -> Result<String, Box<dyn std::error::Error>> {
    // https://developer.entur.org/stop-places-v1-read

    sleep(Duration::from_millis(50));
    let stop_place = get(format!(
        "https://api.entur.io/stop-places/v1/read/quays/{stop_ref}/stop-place"
    ))?
    .text()?;
    let data: Value = serde_json::de::from_str(&stop_place)?;

    Ok(data["name"]["value"].as_str().unwrap().to_string())
}

fn add_stop_names(conn: &Connection) -> rusqlite::Result<(), Box<dyn std::error::Error>> {
    let total: u32 = conn.query_row(
        "SELECT COUNT(*) FROM stop WHERE stop_name IS NULL",
        [],
        |row| row.get(0),
    )?;

    let mut stmt = conn.prepare("SELECT * FROM stop WHERE stop_name IS NULL")?;
    let mut count = 0;
    let stops = stmt.query_map([], |row| {
        let id: u64 = row.get(0)?;
        let stop_ref: String = row.get(1)?;
        let stop_name = get_stop_name(stop_ref).unwrap_or_default();
        println!("\r{count}/{total}\t{stop_name}");
        io::stdout().flush().unwrap();
        count += 1;
        Ok((id, stop_name))
    })?;
    for stop in stops {
        let (id, stop_name) = stop?;
        conn.execute(
            "UPDATE stop SET stop_name = ?1 WHERE id = ?2",
            params![stop_name, id],
        )?;
    }
    Ok(())
}

fn get_or_insert_id(
    conn: &Connection,
    table: &str,
    col: &str,
    value: &str,
) -> rusqlite::Result<u64, Box<dyn std::error::Error>> {
    conn.execute(
        &format!("INSERT OR IGNORE INTO {} ({}) VALUES (?1)", table, col),
        params![value],
    )?;
    let id = conn.query_row(
        &format!("SELECT id FROM {} WHERE {} = ?1", table, col),
        params![value],
        |row| row.get(0),
    )?;

    Ok(id)
}

fn fetch_and_insert(
    conn: &mut Connection,
    client: &Client,
) -> rusqlite::Result<(), Box<dyn std::error::Error>> {
    dotenvy::dotenv()?;
    let requestor_id = std::env::var("REQUESTOR_ID").expect("Error getting REQUESTOR_ID env var");
    let resp = client
        .get(format!(
            "https://api.entur.io/realtime/v1/rest/et?requestorId={requestor_id}"
        ))
        .send()?;
    if resp.status() == reqwest::StatusCode::TOO_MANY_REQUESTS {
        let now: OffsetDateTime = std::time::SystemTime::now().into();
        eprintln!("{now}: 429 rate limited");
        dbg!(resp.headers());
        return Ok(());
    }
    let xml = resp.text()?;
    let data: Data = from_str(&xml).map_err(|err| {
        let preview: String = xml.chars().take(1000).collect();
        eprintln!("{err:?}");
        eprintln!("{preview}");
        err
    })?;
    let journeys = match data.delivery.delivery.frame.journeys {
        Some(j) => j,
        None => return Ok(()),
    };

    let tx = conn.transaction()?;
    {
        let mut stmt = tx.prepare("INSERT OR IGNORE INTO call (line_id, stop_id, delay, aimed_departure, actual_departure) VALUES (?1, ?2, ?3, ?4, ?5)")?;

        for journey in journeys
            .iter()
            .filter(|j| j.calls.as_ref().map_or(false, |v| !v.calls.is_empty()))
        {
            let line_id = get_or_insert_id(&tx, "line", "line", &journey.line_ref)?;

            if let Some(calls) = &journey.calls {
                for call in &calls.calls {
                    let stop_id = get_or_insert_id(&tx, "stop", "stop_ref", &call.stop_point_ref)?;
                    if let (Some(delay), Some(aimed), Some(actual)) = (
                        &call.delay(),
                        &call.aimed_departure_time,
                        &call.actual_departure_time,
                    ) {
                        stmt.execute(params![
                            line_id,
                            stop_id,
                            delay.whole_seconds(),
                            aimed.unix_timestamp(),
                            actual.unix_timestamp(),
                        ])?;
                    }
                }
            }
        }
        // add_stop_names(&tx)?; // too slow :(
    }
    tx.commit()?;

    Ok(())
}

fn main() -> rusqlite::Result<(), Box<dyn std::error::Error>> {
    let db_path = dirs_next::data_dir()
        .expect("Failed to get data dir")
        .join("endelay/db.db");
    std::fs::create_dir_all(db_path.parent().unwrap()).expect("Failed to create db dir");

    let mut conn = Connection::open(db_path)?;
    conn.pragma_update(None, "journal_mode", &"WAL")?;
    conn.pragma_update(None, "synchronous", &"NORMAL")?;
    conn.execute_batch(
        "
        CREATE TABLE IF NOT EXISTS line (
            id INTEGER PRIMARY KEY,
            line TEXT NOT NULL UNIQUE
        );
        CREATE TABLE IF NOT EXISTS stop (
            id INTEGER PRIMARY KEY,
            stop_ref TEXT NOT NULL UNIQUE,
            stop_name TEXT
        );
        CREATE TABLE IF NOT EXISTS call (
            id INTEGER PRIMARY KEY,
            line_id INTEGER NOT NULL,
            stop_id INTEGER NOT NULL,
            delay INTEGER NOT NULL,
            aimed_departure INTEGER NOT NULL,
            actual_departure INTEGER NOT NULL,
            FOREIGN KEY(line_id) REFERENCES line(id),
            FOREIGN KEY(stop_id) REFERENCES stop(id),
            UNIQUE(line_id, stop_id, delay, aimed_departure, actual_departure)
        );",
    )?;

    let running = Arc::new(AtomicBool::new(true));
    let r = running.clone();

    thread::spawn(move || {
        let mut input = String::new();
        loop {
            input.clear();
            if io::stdin().read_line(&mut input).is_ok() {
                if input.trim() == "q" {
                    r.store(false, Ordering::SeqCst);
                    break;
                }
            }
        }
    });

    let now: OffsetDateTime = std::time::SystemTime::now().into();
    println!("{now} Running. Type 'q' + Enter to quit.");

    let client = Client::new();
    while running.load(Ordering::SeqCst) {
        let now: OffsetDateTime = std::time::SystemTime::now().into();
        if let Err(e) = fetch_and_insert(&mut conn, &client) {
            eprintln!("{now}: {e:?}",)
        };

        let sleep_until = now + Duration::from_secs(16);
        while now < sleep_until {
            if !running.load(Ordering::SeqCst) {
                break;
            }
            sleep(Duration::from_millis(100));
        }
    }

    conn.execute_batch("PRAGMA optimize; PRAGMA wal_checkpoint(TRUNCATE);")?;

    Ok(())
}
