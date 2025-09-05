use rusqlite::{Connection, Result};

#[derive(Debug)]
pub struct Row {
    line: String,
    stop: String,
    aimed_departure: u64,
    actual_departure: u64,
}

pub fn create_db() -> Result<()> {
    let conn = Connection::open_in_memory()?;

    conn.execute(
        "CREATE TABLE row (
            id  INTEGER PRIMARY KEY,
            line  TEXT NOT NULL,
            stop  TEXT NOT NULL,
            aimed_departure  INTEGER,
            actual_departure  INTEGER
        )",
        (),
    )?;
    let example_row = Row {
        line: String::from("123"),
        stop: String::from("Uti skauen"),
        aimed_departure: 1757059868,
        actual_departure: 1757060068,
    };
    conn.execute(
        "INSERT INTO row (line, stop, aimed_departure, actual_departure) VALUES (?1, ?2, ?3, ?4)",
        (
            &example_row.line,
            &example_row.stop,
            &example_row.aimed_departure,
            &example_row.actual_departure,
        ),
    )?;
    let mut stmt = conn.prepare("SELECT line, stop, aimed_departure, actual_departure FROM row")?;
    let row_iter = stmt.query_map([], |row| {
        Ok(Row {
            line: row.get(0)?,
            stop: row.get(1)?,
            aimed_departure: row.get(2)?,
            actual_departure: row.get(3)?,
        })
    })?;
    for row in row_iter {
        println!("{:?}", row.unwrap())
    }

    Ok(())
}
