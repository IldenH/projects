use std::fs;

type Alv = Vec<Vec<u32>>;
type Teppe = Vec<Vec<bool>>;

fn main() {
    let alv =
        alv_vector(fs::read_to_string("joe.txt").expect("Should have been able to read the file"));
    let mut teppe = teppe_vector(
        fs::read_to_string("teppe.txt").expect("Should have been able to read the file"),
    );

    let mut sum: u32 = 0;
    for _ in 0..alv.len() {
        let mut temp_teppe = teppe.clone();

        for _ in 0..alv.len() {
            if calculate_score(alv.clone(), temp_teppe.clone()) > sum {
                sum = calculate_score(alv.clone(), temp_teppe.clone())
            }
            temp_teppe = move_x(temp_teppe);
        }

        teppe = move_y(teppe);
    }

    dbg!(sum);
}

fn calculate_score(alv: Alv, teppe: Teppe) -> u32 {
    let mut sum: u32 = 0;
    for (alv_row, teppe_row) in alv.iter().zip(teppe.iter()) {
        for (&alv_value, &teppe_value) in alv_row.iter().zip(teppe_row.iter()) {
            if teppe_value {
                sum += alv_value
            }
        }
    }

    sum
}

fn move_x(mut teppe: Teppe) -> Teppe {
    for row in &mut teppe {
        row.insert(0, false);
    }

    teppe
}

fn move_y(mut teppe: Teppe) -> Teppe {
    teppe.insert(0, vec![false, false, false, false, false]);

    teppe
}

fn teppe_vector(teppe_text: String) -> Teppe {
    let mut teppe: Teppe = vec![vec![]];
    let mut row: usize = 0;
    for character in teppe_text.chars() {
        if character == '\n' {
            row += 1;
            teppe.push(vec![])
        }
        if character == 'x' {
            teppe[row].push(true)
        } else if character == ' ' {
            teppe[row].push(false)
        }
    }
    teppe.pop();

    teppe
}

fn alv_vector(alv_text: String) -> Alv {
    let mut alv: Alv = vec![vec![]];
    let mut row: usize = 0;
    for character in alv_text.chars() {
        if character == '\n' {
            row += 1;
            alv.push(vec![])
        }
        if character.is_numeric() {
            alv[row].push(character.to_digit(10).expect("Should be a number"))
        } else if character == ' ' {
            alv[row].push(0);
        }
    }
    alv.pop();

    alv
}
