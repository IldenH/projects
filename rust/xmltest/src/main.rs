use quick_xml::de::from_str;
use serde::Deserialize;
use serde_json::Value;
use std::collections::HashMap;
use std::fs::read_to_string;

#[derive(Debug, Deserialize)]
#[serde(rename_all = "PascalCase")]
struct Call {
    // aimed_arrival_time: Option<String>,
    // arrival_status: String,
    // destination_display: String,
    // arrival_boarding_activity: String,
    // aimed_departure_time: String,
    // expected_departure_time: String,
    // expected_arrival_time: String,
    stop_point_name: Option<String>,
    // stop_point_ref: String,
    // #[serde(flatten)]
    // extra: HashMap<String, Value>,
}

#[derive(Debug, Deserialize)]
struct JourneyCalls {
    #[serde(rename = "EstimatedCall")]
    calls: Vec<Call>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "PascalCase")]
struct Journey {
    // #[serde(rename = "EstimatedCalls", alias = "RecordedCalls")]
    #[serde(rename = "EstimatedCalls")]
    calls: Option<JourneyCalls>,

    #[serde(rename = "PublishedLineName")]
    line_name: Option<String>,

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

fn main() {
    let xml = read_to_string("estimated_timetable.xml").unwrap();
    let data: Data = from_str(&xml).unwrap();
    let journeys = data.delivery.delivery.frame.journeys;
    // dbg!(&journeys);

    if let Some(journey) = journeys.iter().find(|j| {
        j.calls
            .as_ref()
            .map(|v| !v.calls.is_empty())
            .unwrap_or(false)
    }) {
        println!("{}", journey.line_name.as_ref().unwrap());
        for call in &journey.calls.as_ref().unwrap().calls {
            println!("\t{}", call.stop_point_name.as_ref().unwrap());
        }
    }
}
