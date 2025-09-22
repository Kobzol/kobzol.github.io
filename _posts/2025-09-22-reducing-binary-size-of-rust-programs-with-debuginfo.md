---
layout: "post"
title: "Reducing binary size of (Rust) programs with debuginfo"
date: "2025-09-22 13:00:00 +0200"
categories: rust
#reddit_link: TODO
---

**TL;DR**: There are some [ways](#how-can-we-reduce-the-binary-size) how you can reduce the binary size of (Rust) programs that contain debug information. 

Perhaps contrary to popular belief, Rust binaries can actually be [quite small](https://github.com/johnthagen/min-sized-rust) if you spend some effort on it. However, once you start including debug information (debuginfo) in them, the binary sizes typically start increasing at an alarming rate.

> If you wonder why we should care about binary size when debuginfo is enabled, as that's typically used for debug builds, it is also commonly used for distributing release/production binaries that include at least debug line tables, which are needed to produce quality backtraces.

In this post, I'll shortly describe why debuginfo takes so much space in Rust programs and how we can optimize it. Note that I will only talk about the DWARF debuginfo format and Linux ELF binaries. Furthermore, I will only be considering debuginfo embedded directly in the binary. If you distribute "split" debuginfo in a separate file, you might not care about its size so much, but that approach has other trade-offs, and I won't consider it in this post.

## Why does debuginfo take so much space?

Apart from (DWARF) debuginfo generally taking quite a lot of space on its own, there is a less obvious reason why debuginfo in binaries can be so large, and that is because linkers typically do not "tree-shake" unused debuginfo (unlike unused code, which gets removed). I only found out about this recently, which was the motivation for writing this post.

Let's try to demonstrate that with a simple example. Consider the following crate (let's call it `dep`), which has a single function `foo`:

```rust
pub fn foo() { println!("foo"); }
```
and another crate called `mycrate` that depends on `dep` and calls its `foo` function:
```rust
fn main() {
    dep::foo();
}
```
When compiled with Rust `1.90.0` on x64 Linux in `--release` mode, the resulting `mycrate` binary has exactly `449328` bytes.

If I add another function bar to the `dep` crate, without changing anything else:
```rust
pub fn foo() { println!("foo"); }
pub fn bar() { println!("bar"); }
```
and recompile, the resulting binary still has the exact same size as before. And that is what I would expect, because the `bar` function is not called anywhere, so it should not take space in my binary.

However, the situation changes if I add debuginfo. If I compile the main crate with two versions of `dep` (just `foo` vs `foo + bar`) in release mode with `debug = "line-tables-only"`, the size of the binary jumps from `3874080` bytes to `3874232` bytes! So even if the `bar` function is not used anywhere, its debuginfo is still taking space in my binary :angry: This is not so bad for a single function, but if you consider the amount of code that Rust programs typically depend on, and how much of that code is actually unused, it starts to quickly add up.

This also explains why the binary size suddenly jumped to almost 4 MiB with debuginfo enabled; that is the debuginfo of the standard library being included in it. Even though a lot of it is actually unused/dead code (because my program doesn't use these parts of the stdlib), its whole debuginfo is still included. Even though the stdlib is a bit special in this regard, because it is precompiled, the same would actually happen with a "normal" crate dependency that you build from scratch.

I'm not really an expert on linkers, but from what I understand, when linkers see debuginfo entries that are unused, they do not remove them, but merely mark them with special "tombstone" values. So they effectively become just dead weight that takes space in the binary, but don't do anything. At least this is what MaskRay (who is probably one of the most knowledgeable persons about linkers) [says](https://maskray.me/blog/2021-02-28-linker-garbage-collection#debug-sections). Apparently, removing these debuginfo sections in linkers could be very costly in terms of performance, due to DWARF's tree representation. I found [this](https://groups.google.com/g/llvm-dev/c/gcEs4ITJI_A/m/lwy9_pR4CQAJ?pli=1) forum post where someone claims that they tried to implement it in the LLD linker, and that made it seven times slower. I'm somewhat dubious that this is the best that we could achieve, but for now it seems that linkers simply do not remove unused debuginfo entries and we have to live with that. Maybe a [sufficiently smart](https://github.com/davidlattimore/wild) linker will be able to do it one day :)

Of course, this problem is not unique to Rust, as it also happens for other "natively compiled" languages, such as C or C++. However, for Rust I think that the issue is typically worse than for C/C++, because Rust programs tend to both have a lot of dependencies, and crucially if you compile them with debuginfo, by default you will be building debuginfo for every. single. dependency. that you have, even though most of that debuginfo will likely never be needed. I think that this is not so prevalent for C or C++, because there people often use prebuilt libraries for which they either might not have debuginfo available, or it is fetched through some external mechanism (e.g. `-dbg` packages from the distro package repository) and is thus not embedded directly into the final binary.

## How can we reduce the binary size

As usually, I'll use [hyperqueue](https://github.com/It4innovations/hyperqueue) as a test subject for demonstrating how we can reduce the binary size when debuginfo is included. I tried it in two configurations, the first is simply compiling with `--release`, while the second is compiling with `--profile dist`, which in HQ's case enables more optimizations (1 CGU, thin LTO, etc.). This is the actual configuration that we use for distributing `hyperqueue` to end-users. Both configurations include `line-tables-only` debuginfo.

*[CGU]: Codegen Unit
*[LTO]: Link-Time Optimizations

### Garbage collection

One approach that can be used to reduce debuginfo binary size is to perform garbage collection. That finds the unused placeholder ("tombstone") values and gets rid of them. There are probably more ways of doing that, but I found that the `llvm-dwarfutil`[^llvm-dwarfutil] tool can do it, so I tried it:

```bash
$ llvm-dwarfutil hq hq-gc
```

Here are the results:

| **Version** | `release` profile |     `dist` profile |
|-------------|------------------:|-------------------:|
| Original    | `70924912` (100%) |  `50832304` (100%) |
| GC      	   |  `59046440` (83%) | `53162184`  (104%) |

For the `release` profile, it resulted in a nice 17% binary improvement, not bad! However, for the more optimized (and smaller) `dist` profile, the resulting binary is actually larger. So it seems that sometimes it doesn't really help.

[^llvm-dwarfutil]: Sadly, this binary is currently not distributed in the rustup `llvm-tools` component, so you'll need to get it from elsewhere. On Ubuntu it seems to be contained in the `llvm-<version>` packages installable through `apt`.

However, when it does help, this approach doesn't really have any disadvantages, as far as I am aware (but if you know of any, I'd be glad to learn!), so it still seems quite useful. It did print a warning about not supporting the `.debug_gdb_scripts` section, and some other warnings, but the resulting binary seems to work and produce correct backtraces. The garbage collection took under two seconds.

When I tried to apply the garbage collection to a hello world Rust application compiled in `--release` with debuginfo, it reduces the size from the original ~4 MiB down to ~2 MiB. Not bad at all! Seems like it is able to remove a lot of the unused debuginfo from the Rust standard library.

### Debuginfo compression

The second approach, which we actually use on our CI, and which is probably more widely known, is using debuginfo compression. This can be done using the venerable `objcopy` tool:

```bash
$ objcopy --compress-debug-sections=zlib hq hq-zlib
```

I tried both `zlib` compression (which took ~1s to compress) and `zstd` (which took ~0.1s to compress). Here are the results:

| **Version**   | `release` profile |    `dist` profile |
|---------------|------------------:|------------------:|
| Original      | `70924912` (100%) | `50832304` (100%) |
| `zlib`      	 |  `24775848` (35%) | `18751280`  (37%) |
| `zstd`      	 |  `23413992` (33%) | `17472960`  (34%) |

The results are pretty great! Going from ~50 MiB down to ~18 MiB is really impressive.

I suppose that the disadvantage of this approach is the risk that some tools that work with debuginfo (such as debuggers, profilers or symbolizers) won't be able to understand the compressed debuginfo sections or won't be able to decompress them. This is especially problematic for `zstd`, which is less supported "in the wild". Even here, when I ran the `zstd` compressed binary and it panicked, the stacktrace no longer contained proper line numbers (I guess that `gimli`, which is included in the stdlib and AFAIK deals with decoding the backtraces, can't deal with `zstd`?). That is why we use `zlib`[^zlib-gnu] for our distributed `hyperqueue` artifacts, even though it produces slightly larger binaries than `zstd`.

[^zlib-gnu]: Actually, we use `zlib-gnu`, but I don't remember why anymore :sweat_smile:.

Interestingly, these approaches can be combined to produce even smaller binaries, by first running gargage collection and then compression (the other direction doesn't really make sense). And funnily enough, compressing the garbage-collected `dist` binary, which is actually larger than the *original* binary, produces a smaller file than compressing the original `dist` binary!

Here are the final results with all the approaches I described above:

| **Version** | `release` profile |    `dist` profile |
|-------------|------------------:|------------------:|
| Original    | `70924912` (100%) | `50832304` (100%) |
| GC          |  `59046440` (83%) | `53162184` (105%) |
| `zlib`      |  `24775848` (35%) |  `18751280` (37%) |
| GC + `zlib` |  `20457568` (29%) |  `17318760` (34%) |
| `zstd`      |  `23413992` (33%) |  `17472960` (34%) |
| GC + `zstd` |  `19777752` (28%) |  `16492768` (32%) |

You can find the script that I used to generate this table [here](https://gist.github.com/Kobzol/71f040d6d3a4b356afcdde20fc47dc81), in case you wanted to perform a similar experiment on your own binaries.

On hyperqueue's CI, we currently only [compress](https://github.com/It4innovations/hyperqueue/blob/main/.github/workflows/build.yml#L62) the debuginfo using `objcopy`, but based on these results, we might want to also use the debuginfo GC in the future (although getting ahold of `llvm-dwarfutil` on CI might be a bit annoying).

## Should we do this by default?

A natural question to ask is whether the Rust compiler should do any of the above by default. Last year, I made `--release` Rust binaries [smaller by default]({% post_url 2024-01-23-making-rust-binaries-smaller-by-default %}) by stripping the standard library debuginfo from them when it wasn't required. I think that was a pretty successful initiative, and it is relatively similar to what I described in this post (the compiler invokes a `strip` binary on the binary to remove the debuginfo, while here we invoke `llvm-dwarfutil`/`objcopy`), so it might not be too far-fetched?

That being said, I think that compressing debuginfo goes too far in what I would expect that a compiler invocation would do for me, and has the trade-offs mentioned above. Maybe GC would be a better fit (in fact I expected that the linker already does it for me), but the linkers that we currently use don't seem to have this ability, and doing it post-compilation using e.g. `llvm-dwarfutil` might be unnecessarily slow? Testing this on some ludicrously large binary would probably be needed to get a better intuition about trade-offs involved in this.

Of course, if we ever wanted to do this, we would have to decide whether to do it by default (which would likely increase compile times) or whether we want to make it configurable. But in general, it probably seems too specialized to me to be in `rustc`. Maybe we could at least document it e.g. in the Cargo book or in [min-sized-rust](https://github.com/johnthagen/min-sized-rust).

## Conclusion

Anyway, I wanted to share this post to increase the awareness of compressing and garbage collecting debuginfo in (Rust) binaries, so that we can all ship less data to our users and avoid needless waste. Hopefully you found it useful.

I'm definitely not an expert in this area though, so if you have any suggestions/corrections/tips, I'd be glad to hear from you on [Reddit]({{ page.reddit_link }}).
