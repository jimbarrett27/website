use std::fs;
use regex::Regex;

const DATA_PATH: &str = "app/static/data/advent_of_code/day_8.txt";

pub fn part_1() -> i32 {
    let input = fs::read_to_string(DATA_PATH).expect("Unable to read file");

    let lines: Vec<&str> = input.split('\n').collect();

    let mut code_characters_total: i32 = 0;
    let mut string_characters_total: i32 = 0;
    let re = Regex::new(r#"\\"|\\\\|\\x[\da-f]{2}"#).unwrap();
    for line in lines {

        code_characters_total += line.len() as i32;
        string_characters_total += line.len() as i32 -2;
        
        for matched_str in re.captures_iter(line){
            string_characters_total -= matched_str[0].len() as i32 - 1;

        }
    }
    
    (code_characters_total - string_characters_total) as i32
}

pub fn part_2() -> i32 {
    let input = fs::read_to_string(DATA_PATH).expect("Unable to read file");

    let lines: Vec<&str> = input.split('\n').collect();

    let mut code_characters_total: i32 = 0;
    let mut string_characters_total: i32 = 0;
    let re = Regex::new(r#""|\\"#).unwrap();
    for line in lines {

        string_characters_total += line.len() as i32 + 2;
        code_characters_total += line.len() as i32;

        
        for _ in re.captures_iter(line){
            string_characters_total += 1;

        }
    }
    
    (string_characters_total - code_characters_total) as i32
}