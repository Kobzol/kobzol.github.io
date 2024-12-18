---
layout: "post"
title: "Make the Rust compiler 5% faster with this one weird trick"
date: "2023-10-21 16:37:00 +0200"
categories: rust rustc
reddit_link: https://www.reddit.com/r/rust/comments/17d5doy/make_the_rust_compiler_5_faster_with_this_one/
---
**TL;DR**: On Linux, if you have Transparent Huge Pages enabled, you can try to run `cargo` with
the environment variable `MALLOC_CONF="thp:always,metadata_thp:always"` for a potential ~5% speed boost.

…Sorry for the clickbait title, I just couldn't help myself.

I am regularly trying to search for opportunities how to [speed]({% post_url 2022-10-27-speeding-rustc-without-changing-its-code %})
[up]({% post_url 2023-07-30-optimizing-rust-ci-2023 %}) the Rust compiler without necessarily
changing its code, just by modifying its configuration.

One of the approaches that haven't been explored well so far is the usage of
[huge pages](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/6/html/performance_tuning_guide/s-memory-transhuge)
for memory allocated by the compiler. Linux normally uses 4KiB pages for
[virtual memory paging](https://en.wikipedia.org/wiki/Memory_paging), which can be quite wasteful for
some workloads these days, as such small pages might cause a lot of unnecessary page faults and
[TLB](https://en.wikipedia.org/wiki/Translation_lookaside_buffer) misses.

I have been trying to figure out if supporting huge pages could be useful for the performance of the
Rust compiler. Sadly, configuring huge pages is a mess, and I haven't been able to figure out anything
useful for some time. That is, until `valarauca14` has posted a [helpful guide](https://www.reddit.com/r/rust/comments/1796fm9/comment/k56hu2n/?utm_source=reddit&utm_medium=web2x&context=3)
about using huge pages on Reddit, in response to one of my posts. I noticed something interesting in
the guide, which I haven't seen before. The [jemalloc](https://jemalloc.net/) (the memory allocator
currently used by `rustc` on Linux) can be configured to use (transparent) huge pages (THP), but it
doesn't support THP by default. I wonder what would happen if we changed that?

After a bit of trial and error, I have managed to enable THP support in jemalloc in `rustc`,
and was amazed by the [results](https://perf.rust-lang.org/compare.html?start=45a45c6e60835e15c92374be1f832bc756fc8b1a&end=0ee684d9fbe7d0a7f26b1a97180812d624143a94&stat=wall-time)!
On average, a `~5%` wall-time reduction of compilation time across the board, and a `~60%` reduction
in page faults, with some benchmarks showing up to `~90%` [page fault reduction](https://perf.rust-lang.org/compare.html?start=45a45c6e60835e15c92374be1f832bc756fc8b1a&end=0ee684d9fbe7d0a7f26b1a97180812d624143a94&stat=faults&tab=compile)!
I really didn't expect that it would have such an effect. Sadly, it also increases the
[memory usage](https://perf.rust-lang.org/compare.html?start=45a45c6e60835e15c92374be1f832bc756fc8b1a&end=0ee684d9fbe7d0a7f26b1a97180812d624143a94&stat=max-rss&tab=compile)
of the compiler by `~15%` on average, and by up to `~35%` for some benchmarks. I guess that there's
no free lunch, as usually.

Because huge page configuration inherently depends on the operating system and specific configuration
used by each Rust developer, it will not straightforward to enable huge page support across the board. THP
is also a finicky beast, and it's not always a win to enable it. Furthermore, the memory usage regressions
might be a blocker for enabling this option by default[^mimalloc]. That being said, I will definitely
try to ask around if it would be possible to enable it.

[^mimalloc]: It has already been a blocker in the past, e.g. when we tried to [switch](https://github.com/rust-lang/rust/pull/92249#issuecomment-1193396623)
    from `jemalloc` to [`mimalloc`](https://github.com/microsoft/mimalloc), which resulted in a `~5%`
    compilation time reduction, but sadly also up to `35%` memory usage increase.

However, in the meantime, if you're on Linux, you can try to benefit from this performance increase
on your own. To do that, you have to:

- Enable transparent huge pages, either with the `always` or `madvise` modes. On Ubuntu, you can do
that with the following command:
    ```bash
$ echo madvise > /sys/kernel/mm/transparent_hugepage/enabled
    ```
    Note that you might need superuser rights (`sudo`) to execute this command, and that it might also
    be reset after a restart (depending on your system, for me it was set to `madvise` by default and
    it stays there).
- Use the environment variable `MALLOC_CONF="thp:always,metadata_thp:always"` when compiling Rust code:
    ```bash
$ export MALLOC_CONF="thp:always,metadata_thp:always"
$ cargo build
    ```

There is a lot to be done and experimented regarding the usage of huge pages within the compiler, but until
that work is done, this quick trick can be used for a small compilation boost.

By the way, this "trick" should work for any program that uses jemalloc. You can find more jemalloc
configuration options [here](https://jemalloc.net/jemalloc.3.html).

# Conclusion
If you have any comments or questions, or you have hints about using huge pages, please let me know
on [Reddit](https://www.reddit.com/r/rust/comments/17d5doy/make_the_rust_compiler_5_faster_with_this_one/).
