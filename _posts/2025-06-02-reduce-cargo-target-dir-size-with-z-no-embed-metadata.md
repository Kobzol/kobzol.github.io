---
layout: "post"
title: "Reducing Cargo target directory size with -Zno-embed-metadata"
date: "2025-06-02 14:00:00 +0200"
categories: rust rustc
#reddit_link: TODO
---

Disk usage of the `target` directory is a commonly cited annoyance with Rust (and Cargo)
-- in the last year's [Annual Survey](https://blog.rust-lang.org/2025/02/13/2024-State-Of-Rust-Survey-results/#challenges),
it was the third most pressing issue of Rust users, right after slow compilation[^disk-vs-compilation] and subpar
debugging experience. Given the "build everything from source" compilation model of Rust, and both debuginfo and incremental compilation being enabled by default in the `dev` Cargo profile, it is unlikely that the `target` directory will ever become *lean* and small. However, there are still ways of how we could reduce the `target` directory size by a non-trivial amount. I will describe a brand-new method of achieving that in this blog post.

[^disk-vs-compilation]: Funnily enough, making compilation faster can sometimes increase disk usage; for example, the incremental system of the Rust compiler stores a lot of data on disk, which helps it to make subsequent recompilations faster.

Note that there are also initiatives to reduce the size of the `target` directory along the temporal axis, i.e. prevent it from ballooning over time (see [Cargo Garbage Collection](https://github.com/rust-lang/cargo/issues/12633)). This post is more about how to reduce the size of the target directory overall.

## What takes up the space, anyway?

It is not the focus of this post to dive deep into exploring what exactly takes space in the `target`
directory, but I still think that it is useful to provide at least some background on this. I took
my favourite work project, [hyperqueue](https://github.com/It4innovations/hyperqueue), and compiled
it in several modes to compare the resulting `target` directory sizes[^jemalloc], using `rustc 1.89.0-nightly (2eef47813 2025-05-22)`:

| Optimizations   | Incremental | Debuginfo | `target` size [MiB] |
|-----------------|-------------|-----------|--------------------:|
| No (`dev`)      | No          | No        |                 462 |
| No (`dev`)      | Yes         | No        |                 677 |
| No (`dev`)      | No          | Yes       |                 870 |
| No (`dev`)      | Yes         | Yes       |                1316 |
| Yes (`release`) | No          | No        |                 396 |

[^jemalloc]: I compiled it with `--no-default-features` to avoid compiling the *C* `jemalloc` dependency, as that takes [a lot of space on disk](https://github.com/tikv/jemallocator/pull/119).

From the results, it's clear that both debuginfo and incremental compilation caches take a lot of
space on disk. It might be that we could do something to reduce either of these, but there is one
additional thing that (kind of unnecessarily) causes `target` directory bloat, which is not
easily observable in this table, and that is the metadata of the compiled Rust crates.

## Cargo pipelining & metadata duplication

First, we need to briefly talk about how Rust compilation works (in very, very simplified terms).
When a Rust library crate (`rlib`) is compiled in a "standard" way (i.e. no LTO or other funny
business) with Cargo, the compiler generates (amongst other things) two main outputs:

- Metadata, which contains information necessary to link to that crate from other Rust code.
- Object code, which is the compiled assembly code of the Rust crate.

*[LTO]: Link-time optimizations

The interesting thing about this is that the final object code isn't actually needed in order to start
compiling Rust code that depends on a said library, metadata is enough (the object code will only be
needed at the final linking step). Cargo makes use of this fact, and when it compiles your crate graph,
it uses a technique called [pipelining](https://internals.rust-lang.org/t/evaluating-pipelined-rustc-compilation/10199).
Imagine that you have a binary that depends on crate `B`, which itself depends on crate `A`. When
compiling `A`, Cargo will tell the compiler (using `--emit=metadata,...`) to emit a `.rmeta` file
containing the metadata of `A` as soon as possible. Once that file is ready, we can start compiling
`B` by passing it the `.rmeta` file of `A`, even though the object code of `A` is not ready yet,
and thus partially overlap the compilation of both crates, which improves compile times. I will borrow
(and slightly extend) a cute ASCII diagram from [Alex Crichton's internals post](https://internals.rust-lang.org/t/evaluating-pipelined-rustc-compilation/10199) about pipelining
to succintly show how it works:

```
          --- .rmeta of A generated
          v
[-libA----|--------]
          [-libB----|--------]
                             [-binary-----------]
0s        5s       10s       15s                25s
```

Pipelining has been enabled in Cargo for many years, so it's nothing new, and if you use Cargo, you
are using pipelining every day, perhaps without even knowing about it. However, there is one
suboptimal thing in regard to disk space usage with the pipelining approach.

The problem is that once the process finishes, you will be left with two copies of the metadata of
each library on disk. The first copy is in the final `.rlib` file (along with the object code), and
the second copy is in the `.rmeta` file. As is usual with Cargo, this problem will balloon if you build
your project with multiple configuration options (different Cargo profiles, different compiler/linker
flags, etc.).

A related issue is that if you are compiling a library as a `dylib`,
so that you generate a Rust dynamic library (e.g. `.so` on Linux), that will also contain the
metadata, even though it should not be required to actually consume (call functions from) the
library at runtime. This can be annoying for people who ship Rust `dylib`s, even though that's
usually not very common due to Rust currently not having a stable ABI.

*[ABI]: Application Binary Interface

## Avoiding duplicated metadata

So, what can we do about it? Well, last year, I noticed that many years ago, the illustrious `@bjorn3` has
[proposed](https://github.com/rust-lang/rust/issues/57076) an idea to introduce a compiler flag
that would cause the metadata to *only* be included in the `.rmeta` files, and no longer be present
in the `.rlib/.so` library files. I liked this idea, and since there already was a [prototype](https://github.com/rust-lang/rust/pull/93945)
[implementation](https://github.com/rust-lang/rust/pull/120855) prepared, it didn't seem that hard to push it over the finish line. So I
nerd-sniped myself into finishing the implementation of the flag under bjorn3's mentorship.
I didn't actually make a lot of progress on it last year (because of… [stuff]({% post_url 2024-11-12-phd-postmortem %})),
but this year I finally filed an [MCP](https://github.com/rust-lang/compiler-team/issues/851), which is the usual process
for introducing new compiler flags, refactored the implementation a bit, added tests, and got it
[merged](https://github.com/rust-lang/rust/pull/137535). So long story short, you can now use an
unstable compiler flag in nightly Rust called `-Zembed-metadata=no`, which avoids the metadata
duplication.

*[MCP]: Major Change Proposal

When the flag is used, the `.rlib` file will only store a "metadata stub", which contains
the bare minimum of information necessary for the `.rlib` to be loaded and validated, and the rest
of the metadata will be stored in a `.rmeta` file.

## Cargo integration

Normally, when a new unstable compiler flag is added, people can experiment with it using `RUSTFLAGS`.
However, the way this flag works means that you kind of need to combine it with `--emit=metadata`,
otherwise there will be *no* metadata generated at all, which would not be good. Furthermore, you
will now also need to pass the paths to the `.rmeta` files to the final `rustc` invocation that links
the top-level binary/library, otherwise the metadata will not be found. This essentially means that
this feature also needs some changes within Cargo, otherwise it wouldn't be really usable with it.
So I went and implemented [support](https://github.com/rust-lang/cargo/pull/15378) for this `rustc` flag in Cargo, and exposed it via a new
unstable Cargo flag called `-Zno-embed-metadata`.

Here are results of building `hyperqueue` using `-Zno-embed-metadata`[^build-cmd]:

| Optimizations   | Incremental | Debuginfo | Before [MiB] | After [MiB] | Reduction |
|-----------------|-------------|-----------|-------------:|------------:|----------:|
| No (`dev`)      | No          | No        |          462 |         336 |    -27.3% |
| No (`dev`)      | Yes         | No        |          683 |         558 |    -18.3% |
| No (`dev`)      | No          | Yes       |          874 |         748 |    -14.4% |
| No (`dev`)      | Yes         | Yes       |         1325 |        1199 |     -9.5% |
| Yes (`release`) | No          | No        |          397 |         253 |    -36.3% |

[^build-cmd]: The full command was `cargo +nightly build --no-default-features -Zno-embed-metadata`.

As you can see, the benefits are most notable when building in `release` mode, or in general without
debuginfo or incremental compilation, as their size will usually dwarf the duplicated metadata contents.
Nevertheless, the disk space savings are quite nice, in my opinion.

Originally, I was also hoping that this could speed up compile times a little bit, as less data has
to be written to disk, but from my experiments it seems that the effect is rather miniscule, at least
on a Linux system with an SSD disk.

*[SSD]: Solid-state drive

One of the reasons why I wanted this flag to exist was to slightly reduce the size of the distributed
Rust compiler toolchain, particularly the standard library `.so` file. I didn't get a chance to do
a full benchmark yet, as it's a bit annoying to dogfood a Cargo feature, because I have to wait
until the Cargo change reaches the `beta` channel, so that I could use it for compiling the compiler
itself (the first stage of `rustc` is compiled using the `beta` compiler/Cargo), which will take
several weeks.

However, I did some initial local tests, and it seems that using this flag reduces the size of the `x86_64-unknown-linux-gnu`
standard library `.so` file from ~13 MiB to ~3 MiB, which seems nice.

## Stabilization plan

I think that unless we find some major issues, we should make the `-Zno-embed-metadata` behavior
the default in Cargo, to reduce the disk space usage of the `target` directory for everyone.
Currently, it seems like it might be considered to be a backwards compatibility break though, as the Cargo
team is unsure if some people weren't relying on the metadata being present in the `.rlib`
files. In general, it's quite tricky to determine whether something is a breaking change in Cargo or
not, if it hasn't been previously documented ([Hyrum's Law](https://www.hyrumslaw.com/) is ever-present).

In terms of how to technically perform the migration, I think that we could use the new behavior by default
on the `nightly` toolchain for some time[^lld-nightly] to find potential issues in the wild,
and flip the Cargo flag to allow opting out of (instead of opting in) the new behavior
(so it would essentially become `-Zembed-metadata`).

[^lld-nightly]: Same as we did with the [lld](https://blog.rust-lang.org/2024/05/17/enabling-rust-lld-on-linux/) linker.

If you are interested in the future of this feature, you can observe its status in
the [rustc](https://github.com/rust-lang/rust/issues/139165) and [Cargo](https://github.com/rust-lang/cargo/issues/15495) tracking issues.

## Conclusion

I would be interested in how this flag fares in real-world scenarios, whether it causes any issues,
and how much disk space it can save. If you would like to try it out, use a recent `rustc` and Cargo
and build your project using e.g. `cargo +nightly build -Zno-embed-metadata`. You can use e.g.
[this script](https://gist.github.com/Kobzol/72d9c6cbade6499206859e09e06760f1) as an inspiration for
benchmarking the effect of the flag.

If you try it out, please let me know about your results on [Reddit]({{ page.reddit_link }})!
