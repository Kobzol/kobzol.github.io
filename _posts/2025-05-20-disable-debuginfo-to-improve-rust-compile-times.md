---
layout: "post"
title: "Disable debuginfo to improve Rust compile times"
date: "2025-05-20 15:00:00 +0200"
categories: rust rustc
reddit_link: https://www.reddit.com/r/rust/comments/1kr7ri4/psa_you_can_disable_debuginfo_to_improve_rust/
---

> This blog post is essentially a PSA on how you can easily improve `dev` incremental rebuild performance.

*[PSA]: Public service announcement

At [RustWeek](https://rustweek.org/), we led many discussions on compiler performance, and what we can do to improve it. One of the discussion points in this area was the generation of debug information (debuginfo), which happens by default in the Cargo `dev` (unoptimized) profile. Now, I suppose that it's not surprising that generating debuginfo is not *free* and costs some compilation time. But I'm not sure if people actually realize *just how expensive* it currently is, especially for incremental (re)builds.

[Here](https://perf.rust-lang.org/compare.html?start=a8e4c68dcb4dc1e48a0db294c5323cab0227fcb9&end=824ee216c0852d0622837402ed8aaf3a74ab4ac4&stat=instructions:u) are results of a run of the [compiler benchmark suite](https://github.com/rust-lang/rustc-perf) where I forcefully disabled debuginfo generation. In some situations, especially for incremental rebuilds, disabling debuginfo can make your compilation 30-40% faster! And this benchmark was already performed with the fast `lld` linker, which is not used by default on the x64 Linux target ([yet](https://github.com/rust-lang/rust/pull/140525)); I expect that with the default Linux linker (BFD), the improvements would be actually *way* higher, because linking debuginfo can be quite slow. You won't get such a large improvement in all situations, of course, but it can definitely be worth it to consider disabling debuginfo.

There are essentially two ways how we can improve this situation. We could make debuginfo generation faster, as I suspect that it is currently quite suboptimal, particularly in incremental builds, or we can avoid generating it by default. But until either of that happens, you can speed up your (unoptimized) incremental rebuilds *today* by disabling debuginfo in your `Cargo.toml` file:

```toml
[profile.dev]
debug = false
```

Note that this will also remove source code lines from stack traces, making them much less useful. If you want to keep that information, you can use `debug = "line-tables-only"` instead, which is a compromise between full and no debuginfo. It still provides a [pretty nice speedup](https://perf.rust-lang.org/compare.html?start=f8e9e7636aabcbc29345d9614432d15b3c0c4ec7&end=280a1abf776b68a28cbb5cd830d3123723354b0f&stat=instructions:u) vs the default (full) debuginfo.

I personally think that generating debuginfo by default is a bit wasteful. Based on various polls and survey results that I saw, many Rust programmers simply don't use a debugger at all. But even if you do use it, I would estimate that you don't end up actually running a debugger on a large fraction of your builds, even though you do pay the debuginfo generation cost for every build (by default).

I'm planning to work on removing debuginfo (or changing it to `line-table-only`) from the default `dev` profile in Cargo, but it will take some design work and time (and it's unclear if it will actually happen). We should probably also make debuginfo generation faster (and smarter for incremental builds) in the compiler.

> Removing the debuginfo generation is actually the only optimization that I do for the stable compiler in the [cargo-wizard](https://github.com/Kobzol/cargo-wizard) tool; other approaches designed to speed up compilation (such as the parallel frontend, the Cranelift backend or using a different linker) are either unstable or cannot be easily configured directly through `Cargo.toml`.

If you have any thoughts on this, let me know on [Reddit]({{ page.reddit_link }})!
