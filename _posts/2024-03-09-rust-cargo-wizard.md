---
layout: "post"
title: "Automating Cargo project configuration using cargo-wizard"
date: "2024-03-10 16:00:00 +0100"
categories: rust cargo
---

**TL;DR**: I created a Cargo subcommand called [`cargo-wizard`](https://github.com/kobzol/cargo-wizard) that simplifies the configuration of Cargo projects for maximum runtime performance, fastest compilation time or minimal binary size.

As a member of the [compiler performance working group](https://www.rust-lang.org/governance/teams/compiler#Compiler%20performance%20working%20group), and generally as someone who cares a lot about performance, I'm always quite excited about the continuous improvements to Rust's [compilation times](https://nnethercote.github.io/2024/03/06/how-to-speed-up-the-rust-compiler-in-march-2024.html), runtime performance and [binary size]({% post_url 2024-01-23-making-rust-binaries-smaller-by-default %}). Many of these improvements silently improve your Rust programs or the compiler, and you might not even notice them, except for something being slightly faster or smaller.

However, for various reasons, not all optimizations are always applied by default, and you might need to properly configure your Cargo projects using the [many](https://doc.rust-lang.org/cargo/reference/profiles.html) [available](https://doc.rust-lang.org/cargo/reference/config.html) configuration options to enable them. This means that many Rust users don't take advantage of them, simply because they don't know that they exist or how can they be enabled.

It's a running joke that the most common solution to fix the "slow performance" of a Rust program is to compile with `--release`. But that's just one of many things that can be configured. How many people use [LTO](https://doc.rust-lang.org/cargo/reference/profiles.html#lto), gather [PGO](https://github.com/Kobzol/cargo-pgo) profiles or configure the number of [CGU](https://doc.rust-lang.org/cargo/reference/profiles.html#codegen-units)s? How many people have experimented with the new [parallel frontend](https://blog.rust-lang.org/2023/11/09/parallel-rustc.html) or switched the [linker](https://nnethercote.github.io/perf-book/build-configuration.html#linking) that they use?

While these concepts are probably not new to experienced system programmers, people coming e.g. from a web development or a scripting language background might not know about them. The great thing about Rust and Cargo is that you don't even need to know how these things work, you can just configure them with a few lines in a TOML file, and then reap the benefits. But the configuration step is still crucial.

*[LTO]: Link-time optimizations
*[PGO]: Profile-guided optimizations
*[CGU]: Codegen units

I think that there are two issues that we could improve upon in this area:
- **Discoverability** - how can I easily find out the most important Cargo configuration options that can help me improve the performance of my Rust program, and/or the speed of developing it? While Cargo has [pretty](https://doc.rust-lang.org/cargo/reference/profiles.html) [nice](https://doc.rust-lang.org/cargo/reference/config.html#configuration-format) documentation, the useful tidbits are often distributed amongst multiple places. I have to give a shoutout to the [Rust Performance Book](https://nnethercote.github.io/perf-book/build-configuration.html) by Nicholas Nethercote, which makes this information readily available on a single place, which is awesome.
- **Automation** - even if I am aware of all the available options, how can I easily apply them to my existing Cargo projects or to each new project that I create? This might seem trivial, but I actually think that it is quite important to make this easier. Even though I follow the development of `rustc` and know a lot about all the in-progress improvements, I realized that I almost never use them for my own projects. Just recently, I switched to the `lld` linker for one of the [projects](https://github.com/It4innovations/hyperqueue) that I work on in my day job, and it has cut its incremental rebuild time in half[^mold]! It's mostly because I'm lazy and don't want to look up and configure these options all the time.

[^mold]: Yes, I have also tried [`mold`](https://github.com/rui314/mold), but it didn't seem to help for this specific project.

In short, I saw an opportunity for automation, so I created YACS (Yet Another Cargo Subcommand) called [`cargo-wizard`](https://github.com/kobzol/cargo-wizard). It can apply three predefined templates (fast compilation time, fast runtime and minimal binary size) to your Cargo workspace with a single command, which mostly solves the *automation* issue. It also allows you to customize the templates and shows you the available configuration options that can be used to optimize your project. This can hopefully help with the *discoverability* issue.

As with most other Cargo subcommands, you can install it easily with the following command:

```bash
$ cargo install cargo-wizard
```

`cargo-wizard` can be used non-interactively using the `cargo wizard apply` command, but where's the fun in that, so here is an example of its interactive TUI dialog interface[^inquire]:

[^inquire]: Created using the cool [inquire](https://github.com/mikaelmello/inquire) crate.

<img src="/assets/posts/cargo-wizard/wizard-demo.gif" width="100%" alt="Interactive usage of cargo-wizard." />

*[TUI]: Terminal user interface

The idea of `cargo-wizard` is that instead of having to remember all the useful configuration options and having to manually apply them to your project, you can just run `cargo wizard` and let it do that for you in a few seconds, on any Cargo project that you work on.

> There are some things that are out of scope for `cargo-wizard`, for example more complicated compilation workflows, like PGO. But don't worry, you can use my other Cargo subcommand, [cargo-pgo](https://github.com/kobzol/cargo-pgo), for that :)

Currently, `cargo-wizard` is mostly focused on performance configuration options, but in theory nothing stops it from becoming a general tool for interactive configuration of Cargo projects. And who knows, maybe one day it can even become a part of Cargo itself :)

# Conclusion
I hope that you will find `cargo-wizard` useful and that it will help you to quickly configure your Cargo projects so that you can avoid having to keep all the useful options in your head. If you find bugs or want to suggest new features, please let me know in the [issue tracker](https://github.com/kobzol/cargo-wizard/issues). Pull requests are, of course, also welcome :)

If you have any comments or questions about this blog post or `cargo-wizard`, you can also let me know on [Reddit](https://www.reddit.com/r/rust/comments/1bbcdzs/cargowizard_configure_your_cargo_project_for_max/).
