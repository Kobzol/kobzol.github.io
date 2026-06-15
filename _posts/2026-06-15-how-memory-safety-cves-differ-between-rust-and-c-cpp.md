---
layout: "post"
title: "How memory safety CVEs differ between Rust and C/C++"
date: "2026-06-15 17:00:00 +0200"
categories: rust
#reddit_link: TODO
---

CVE is a database used for categorizing and reporting security vulnerabilities in software. There
are various kinds of vulnerabilities that can be reported. Some of them are caused simply by bugs
in the program logic (like a recent CVE reported in [Cargo][cargo-cve]), but some of the most nasty
ones are caused by memory unsafety, which can easily lead to exploits. In this post I want to focus
on the latter kind of CVEs, how they are reported, especially in libraries, and how it differs
between Rust and C or C++.

*[CVE]: Common Vulnerabilities and Exposures

Because sometimes I see people online who compare the number of CVEs in Rust and C/C++ software, which
tends to be accompanied by claims about Rust not being *really* memory safe or not being worth
adopting when CVEs can still exist in it. And sometimes I also observe similar views when I teach Rust
to programmers who are used to programming in C or C++.

Now, anyone is, of course, free to do such comparisons, and make their own conclusions based on it. But I think that there is an important difference in how potential vulnerabilities related to memory safety are treated in Rust and C/C++, which might not be obvious at first, especially if you don't know how Rust works. I'd like to explain that in this post.

But first, I should clarify that it is absolutely possible to cause memory unsafety bugs and undefined
behaviour in Rust. In the vast majority of cases[^compiler-bug], the `unsafe` keyword is required for
this to happen, but anyone who claims that Rust programs cannot experience UB at all is simply incorrect.
It is also perfectly possible to cause general [vulnerabilities][rustsec] (meaning those unrelated
to memory unsafety) in Rust. Forgetting to add a check that your admin dashboard is only accessible to admins can happen in any language, after all.

*[UB]: Undefined Behaviour

[^compiler-bug]: Essentially only except for [compiler bugs](https://github.com/Speykious/cve-rs).

And yet, there is something very different between potential vulnerabilities in Rust and C or C++, which is
related to the core reason of why Rust *is* actually much more memory safe [in practice][google-report] than C
or C++. I'll try to demonstrate it on the [`curl`][curl] networking library, which is written in C.

## Potential vulnerability in curl?

`(lib)curl` is one of the most used and well-maintained open source libraries in the world. Its primary
developer, [Daniel Stenberg][daniel], is one of the most prolific open source maintainers of our time,
and together with many other people, he has been dilligently improving this library for the past 30 years.
Despite having to deal with a recent [avalanche][curl-cve] of CVEs found by LLMs,
he and his collaborators are doing a very good job of keeping `curl` safe from potential exploits and vulnerabilities,
and they take pride in `curl` being a very robust piece of software.

So, let's take that to the test, shall we? I opened the [documentation](https://curl.se/libcurl/c/allfuncs.html)
of `libcurl` and found the first function I saw that accepts an argument, [`curl_getenv`](https://curl.se/libcurl/c/curl_getenv.html). This is supposed to be a simple function that provides a portable
abstraction for getting the value of an environment variable across different operating systems.
`curl` is supposed to be safe and robust, so surely this function doesn't contain any UB or memory unsafety, right?
So what about the following C program?

```c
#include <curl/curl.h>

int main(void) {
    curl_getenv(NULL);
}
```

This 5-line C program is as simple as it gets, it just calls the `curl_getenv` function with a
`NULL` pointer argument, and compiles without any warnings. And yet, when you execute it, you (might)
get a segfault, and thus a memory safety bug, and thus a potential vulnerability/exploit:

```bash
$ gcc test.c -otest -lcurl -Wall -Wextra
$ ./test
Segmentation fault (core dumped)
```

> Of course, this program is artificially simple, but that's kind of the point. In practice, situations
like this can (and do) easily happen in larger programs by accident all the time.

Huh. So maybe `curl` isn't so safe after all? Should I go and report this as a vulnerability in `curl`?!

No, of course not. That would be stupid. I know that, you know that. But how do we actually know it?
That's the interesting part.

Consider a very similar program that would call the function like this: `curl_getenv("FOO")`. What if
that program would still segfault, and thus contain a potential vulnerability? I am sure that the `curl`
maintainers would like to know about that happening, and would consider it to be a pretty big issue if I reported it! At the same time, I'm sure that they would (rightfully) tell me off if I reported the first program as a vulnerability in `curl`. Yet those two programs differ only by so little.

So, what gives? Well, in practice, UB like the one in my original example is said to be caused by "wrong usage"[^skill-issue], and it is not considered to be an issue in the library or API that I am using, but in my (application)
code. This is done mostly for the following two reasons:

- In C, it is often not possible to specify the contract (invariants, preconditions,
  postconditions, etc.) of APIs precisely[^cpp] due to its limited type system, and library authors often
  don't bother describing all possible kinds of wrong usage, as it would not be practical.

  Indeed, the [documentation](https://curl.se/libcurl/c/curl_getenv.html) of `curl_getenv` does not say that calling it with `NULL` is forbidden and might lead to a segfault! The authors thus assume that you will use the library "correctly" (whatever that means), and if you don't, then any caused vulnerabilities are your fault.
- The fact that it is so [simple][c-ub] to trigger UB by accident in C or C++ means that if we reported all
  the *potential possibilities* of causing a vulnerability, such as the one in my example program, most C or C++
  libraries would be flooded by millions of CVEs. It wouldn't make sense to do that, because there would
  be five different ways of potentially causing a vulnerability in every function call.

*[API]: Application Programming Interface

[^skill-issue]: Someone might even say "skill issue" :laughing:

[^cpp]: In C++, the type system offers many more amenities for describing invariants, yet it still also offers many other ways to sneakily introduce UB by accident, so the end result is similar.

And thus, in C and C++, we usually do not consider similar situations to warrant a CVE in the used library.
In other words, we create CVEs for specific *misuses* of a library, not for the existence of a library API that
*can be misused*.

## How does it differ in Rust?

So, what is the crucial difference between how the situation above would be treated in C or C++ and
in Rust? [`hyper`][hyper] is likely the most popular networking/HTTP library in Rust, spiritually
similar to `libcurl` in C. Imagine that `hyper` would have a similar simple function that would take
an argument, I would write a Rust program like this:

```rust
fn main() {
    hyper::foo(None);
}
```

Then I'd hit `cargo run`, and the program would segfault. Would that be a CVE in `hyper`? Yes, absolutely[^compiler-bugs]!

[^compiler-bugs]: Again, barring any compiler bugs or hardware issues with my RAM module :)

The program does not contain any `unsafe` blocks, so if a memory bug occurs, it had to be caused by the hyper library having a soundness bug.

The difference is that in Rust, when it is *in any conceivable way possible* to use a library such
that a memory bug occurs, without using `unsafe` in the user code, it is always a bug in the library,
not in the user code. That is why we call such APIs *unsound*, or say that they have a *soundness hole*, because there is
a way to use them wrong (w.r.t. memory safety) in safe Rust.

In other words, we create CVEs when it is *possible* to use a safe library API in a way that might cause a memory bug, even if we haven't (yet) found any program in the wild that would actually do so. This means that some of the CVEs reported in Rust are much more "strict" than the ones in C or C++, which some people [don't find "fair"][walton-tweet].

If we applied the same logic to C, then `curl_getenv` should be flagged as a CVE in `curl`, because it is possible to use it in a way that causes a memory bug. But of course, this doesn't really make sense in C, because there is no concept of safe and `unsafe` C (or rather, all C code is implicitly `unsafe`), which is why I said earlier that reporting this CVE would be stupid.

The answer to the question "do I use this function correctly" (with respect to memory safety issues,
not logic bugs), which is often difficult to figure out in C or C++, is very simple in Rust:
- If the called function is not marked with `unsafe`, then the answer is simply `YES`. It is impossible to use it incorrectly.
- If the called function is `unsafe`, I must mark the call with an `unsafe` block, which makes it immediately obvious during code review and in the codebase that this place is potentially dangerous. In this (usually very rare)
  case, we revert back to the level of C or C++.

The first part of the answer is what enables Rust's memory safety to scale in practice. If you do not use `unsafe` in your code, which is not needed in the vast majority of situations (unless you are writing something like an operating system or a lock-free data structure), and don't encounter a compiler bug, you *know* that any potential causes of memory unsafety are not your fault. If a library does not expose any `unsafe` interface, you simply *cannot* use it in a way that would cause memory bugs, unless the library uses `unsafe` internally and has a bug. But if that happens, the bug is fixed *within* that library, and all its users are then again automatically safe from memory bugs.

This is the difference between Rust and C or C++. Even though the developers of `curl` are doing awesome work to build a perfectly safe and robust C library, the millions of other C programs that use it can still very easily introduce memory unsafety just by "holding it wrong", without the `curl` developers having any way of preventing that.

## Conclusion

I used `curl` as an example, but the same holds for pretty much any C or C++ library, including
the standard libraries of those two languages (and also other memory unsafe languages in general).
Originally I wanted to show more examples, but in the end I realized that they are all the same, so I stayed with the single `curl` function, because I think it demonstrates the difference well.

What I described in this blog post is not really ground-breaking in any way, and I think that it is kind of
universally understood by most people who know how Rust works. But I also don't remember seeing any blog
post about this, and I was repeatedly explaining it to some people, so I wanted to write down
some thoughts about it, so that I can simply link to them the next time this debate happens again.

I hope that what I described above shows that comparing raw numbers of CVEs per line of code of Rust
and C or C++ is all kinds of misleading, and we should take that into account when comparing the
memory safety of Rust and other systems programming languages.

If you have a different idea on how CVEs (should) work in Rust or C/C++, let me know on [Reddit]({{ page.reddit_link }}).

[cargo-cve]: https://blog.rust-lang.org/2026/05/25/cve-2026-5222/
[c-ub]: https://blog.habets.se/2026/05/Everything-in-C-is-undefined-behavior.html
[curl]: https://curl.se/
[curl-cve]: https://daniel.haxx.se/blog/2026/05/26/the-pressure/
[daniel]: https://daniel.haxx.se/
[google-report]: https://blog.google/security/rust-in-android-move-fast-fix-things
[hyper]: https://github.com/hyperium/hyper
[rustsec]: https://rustsec.org/advisories/
[walton-tweet]: https://xcancel.com/pcwalton/status/1579643729836924929
