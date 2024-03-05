---
layout: "post"
title: "A list of random Rust concepts and terms"
date: "2023-10-11 20:50:00 +0200"
categories: rust
---

This semester, I have been teaching an unofficial [Rust course](https://github.com/Kobzol/rust-course-fei)
at my [university](https://www.vsb.cz/en).

TODO: link materials
I don't really have materials for sharing, because the course has been in the Czech language, and mainly
because most of the time, it was just me doing live coding and explaining concepts as I went. However,
I thought that there might be one thing worth sharing.

When preparing materials (e.g. for university courses or presentations/talks), I like to first write
down as many concepts that I want to explain to others, in a single, long list. I like this approach
because it allows me to quickly dump a lot of unrefined ideas without having to think about them in
detail (the exploration phase), and then, once I have enumerated everything that I could think of,
I can just go through them one by one, organize them into some logical structure and expand upon them
(the exploitation phase).

I have created such a list for my Rust course. It is quite raw, contains many trivial things,
and perhaps it's indecipherable to anyone else but me. But still, I thought that *maybe* it could be
useful to some other Rust programmers, e.g. to find a concept or a term or two that they perhaps
didn't know about. This blog post won't help with explaining these concepts, of course, but that is
just a Google search away :)

So, here goes:

- Rust history
  - Graydon (elevator story)
  - parallel CSS in Mozilla
  - Servo
- Governance
  - teams
  - Zulip
  - release train
- Tooling
  - Rustup
  - rustc
  - Cargo
    - compilation model (crate = compilation unit)
    - check
    - build
    - run
    - fmt
    - test
    - bench
    - clippy
    - doc
- Variables
    - let
    - initialization is required
    - delayed initialization (declare first)
    - type inference
    - type suffixes (1u32, 3f32)
    - mut (doesn't affect behavior, just a lint)
    - shadowing
- Tuples
  - heterogeneous collection of fixed-size
- Arrays
- If conditions
    - expression oriented language (if is an expression)
    - if without else => returns unit type
- Cycles
    - loop => expression
    - break with a value
    - break with a label
    - semicolon at the end of an expression
    - any block is an expression
- Functions
    - return at the end of a function
    - no forward declaration needed
    - no function overloading
- Tests
    - #[test]
    - cargo test
- Structs
  - product types
  - field definition
  - cannot construct if fields are not visible
  - tuple structs
    - can be viewed as a named tuple
    - can be viewed as a struct with numeric fields
  - newtype pattern (e.g. strongly typed IDs)
- Modules
  - unit of encapsulation
  - struct vs field visibility
  - modules allow us to encapsulate invariants
- Enums
  - sum types
  - enable describing only the data and situations that are valid
- Pattern matching
    - match
    - or patterns
    - underscore placeholder
    - if let, while let
    - let else
    - let with irrefutable pattern
    - if guards
    - @ binding
    - function parameters can be pattern matched
- Destructuring
  - arrays (`let [a, ..] = array`)
  - tuples (`let (a, b) = (1, 2)`)
  - structures (`let Foo {a, b} = foo`)
  - assignment (`(a, b) = (1, 2)`)
- Ownership
  - destructive moves
  - affine type system
  - Copy
  - value vs referential semantics
  - why is `u32` copy?
  - why is `Copy` needed for array init?
- Mutability vs aliasing
- Borrowing
  - shared references
    - can't mutate
    - can't move
    - are Copy
  - unique references
    - can be created only if you own the value
    - can't share
    - can't move
    - are not Copy
    - reborrow (can pass `&mut` twice to a function without error)
- Lifetimes
  - lifetime inference
  - `'static` lifetime
  - reference to a constant (`&5`)
  - lifetime elision      
  - local reasoning
    - lifetimes have to work in the function signature
  - lifetimes in structs
- Slices
  - address + size
  - fixed size, can unify arrays, vecs, …
  - bound checks
- Vec
  - vec! macro
  - passing &Vec<u32> vs &[u32]
- Strings
  - dynamically sized type (DST) - str, [u8]
  - String vs str (owned, borrowed)
  - OsString/OsStr, PathBuf/Path
  - Cow<str> - copy on write
  - UTF-8, indexing
  - read-only
- Methods
    - impl outside of type
    - methods vs associated methods
    - method receiver
- Modules
    - use imports
    - reexports
    - glob imports
    - prelude
- Option
  - ok_or
  - adapters
- Result
  - map_err
  - adapters
- error propagation
    - ?
- error handling

- strings
    - str
        - indexing, UTF-8
        - čahoj
    - String
        - Vec<u8> inside
        - push
        - to_lowercase vs make_ascii_lowercase
        - as_str vs & + Deref
    - string types
        - owned vs borrowed
        - Vec<u8> vs String, vs OsStr, vs PathBuf
    - is_uppercase
        - why doesn't &str implement Iterator?
    - to_lowercase
        - OwnedOrBorrowed, Cow
    - strip_prefix
    - lifetime struct - parsing
        - parse_name

- basic parsing
    - errors
    - map_err
- add subinstruction
    - destexpr into readexpr
- parse labels
    - HashMap
        - insert (Eq + Hash)
        - get (Borrow)
- add jnz instruction

- traits
    - generic parameters
    - associated types
    - input vs output parameters

- built-in traits
    - Display, Debug
    - impl Copy + Clone
        - derive
    - Default
    - Operators
        - Index
            - with multiple keys
        - Add, Mul
    - Deref
    - Drop
        - timer
    - PartialEq, Eq, PartialOrd, Ord, Hash
    - From + Into
        - orphan rule, multiple types

- iterators
    - Iterator trait
    - implement custom iterator
        - split by spaces
        - generators
    - iter vs into_iter
    - map, filter, filter_map, count, sum, fold, zip
    - collect

# Borrowing
- shared vs unique borrows

# Lifetimes
- how the borrow checker works
- dangling references

# Vec and String
- slice
    - slice indexing
    - bounds checking
- Vec
    - vec! macro
- str
- String
    - construction from &str

# Methods
- methods
- associated methods
- Better API with fun(self)

# Enums
- Option and Result

# Pattern matching
- if-let, while-let and let-else

# Error handling
- unwrap, expect
- ? operator

# Traits
- default impls
- supertraits
- Copy, Clone, AsRef, Deref, Debug, Display, Eq, Ord, Hash, Default, Drop, Index
    - auto traits
- From, Into, TryFrom, FromStr, Read, Write, Add, Mul
- marker traits
    - Send, Sync, Sized
- derive
- orphan rule
    - newtype
    - JSON vs XML output
- dyn Trait
- object safety

# Generics
- where clauses
- impl Trait
- generic traits/structs
- associated types (output) vs generic arguments (input)
    - why doesn't String implement iterator?

# Const
- const
- associated const
- statics

# Standard library
- Box
- HashMap
- Cow

# Interior mutability
- Rc, Arc, RefCell, Cell

# Closures
- move
- clone data before closure
- Fn/FnMut/FnOnce

# Iterators
- Iterator trait
- iter vs into_iter
- map, filter, filter_map, count, sum, fold, zip
- collect
- implement custom iterator

# Macros
- declarative macros
- procedural macros

# Panicking
- catch_unwind
- backtraces

# External crates
- serde
- clap
- log
- nom/winnow?

# Parallelism
- data races
- threads
- channels
- atomics
- mutexes

# Async
- coroutines/generators
- Pin
- Waker
- channels

# Unsafe
- miri

# FFI
- bindgen
- PyO3
- napi
- build scripts

# Conclusion
If you have any comments or questions about the runtime benchmarks, or you want to suggest your
own benchmarks to be added to the suite, let me know on [Reddit](https://reddit.com/r/rust/s/rt6P4xLcSf) or send a PR to
[`rustc-perf`](https://github.com/rust-lang/rustc-perf).
