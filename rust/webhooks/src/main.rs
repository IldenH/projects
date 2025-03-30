use serde::{Deserialize, Serialize};
use warp::Filter;

#[derive(Debug, Serialize, Deserialize)]
struct WebHookPayload {
    event: String,
    data: serde_json::Value,
}

#[tokio::main]
async fn main() {
    let webhook_route = warp::post()
        .and(warp::path("webhook"))
        .and(warp::body::json())
        .map(|payload: WebHookPayload| {
            println!("{:?}", payload);
            warp::reply::json(&payload)
        });

    println!("Listening on http://127.0.0.1:3030/webhook");
    warp::serve(webhook_route).run(([127, 0, 0, 1], 3030)).await;
}
