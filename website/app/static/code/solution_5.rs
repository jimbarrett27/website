use std::{fs, collections::HashSet};

const DATA_PATH: &str = "app/static/data/advent_of_code/day_5.txt";

fn string_is_nice_1(s: &str) -> bool {
    
    let mut vowel_count: i32 = 0;
    let mut double_letters: bool = false;
    let mut bad_combo: bool = false;
    for i in 0usize..s.len() {
        let c = s.chars().nth(i).unwrap();
        match c {
            'a' | 'e' | 'i' | 'o' | 'u' => vowel_count += 1,
            _ => ()
        }
        if i > 0 {
            let previous_char: char = s.chars().nth(i-1).unwrap();
            if c == previous_char {double_letters = true};

            if (c == 'b') & (previous_char == 'a') {bad_combo = true};
            if (c == 'd') & (previous_char == 'c') {bad_combo = true};
            if (c == 'q') & (previous_char == 'p') {bad_combo = true};
            if (c == 'y') & (previous_char == 'x') {bad_combo = true};
        }
    }
    (vowel_count > 2) & double_letters & (!bad_combo)
}

pub fn part_1() -> i32 {
    let input = fs::read_to_string(DATA_PATH).expect("Unable to read file");
    let lines: Vec<&str> = input.split('\n').collect();
    let mut total_nice: i32 = 0;
    for line in lines {
        if string_is_nice_1(line) {total_nice += 1};
    }

    total_nice
}

fn string_is_nice_2(s: &str) -> bool {
    
    let mut one_letter_gap_pairs: bool = false;
    let mut double_pair: bool = false;
    let mut previous_combo: (char, char) = ('0','0');
    let mut seen_pairs: HashSet<(char, char)> = HashSet::new();
    for i in 0usize..s.len() {
        let c = s.chars().nth(i).unwrap();
        
        if i > 0 {
            let previous_char: char = s.chars().nth(i-1).unwrap();
            let pair: (char, char) = (previous_char,c);
            if pair != previous_combo {
                if seen_pairs.contains(&pair) {double_pair = true};
                seen_pairs.insert(pair);
                previous_combo = pair;
            }
            else {previous_combo = ('0','0')}
        }

        if i > 1 {
            let two_letters_back: char = s.chars().nth(i-2).unwrap();
            if c == two_letters_back {one_letter_gap_pairs = true};

        }
    }

    double_pair & one_letter_gap_pairs
}

pub fn part_2() -> i32 {
    let input = fs::read_to_string(DATA_PATH).expect("Unable to read file");
    let lines: Vec<&str> = input.split('\n').collect();
    let mut total_nice: i32 = 0;
    for line in lines {
        if string_is_nice_2(line) {total_nice += 1};
    }

    total_nice
}