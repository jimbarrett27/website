use std::cmp;
use std::fs;

const DATA_PATH: &str = "app/static/data/advent_of_code/day_6.txt";

fn unpack_coords(word: &str) -> (usize, usize) {
    let coords: Vec<usize> = word.split(',').map(|x| x.parse().unwrap()).collect();
    (coords[0], coords[1])
}

pub fn part_1() -> i32 {
    let input = fs::read_to_string(DATA_PATH).expect("Unable to read file");
    let lines: Vec<&str> = input.split('\n').collect();

    let mut lights: [[bool; 1000]; 1000] = [[false; 1000]; 1000];

    for line in lines {
        let words: Vec<&str> = line.split(" ").collect();

        if words[0] == "toggle" {
            let start_coords = unpack_coords(words[1]);
            let end_coords = unpack_coords(words[3]);

            for i in start_coords.0..end_coords.0 + 1 {
                for j in start_coords.1..end_coords.1 + 1 {
                    lights[i][j] = !lights[i][j];
                }
            }
        } else if words[1] == "on" {
            let start_coords = unpack_coords(words[2]);
            let end_coords = unpack_coords(words[4]);
            for i in start_coords.0..end_coords.0 + 1 {
                for j in start_coords.1..end_coords.1 + 1 {
                    lights[i][j] = true;
                }
            }
        } else if words[1] == "off" {
            let start_coords = unpack_coords(words[2]);
            let end_coords = unpack_coords(words[4]);
            for i in start_coords.0..end_coords.0 + 1 {
                for j in start_coords.1..end_coords.1 + 1 {
                    lights[i][j] = false;
                }
            }
        } else {
            continue;
        }
    }

    let mut total: i32 = 0;
    for i in 0usize..1000 {
        for j in 0usize..1000 {
            if lights[i][j] {
                total += 1
            };
        }
    }

    total
}

pub fn part_2() -> i32 {
    let input = fs::read_to_string(DATA_PATH).expect("Unable to read file");
    let lines: Vec<&str> = input.split('\n').collect();

    let mut lights: [[i32; 1000]; 1000] = [[0; 1000]; 1000];

    for line in lines {
        let words: Vec<&str> = line.split(" ").collect();

        if words[0] == "toggle" {
            let start_coords = unpack_coords(words[1]);
            let end_coords = unpack_coords(words[3]);

            for i in start_coords.0..end_coords.0 + 1 {
                for j in start_coords.1..end_coords.1 + 1 {
                    lights[i][j] += 2;
                }
            }
        } else if words[1] == "on" {
            let start_coords = unpack_coords(words[2]);
            let end_coords = unpack_coords(words[4]);
            for i in start_coords.0..end_coords.0 + 1 {
                for j in start_coords.1..end_coords.1 + 1 {
                    lights[i][j] += 1;
                }
            }
        } else if words[1] == "off" {
            let start_coords = unpack_coords(words[2]);
            let end_coords = unpack_coords(words[4]);
            for i in start_coords.0..end_coords.0 + 1 {
                for j in start_coords.1..end_coords.1 + 1 {
                    lights[i][j] = cmp::max(lights[i][j] - 1, 0);
                }
            }
        } else {
            continue;
        }
    }

    let mut total: i32 = 0;
    for i in 0usize..1000 {
        for j in 0usize..1000 {
            total += lights[i][j];
        }
    }

    total
}
