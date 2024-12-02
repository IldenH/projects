// By considering the terms in the Fibonacci sequence whose values do not exceed four million, find the sum of the even-valued terms.

fn main() {
    println!("{}", even_fibonacci_numbers(4000000))
}

fn even_fibonacci_numbers(target: u32) -> u32 {
    let mut numbers = vec![1, 2];
    for i in 2.. {
        if numbers[numbers.len() - 1] > target {
            break;
        }
        numbers.push(numbers[i - 2] + numbers[i - 1]);
    }

    let mut sum = 0;
    for number in numbers {
        if number % 2 == 0 {
            sum += number;
        }
    }

    sum
}
