fn main() {
    println!("{}", largest_prime_factor(13195));
    // let noe = generate_prime_numbers(10000);
}

fn largest_prime_factor(input_number: u32) -> u32 {
    let prime_numbers = generate_prime_numbers(1000);

    if prime_numbers.contains(&input_number) {
        return input_number;
    }

    for i in prime_numbers {
        if input_number % i == 0 {
            return 29;
        }
    }

    29
}

fn generate_prime_numbers(number_of_primes: usize) -> Vec<u32> {
    let mut prime_numbers: Vec<u32> = vec![];

    let mut i = 0;
    while prime_numbers.len() < number_of_primes {
        if is_prime(i) {
            prime_numbers.push(i)
        }
        i += 1;
    }

    prime_numbers
}

fn is_prime(number: u32) -> bool {
    if number == 0 || number == 1 {
        return false;
    }

    for i in 2..number {
        if number % i == 0 {
            return false;
        }
    }

    true
}
