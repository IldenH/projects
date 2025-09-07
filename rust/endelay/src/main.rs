use quick_xml::de::from_str;
use rusqlite::{Connection, params};
use serde::{Deserialize, Deserializer};
use serde_json::Value;
use std::collections::HashMap;
use std::fs::read_to_string;
use std::io;
use std::io::Write;
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

    #[serde(flatten)]
    extra: HashMap<String, Value>,
}

impl Call {
    fn delay(&self) -> Option<time::Duration> {
        match (self.actual_departure_time, self.aimed_departure_time) {
            (Some(actual), Some(aimed)) => Some(actual - aimed),
            (None, _) => None,
            (_, None) => None,
        }
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

    #[serde(flatten)]
    extra: HashMap<String, Value>,
}

#[derive(Debug, Deserialize)]
struct Frame {
    #[serde(rename = "EstimatedVehicleJourney")]
    journeys: Vec<Journey>,
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
    let stop_place = ureq::get(format!(
        "https://api.entur.io/stop-places/v1/read/quays/{stop_ref}/stop-place"
    ))
    .call()?
    .body_mut()
    .read_to_string()?;
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
        let stop_name = get_stop_name(stop_ref).unwrap_or(String::from(""));
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

fn main() -> rusqlite::Result<(), Box<dyn std::error::Error>> {
    let mut conn = Connection::open("./db.db")?;
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
            FOREIGN KEY(stop_id) REFERENCES stop(id)
        );",
    )?;

    // let xml = ureq::get("https://api.entur.io/realtime/v1/rest/et?datasetId=SKY")
    //     .call()?
    //     .body_mut()
    //     .read_to_string()?;
    let xml = read_to_string("estimated_timetable.xml")?;
    let data: Data = from_str(&xml)?;
    let journeys = data.delivery.delivery.frame.journeys;

    let tx = conn.transaction()?;
    {
        let mut stmt = tx.prepare("INSERT INTO call (line_id, stop_id, delay, aimed_departure, actual_departure) VALUES (?1, ?2, ?3, ?4, ?5)")?;

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

    conn.execute_batch("VACUUM; PRAGMA optimize;")?;

    Ok(())
}
