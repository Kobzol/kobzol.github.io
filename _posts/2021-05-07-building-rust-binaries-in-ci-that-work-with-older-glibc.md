---
layout: "post"
title: "Building Rust binaries in CI that work with older GLIBC"
date: "2021-05-07 08:39:00 +0100"
categories: rust ci
---
**TL;DR**: This post documents my attempts of building a Rust binary in CI that would work on older
Linux systems. I was using GitHub Actions, but it should be also applicable for other CI systems.
You can find the final solution [at the end](#solution). 

If you are developing a Rust project, it might be a good idea to continously build and test your
crate in CI to make sure that it is working properly. If you're using GitHub CI, this is
fortunately very easy thanks to the awesome [toolchain](https://github.com/actions-rs/toolchain)
and [cargo](https://github.com/actions-rs/cargo) CI actions.

If you are developing a binary crate, and you want to take it a step further, you can also use CI to
automatically build a binary executable and attach it to a GitHub release[^1] so that the users will
be able to download and use the binary without installing a Rust toolchain.

[^1]: You can do this e.g. on every new git tag pushed to the repository.

Since Rust is touted for using static linking, which should simplify binary distribution, it sounds
simple. And for the most part, it actually is. However, there is one problem called GLIBC.

# The problem with GLIBC
Even though Rust uses static linking for almost everything by default, it still links dynamically
to the C standard library. More specifically, it usually links to the
[GLIBC](https://www.gnu.org/software/libc/) implementation.

This is usually not an issue, since GLIBC is available pretty much universally on Linux systems.
However, it starts being a problem when you compile a Rust binary on a Linux system which uses a
newer version of GLIBC, and then try to run this binary on a different system that uses an older
version of GLIBC.

This is exactly what happened to me, and I definitely wasn't alone
([1](https://github.com/rust-lang/rust/issues/57497),
[2](https://github.com/rust-analyzer/rust-analyzer/issues/4426),
[3](https://github.com/rust-lang/rust/issues/36826)). I was building the binary on GitHub CI, which
used GLIBC `2.23` at the time, and then trying to run the binary on CentOS 7 with GLIBC `2.17`.

When I did that, I got this error:
```bash
$ ./program
./program: /lib64/libc.so.6: version `GLIBC_2.18' not found (required by ./program)
```

To find out what was causing my binary to require `GLIBC 2.18`, I ran `objdump`:
```bash
$ objdump -T ./program | grep GLIBC_2.18
0000000000000000  w   DF *UND*  0000000000000000  GLIBC_2.18  __cxa_thread_atexit_impl  
```

Great. A single function (which is used in [destructors of TLS](https://github.com/rust-lang/rust/issues/57497#issuecomment-454449134)
objects), is hampering my ability to run the binary on the other system.

*[TLS]: Thread-local storage

I tried to compile the crate on the target CentOS 7 system and that worked flawlessly. So obviously,
the function wasn't necessarily required, but for some reason the executable linked to it if it was
compiled with a more recent GLIBC version. This [issue](https://github.com/rust-lang/rust/issues/36826)
stated that this function should have been linked as a weak symbol, but for some reason (either due
to a bug in GCC, Rustc or both), it didn't behave in such a way.

# Failed attempts
It seems that I wasn't the only one with the [exact same problem](https://stackoverflow.com/questions/39744926/how-can-i-compile-a-rust-program-so-it-doesnt-use-cxa-thread-atexit-impl),
but I couldn't find any specific solution how to fix this easily. Therefore, I set out to test various
approaches that I hoped could work.

# Patching the binary
I found some guides on how to patch the binary manually to not require the offending symbols
and/or link to an additional C file with the missing symbols to avoid depending on the symbol from
GLIBC. I rejected these ideas outright, as they would probably be quite brittle, and I wanted
something simple that could be done in CI with a few lines.

# Removing dependency on GLIBC
This is an obvious first solution. If dynamic linking and GLIBC versions are a problem, just remove
the need to use dynamic linking! Since GLIBC is not really amenable to [static linking](https://stackoverflow.com/questions/57476533/why-is-statically-linking-glibc-discouraged),
a different `libc` implementation is needed. An obvious candidate is [MUSL](https://www.musl-libc.org/),
which is supported by Rust out of the box.

Building Rust binary with `musl` is actually [quite simple](https://doc.rust-lang.org/edition-guide/rust-2018/platform-and-target-support/musl-support-for-fully-static-binaries.html).
You just have to add the `x86_64-unknown-linux-musl` target using e.g. `rustup` and use it when
building the binary:
```bash
$ cargo build --target x86_64-unknown-linux-musl
```

In GitHub Actions, you can do it with the following setup:
```yaml
- name: Install stable toolchain
  uses: actions-rs/toolchain@v1
  with:
    profile: minimal
    toolchain: stable
    override: true
    target: x86_64-unknown-linux-musl

- name: Build
  uses: actions-rs/cargo@v1
  with:
    command: build
    args: --release --target x86_64-unknown-linux-musl
```

This alone would probably solve my issue. However, I found that I actually cannot compile my crate
with `musl`, because I was using the [jemalloc](https://crates.io/crates/jemallocator) allocator,
and it refused to compile with `musl` for some reason[^2]. Since the default `musl` allocator can be
[quite slow](https://www.reddit.com/r/rust/comments/gdycv8/why_does_musl_make_my_code_so_slow/),
just removing jemalloc didn't sound like a good option to me.

[^2]: Even when disabling the default features.

Also, even if this worked, it would mean that the binary would use a different `libc` implementation,
which wasn't exactly what I wanted. I wanted to use GLIBC.

# Building with an older GLIBC version
Since I knew that when the binary was compiled on a system with GLIBC `2.17`, it would work, the next
obvious step was to try to build the binary with an older GLIBC version in CI. This sounded simple,
but it actually took several attempts to get it right on GitHub Actions.

#### Using an older Ubuntu version
Since I needed to have an older GLIBC version in CI, my first attempt was to switch from
`ubuntu-latest` to `ubuntu-16.04`, with the hope that it would have an older GLIBC version. Sadly,
this didn't work. When I printed the version of `GLIBC` in the CI workflow using this command:
```bash
$ ldd --version
```
I saw that it was still using something like `2.23` and the built binary didn't work on CentOS 7.
I also knew that `ubuntu-16.04` would be deprecated soon, so this wouldn't be a long-standing solution.

#### Using `cross` to cross-compile using a different toolchain
The [cross](https://github.com/rust-embedded/cross) project allows you to easily cross-compile your
Rust binary to a different toolchain. It has a target called `x86_64-unknown-linux-gnu`, which
(at the time of writing) specified that it uses GLIBC `2.15`, which sounded perfect for my use-case.

It is also very easy to use `cross` in GitHub Actions, so I tried this:
```yaml
- name: Build
  uses: actions-rs/cargo@v1
  with:
    command: build
    use-cross: true
    args: --release --target x86_64-unknown-linux-gnu
```
This downloaded a Docker image with the corresponding toolchain, cross-compiled the binary, and…
surprise, surprise, it still didn't work. I have no idea why, but it seems that it somehow still
linked to the GLIBC from the CI system (which was more recent), rather than to the `2.15` GLIBC
from the `cross` Docker container.

# Solution
After doing some more Googling, I stumbled upon [this PR](https://github.com/explosion/tokenizations/pull/7)
from a Python project that was using Rust. It was dealing with a similar problem, and solved it by
using a Docker container with an older GLIBC version, which was used for the whole CI workflow run.
This was actually a pretty straightforward solution how to get a system with an older GLIBC, but I
had no idea that GitHub CI even offered this :man_shrugging:.

I tried to use this "trick" by setting the `container` attribute of my CI workflow file to the
`manylinux-2010` image, which is commonly used for building Python libraries with native dependencies:

```yaml
jobs:
  create-release:
    runs-on: ubuntu-latest
    container: quay.io/pypa/manylinux2010_x86_64
```

I thought that my issue was finally solved, but instead I was met with this CI job output:
```
> Run actions-rs/toolchain@v1
/usr/bin/docker exec  8540a7685eadc59ea7b6496c3fee1b7db6498d2d6b11ec3b11dbb20d1afe762f sh -c "cat /etc/*release | grep ^ID"
/__e/node12/bin/node: /usr/lib64/libstdc++.so.6: version `GLIBCXX_3.4.14' not found (required by /__e/node12/bin/node)
/__e/node12/bin/node: /usr/lib64/libstdc++.so.6: version `GLIBCXX_3.4.18' not found (required by /__e/node12/bin/node)
/__e/node12/bin/node: /usr/lib64/libstdc++.so.6: version `CXXABI_1.3.5' not found (required by /__e/node12/bin/node)
/__e/node12/bin/node: /usr/lib64/libstdc++.so.6: version `GLIBCXX_3.4.15' not found (required by /__e/node12/bin/node)
/__e/node12/bin/node: /lib64/libc.so.6: version `GLIBC_2.16' not found (required by /__e/node12/bin/node)
/__e/node12/bin/node: /lib64/libc.so.6: version `GLIBC_2.17' not found (required by /__e/node12/bin/node)
/__e/node12/bin/node: /lib64/libc.so.6: version `GLIBC_2.14' not found (required by /__e/node12/bin/node)
```

Great. So before, we had too recent GLIBC, now we have too old GLIBC. It turns out that some actions
that I was using in the CI workflow were executed using NodeJS 12, which required at least GLIBC
`2.17`.

The [tokenizations](https://github.com/explosion/tokenizations) project that inspired me to use the
`container` attribute solved this in a rather crude way. It stopped using the nice GitHub actions
and instead installed the Rust toolchain manually.

I didn't really like that solution though, so I needed to find a different Docker image, one that
would solve both issues. The Rust GitHub actions required *at least* GLIBC `2.17` and my CentOS
system needed *at most* GLIBC `2.17`. Well, what a coincidence :laughing:.

I just needed to find an image that had GLIBC version exactly `2.17`. Luckily, it turned out that
the only remaining available `manylinux` image, `manylinux2014`, had exactly that. But even if
it hadn't, it would probably be ok to find or create any other Docker image with GLIBC set to `2.17`.

My final solution was thus to add this single line to my workflow file:
```yaml
container: quay.io/pypa/manylinux2014_x86_64
```

If only I had known that before spending several hours trying to get it to work :)

# Conclusion
In light of my described troubles, it now seems almost scary that the vast majority of programs
actually have a "hidden" dependency on a fundamental C library, which often times works "by accident".

Anyway, that's all for my adventure. I wrote about it because I hope that it might be useful to some
of you in the future. You can find the final workflow file that I have used for building the binary
[here](https://github.com/It4innovations/hyperqueue/blob/498a162e9f17506bfe4a274f7afe2773bb25c0ee/.github/workflows/release.yml).
If you have any comments, let me know on [Reddit](https://www.reddit.com/r/rust/comments/n6udyk/building_rust_binaries_in_ci_that_work_with_older/).

P.S.: If you find yourself debugging GitHub Actions frequently, check [act](https://github.com/nektos/act).
It allows you to run your GitHub workflows locally, which can speed up the time spent debugging them
considerably.
