---
layout: "post"
title: "Optimizing Rust programs with PGO and BOLT using cargo-pgo"
date: "2023-07-28 14:42:00 +0200"
categories: rust cargo
reddit_link: https://www.reddit.com/r/rust/comments/15bwihd/optimizing_rust_programs_with_pgo_and_bolt_using/
---

Last year I was working on [improving]({% post_url 2022-10-27-speeding-rustc-without-changing-its-code %})
the Profile-guided optimization (PGO) workflow used to build the Rust compiler. While doing that, I
realized that while PGO works fine for Rust, it is not as straightforward to use and as discoverable
as I would have liked. That led me to the creation of [`cargo-pgo`](https://github.com/Kobzol/cargo-pgo),
a Cargo subcommand that makes it easier to optimize Rust binaries with PGO (and BOLT, see below).

I have actually implemented this tool over a year ago, and already posted about it on
[Reddit](https://www.reddit.com/r/rust/comments/wff8ud/cargopgo_cargo_subcommand_for_optimizing_binaries/),
but I figured that it might be useful to also write a short blog post about it here to explain a
little bit how PGO/BOLT works for Rust and how `cargo-pgo` automates it.

# What is PGO, anyway?
Profile-guided optimization (PGO) is a program optimization technique that allows a compiler to better
optimize your code thanks to having a better idea of how will your program behave on real-world
workloads. This is done using a recorded representation of program behavior, which  is usually called
a "profile", hence the term profile-guided optimization. In a way, it is sort of like a JIT for compiled
programs - instead of optimizing a program based on its runtime behavior while it is running, you run
the program, record its behavior, and then re-compile it using this additional information.

*[JIT]: Just-in-time (compilation)

The PGO workflow usually looks something like this:
1. You compile an "instrumented" version of your program. The compiler will insert additional
instrumentation instructions into it, which will record useful information when the program is executed.
2. You execute the instrumented binary on some representative workload(s). This will generate a set
of profiles on disk, which will contain information about your program behavior - things like how
many times was each function called or how many times was a conditional branch taken.
3. You compile your binary again, this time providing the gathered profiles to the compiler. It
should then be able to optimize the code better, because it will have a better idea of your program
runtime behavior.

PGO is a common technique in the C/C++ world, and it is also well-supported by Rust[^1]. There is a
[PGO guide](https://doc.rust-lang.org/rustc/profile-guided-optimization.html) in the official Rust
compiler documentation, which describes the steps that you need to perform to get it working. In short,
you need to pass a special compiler flag to `rustc` when building your crate, gather the profiles by
running your program, use a separate LLVM tool to merge the gathered profiles and then pass a different
flag to `rustc`, which needs to point to the merged profile. It's not super complicated, but it's also
quite far from the typical frictionless experience of running a single `cargo <foo>` command that
does everything you need.

[^1]: Although I'm not sure how known it is and how many people actually use it.

# Automating PGO
That is why I decided to create [`cargo-pgo`](https://github.com/Kobzol/cargo-pgo), a Cargo subcommand
that is designed to make it as easy as possible to apply PGO to Rust crates. So, how does it work?

First, you need to install it with the following command:
```bash
$ cargo install cargo-pgo
```
After that, you can start using the various `cargo pgo <...>` commands.

<details markdown=1>
<summary>How does this Cargo integration work?</summary>

Cargo has this ingenious feature where it basically allows you to add custom subcommands to it
transparently. If you execute e.g. `cargo foo bar`, and Cargo doesn't know the command `foo`, it will
try to search for a `cargo-foo` binary in `PATH`. If it finds it, it will delegate the executed command
to the binary, and basically invoke `cargo-foo bar`.

In this way, you can add custom third-party subcommands to Cargo quite easily.
</details>

You may recall that the first step of the PGO workflow is to generate an instrumented binary. You can
do that using `cargo pgo build`, which does several things for you:
1. It passes the `--release` flag to Cargo. Just to make sure that you don't forget :smile:. There's
not much point in PGO optimizing debug builds.
2. It passes an explicit `--target` flag to Cargo, which avoids PGO instrumenting
[build scripts](https://doc.rust-lang.org/rustc/profile-guided-optimization.html#a-complete-cargo-workflow).
3. It creates a directory for storing the PGO profiles under the `target` artifact directory. It will
also automatically clear this directory to remove any stale profiles, unless you pass the `--keep-profiles`
flag.
4. And finally, it compiles your target with the `-Cprofile-generate=<profile-dir>` flag,
which will cause `rustc` to enable PGO instrumentation.

#### Gathering profiles
After you have an instrumented binary, you should execute it on some realistic workloads to gather
the profiles. You should gather enough profiles to provide proper context for the compiler, but it's
hard to say in general what is the correct amount. Usually I just let the program run at least for a
minute or so.

Sometimes you might not have an easy way of running your code on a representative workload, and you
would like to gather profiles e.g. from tests or benchmarks. `cargo pgo` has your back! With
`cargo pgo test` or `cargo pgo bench`, you can generate profiles by running instrumented tests or
benchmarks, and then use these profiles to optimize a separate binary executable (it doesn't make
much sense to optimize tests/benchmarks themselves with PGO).

#### More precise profiles
If you run `cargo pgo build`, you might notice that it will tell you that you might want to execute
the instrumented binary with a `LLVM_PROFILE_FILE` environment variable. What is this about?

By default, the instrumented binary will store all profiles into a single `.profraw` file. This is fine
for most use-cases. However, if your program creates multiple processes or if you execute the instrumented
program multiple times in parallel, some data in the profile might get lost or overwritten. This happens
because the file will be read and written in parallel by multiple processes, effectively resulting in
a race condition. This race condition is mostly harmless, however it can result in less precise profiles.

To resolve this potential problem, you can run the instrumented binary with the environment variable
`LLVM_PROFILE_FILE` set to a path containing a special placeholder value `%p`. This will essentially
cause the instrumented program to generate one `.profraw` file per process[^2]. For example:

```bash
$ LLVM_PROFILE_FILE=./target/pgo-profiles/%m_%p.profraw
  ./target/release/x86_64-unknown-linux-gnu/foo
```

[^2]: The `%m` placeholder is "module" (I think?) and basically describes the signature of the instrumented binary.

Creating one file per process should result in more precise profiles and thus a better optimized program.
When I enabled this "trick" for the Rust compiler itself, it resulted in
[pretty](https://github.com/rust-lang/rust/pull/97110#issuecomment-1129089080)
[nice](https://github.com/rust-lang/rust/pull/97137#issuecomment-1130555410) ~1% instruction count
improvements across the board, although it's hard to say whether this will generalize to other programs.
It should also be noted that if you create a lot of processes, the disk usage of all these profile
files can get large pretty quickly! For `rustc`, a single profile takes tens of megabytes, while
creating a separate profile for each process consumes almost `60 GiB`!

# Final optimization step
Once you have gathered the PGO profiles, you can run `cargo pgo optimize`. It will merge all
gathered profiles using the `llvm-profdata` tool and then compile your target with the `-Cprofile-use`
flag, pointing it to the single merged profile file. It will also print helpful stats about the
gathered profiles (like their count and total size before and after merging).

# Running PGO on CI
If you want to apply PGO to binary artifacts that you then distribute to end users, you might want
to run PGO in a CI (continuous integration) workflow. If you install `cargo-pgo` in your CI script,
and you are able to run your instrumented binary on some (probably small) workload directly on the CI
machine, then this becomes quite straightforward. I created a simple example of a GitHub Actions
[workflow](https://github.com/Kobzol/cargo-pgo/blob/658b8e1b310ac0f11783f9319547af4cf36d4e3f/ci/pgo.yml)
that shows how this could be done.

# Going beyond PGO
The (LLVM-based) PGO implementation offered by the Rust compiler is just one of many existing so-called
Feedback-directed optimization (FDO) tools, which leverage some sort of runtime profiles to better
optimize programs. Another such tool is a post-link optimizer called [BOLT](https://github.com/llvm/llvm-project/blob/main/bolt/README.md).
"Post-link" means that it takes a fully compiled and linked program binary as an input, and then uses
profiles to optimize the binary, even without access to its source code. This differs from "classic"
PGO, which optimizes the program during compilation, and thus has access to its source code. Its main
goal is to better reorganize instructions within the binary, in particular to improve instruction cache
utilization.

BOLT is a part of LLVM, and can provide additional performance improvements even on top of an already
PGO-optimized binary. Last year, I have [enabled BOLT](https://github.com/rust-lang/rust/pull/94381)
for LLVM[^3] used by the Rust compiler, which resulted in ~2-5% cycle
[improvements](https://perf.rust-lang.org/compare.html?start=e495b37c9a301d776a7bd0c72d5c4a202e159032&end=8dfb40722da197e77a33a19eb9d3fd6512831341&stat=cycles:u)
across the board.

[^3]: BOLT for `rustc` is still [WIP](https://github.com/rust-lang/rust/pull/102487).

Sadly, it might not be that easy to even get ahold of a precompiled version of BOLT. While it is distributed
through Ubuntu/Debian packages, they seem to be [broken currently](https://github.com/Kobzol/cargo-pgo/issues/31).
Since LLVM 16, [LLVM GitHub releases](https://github.com/llvm/llvm-project/releases/tag/llvmorg-16.0.4)
contain a precompiled `llvm-bolt` binary[^5], which allows you to get a working version of BOLT relatively
easily, however it has to be available for your architecture and platform. If it is not, then you
basically have to go and compile LLVM + BOLT [yourself](https://github.com/Kobzol/cargo-pgo#bolt-installation)[^4],
which is quite annoying and can also difficult to do on CI.

[^4]: We do exactly this in Rust CI workflows.

[^5]: And also the `merge-fdata` tool, which is needed for merging BOLT profiles. It is basically a BOLT analogue to the `llvm-profdata` PGO tool.

Same as with PGO, BOLT uses a workflow where you first need to gather profiles of your program running
on some workload, and then use these profiles to re-optimize your binary. BOLT can gather these
profiles in two modes:
- Sampling: In this mode, you simply execute your binary under a profiler (`perf`), which gathers
hardware counter data from its execution and uses this information to generate the required profiles.
- Instrumentation: This mode is similar to PGO instrumentation. BOLT modifies your binary to add
additional instructions that will generate the profiles during runtime. The advantage of this mode is
that it doesn't require access to CPU/HW counters, which makes it usable in CIs which do not allow this
(such as GitHub Actions). I also think that instrumentation should be able to generate more precise profiles.
The disadvantage is that you need to have an additional instrumentation step. The instrumented binary
is also slower, and it will thus take it more time to gather the same amount of profile data as with
the sampling approach. But this might not be a big deal.

Here is an example of how you could use BOLT manually using the instrumentation mode:
```bash
# Build your binary with linker relocations, so that BOLT can instrument it
$ RUSTFLAGS="-C link-args=-Wl,-q" cargo build --release
# Instrument the binary with BOLT
$ llvm-bolt ./target/release/<binary> -o instrumented -instrument
# Run the instrumented binary on some workload
$ ./instrumented <...>
# Merge the generate profiles, which are by default stored into /tmp/*.fdata
$ merge-fdata /tmp/*.fdata > merged.profdata
# Finally, optimize the binary with BOLT
$ llvm-bolt -o optimized -data merged.profdata <BOLT flags...>
```

As you can see, the process is quite involved. Using BOLT is actually more tricky than using PGO, because
it is not integrated into the Cargo workflow, but instead it operates on the finished Rust
artifacts. You should thus make sure not to modify the original artifacts built by `cargo` so that
you do not mess with its cache and that you don't instrument the same file with BOLT twice (it will
result in an error). 

To make this easier, I also added support for BOLT to `cargo-pgo`. It uses a workflow that is quite
similar to the PGO one, and does the instrumentation, profile merging and optimization for you:
```bash
# Build a BOLT instrumented binary
$ cargo pgo bolt build
# Run the binary to gather profiles
$ ./target/.../<binary>-bolt-instrumented
# Optimize the binary with BOLT using the gathered profiles
$ cargo pgo bolt optimize
# Now you can use ./target/release/<binary>-bolt-optimized
```

The instrumented and optimized files are named with a suffix (`-bolt-instrumented` and `-bolt-optimized`)
to avoid messing with artifacts built by Cargo.

`cargo-pgo` is even able to combine both PGO and BOLT using the `--with-pgo` flag[^6]:
```bash
# Build PGO instrumented binary
$ cargo pgo build
# Run binary to gather PGO profiles
$ ./target/.../<binary>
# Build BOLT instrumented binary using PGO profiles
$ cargo pgo bolt build --with-pgo
# Run binary to gather BOLT profiles
$ ./target/.../<binary>-bolt-instrumented
# Optimize a PGO-optimized binary with BOLT
$ cargo pgo bolt optimize --with-pgo
```

[^6]: It would be nicer to do this in a more composable way, like `cargo pgo bolt build -- cargo pgo pgo optimize` or something like that, but alas. A possible future improvement :)

This combined PGO + BOLT workflow should provide the largest performance improvements[^7], at the cost
of increased build time - you need to recompile and run your program several times.

[^7]: Although it is not *guaranteed* that it will actually improve performance, of course.

# Conclusion
There's probably more to say about both PGO and BOLT, but this post was mainly supposed to serve as a short
intro into how to use these techniques with Rust, and how to leverage `cargo-pgo` to make this simpler,
and I think that it has achieved that goal.
Let me know on [Reddit](https://www.reddit.com/r/rust/comments/15bwihd/optimizing_rust_programs_with_pgo_and_bolt_using/?sort=new) or on the `cargo-pgo` [issue tracker](https://github.com/Kobzol/cargo-pgo/issues)
if you have any questions regarding the usage of PGO/BOLT for Rust crates.
