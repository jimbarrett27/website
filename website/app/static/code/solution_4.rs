use md5::{self, Digest};

pub fn part_1() -> i32 {
    let puzzle_input: String = String::from("bgvyzdsv");

    let mut i: i32 = 100000;
    loop {
        let numbers: String = i.to_string();
        let full_input: String = puzzle_input.clone() + &numbers;

        let digest: Digest = md5::compute(full_input.as_bytes());
        let as_str = format!("{:?}", digest);

        let x = &as_str[..5];

        if *x == String::from("00000") {
            break;
        }

        i += 1;
    }

    i
}

pub fn part_2() -> i32 {
    let puzzle_input: String = String::from("bgvyzdsv");

    let mut i: i32 = 100000;
    loop {
        let numbers: String = i.to_string();
        let full_input: String = puzzle_input.clone() + &numbers;

        let digest: Digest = md5::compute(full_input.as_bytes());
        let as_str = format!("{:?}", digest);

        let x = &as_str[..6];

        if *x == String::from("000000") {
            break;
        }

        i += 1;
    }

    i
}
