#![feature(cstr_memory2)]
#![allow(dead_code, deprecated, unused_imports)]

extern crate libc;
extern crate rand as random;
extern crate rustc_serialize as serialize;

mod cipher;

use cipher::{Mode, zombify};
use std::ffi::{CStr, CString};
use std::fs::File;
use std::io::Read;
use std::sync::mpsc;
use std::{str, slice, thread};
use libc::{size_t, c_char};

// You'll be needing Nightly rust, because `from_ptr` for C-types is unstable and deprecated

#[no_mangle]
// FFI function just to kill a transferred pointer
pub extern fn kill_pointer(p: *const c_char) {
    unsafe { CString::from_ptr(p) };     // Theoretically, Rust should take the ownership back
}   // variable goes out of scope here and the C-type string should be destroyed

#[no_mangle]
// FFI function to be called from Python (I've commented out some of the methods I'd tried)
pub extern fn get_stuff(array: *const *const c_char, length: size_t) -> *const c_char {
    // get the raw pointer values to the strings from the array pointer
    let array = unsafe { slice::from_raw_parts(array, length as usize) };
    let mut stuff: Vec<&str> = array.iter()
        .map(|&p| unsafe { CStr::from_ptr(p) })         // get the C-type string from the pointer
        .map(|c_string| c_string.to_bytes())            // convert the raw thing to bytes
        .map(|byte| str::from_utf8(byte).unwrap())      // finally collect the corresponding strings
        .collect();
    let word = stuff.pop().unwrap();
    let key = stuff.pop().unwrap();

    // // pure iteration (decreases the time by a factor of 50 ± 10)
    // let occurrences = stuff
    //                   .iter()
    //                   .map(|file_name| count_words(&file_name, &key, &word))
    //                   .collect::<Vec<String>>();

    // // basic concurrency - threads (decreases the time by a factor of 65 ± 10)
    // let threads: Vec<_> = stuff
    //                       .into_iter()
    //                       .enumerate()
    //                       .map(|(idx, file_name)| {
    //                           thread::spawn(move || (idx, count_words(&file_name, &key, &word)))
    //                       }).collect();
    // let mut result: Vec<_> = threads
    //                          .into_iter()
    //                          .map(|handle| handle.join().unwrap())
    //                          .collect();

    // channels show more or less the same performance (decrease the time by a factor of 80 ± 10)
    let (tx, rx) = mpsc::channel();
    let threads: Vec<_> = stuff
                          .into_iter()
                          .enumerate()
                          .map(|(idx, file_name)| {
                              let tx = tx.clone();
                              thread::spawn(move || {
                                  tx.send((idx, count_words(&file_name, &key, &word))).unwrap()
                              })
                          }).collect();
    let mut result: Vec<(usize, String)> = threads
                                           .iter()
                                           .map(|_| rx.recv().unwrap())
                                           .collect();

    // sorting and remapping is necessary for output from threads (because they come in randomly)
    result.sort_by(|&(idx_1, _), &(idx_2, _)| idx_1.cmp(&idx_2));
    let occurrences: Vec<String> = result
                                   .iter()
                                   .map(|&(_, ref string)| string.clone())
                                   .collect();

    let count_string = occurrences.join(" ");
    CString::new(count_string).unwrap().into_ptr()      // the FFI code should now own the memory
}

// Gives a tuple of a file's size and a vector of its contents
fn fopen(path: &str) -> (usize, Vec<u8>) {
    let file = File::open(path);
    let mut contents: Vec<u8> = Vec::new();
    // of course, assuming that there won't be any problem in reading the file
    let file_size = file.unwrap().read_to_end(&mut contents).unwrap();
    (file_size, contents)
}

// Checks if the big vector contains the small vector slice and returns a string of indices
fn search(text_vec: &[u8], word: &str) -> String {
    // We're safe here, because we've already filtered the "failure" case
    let mut text = &*(String::from_utf8_lossy(text_vec));
    let mut indices = Vec::new();
    let mut idx = 0;
    let (limit, jump) = (text.len() - 1, word.len());
    while let Some(i) = text.find(word) {       // FIXME: I don't think this is efficient
        idx += i;
        indices.push(idx.to_string());
        idx += jump;
        match idx >= limit {
            true => break,
            false => text = &text[(i + jump)..],
        }
    }
    match indices.is_empty() {
        true => "0".to_owned(),
        false => indices.join(":"),
    }
}

// This just decrypts the file and counts the word in it (just to simplify things)
fn count_words(file_name: &str, key: &str, word: &str) -> String {
    let contents = fopen(&file_name).1;
    let decrypted = zombify(Mode::Decrypt, &contents, key);
    if decrypted.is_empty() {
        println!("\nCannot decrypt the story! (filepath: {})", file_name);
        return "0".to_owned();
    } search(&decrypted, word)
}
