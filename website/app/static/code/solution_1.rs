use std::fs;

const DATA_PATH: &str = "app/static/data/advent_of_code/day_1.txt";

pub fn part_1() -> i32 {
    let input = fs::read_to_string(DATA_PATH).expect("Unable to read file");

    let mut floor_count: i32 = 0;

    for c in input.chars() {
        match c {
            '(' => floor_count += 1,
            ')' => floor_count -= 1,
            _ => (),
        }
    }

    floor_count
}

pub fn part_2() -> i32 {
    let input = fs::read_to_string(DATA_PATH).expect("Unable to read file");

    let mut floor_count: i32 = 0;
    let mut char_count: i32 = 0;
    for c in input.chars() {
        char_count += 1;
        match c {
            '(' => floor_count += 1,
            ')' => floor_count -= 1,
            _ => floor_count += 0,
        }

        if floor_count == -1 {
            break;
        }
    }

    char_count
}
