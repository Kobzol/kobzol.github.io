---
layout: "post"
title: "Reducing Cargo target directory size with -Zno-embed-metadata"
date: "2025-05-06 13:00:00 +0200"
categories: rust
#reddit_link: https://www.reddit.com/r/programming/comments/1kg37vm/git_stash_driven_refactoring
---

Disk usage of the `target` directory is one of the most frequently cited annoyances with Rust (and Cargo)
-- in the last year's [Annual Survey](https://blog.rust-lang.org/2025/02/13/2024-State-Of-Rust-Survey-results/#challenges),
it seemed to be the third most pressing issue of Rust users, right after slow compilation[^disk-vs-compilation] and subpar
debugging experience. Given the "build everything from source" compilation model of Rust, and both debuginfo and incremental compilation being enabled by default in the `dev` Cargo profile, it is unlikely that the `target` directory will ever become *lean*. But there are still ways of reducing the `target` directory size by a non-trivial amount. I will try to explore that in this blog post, with the focus on one particular solution.

[^disk-vs-compilation]: Funnily enough, reducing disk usage here might actually go against making compilation faster; for example, the incremental system of the Rust compiler stores a lot of data on disk, which helps it make subsequent recompilations faster.

Note that there are initiatives to reduce the size of the `target` directory along the temporal axis, i.e. prevent it from ballooning over time (see [Cargo Garbage Collection](https://github.com/rust-lang/cargo/issues/12633)). This post is more about how to reduce the size of the target directory overall.

## What takes up the space, anyway?

## Avoid duplicating metadata

- What, you never heard of this flag?

## Integration in Cargo

- BC break

## Conclusion
If you have any comments, let me know on [Reddit]({{ page.reddit_link }}).
