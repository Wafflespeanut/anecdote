## Biographer (v0.5.0)

This is a little project of mine - a command-line utility to remember everyday memories.

It puts your stories (with a MD5-hashed filename) into a directory for later viewing. Once stored, it doesn't disturb the original story (unless you play around). It decrypts to a temporary file for viewing, which also gets deleted almost immediately. While updating the stories, it just appends your story to the previous story.

It supports some basic encryption. I've used a simple algorithm to hex and shift the ASCII values in the files, which is similar to a *hexed* 256-char Vigenere cipher using byte-wise XOR along with [cipher-block chaining](https://en.wikipedia.org/wiki/Block_cipher_mode_of_operation#Cipher_Block_Chaining_.28CBC.29) to introduce some *randomness* into the final ciphertext<sup>[1]</sup> (and, it can also detect incorrect passwords).

A local file has a SHA-256 hash of the original password, so that instead of typing the password every time you write/view some story, you can simply sign in, which asks you for a password only once per session *(of course!)*.

And, the cool part - you can search through your stories for a specific word (between a range of dates) either using Python (which takes some time, depending on the number of stories you have) or the provided Rust library (which amplifies the performance by a factor of ~200). But, it's a very basic search - it just looks for an exact match, and so it's case-sensitive).

Regarding cross-platforms, I've tested it on Windows 8 and Ubuntu, but I'm not sure about other OS (I guess it works for them just as well).

<sup>[1]: **It's not much secure!**, but that's not my goal either! We need confidentiality, not integrity. So, this is just to prevent people from peeking into the stories using text editors. Protecting the stories however, is *(always)* on your side. Well, if someone's really involved, then he'll be able to crack it in a few days.</sup>

### Usage

**The script runs best on Linux terminal** (by which I mean the display, speed, and specifically `KeyboardInterrupt`, which is necessary for navigation throughout the program). Running on IDEs isn't recommended as they expose your password, do it at your risk.

As for Windows users, since your command prompts suck, things work quite (slowly and) differently for you. For example, a `KeyboardInterrupt` almost always terminates the program. So, I had to make use of `EOF` to work around it, which means you have to use <kbd>Ctrl</kbd>+<kbd>Z</kbd> and <kbd>Enter</kbd> instead of <kbd>Ctrl</kbd>+<kbd>C</kbd>.

**Note to the users:** Though I've covered most of the possible problems that arrive with an user's input, I suggest you to read the messages carefully before you break things up! (like, losing your stories)

### Installation

- Clone the repo. **Note that you'll need Python first!**
- It'd be best if you have `python` in your path environment variable. You can just `cd` into the repo and execute `python Diary.py`.
- If you're really interested in using the Rust library for searching (which is gonna be useful only if you have some appreciable amount of stories already), then download the [nightly version of Rust](http://www.rust-lang.org/install.html) (v1.3.0), `cd` into the folder and run `cargo build --release` and make sure that you're compiling from and for the right architecture (i.e., 32-bit Rust for 32-bit Python)
