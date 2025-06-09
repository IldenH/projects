use quick_xml::de::from_str;
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
    let timestamp_text_wrapper: Option<TimestampText> = Option::deserialize(deserializer)?;

    match timestamp_text_wrapper {
        Some(wrapper) => {
            match OffsetDateTime::parse(
                &wrapper.text,
                &time::format_description::well_known::Rfc3339,
            ) {
                Ok(odt) => Ok(Some(odt)),
                Err(e) => Err(serde::de::Error::custom(format!(
                    "Failed to parse OffsetDateTime: {e}"
                ))),
            }
        }
        None => Ok(None),
    }
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
    // #[serde(rename = "EstimatedCall", alias = "RecordedCall")]
    // #[serde(rename = "EstimatedCall")]
    #[serde(rename = "RecordedCall")]
    calls: Vec<Call>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "PascalCase")]
struct Journey {
    // #[serde(rename = "EstimatedCalls", alias = "RecordedCalls")]
    // #[serde(rename = "EstimatedCalls")]
    #[serde(rename = "RecordedCalls")]
    calls: Option<JourneyCalls>,

    #[serde(rename = "PublishedLineName")]
    line_name: Option<String>,
    line_ref: String,
    #[serde(rename = "OperatorRef")]
    operator: Option<String>,
    vehicle_mode: Option<String>,
    #[serde(deserialize_with = "deserialize_xml_timestamp")]
    recorded_at_time: Option<OffsetDateTime>,

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
    let xml = ureq::get("https://api.entur.io/realtime/v1/rest/et?datasetId=SKY")
        .call()?
        .body_mut()
        .read_to_string()?;
    // let xml = read_to_string("estimated_timetable.xml")?;
    let data: Data = from_str(&xml)?;
    let journeys = data.delivery.delivery.frame.journeys;
    // dbg!(&journeys);

    for journey in journeys.iter().filter(|j| {
        j.calls
            .as_ref()
            .map(|v| !v.calls.is_empty())
            .unwrap_or(false)
    }) {
        if !journey.line_ref.contains("SKY") {
            continue;
        }
        println!("{}\t{:?}", journey.line_ref, journey.recorded_at_time);
        for call in &journey.calls.as_ref().unwrap().calls {
            // let stop_place = ureq::get(format!(
            //     "https://api.entur.io/stop-places/v1/read/quays/{}/stop-place",
            //     call.stop_point_ref
            // ))
            // .call()?
            // .body_mut()
            // .read_to_string()?;
            // let data: Value = serde_json::de::from_str(&stop_place)?;
            // let stop_point_name = &data["name"]["value"].as_str().unwrap();
            if call.aimed_departure_time == None || call.actual_departure_time == None {
                println!("\t{}\tNone", call.stop_point_ref);
            } else {
                println!(
                    "\t{}\t{}, {:?}\t{:?}",
                    call.stop_point_ref,
                    call.delay().unwrap_or_default().whole_seconds(),
                    call.aimed_departure_time.unwrap().time(),
                    call.actual_departure_time.unwrap().time()
                );
            }
        }
    }

    Ok(())
}
