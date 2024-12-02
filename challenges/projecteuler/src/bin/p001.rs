// Find the sum of all the multiples of 3 or 5 below 1000.

fn main() {
    println!("{}", sum_multiples_of_3_5(1000))
}

fn sum_multiples_of_3_5(target: u32) -> u32 {
    let mut sum = 0;
    for number in 1..target {
        if number % 3 == 0 || number % 5 == 0 {
            sum += number
        };
    }

    sum
}
