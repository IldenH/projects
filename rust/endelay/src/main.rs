use quick_xml::de::from_str;
use rusqlite::{Connection, Result, params};
use serde::{Deserialize, Deserializer};
use serde_json::Value;
use std::collections::HashMap;
use std::fs::read_to_string;
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

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut conn = Connection::open("./db.db")?;
    conn.execute(
        "CREATE TABLE IF NOT EXISTS call (
            id  INTEGER PRIMARY KEY,
            line  TEXT NOT NULL,
            stop  TEXT NOT NULL,
            delay INTEGER NOT NULL,
            aimed_departure  INTEGER NOT NULL,
            actual_departure  INTEGER NOT NULL
        )",
        (),
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
        let mut stmt = tx.prepare("INSERT INTO call (line, stop, delay, aimed_departure, actual_departure) VALUES (?1, ?2, ?3, ?4, ?5)")?;

        for journey in journeys
            .iter()
            .filter(|j| j.calls.as_ref().map_or(false, |v| !v.calls.is_empty()))
        {
            if let Some(calls) = &journey.calls {
                for call in &calls.calls {
                    // let stop_place = ureq::get(format!(
                    //     "https://api.entur.io/stop-places/v1/read/quays/{}/stop-place",
                    //     call.stop_point_ref
                    // ))
                    // .call()?
                    // .body_mut()
                    // .read_to_string()?;
                    // let data: Value = serde_json::de::from_str(&stop_place)?;
                    // let stop_point_name = &data["name"]["value"].as_str().unwrap();
                    if let (Some(delay), Some(aimed), Some(actual)) = (
                        &call.delay(),
                        &call.aimed_departure_time,
                        &call.actual_departure_time,
                    ) {
                        stmt.execute(params![
                            journey.line_ref,
                            call.stop_point_ref,
                            delay.whole_seconds(),
                            aimed.unix_timestamp(),
                            actual.unix_timestamp(),
                        ])?;
                    }
                }
            }
        }
    }
    tx.commit()?;

    conn.execute_batch("VACUUM; PRAGMA optimize;")?;

    Ok(())
}
