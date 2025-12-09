fn main() {
    dbg!(tverrsum_prime_numbers(10_000).iter().sum::<u64>());
}

fn tverrsum_prime_numbers(goal: usize) -> Vec<u64> {
    let mut tverrsum_prime_numbers: Vec<u64> = vec![];
    let primes = prime_numbers(500_000);
    let mut number = 1;

    while tverrsum_prime_numbers.len() < goal {
        if is_prime(number) {
            let index = primes.iter().position(|&x| x == number).unwrap() + 1;
            if tverrsum(number) == tverrsum(index as u64) {
                tverrsum_prime_numbers.push(number);
            }
        }
        number += 2;
    }

    tverrsum_prime_numbers
}

fn prime_numbers(goal: usize) -> Vec<u64> {
    let mut prime_numbers: Vec<u64> = vec![2];
    let mut current_number: u64 = 1;

    while prime_numbers.len() < goal {
        if is_prime(current_number) {
            prime_numbers.push(current_number);
        }
        current_number += 2;
    }

    prime_numbers
}

fn tverrsum(number: u64) -> u64 {
    number
        .to_string()
        .chars()
        .map(|character| character.to_digit(10).unwrap() as u64)
        .sum::<u64>()
}

fn is_prime(number: u64) -> bool {
    if number < 2 {
        return false;
    }
    for i in 2..=((number as f64).sqrt() as u64) {
        if number % i == 0 {
            return false;
        }
    }
    true
}
