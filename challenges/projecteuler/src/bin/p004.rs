fn main() {
    println!("{}", is_palindrome(9009));
}

fn is_palindrome(input_number: u32) -> bool {
    let mut number = input_number;
    println!("{}", input_number / 1000);
    number -= (input_number / 1000);
    dbg!(number);
    println!("{}", number / 100);
    println!("{}", number / 1);
    number == 9009
}
