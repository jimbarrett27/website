use std::fs;
use std::collections::{HashMap, HashSet};

const DATA_PATH: &str = "app/static/data/advent_of_code/day_7.txt";

fn resolve_signal(instructions: &Vec<&str>) -> i32 {

    let mut instructions = instructions.clone();
    let mut signals: HashMap<&str, u16> = HashMap::new();
    
    loop {

        let instruction = instructions.pop().unwrap();
        let words: Vec<&str> = instruction.split(" ").collect();

        let to_signal = words[words.len() - 1]; 
        
        if words[0] == "NOT" {
            let from_signal = words[1];
            if !signals.contains_key(from_signal) {
                instructions.insert(0, instruction);
                continue;
            }

            signals.insert(to_signal, !signals.get(from_signal).unwrap()); 
        }

        if (words[1] == "RSHIFT") || (words[1] == "LSHIFT") {
            let from_signal = words[0];
            if !signals.contains_key(from_signal) {
                instructions.insert(0, instruction);
                continue;
            }

            let signal = signals.get(from_signal).unwrap();
            let shift_amount: u16 = words[2].parse().unwrap();

            match words[1] {
                "RSHIFT" => signals.insert(to_signal, signal >> shift_amount),
                "LSHIFT" => signals.insert(to_signal, signal << shift_amount),
                _ => None
            };
            
        }
        
        if (words[1] == "AND") || (words[1] == "OR") {
            let from_signal_1 = words[0];
            let from_signal_2 = words[2];
            
            if !signals.contains_key(from_signal_2)  {
                instructions.insert(0, instruction);
                continue;
            }
            if !signals.contains_key(from_signal_1) &&  !words[0].parse::<u16>().is_ok()  {
                instructions.insert(0, instruction);
                continue;
            }

            let mut signal_1;
            if signals.contains_key(from_signal_1) {
                signal_1 = signals.get(from_signal_1).unwrap();
            }
            else {
                signal_1 = &1;
            }
            
            let signal_2 = signals.get(from_signal_2).unwrap();
            match words[1] {
                "AND" => signals.insert(to_signal, signal_1 & signal_2),
                "OR" => signals.insert(to_signal, signal_1 | signal_2),
                _ => None
            }; 
        }

        if words[1] == "->" {
            if words[0].parse::<u16>().is_ok() {
                let val: u16 = words[0].parse().unwrap();
                signals.insert(to_signal, val);
            }
            else {
                
                let from_signal = words[0];
                if !signals.contains_key(from_signal) {
                    instructions.insert(0, instruction);
                    continue;
                }
                signals.insert(to_signal, *signals.get(from_signal).unwrap());
            }
        }

        if instructions.is_empty() {
            break;
        }

        
    }

    signals["a"] as i32
}

pub fn part_1() -> i32 {

    let input = fs::read_to_string(DATA_PATH).expect("Unable to read file");

    let instructions: Vec<&str> = input.split('\n').collect();

    let signal: i32 = resolve_signal(&instructions);
    
    signal
}

pub fn part_2() -> i32 {

    let input = fs::read_to_string(DATA_PATH).expect("Unable to read file");

    let instructions: Vec<&str> = input.split('\n').collect();
    let signal: i32 = resolve_signal(&instructions);

    let mut new_instructions: Vec<&str> = instructions.clone();
    for i in 0..new_instructions.len() {
        if new_instructions[i].ends_with("-> b") {
            new_instructions.remove(i);
            break;
        }
    }
    let new_instruction: &str = &format!("{:?} -> b", signal);
    new_instructions.push(new_instruction);

    let new_signal: i32 = resolve_signal(&new_instructions);
    
    new_signal
}