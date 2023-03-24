use std::fs;

const DATA_PATH: &str = "app/static/data/advent_of_code/day_2.txt";

pub fn part_1() -> i32 {
    let input = fs::read_to_string(DATA_PATH).expect("Unable to read file");

    let mut total_paper: i32 = 0;
    for line in input.split('\n') {
        let mut sorted_dims: Vec<i32> = line.split('x').map(|x| x.parse().unwrap()).collect();
        sorted_dims.sort();

        total_paper += 2
            * (sorted_dims[0] * sorted_dims[1]
                + sorted_dims[0] * sorted_dims[2]
                + sorted_dims[1] * sorted_dims[2]);
        total_paper += sorted_dims[0] * sorted_dims[1];
    }

    total_paper
}

pub fn part_2() -> i32 {
    let input = fs::read_to_string(DATA_PATH).expect("Unable to read file");

    let mut total_ribbon: i32 = 0;
    for line in input.split('\n') {
        let mut sorted_dims: Vec<i32> = line.split('x').map(|x| x.parse().unwrap()).collect();
        sorted_dims.sort();

        total_ribbon += 2*(sorted_dims[0] + sorted_dims[1]);
        total_ribbon += sorted_dims[0] * sorted_dims[1] * sorted_dims[2];
    }

    total_ribbon
}
