use std::collections::HashMap;

fn main() {
    let number_words = generate_map();

    let mut sum = 0;
    for value in number_words.values() {
        sum += value.len();
    }
    dbg!(sum);
}

fn generate_map() -> HashMap<usize, String> {
    let mut number_words: HashMap<usize, String> = HashMap::new();
    number_words.insert(0, "".to_string());
    number_words.insert(1, "one".to_string());
    number_words.insert(2, "two".to_string());
    number_words.insert(3, "three".to_string());
    number_words.insert(4, "four".to_string());
    number_words.insert(5, "five".to_string());
    number_words.insert(6, "six".to_string());
    number_words.insert(7, "seven".to_string());
    number_words.insert(8, "eight".to_string());
    number_words.insert(9, "nine".to_string());
    number_words.insert(10, "ten".to_string());
    number_words.insert(11, "eleven".to_string());
    number_words.insert(12, "twelve".to_string());
    number_words.insert(13, "thirteen".to_string());
    number_words.insert(14, "fourteen".to_string());
    number_words.insert(15, "fifteen".to_string());
    number_words.insert(16, "sixteen".to_string());
    number_words.insert(17, "seventeen".to_string());
    number_words.insert(18, "eighteen".to_string());
    number_words.insert(19, "nineteen".to_string());
    number_words.insert(20, "twenty".to_string());
    number_words.insert(30, "thirty".to_string());
    number_words.insert(40, "forty".to_string());
    number_words.insert(50, "fifty".to_string());
    number_words.insert(60, "sixty".to_string());
    number_words.insert(70, "seventy".to_string());
    number_words.insert(80, "eighty".to_string());
    number_words.insert(90, "ninety".to_string());
    number_words.insert(100, "hundred".to_string());
    number_words.insert(1000, "onethousand".to_string());

    for number in 20..100 {
        let tens: usize = number / 10;

        let word: String =
            number_words[&(tens * 10)].clone() + &number_words[&(number - tens * 10)];

        number_words.insert(number, word.clone());
    }

    for number in 101..1000 {
        let hundreds: usize = number / 100;

        let word: String = number_words[&hundreds].clone()
            + &number_words[&100].clone()
            + "and"
            + &number_words[&(number - hundreds * 100)];

        number_words.insert(number, word.clone());
    }

    number_words
}
