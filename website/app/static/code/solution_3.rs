use std::collections::HashSet;
use std::fs;

const DATA_PATH: &str = "app/static/data/advent_of_code/day_3.txt";

pub fn part_1() -> i32 {

    let input = fs::read_to_string(DATA_PATH).expect("Unable to read file");

    let mut visited_points: HashSet<(i32, i32)> = HashSet::new();
    visited_points.insert((0,0));
    let mut current_pos: Vec<i32> = vec![0,0];

    for c in input.chars() {
        match c {
            '>' => current_pos[0] += 1,
            '^' => current_pos[1] += 1,
            '<' => current_pos[0] -= 1,
            'v' => current_pos[1] -= 1,
            _ => ()
        }

        visited_points.insert((current_pos[0], current_pos[1]));
    }

    visited_points.len() as i32

}

pub fn part_2() -> i32 {

    let input = fs::read_to_string(DATA_PATH).expect("Unable to read file");

    let mut visited_points: HashSet<(i32, i32)> = HashSet::new();
    visited_points.insert((0,0));
    
    let mut current_pos: [Vec<i32>; 2] = [vec![0,0], vec![0,0]];

    let mut santas_turn: bool = true;

    for c in input.chars() {
        
        let index: usize = if santas_turn {0} else {1};

        match c {
            '>' => current_pos[index][0] += 1,
            '^' => current_pos[index][1] += 1,
            '<' => current_pos[index][0] -= 1,
            'v' => current_pos[index][1] -= 1,
            _ => ()
        }

        visited_points.insert((current_pos[index][0], current_pos[index][1]));
        santas_turn = !santas_turn;
    }

    visited_points.len() as i32

}