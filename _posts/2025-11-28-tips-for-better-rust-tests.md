---
layout: "post"
title: "Tips for better (Rust) tests"
date: "2025-12-10 15:00:00 +0100"
categories: rust testing
#reddit_link: TODO
---

Recently, I had a talk at the [Rust Prague meetup](https://www.meetup.com/rust-prague/events/311846118/) about my experiences with testing, along with tips for making tests better. Some people that couldn't attend told me that they would like to see the talk, but sadly the recording of that talk in English[^czech-recording] might not be available online, so I thought I could also turn it into a blog post. If you ever saw one of my talks, you know that they tend to be [programmed]({% post_url 2021-01-07-elsie-programmable-presentations %}) and have a lot of slides[^slide-count] :sweat_smile:, so this post is also quite long. I skip the intro and some code samples, and only focus on the main ideas of my talk: the annoyances that I have with tests, and some tips for reducing those annoyances. The slides for this talk can be found [here](https://github.com/Kobzol/talks/blob/main/2025/rust-prague/tips-for-better-tests/slides.pdf).

The primary case study on which I'll demonstrate various testing strategies will be the [bors](https://github.com/rust-lang/bors) merge queue bot. It is a web application that listens for webhooks from GitHub repositories. You can control it through commands sent in GitHub pull request comments. When the bot receives a command, it executes it and returns the response as a comment on the same PR.

I will be focusing on Rust, although most of the tips should apply also to other programming languages.

[^czech-recording]: If you understand Czech or you don't mind using auto-translated subtitles on YouTube, you can check a dry-run version of the talk in Czech [here](https://www.youtube.com/watch?v=rC2j8oV7UTA).

[^slide-count]: I managed to get through 262 "slides" (more like steps/fragments) in ~40 minutes. I think that is actually a record for me. I was actually relieved that my voice still worked at the meetup, as I was talking non-stop the whole previous day and also the day of the meetup while doing a Rust training.

# Annoyance 1: Tests break during refactoring
The following often annoys me: I refactor some code, fix compiler errors, iterate until `cargo build` is green, and then I feel happy that I can `git commit` and move forwards. But then I remember that I also have tests! So I run `cargo test`… and find out that they don't even compile :sad: Fixing that can be an incredible time waste, and it's generally not a very entertaining process. If I changed only the implementation, and not the behavior, of my code, why do tests need to be updated?!

## Tip 1: Write high-level test APIs or DSLs
One thing that causes the situation described above is when tests use the tested code directly, using too "low-level" APIs. If I add/remove a field of a structure or add/remove a parameter of a function, and that structure or function is being directly tested/used by a hundred tests, I will have to go through them and update them all. Sometimes IDE refactorings can help with this, but they are not a panacea. Rust is especially burdened by this, as it does not support default and named parameters out of the box, which are very useful for tests specifically.

And thus I try to "shield" my tests from the API of the code that they are testing, by creating high-level (test-only) APIs or even DSLs. There are various approaches for that.

### Builder pattern
One option is to simply use a builder pattern. When creating "domain data types" in tests, I try to do it using builders (usually with the [`derive_builder`](https://docs.rs/derive_builder/latest/derive_builder/) or the [`bon`](https://docs.rs/bon/latest/bon/) crate).

```rust
#[test]
fn test_set_priority() {
  let bors = ...;
  let pr = PRBuilder::default().author("bot");
  ...
}
```

This already reduces the need to maintain tests, as it allows me to select a set of reasonable defaults at a single place (the builder), and when a domain type changes, I can just update that one single spot, and all tests will still continue working (or at least they will still *compile*). At the same time, individual tests can still easily override the properties of the created objects using builder methods.

### Extensible test helpers
The builder pattern helps with types, but what about functions? Again, I find it useful to create another level of indirection here, by calling "wrapper" test helper functions in tests, rather than using the tested code directly. When the interface of the tested code changes, I can then just modify the wrapper at a single place.

Of course, on its own this just moves the same problem to the wrapper method. What if I need to pass a new parameter to the tested function? Let's say that I have a function to post a comment to bors that I want to use in my tests, which receives the repository and number of the PR to which to post the comment, the contents of the comment and information about the comment author. I could:

1. Just call the function directly, passing all required parameters to it:
  ```rust
bors.post_comment("test-org", 1, "Hello bors!", User::new("user1"));
  ```
  This is very verbose, because in most test usages, the repository, PR number and author will be the same. And when I will need to pass something more to the function in the future, all my tests will break again.
2. Use one function for the common case, and another for the complex case:
  ```rust
bors.post_comment("@bors r+");
bors.post_comment_ext("test-org", 1, "@bors help", User::new("user1"));
  ```
  This is better, but it requires creating two functions per tested API, which is annoying, and all users of the `_ext` function will break when the API changes. Also, modifying a single non-default parameter requires me to specify all of the parameters.
3. Use builder pattern for the arguments:
  ```rust
bors.post_comment(Comment::new("@bors r+"));
bors.post_comment(Comment::new("@bors r+").author(User::new("user1")));
  ```
  This makes the test code resilient against API changes, but it is also quite verbose for the common case (and as I'll talk about later below, I find readability of tests to be very important).

None of the approaches above are ideal. What I tend to do instead in similar situations is to combine the builder pattern with the succint common case, using an "`Into` trick", where I implement `From<{subset of domain data}> for {domain-type}` for some common subsets of data:

```rust
// Test helper function:
fn post_comment<C: Into<Comment>>(c: C) { ... }

impl<'a> From<&'a str> for Comment {
    fn from(value: &'a str) -> Comment {
         Comment::new(value)
    }
}

impl<'a> From<(u32, &'a str)> for Comment {
    fn from((pr, comment): (u32, &'a str)) -> Comment {
         Comment::new(comment).pr(pr)
    }
}

// Tests:
// Default repo/PR/author
bors.post_comment("@bors r+");

// Default repo, PR 2, default author
bors.post_comment((2, "@bors r+"));

// Default repo, PR 2, author "user"
bors.post_comment(Comment::new("@bors r+").pr(2).author("user"));
```

With this approach, I can have test functions that both make the common cases succint and readable, but are also easily extensible when needed, while also being resilient against API changes of the tested code.

### Aside: magical code
The `Into` code above is quite "magical and smart". Should we write code like that? I sometimes see that code reviewers focus a lot on making sure that "normal" code is as DRY as possible, does not contain any duplication, etc. But on the other hand, if a PR adds 20 new tests that are essentially copy-pasted from one another with some only a bunch of details modified, it might not be taken into account at all ("it's just test code, who cares").

*[DRY]: Don't Repeat Yourself

Well, I think that we should care. Test code is code, after all, and if you spend 30 minutes writing a new feature, and then an hour fixing all the tests that stopped compiling after that change, it is not very productive. I actually think that we should switch the approach to code duplication in code reviews. Sometimes, having some light duplication in normal code can be much better than introducing the wrong abstraction. But on the other hand, having tests heavily duplicated can have a very high maintenance cost, which also might be kind of invisible ("yes, I need to spend an hour fixing tests, that's just how it is"). So don't be afraid to write smart and magical APIs to make your tests less duplicated!

## Tip 2: Test public (rather than private) interfaces
Or it could also say "Test behavior, not implementation" or "Prefer black-box tests".

![Classic testing pyramid, with unit tests being the majority of tests](/assets/posts/tips-for-better-tests/testing-pyramid-1.jpg)

[Aleksey Kladov](https://github.com/matklad) has this lovely [quote](https://matklad.github.io/2021/05/31/how-to-test.html#Test-Features-Not-Code) on the topic: "Can you re-use the test suite if your entire software is replaced with an opaque neural network?". If you can do that, then 

Let's take a look at the following test:
```rust
#[test]
fn test_try_build() {
    let bors = // create test context
    bors.post_comment("@bors try");
    let comment = bors.get_comment();
    assert_eq!(comment, "Try build started");

    let ci_workflow = Workflow::from(bors.try_branch());
    bors.workflow_start(&ci_workflow);
    bors.workflow_success(&ci_workflow);

    let comment = bors.get_comment();
    assert_eq!(comment, "Try build successful");
}
```

The test simply crates HTTP requests and reads HTTP responses from a running `bors` application

## Acknowledgement
While preparing my talk, I knew that a lot of my testing opinions were formed by reading Matklad's blog posts, and in fact also by working on [codebases]({% post_url 2020-08-23-contributing-0-setup %}) that he had bootstrapped. Then I found one of his older [blog posts](https://matklad.github.io/2021/05/31/how-to-test.html) and realized that my talk mostly mirrors it :laughing: So I wanted to acknowledge it as a big source of inspiration for me.

## Conclusion

It was a lot of fun to present this talk at the meetup. I saw a bunch of people continously nodding their heads while listening to my talk, so I think that the test annoyances were quite relatable :laughing:

I didn't have time in the talk to get to other interesting testing topics, such as [fuzz testing](https://github.com/rust-fuzz/cargo-fuzz), [property testing](https://proptest-rs.github.io/proptest/intro.html) or [mutation testing](https://mutants.rs/). Although I don't actually have that much direct experience with these, so I couldn't provide deep insights there anyway.

Did you find something relatable in my test experiences? Let me know [Reddit]({{ page.reddit_link }}).
