---
layout: "post"
title: "Making Rust binaries smaller by default"
date: "2024-01-23 18:26:00 +0100"
categories: rust cargo
---

Have you ever tried to compile a helloworld Rust program in `--release` mode? If yes, have
you *seen its binary size*? Suffice to say, it's not exactly small. Or at least it wasn't small
until recently. This post details how I found about the issue and my attempt to fix it in Cargo.

# Binary size analysis
I'm a member of the (relatively recently established)
[#wg-binary-size](https://www.rust-lang.org/governance/teams/compiler#Binary%20size%20working%20group) working group,
which is trying to find opportunities to reduce the binary size footprint of Rust programs and libraries.
Since I also maintain the [Rust benchmark suite]({% post_url 2023-08-18-rustc-benchmark-suite %}), my main
task within the working group is to improve our tooling that measures and tracks the binary size of Rust programs.

As part of that effort, I recently added a new [command](https://github.com/rust-lang/rustc-perf/pull/1772) to
the benchmark suite, which allows examining and comparing the sizes of individual sections and symbols of a Rust
binary (or a library) between two versions of the compiler.

The output of the command looks like this:

![Output of the binary analysis command](/assets/posts/cargo-strip-release-binaries/binary-size-analysis.png)

While testing the command, I noticed something peculiar. When compiling the test binary in release mode
(using `--release`), the analysis command showed that there are (DWARF) debug symbols in the binary. My
immediate reaction was that I have a bug in my command and that I have to be compiling in debug mode by accident.
Surely Cargo wouldn't add debug symbols to my binary in release mode by default, right? Right?

<details markdown=1>
<summary>My reaction to Cargo's behavior</summary>

![Anakin/Padmé meme about Cargo and debug symbols](/assets/posts/cargo-strip-release-binaries/cargo-meme.jpeg)

</details>

<br />

I spent maybe 15 minutes looking for the bug before I realized that there is no bug in my code. There *are* debug
symbols in each Rust binary compiled in release mode by default, and this has been true for a *long time*. In fact,
there is an [old Cargo issue](https://github.com/rust-lang/cargo/issues/4122) (almost 7-year-old, to be precise) that
mentions this exact problem.

# Why does this happen?
This is consequence of how the Rust standard library is distributed. When you compile a Rust crate, you don't also
compile the standard library[^build-std]. It comes precompiled, typically using Rustup, in the `rust-std` component.
To reduce download bandwidth[^reduced-size], it does not come in two variants (with and without debug symbols), but only in the
more general variant with debug symbols.

[^build-std]: Unless you use [`build-std`](https://doc.rust-lang.org/cargo/reference/unstable.html#build-std), which is
    however sadly still unstable.

[^reduced-size]: While at the same time, ironically, increasing the size of Rust binaries on disk.

On Linux (and also other platforms), the debug symbols are embedded directly in the object files of the library itself
by default (instead of being distributed via
[separate files](https://doc.rust-lang.org/cargo/reference/profiles.html#split-debuginfo)). Therefore, when you link
to the standard library, you get these debug symbols "for free" also in your final binary, which causes binary size
bloat.

This actually contradicts Cargo's [own documentation](https://doc.rust-lang.org/cargo/reference/profiles.html#debug),
which claims that if you use `debug = 0` (which is the default for release builds), the resulting binary will not contain
any debug symbols. But this is clearly not what happens now.

EDIT: Just to clarify, Cargo was putting the debuginfo of the Rust standard library into your program by default.
It was *not* including the debuginfo of your own crate in release mode by default.

# Why is it a problem?
If you take a look at the binary size of a Rust helloworld program compiled in release mode on Linux, you'll
notice that it has about ~4.3 MiB[^rustc-version]. While it's true that we have a lot more disk space
today than in the past, that's still abhorrently much.

[^rustc-version]: Tested with `rustc 1.75.0`.

Now, you might think that this is a non-issue, because anyone who wants to have smaller binaries simply strips them.
That is a good point - in fact, after stripping the debug symbols from the mentioned helloworld binary[^strip-cmd],
its size is reduced to merely `415 KiB`, only about 10% of the original size. However, the devil is in the ~~details~~
defaults.

[^strip-cmd]: For example with `strip --strip-debug <binary>`.

And **defaults matter!** Rust advertises itself as a language that produces highly efficient and optimal code, but this
impression isn't really supported by a helloworld application taking more than 4 megabytes of space on disk. I can
imagine a situation where a seasoned C or C++ programmer wants to try Rust, compiles a small program in release
mode, notices the resulting binary size, and then immediately gives up on the language and goes to make fun of
it on the forums.

Even though the issue goes away with just a single `strip` invocation, it is still a problem in my view. Rust tries to
appeal to programmers coming from many different backgrounds, and not everyone knows that something like stripping
binaries even exists. So it is important that we do a better job here, *by default*.

> Note that the size of the `libstd` debug symbols is around 4 megabytes on Linux, and this size is constant, so even
> though for helloworld it takes ~90% of the size of the resulting binary, for larger programs its effect will be smaller.
> But still, four megabytes is nothing to sneeze at, since it is included in every Rust binary built everywhere by default.

# Proposing a change to Cargo
After I have realized that this is the default behavior of Cargo, I have actually remembered that I have just
rediscovered this exact issue perhaps for the third time already. I have just never really acted upon it before and then
always managed to forget about it.

This time, I was determined to do something about it. But where to start? Well, usually it's not a bad idea to just
ask around on the [Rust Zulip](https://rust-lang.zulipchat.com/), so I did [exactly that](https://rust-lang.zulipchat.com/#narrow/stream/246057-t-cargo/topic/Setting.20.60strip.3Ddebuginfo.60.20by.20default.20when.20.60debug.3D0.60).
It turns out that I wasn't the first person to ask that very same question, and that it came up multiple times over the years.
The proposed solution was to simply strip debug symbols from Rust programs in release mode by default, which would remove
the binary size bloat problem. In the past, this used to be blocked by the stabilization of `strip` support in Cargo,
but that has actually already happened back at the
[beginning of 2022](https://github.com/rust-lang/cargo/blob/master/CHANGELOG.md#cargo-159-2022-02-24).

So, why wasn't this proposal implemented yet? Were there any big concerns or blockers? Well, not really. When I
have asked around on Zulip, pretty much everyone thought that it would be a good idea. And while there were some
earlier attempts to do this, they haven't been pushed through.

So, to sum up, it hasn't been done yet because no one had done it yet :) So I set out to fix that. To test
if stripping by default could work, I created a PR to the compiler and started a perf benchmark. The binary size
[results](https://perf.rust-lang.org/compare.html?start=e004adb5561b724ac18f5b24584648ca4e42b6ad&end=9d280f70157edca19af117734c1223f5dd0dcd52&stat=size%3Alinked_artifact&tab=compile) (for tiny crates) looked pretty good, so that gave me hope that the approach of stripping by default
could indeed work.

Funnily enough, this change also made compilation time of tiny crates (like helloworld) up to
[2x faster](https://perf.rust-lang.org/compare.html?start=e004adb5561b724ac18f5b24584648ca4e42b6ad&end=9d280f70157edca19af117734c1223f5dd0dcd52&stat=instructions%3Au&tab=compile)
on Linux! How could that be, when we're doing more work, by including stripping in the compilation process? Well,
it turns out that the default Linux linker ([`bfd`](https://ftp.gnu.org/old-gnu/Manuals/ld-2.9.1/html_chapter/ld_5.html))
is brutally slow[^bfd-speedup], so by removing the debug symbols from the final binary, we actually reduce the amount
of work the linker needs to perform, which makes compilation faster. Sadly, this has an observable effect only for really
tiny crates.

> There is an ongoing effort to use a faster linker (`lld`) by default on Linux (again, defaults matter :smile:). Stay tuned! 

[^bfd-speedup]: Although recently, there have been an [effort](https://www.youtube.com/watch?v=h5pXt_YCwkU) to speed it up.

After showing these results to the Cargo maintainers, they have [asked](https://rust-lang.zulipchat.com/#narrow/stream/246057-t-cargo/topic/Setting.20.60strip.3Ddebuginfo.60.20by.20default.20when.20.60debug.3D0.60/near/408965413)
me to write down a [proposal](https://github.com/rust-lang/cargo/issues/4122#issuecomment-1868318860)
on the original Cargo issue. In this mini-proposal, I have explained what change to the Cargo defaults I want to make,
how it could be implemented, and what are other considerations of the change.

For example, one thing that was noted is that if we strip the debug symbols by default, then backtraces of release builds
will… not contain any debug info, such as line numbers. That is indeed true, but my claim is that these have not been useful
anyway. If you have a binary that only has debug symbols for the standard library, but not for your own code, then even
though the backtrace will contain some line numbers from `stdlib`, it will not really give you any useful context (you
can compare the difference [here](https://gist.github.com/Kobzol/27ad8fa8aae1ccb7642925ab99ca8897)).
There were also some implementation considerations, for example how to handle situations where only some of your target's
dependencies request debug symbols. You can find more details in the
[proposal](https://github.com/rust-lang/cargo/issues/4122#issuecomment-1868318860).

After I wrote the proposal, it went through the FCP process. The Cargo team members [voted](https://github.com/rust-lang/cargo/issues/4122#issuecomment-1868371491)
on it, and once it was [accepted](https://github.com/rust-lang/cargo/issues/4122#issuecomment-1891039373) after a
10-day waiting period designed for any last concerns (the FCP), I could [implement](https://github.com/rust-lang/cargo/pull/13257)
the proposal, which was actually surprisingly straightforward.

*[FCP]: Final Comments Period

The PR has been [merged](https://github.com/rust-lang/cargo/pull/13257#issuecomment-1892589315)
a week ago, and it is now in nightly! :tada:

The TLDR of the change is that Cargo will now by default use `strip = "debuginfo"` for the `release` profile
(unless you explicitly request debuginfo for some dependency):
```toml
[profile.release]
# v This is now used by default, if not provided
strip = "debuginfo"
```

In fact, this new default will be used for *any profile* which does not enable debuginfo anywhere in its dependency
chain, not just for the `release` profile.

There was one unresolved concern about using `strip` on macOS, because it seems that there can be some
[issues](https://github.com/rust-lang/cargo/issues/11641) with it. The change has been in nightly for a week and
I haven't seen any problems, but if this will cause any issues, we can also perform the debug symbols stripping selectively,
only on some platforms (e.g. Linux and Windows). Let us know if you find any issues with stripping using Cargo on macOS!

# Conclusion
In the end, this was yet another case of "if you want it done, just do it", which is common in open-source projects :)
I'm glad the change went through, and I hope that we won't find any major issues with it and that it will be stabilized
in the upcoming months.

If you have any comments or questions, please let me know on [Reddit](https://www.reddit.com/r/rust/comments/19dwxel/making_rust_binaries_smaller_by_default/).
