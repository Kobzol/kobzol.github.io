---
layout: "post"
title: "Speeding up the Rust compiler without changing its code"
date: "2022-10-27 09:57:00 +0200"
categories: rust rustc
reddit_link: https://www.reddit.com/r/rust/comments/yeunrs/speeding_up_the_rust_compiler_without_changing/
---

…Yes, I know that the title looks like a clickbait. But it's actually not that far from the truth :)

I have started contributing to `rustc` this year as a part of the
[`#wg-compiler-performance`](https://www.rust-lang.org/governance/teams/compiler#Compiler%20performance%20working%20group),
which is focused on making the Rust compiler as fast as possible. This post describes some things
that I and several other `rustc` developers have been working on for the last several months in order
to help fulfill this goal.

What's possibly a bit unusual is that most of my efforts weren't focused on improving the source code
of `rustc` itself, but rather on improving the way we compile/build `rustc` in order to make sure
that it's as efficient as possible.

There is a tracking issue that tracks `rustc` build optimizations [here](https://github.com/rust-lang/rust/issues/103595).

I'll try to talk about the individual changes in chronological order, but some them were overlapping,
so it might not match up perfectly. I will also add links to PRs, performance results and
mean/max. improvements to each section where it is applicable. The efforts mentioned here were done
with the help and guidance of many other `rustc` developers ([@nnethercote](https://github.com/nnethercote),
[@lqd](https://github.com/lqd), [@Mark-Simulacrum](https://github.com/Mark-Simulacrum), [@bjorn3](https://github.com/bjorn3)
and many others). I'm very thankful for their continued help and assistance.

# How was `rustc` built at the start of 2022?
Before we begin talking about the improvements that were made this year, I'll try to describe how
was `rustc` built for Linux targets on CI at the beginning of 2022. We will see at the end
of the blog post that the pipeline has been modified since then, but it's still quite similar.
This build pipeline is used for building the actual release artifacts that are distributed via
e.g. `rustup` and eventually find their way to Rust end-users (on Linux). 

1. LLVM is built with PGO instrumentation (LLVM build #1).
2. `rustc` that uses LLVM #1 is built.
3. PGO profiles for LLVM are gathered by compiling `libcore`.
4. LLVM is built (LLVM build #2).
5. `rustc` that uses LLVM #2 is built with PGO instrumentation.
6. PGO profiles for `rustc` are gathered by compiling some popular/big crates, like `cargo`,
plus some stress tests.
The compilation is performed using the [`rustc-perf`](https://github.com/rust-lang/rustc-perf)
performance suite.
7. LLVM is built with the PGO profiles gathered in step 3 (LLVM build #3).
8. `rustc` that uses LLVM #3 is built with the PGO profiles gathered in step 6.

*[PGO]: Profile-guided optimizations

<details markdown=1>
<summary>What is PGO?</summary>

Profile-guided optimization is a technique for optimizing programs. It observes how does a program
behave when it executes some common workload, and then uses this information to better optimize the
program.

PGO workflow usually works like this:

1. You compile the program with "instrumentation", which is additional code injected by the compiler.
2. You run the program on some workload that represents its common usage. When the program is executed,
the injected code takes note about the program's behavior. What functions are called the most?
What parts of functions are almost never executed? Which branches are often taken?
The injected code records and stores this data in a profile (a file or a set of files).
3. You re-compile the program again, but this time you provide the gathered profile, so that the
compiler can optimize the program in a better way.
4. You enjoy a faster, more efficient program.
5. ????
6. Profit!!!

</details>

This build pipeline is implemented in the
[`pgo.sh`](https://github.com/rust-lang/rust/blob/85d089b41e2a0c0f07ab34f6c5a7c451389f25e6/src/ci/pgo.sh)
bash script (although I'm planning to rewrite it in Python soon). It has to recompile both LLVM
and `rustc` several times, therefore it takes quite a lot of time (about 1.5 hours). The PGO gathering
steps are performed separately for LLVM and `rustc`, which prolongs the time (originally these steps
were performed at once, but there were some issues with this approach).

Now that we have a high-level overview of how the build pipeline works, let's take a look at how
we have tried to improve it this year and how it has evolved in the process.

# Expanding LLVM PGO profiling ([#94704](https://github.com/rust-lang/rust/pull/94704))
While reading the build pipeline above, maybe you have wondered why do we gather the PGO profile for
LLVM on the `libcore` crate only, while `rustc` enjoys being profiled on real-world crates. I have
wondered about this too, so I have tried to change it in this [PR](https://github.com/rust-lang/rust/pull/94704).

It took some back and forth to experiment with the set of crates that it made sense to profile before
we started hitting diminishing returns, but otherwise it was a pretty simple change, and provided
very nice gains! Note that when we gather LLVM PGO profiles, we always perform codegen
(we do not profile `check` builds), since we only care about profiling the LLVM codegen backend,
not the `rustc` frontend.

[Final results (instruction counts)](https://perf.rust-lang.org/compare.html?start=b2763cc4cfa761a1d42cc01c7603ba6a98c09ecd&end=ebed06fcba3b58913a5087039a81478d43b47b2f):
- Mean improvement: -2.48%
- Max improvement: -5.56%

# Updating LLVM ([#95171](https://github.com/rust-lang/rust/pull/95171))
Sometimes it helps just to bump dependencies. On CI, we use a host compiler (LLVM) to compile
a target compiler (also LLVM), which is then used by `rustc` to compile Rust programs.
In [#95171](https://github.com/rust-lang/rust/pull/95171), I have updated the host LLVM from `13.0.0`
to `14.0.2`. It didn't help much with compilation speed, but it had a great effect on max RSS
(a metric that measures the peak memory usage of `rustc` during crate compilation).

Why did this help? We have compiled LLVM with a newer compiler, which reduced the memory usage of
LLVM when it was used by `rustc`, thus also reducing the memory usage of compiling Rust crates.

[Final results (max RSS)](https://perf.rust-lang.org/compare.html?start=b2c2a32870e15af02eb89de434c36535439dbf5a&end=1388b38c52d1ca9fbc80bf42fa007504fb0b1b41&stat=max-rss):
- Mean improvement: -4.75%
- Max improvement: -12.34%

# Updating the PGO benchmark suite ([#95724](https://github.com/rust-lang/rust/pull/95724))
This year, there has been an [effort](https://hackmd.io/d9uE7qgtTWKDLivy0uoVQw) to update the
benchmarks in the `rustc-perf` benchmark suite, which is used both for measuring the performance
of `rustc` after each merged commit (the [perf.rlo](https://perf.rust-lang.org/) dashboard), but also
for local experiments and profiling done by `rustc` developers. Old benchmarks have been deprecated,
similar benchmarks were merged, new benchmarks were introduced and some popular crate benchmarks were
updated to newer versions of said crates.

Even though the suite itself was updated, the CI build script was still using an old version from
May 2021 for gathering the PGO profiles. Therefore, in [#95724](https://github.com/rust-lang/rust/pull/95724)
I have updated the version of `rustc-perf` used in CI, along with the set of crates that we compile
to gather PGO profiles.

This change resulted in performance wins, but it was also a kind of self-fulfilling prophecy, as we
were now PGO profiling `rustc` on an exact subset of crates that were also later used to measure the
performance of `rustc`. That being said, I think that it makes sense to update the PGO crates regularly.
It's better if `rustc` compiles modern, heavily used (versions of) crates as efficiently as possible,
rather than being super optimized for older crate versions that are no longer being used.

[Final results (instruction counts)](https://perf.rust-lang.org/compare.html?start=4bb685e4714a2b310774f45c3d023d1743de8bd0&end=399dd8049d4b27329350937e3e17077205bdc0bf)
- Mean improvement: -0.75%
- Max improvement: -2.71%

# Trying out PGO on macOS ([#96732](https://github.com/rust-lang/rust/pull/96732))
At this point in time, PGO was only being performed for Linux, so Windows and macOS (and of course
also other targets!) were being left out of possibly 10-20% performance improvements that PGO can
provide.

In [#96732](https://github.com/rust-lang/rust/pull/96732), I have tried to apply PGO also on macOS
to see what happens. It seemed like it could work, but the problem turned out to be in the duration
of the CI builds. The macOS runners on GitHub are incredibly slow. To put this into perspective, at
this point in time, the Linux builds took about 1.5 hours, and that was with the full build pipeline
described above, which rebuilds both LLVM and `rustc` three times! While the macOS builds took about
two hours, with LLVM pre-built and `rustc` being built only once[^1].

[^1]: Well, we always do stage 2 builds, so each `rustc` "build" actually compiles the compiler two times, but that's another story.

It seems like there might be some improvements to macOS CI `rustc` performance on the horizon, but
for now, this was an unsuccessful experiment.

Another idea that I tried was to download the PGO profiles from earlier Linux builds and try to
use them for optimizing macOS `rustc` builds (thus skipping the slow PGO gathering and LLVM/`rustc`
rebuild steps), but it seemed that it's not so trivial to reuse PGO artifacts between platforms
(which was kind of to be expected, to be honest), mainly because of symbol issues. 

# Improving precision of `rustc` PGO ([#97110](https://github.com/rust-lang/rust/pull/97110))
When you use a PGO instrumented `rustc`, it will write the gathered profiles to a single file by
default. When [@lqd](https://github.com/lqd) was trying to port the PGO pipeline to Windows, he noticed
that this file was sometimes being overwritten when `rustc` was being invoked concurrently.
While this didn't seem to cause any issues on Linux, I wondered if this overwriting was affecting
the profiles in any way.

That's why in [#97110](https://github.com/rust-lang/rust/pull/97110), I have tried to tell `rustc`
to use a separate profiling file for each `rustc` process (basically I added the PID to the filename).
And it has helped! Probably now that the file wasn't being overwritten, the profiles were more
precise and therefore `rustc` could use them to better optimize itself.

As a slight disadvantage, creating so many profiles resulted in 20+ GiB of disk space being used, but
that wasn't a large problem, since the profile files are created on CI, and they are temporary anyway,
as we then merge them to a single, rather small (tens/hundreds of MiB) file after the profiling is done.

[Final results (instruction counts)](https://perf.rust-lang.org/compare.html?start=a084b7ad35adb508bd2e053fc2a1b9a53df9536c&end=e5732a21711e7cefa6eb22e1790406b269d6197a)
- Mean improvement: -0.34%
- Max improvement: -1.23%

# Applying PGO to `libstd` ([#97038](https://github.com/rust-lang/rust/pull/97038))
Although we use PGO for LLVM and `rustc`, I was thinking that we could also use it for `libstd`.
So far, I haven't been able to get it working properly, but it's still definitely on my TODO list.

# Updating `rustc` PGO benchmark list ([#97120](https://github.com/rust-lang/rust/pull/97120))
In [#97120](https://github.com/rust-lang/rust/pull/97120), I have further updated the set of crates
that is used to gather PGO profiles for `rustc`, as the old set was missing trait heavy crates
like `diesel`. Although this change has helped the most on the crates that were added to the PGO set
(as expected), it also seemed to help across the board, so we had assumed that we weren't overfitting
too much to the PGO crates, and decided to merge this change.

[Final results (instruction counts)](https://perf.rust-lang.org/compare.html?start=222c5724ecc922fe67815f428c19f82c129d9386&end=ee160f2f5e73b6f5954bc33f059c316d9e8582c4&stat=instructions:u)
- Mean improvement: -0.51%
- Max improvement: -1.29%

# Improving precision of LLVM PGO ([#97137](https://github.com/rust-lang/rust/pull/97137))
This was basically the same thing that I have described above (adding PID to PGO profile filenames),
but this time for LLVM rather than `rustc`. This turned out to be a bit more involved because LLVM
uses a different approach for setting the profile paths than `rustc`, but it wasn't that complicated
in the end, and it has resulted in a small, but nice win.

[Final results (instruction counts)](https://perf.rust-lang.org/compare.html?start=c7b0452ece11bf714f7cf2003747231931504d59&end=63641795406e1831a822f011242fdfb225fc8fbc&stat=instructions:u)
- Mean improvement: -0.63%
- Max improvement: -1.03%

# Trying out Call-Site aware PGO for LLVM ([#97153](https://github.com/rust-lang/rust/pull/97153))
In my quest of finding all the possible compiler knobs and techniques that could be used to optimize
`rustc`, I have stumbled on something called [Call-site aware PGO](https://llvm.org/devmtg/2020-09/slides/PGO_Instrumentation.pdf).
Up to that time, I had no idea that something like that has even existed, so I have naturally
immediately tried to apply it to `rustc`'s LLVM :)

The results were quite mixed. Some attempts did not result in any improvements at all,
some had quite nice [cycle wins](https://perf.rust-lang.org/compare.html?start=3b9cf893d0cd1236b988ac2401869eadc39eff76&end=caeb6dc8dd5a8bfe01904e193e82abed28bc5a42&stat=cycles:u).
But the problematic part was that CS-PGO is layered on top of the normal PGO workflow, so we needed
yet another rebuild of LLVM + `rustc`, which has of course made the CI build even slower.

Since it did not bring clear benefits, I have decided to abandon CS-PGO for now. But I think that
this definitely warrants another attempt some time in the future.

# Static linking of `rustc` ([#97154](https://github.com/rust-lang/rust/pull/97154))
While trying to examine what was the state of compiler knobs used for building `rustc`, I was a bit
confused by the apparent lack of LTO, a crucial compiler optimization technique. I refused to believe
that it was not being used for compiling `rustc`, but I couldn't find any trace of it.

As a short summary, when `rustc` compiles a crate, it splits the crate (and also its dependencies)
into multiple CGUs, pieces of code that are optimized separately by the codegen backend (usually LLVM).
This makes the compilation parallelizable, but it can also miss out on some optimizations, because
the codegen units are not optimized together, but each on their own. LTO has the ability to optimize
also across these codegen units, and thus potentially generating better code, at the cost of longer
compilation time.

*[LTO]: Link-time optimization
*[CGU]: Codegen unit

When you compile Rust programs with `rustc`, you can choose amongst three LTO modes (in addition to
turning LTO off completely):
- `crate-local thin LTO` - LTO is used to optimize across codegen units, but always only within
a single crate. This mode is used by default for `release` builds.
- `thin LTO` - LTO is used to also optimize across crates.
- `fat LTO` - same as `thin` LTO, but it can in theory optimize even better. But it also typically
makes compilation much slower than `thin` LTO.

After examining the situation, I learned that `rustc` was being compiled with the default
`crate-local thin LTO`. Since the compiler consists of 50+ crates and even more external
dependencies, it seemed to me that this very basic form of LTO wasn't doing it justice, and we
needed at least `thin` LTO to achieve better performance.

I wasn't able to apply thin LTO for `rustc` at that time (more on that in a later section below),
but I was able to force `rustc` to link statically and then use LTO for it. Normally, the compiler
is built in two parts. A dynamic shared library (`dylib`) called `librustc_driver.so` (which
exports all the important functions offered by the compiler, and which is used by other tools like
`rustdoc` or `clippy`) and `rustc`, a very thin binary that mostly just links to `librustc_driver.so`
and then calls its entry function. I have tried to change this in [#97154](https://github.com/rust-lang/rust/pull/97154)
to "inline" the dynamic library directly into `rustc` by statically linking it, and then to apply
`thin` LTO to it.

This has showed me a couple of interesting things:
- Using static linking, even without LTO,
[helps performance](https://perf.rust-lang.org/compare.html?start=a2cdcb3fea2baae5d20eabaa412e0d2f5b98c318&end=7288ad0fd327a539b7e8c597da7ce2f96ac7b3c4&stat=instructions:u)
(probably by removing dynamic function resolving), which is especially good for tiny crates, where
this takes a relatively large part of the whole compilation process (since it's so short when the
crate is small).
- Using (thin) LTO helps. [A lot!](https://perf.rust-lang.org/compare.html?start=dec689432fac6720b2f18101ac28a21add98b1b8&end=268d09249194cf2ba741a0398e14d8cc1de9cf0f&stat=instructions:u).
Although this perf. result also contains the wins gained by static linking, it still contains some
pretty impressive results. This gave me hope that LTO could be really useful, so I have further
continued to try to get it to work.
- Using fat LTO vs thin LTO does not seem like an obvious ([big win](https://perf.rust-lang.org/compare.html?start=268d09249194cf2ba741a0398e14d8cc1de9cf0f&end=f488095246805f2455f7bee92f747aeddd049af1&stat=instructions%3Au)),
but with fat LTO it takes much more time to compile `rustc`. So it might not be worth it to use it.

So, static linking it is? Well, not really. As I have learned by asking around, it would not really
be practical to link `rustc` statically, among other things because of the way codegen backends are used.
They are loaded into the `rustc` process directly via `dlopen`, and they expect that they will be able
to use the symbols from `librustc_driver.so`. Doing this with a statically linked binary that would
have to export these symbols seemed to be way too complicated. But it is probably something that
might get revisited in the future.

# Using PGO on Windows ([#96978](https://github.com/rust-lang/rust/pull/96978))
As a part of porting our optimized build pipeline to other platforms than Linux,
[@lqd](https://github.com/lqd) has managed, in a heroic effort, to port PGO to Windows.

I don't even want to imagine how much time and effort it must have taken, but the results speak for
[themselves](https://github.com/rust-lang/rust/pull/96978) :)

Sadly, we don't currently do any performance measurements on CI for other platforms than Linux, so
the results had to be verified manually on a Windows system.

# Using ICF for `rustc` ([#99062](https://github.com/rust-lang/rust/pull/99062))
While reading the [Rust for Rustaceans](https://nostarch.com/rust-rustaceans) book by the
one and only [@jonhoo](https://github.com/jonhoo), I was reminded of the
[polymorphization](https://rust-lang.github.io/compiler-team/working-groups/polymorphization/) initiative,
an experimental `rustc` optimization that tries to merge identical generic functions in order
to reduce the number of monomorphized functions that we send to LLVM and thus (potentially) greatly
reduce compilation times.

While polymorphization is sadly still probably far from being completed, I wondered whether we could
do a poor man's version of polymorphization, by merging together identical compiled functions
on the binary level. For example, I noticed that functions like `core::ptr::read<u32>` and
`core::ptr::read<i32>` were both stored in the final `rustc` binary, even though they had identical
instructions. It turns out that there's a name for this technique -
[Identical Code Folding](https://tetzank.github.io/posts/identical-code-folding/).

To use this technique, I had to switch the linker that we use on CI to `lld`, the linker from the
LLVM suite. With that, I was able to use the `--icf=all` flag to (very aggressively) prune the
duplicated functions during linking.

I had hoped that ICF would decrease the binary size of `librustc_driver.so`, and it did, but only
[very slightly](https://github.com/rust-lang/rust/pull/99062#issuecomment-1179524667) (~1%),
probably because switching from `ld` to `lld` has actually increased the binary size by ~3%, so the
baseline was different.

Using ICF didn't improve instruction counts (expectedly), but it had very nice wins for cycle counts,
probably because of better instruction cache utilization. Before, the duplicated functions were
located across different places in the binary, but now, after deduplication, they should be in the
same place, which should in turn improve i-cache utilization.

When examining the results in more detail later (after my PR has [broken](https://github.com/rust-lang/rust/issues/99440)
a few things), it turned out that most of the wins actually came from using `lld` as a linker, and
not ICF itself. Well, I don't really care, as long as the compiler gets faster :) A win is a win.

[Final results (cycles)](https://perf.rust-lang.org/compare.html?start=263edd43c5255084292329423c61a9d69715ebfa&end=246f66a905c2815f2c9b9c3d6b1e0649f3360ef8&stat=cycles:u)
- Mean improvement: -3.06%
- Max improvement: -6.11%

# Using BOLT to optimize LLVM ([#94381](https://github.com/rust-lang/rust/pull/94381))
I'm writing about BOLT as one of the last sections of this blog post, but it was actually one of the
first things that I have tried this year. It just took a long time to finish :)

BOLT was originally a [research project](https://research.facebook.com/publications/bolt-a-practical-binary-optimizer-for-data-centers-and-beyond/)
by ~~Facebook~~ Meta. It is a compiler optimization technique, which is partly similar to PGO,
although it works on the level of compiled binaries rather than on the level of compiler IR. In short,
it can gather profiles from a binary that is being executed, and then re-optimize said binary with
the gathered profiles. It can do all that without actually needing to re-compile the binary, which
is quite cool. By smartly moving stuff inside the binary around, it can improve i-cache utilization
and thus improve the performance, even if the binary was previously already optimized with LTO and/or
PGO.

*[IR]: Intermediate representation (of code)

Originally, BOLT has lived in a separate [repository](https://github.com/facebookincubator/BOLT)
(basically a fork of LLVM), but since LLVM 14 it has been integrated into the mainline LLVM repo.
This was a signal to me that BOLT is stable enough so that we can try to use it to optimize the Rust
compiler (*narrator voice: it wasn't stable enough*).

I had some troubles with applying BOLT to `rustc` itself (after all, it was mostly meant for C/C++
binaries), but someone (I don't remember who, maybe `@Mark-Simulacrum`) gave me the idea to try it
on the LLVM that we use in `rustc`. After all, it's a C++ program, and I found several demo examples
on GitHub that were using BOLT to optimize `clang`.

There are two ways BOLT can gather the profiles. Either by instrumenting (modifying the code of a
binary by injecting code that records execution metadata) or by sampling (gathering performance
counters during the execution of an unmodified binary).
The sampling approach is much simpler, since we don't have to instrument the binary, but sadly it
was a no-go, since the performance counters required for sampling (LBR) weren't available on GitHub
CI machines (and they aren't even available on AMD CPUs, which are in my local machine).

*[LBR]: Last branch record

Therefore, I had to resort to instrumentation. Sadly, this is where the problems have begun. The
instrumented LLVM library was nondeterministically segfaulting when being used by `rustc`. It was
very difficult to debug. I created and monitored several LLVM issues that were dealing with a similar
instability of BOLT, but that was all I could do at the time (without delving really deep into LLVM).
I was also trying to run the whole CI pipeline locally, which was sometimes working, sometimes not.
This "segfault non-determinism" didn't give me a lot of hope that this could be resolved without some
upstream BOLT patches, so I just had to wait until they will arrive.

My original attempt was in February, since then I have repeatedly (~every month) tried to apply
BOLT with the newest trunk LLVM version, but the results were mostly the same. This resulted in the
poor [PR](https://github.com/rust-lang/rust/pull/94381) having several tens of CI run attempts and
almost three hundred comments (most of them probably generated automatically by bots).

I think that the instability problems were caused by the fact that I was using BOLT in a slightly
non-standard way. Instrumentation probably wasn't supported as well as sampling, and I was also
trying to optimize a shared library, which was still quite experimental in BOLT, since it was mostly
focused on optimizing actual executable binaries.

Things started to finally turn better when LLVM 15 was released. With the updated LLVM that contained
a set of BOLT patches, the instrumentated `libLLVM.so` started working without crashes, and hopefully
it will stay that way :crossed_fingers:.

Once it was working, I was finally able to implement support for BOLT properly and perform performance
experiments. And the results weren't bad at all! Up to 10% max RSS improvements and up to 5% cycle
improvements on real-world crates. It seems like it was definitely worth it to "persevere" and wait
until BOLT gets stable enough so that we can use it.

The cost of this was of course yet another rebuild of LLVM and `rustc` in CI, which increased the
CI time by around 15-20 minutes. I think that in this case it was worth it, but the CI times will
probably need to be optimized soon, before it gets out of hand (more on that below).

[Final results (max RSS)](https://perf.rust-lang.org/compare.html?start=e495b37c9a301d776a7bd0c72d5c4a202e159032&end=8dfb40722da197e77a33a19eb9d3fd6512831341&stat=max-rss)
- Mean improvement: -3.97%
- Max improvement: -10.25%

[Final results (cycles)](https://perf.rust-lang.org/compare.html?start=e495b37c9a301d776a7bd0c72d5c4a202e159032&end=8dfb40722da197e77a33a19eb9d3fd6512831341&stat=cycles:u)
- Mean improvement: -3.67%
- Max improvement: -6.60%

# Using linker plugin LTO ([#101524](https://github.com/rust-lang/rust/pull/101524))
During the year, I was occasionally returning to my quest for using LTO for `rustc`. The results from
the static linking were great, but I knew that using static linking wasn't actually a usable solution,
so I needed to try something else. I still couldn't figure out using LTO for the `librustc_driver.so`
`dylib`, but I remembered that there is another way that LTO could be done, using so-called
[Linker-plugin-based LTO](https://doc.rust-lang.org/rustc/linker-plugin-lto.html).

This approach delegates the LTO work to the linker itself, rather than implementing it within the
compiler (in simplified terms). From the example given by Rust documentation, I thought that I had
to use `clang` as a linker to get it to work, which led me down a path of futile attempts to get
`clang` working as a linker on CI. Then I decided to scratch all that, and just add a single line
(`-Clinker-plugin-lto`) to the `rustc` build system… and lo and behold, it has worked! Using a single
line, I was able to achieve up to ~10% [improvements](https://perf.rust-lang.org/compare.html?start=57f097ea25f2c05f424fc9b9dc50dbd6d399845c&end=5cfc0ac435c3b70dbc499c8811c19f413ce3619a&stat=instructions:u)
on real-world crates, which was quite exciting.

There was also the possibility that `rustc` code could be cross-optimized with LLVM (this is one of
the motivations behind linker-plugin LTO), which sounds quite cool. But it would also require pretty
large changes in the `rustc` build process (I think) so I haven't attempted that (yet).

Sadly, after the initial excitement, I realized that this approach, while being quite helpful in
terms of `rustc` performance, had some issues, much like the static linking mentioned before:

- It basically required the usage of the `lld` linker, which might not be so easy to use on other
platforms than Linux. It would be a shame if such a fundamental performance gain wasn't readily
available on other platforms.
- It only supported thin LTO, not fat LTO (AFAIK), which also seemed like a slight disadvantage.
- I haven't been able to verify this yet, but I think that this could cause issues when
we update LLVM. Once every ~6 months, a new version of LLVM is released. The `rustc` repository
usually switches to the new version quite soon, months or weeks before the final version is released,
to prepare for it by making changes in its usage of LLVM. I think that after the next switch, the
linker plugin LTO would have a problem, since the LLVM used by `rustc` and the LLVM used to compile
`rustc` would get desynchronized, which could spell trouble for the linker-plugin LTO, which requires
LLVM IR compatibility. But I'm not sure if this would actually happen, it was just a potential problem
that has occurred to me.

Anyway, even though the wins were nice, in the meantime there was advance on the `dylib` LTO front
(see below), so I have abandoned this approach.

# Using LTO for optimizing `librustc_driver.so` ([#101403](https://github.com/rust-lang/rust/pull/101403))
I wasn't really moving anywhere with my attempts to apply LTO to the `librustc_driver.so` `dylib`.
I found a [topic](https://rust-lang.zulipchat.com/#narrow/stream/122651-general/topic/compiling.20rustc.20with.20LTO/near/282996049)
about using LTO for `rustc` on the Rust Zulip forum, so I tried to ask there. I got an answer from
`bjorn3`, who is IMO one of the leading experts on `rustc` backends, codegen, and basically anything
Rust :D His response wasn't very optimistic (you can read it in the topic link above), so I put LTO
to rest for some time.

It was still nagging me that we don't do LTO though, so after some time I reached out to `bjorn3`
directly and asked if he thought that there's any hope for `dylib` LTO. During that time, I also
tried static linking of `rustc` + LTO (as described above), which had very nice results, so it gave
us additional motivation to try using LTO for the `librustc_driver.so` `dylib`. After a bit of
nerd-sniping, `bjorn3` conjectured a way that it could be done in theory. He then returned after an
hour or so and wrote me that he got it working :laughing:.

This was the road that led to [#101403](https://github.com/rust-lang/rust/pull/101403). We needed
to resolve some issues (mostly cosmetic), but in the end it was not at all that difficult to get it
working (barring future issues, which tend to almost always come after such fundamental PRs :) ).

I volunteered to work on `bjorn3`'s groundwork, which turned out to be a very fun process, because
I couldn't push to `bjorn3`'s branch, so he always had to force-push a branch from my fork to his
fork's branch to update the PR. What a fun endeavour :)

Anyway, in the end the perf. results were pretty impressive (5-10% wins on real-world crates) :tada:.
It has also caused some max RSS regressions sadly, and the size of the `librustc_driver.so` was slightly
increased, but I think that this has been worth it for such a large performance boost.

Sometimes when a feature is missing, it's not because it's impossible or very difficult to implement
it, but because nobody has tried to implement it yet :)

After merging the LTO PR, I have tried to reapply linker-plugin LTO to compare its performance to
the `dylib` LTO approach. The [results](https://github.com/rust-lang/rust/pull/101524#issuecomment-1289342528)
hinted that linker-plugin LTO wasn't really more efficient, so I have decided not to pursue it further.

[Final results (instruction counts)](https://perf.rust-lang.org/compare.html?start=9be2f35a4c1ed1b04aa4a6945b64763f599259ff&end=1ca6777c014813e3bdb98d155562fc3d111d86dd&stat=instructions:u)
- Mean improvement: -4.10%
- Max improvement: -9.62%

# Conclusion
Thanks for reading up to this point! By now you have seen most of the `rustc` build pipeline
optimizations that we have been working on this year (and that I am aware of). To summarize, here
is the actual build pipeline of (Linux) `rustc` on CI, as of October 2022:

1. LLVM is built with PGO instrumentation (LLVM build #1).
2. `rustc` that uses LLVM #1 is built.
3. PGO profiles for LLVM are gathered by compiling several popular crates (`serde`, `ripgrep`, `clap`,
etc.).
4. LLVM is built (LLVM build #2).
5. `rustc` that uses LLVM #2 is built with PGO instrumentation.
6. PGO profiles for `rustc` are gathered by compiling several popular crates (`cargo`, `diesel`),
plus some stress tests.
7. LLVM is built with the profiles gathered in step 3 (LLVM build #3) and with BOLT instrumentation.
8. BOLT profiles for LLVM are gathered by compiling the same crates as in step 3.
9. LLVM is built with the PGO profiles gathered in step 3 and with the BOLT profiles gathered
in step 8 (LLVM build #4).
10. `rustc` that uses LLVM #4 is built with the PGO profiles gathered in step 6.

Build systems are fun :)

One of the reasons why I was and still am interested in these techniques is that most of them should
"scale", looking into the future. If you find a bottleneck in the compiler and optimize it, you can
get a really nice speedup. But if someone else comes later and rewrites or deletes that code, you
might need to optimize the same code again, or find another place where a bottleneck happens.
On the other hand, if you enable a build optimization technique, like PGO, LTO or BOLT, it should
improve the performance of the compiler after each and any change of the compiler's code, without
us needing to do anything more. This is what I mean by "scaling".

Of course, there's a limit to the amount of build/compilation optimizations that one can apply
(there's just not that many of them). But after a year of trying, I still feel like we're not at the
end :) Unfortunately, most of the demonstrated improvements have helped only Linux users, so one of
our goals going forward is to try to port these improvements to other (tier-1) platforms, like macOS
and Windows.

There are also some next steps that we're planning to explore (in no particular order):

- Use BOLT also for rustc ([PR](https://github.com/rust-lang/rust/pull/102487)) - so far the results
were lackluster.
- Use LTO for `rustdoc` ([PR](https://github.com/rust-lang/rust/pull/102885)) - haven't managed to
get any speed-ups so far.
- Use LTO on more platforms (macOS, Windows).
- Use PGO on more platforms (macOS).
- Try to use fat LTO for `librustc_driver.so` ([PR](https://github.com/rust-lang/rust/pull/103453)) -
so far no real improvements and the CI build times are incredibly slow with fat LTO.
- Port the whole build pipeline from bash to Python ([PR](https://github.com/rust-lang/rust/pull/103019))
to get better statistics about the build process, and possibly also to speed it up by introducing
some non-trivial caching. Having a slow CI build is annoying, because it makes it slower to
merge PRs, test PRs (with so-called `try` builds that test integration of the PR) and also to
measure performance of PRs (because perf. runs on PRs always do a `try` build first).
- Revisit Call-site aware PGO ([PR](https://github.com/rust-lang/rust/pull/97153)).
- Revisit `libstd` PGO ([PR](https://github.com/rust-lang/rust/pull/97038)).

On an unrelated note, I have been also working on implementing support for runtime benchmarks
into the Rust performance suite, so that we could not only measure the compilation speed of `rustc`,
but also the performance of Rust programs compiled by it. But more on that later :)

Anyway, that's all for now. If you have any ideas how to speed up `rustc` (but rememember, without
changing its source code! :laughing:) or any other comments, let me know on [Reddit](https://www.reddit.com/r/rust/comments/yeunrs/speeding_up_the_rust_compiler_without_changing/).
