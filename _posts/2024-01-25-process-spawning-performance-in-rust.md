---
layout: "post"
title: "Process spawning performance in Rust"
date: "2024-01-25 15:13:00 +0100"
categories: rust
---

As part of my PhD studies, I'm working on a distributed task runtime called [HyperQueue](https://github.com/it4innovations/hyperqueue). Its goal is to provide an ergonomic and efficient way to execute task graphs on High-Performance Computing (HPC) distributed clusters, and one of its duties is to be able to spawn a large amount of Linux processes efficiently. HyperQueue is of course written in Rust[^cpp-distributed], and it uses the standard library's [`Command`](https://doc.rust-lang.org/std/process/struct.Command.html) API to spawn processes[^tokio]. When I was benchmarking how many processes it can spawn per second on an HPC cluster, I found a few surprising performance bottlenecks, which I will describe in this post. Even though most of these bottlenecks are only significant if you literally spawn thousands of processes per second, which is not a very common use-case, I think that it's still interesting to understand what causes them.

[^cpp-distributed]: Before we knew Rust, we were developing distributed systems in our lab in C++. Suffice to say… it was not a good idea.

[^tokio]: Well, it actually uses [`tokio::process::Command`](https://docs.rs/tokio/latest/tokio/process/struct.Command.html), but that's just an async wrapper over [`std::process::Command`](https://doc.rust-lang.org/std/process/struct.Command.html) anyway.

# High-Performance Command spawning
My investigation into Rust process spawning performance on Linux started a few years ago, when I was trying to measure what is the pure internal overhead of executing a task graph in HyperQueue (HQ). To do that, I needed the executed tasks to be as short as possible, therefore I let them execute an "empty program" (`sleep 0`). My assumption was that since running such a process should be essentially free, most of the benchmarked overhead would be coming from HyperQueue.

While running the benchmarks, I noticed that they behave quite differently on my local laptop and on the [HPC cluster](https://docs.it4i.cz/karolina/introduction/) that I was using. After a bit of profiling and looking at [flamegraphs](https://github.com/flamegraph-rs/flamegraph), I realized that the difference was in process spawning. To find out what was the cause of it, I moved outside HyperQueue and designed a benchmark that purely measured the performance of spawning a process on Linux in Rust. Basically, I started to benchmark this:

```rust
Command::new("sleep").arg("0").spawn().unwrap();
```

Notice that here I only benchmark the *spawning* (i.e. starting) of a process. I'm not waiting until the process stops executing[^wait-process].

[^wait-process]: Although my benchmark harness does wait for all the spawned processes to end after each benchmark iteration, otherwise Linux starts to complain pretty quickly that you're making too many processes.

> The code of my benchmark harness can be found [here](https://github.com/Kobzol/rust-cmd-spawn-bench).

On my laptop, spawning 10 000 processes takes a little bit under a second, not bad. Let's see what happens if we do a few benchmarks to compare how long does it take to spawn `N` processes (the X axis) locally vs on the cluster:

<img src="/assets/posts/process-spawning/spawn-rust-local-vs-cluster.png" width="500" alt="Performance comparison of process spawning between my laptop and the cluster. The cluster doesn't win." />

Uh-oh. For 25 thousand processes, it's ~2.5s locally, but ~20s on the cluster, almost ten times more. That's not good. But what could cause the difference? The cluster node has `256 GiB` RAM and a `128-core` AMD Zen 2 CPU, so simply put it is *much* more powerful than my local laptop.

Well, spawning a process shouldn't ideally do that much work, but it will definitely perform some syscalls, right? So let's compare what happens locally vs on the cluster with the venerable [`strace`](https://man7.org/linux/man-pages/man1/strace.1.html) tool (I kept only the interesting part and removed some noisy things like memory addresses and return values):

```bash
(local) $ strace ./target/release/spawn
clone3({flags=CLONE_VM|CLONE_VFORK, …}, …) = …
```

```bash
(cluster) $ strace ./target/release/spawn
socketpair(AF_UNIX, SOCK_SEQPACKET|SOCK_CLOEXEC, 0, [3, 4]) = …
clone(child_stack=NULL, flags=CLONE_CHILD_CLEARTID|CLONE_CHILD_SETTID|SIGCHLD, … = …
close(4) = …
recvfrom(3, …) = …
```

Okay, it does indeed look a bit different. A different syscall (`clone3` vs `clone`) is used, different flags are passed to it, and in addition the program opens up a Unix socket on the cluster for some reason (more on that later). Different syscalls could explain the performance difference, but why are they even different in the first place? We'll find out soon, but first we'll need to understand how process spawning works in Linux.

# The perils of forking
Apparently, there are [many ways](https://stackoverflow.com/questions/4856255/the-difference-between-fork-vfork-exec-and-clone) how to create a process that executes a program on Linux, with various trade-offs. I'm not an expert in this area by any means, but I'll try to quickly describe my understanding of how it works, because it is needed to explain the performance difference.

The traditional way of creating a new process on Linux is called *forking*. The [`fork`](https://man7.org/linux/man-pages/man2/fork.2.html) syscall essentially clones the currently running process (hence its name), which means that it will continue running forward in two copies. `fork` lets you know which copy is the newly created one, so that you can do something different in it, typically execute a new program using [`exec`](https://man7.org/linux/man-pages/man3/exec.3.html), which replaces the address space of the process with fresh data loaded from some binary program.

Back in the days of yore, `fork` used to literally copy the whole address space of the forked process, which is quite wasteful and slow if you want to run `exec` immediately after forking, which replaces all its memory anyway. To solve this performance issue, a new syscall called [`vfork`](https://man7.org/linux/man-pages/man2/vfork.2.html) was introduced. It's basically a specialized version of `fork` that expects you to immediately call `exec` after forking, otherwise it results in undefined behavior. Thanks to this assumption, it doesn't actually copy the memory of the original process, and thus improves the performance of process spawning.

Later, `fork` was changed so that it no longer copied the actual contents of the process memory, and switched to a "copy-on-write" (CoW) technique. This is implemented by copying the page tables of the original process, and marking them as read-only. When a write is attempted on such a page, it is cloned on-the-fly before being modified (hence the "copy-on-write" term), which makes process memory cloning lazy and avoids doing unnecessary work.

Since `fork` is now much more efficient, and there are [some](https://ewontfix.com/7/) [issues](https://lisper.in/vfork-is-still-evil) with `vfork`, it seems that the [conventional wisdom](https://stackoverflow.com/a/4856460/1107768) is to just use `fork`, although we will see that it is not so simple.

So, why have we seen `clone` syscalls, and not `fork`/`vfork`? That's just an implementation detail of the kernel. These days, `fork` is actually implemented in terms of a much more general syscall called [`clone`](https://man7.org/linux/man-pages/man2/clone.2.html), which can create both threads and processes[^thread-process], and can also use the "vfork mode", where it doesn't copy process memory at all.

[^thread-process]: To the Linux kernel, these are essentially the same thing anyway, just with different memory mappings and other configuration.

Armed with this knowledge, let's compare the syscalls again:
```bash
(local)
clone3({flags=CLONE_VM|CLONE_VFORK, …}, …) = …

(cluster)
clone(child_stack=NULL, flags=CLONE_CHILD_CLEARTID|CLONE_CHILD_SETTID|SIGCHLD, … = …
```

The `clone3` call is essentially a `vfork`, since it uses the `CLONE_VM` and `CLONE_VFORK` flags (more on these later in the post), while the `clone` call is essentially a `fork`.

So what causes the difference? We'll have to take a look inside the Rust standard library to find out. The Linux [`Command::spawn`](https://github.com/rust-lang/rust/blob/df0c9c37c1d7458d1d06b370912f6595e0295079/library/std/src/sys/pal/unix/process/process_unix.rs#L72) implementation is relatively complicated. It does a bunch of stuff that I don't completely understand, and that would probably warrant a blog post of its own, but there is one peculiar thing that immediately caught my attention - it exercises a [different code-path](https://github.com/rust-lang/rust/blob/df0c9c37c1d7458d1d06b370912f6595e0295079/library/std/src/sys/pal/unix/process/process_unix.rs#L474) based on the version[^glibc-parse] of `glibc` (the C standard library implementation) of your environment:

[^glibc-parse]: Fun fact: the standard library [parses](https://github.com/rust-lang/rust/blob/99128b7e45f8b95d962da2e6ea584767f0c85455/library/std/src/sys/pal/unix/os.rs#L762) the glibc version [every time](https://github.com/rust-lang/rust/blob/df0c9c37c1d7458d1d06b370912f6595e0295079/library/std/src/sys/pal/unix/process/process_unix.rs#L474) you try to spawn a process. Luckily, it's probably just a few instructions.

1. It you have [at least](https://github.com/rust-lang/rust/blob/df0c9c37c1d7458d1d06b370912f6595e0295079/library/std/src/sys/pal/unix/process/process_unix.rs#L473) `glibc 2.24`, it will use a "fast path", which involves calling the [`posix_spawnp`](https://man7.org/linux/man-pages/man3/posix_spawn.3.html) `glibc` function, which then in turns generates the efficient `clone3(CLONE_VM|CLONE_VFORK)` syscall (effectively `vfork`).
2. If you have an older `glibc` version (or if you use some complicated [spawn parameters](https://github.com/rust-lang/rust/blob/df0c9c37c1d7458d1d06b370912f6595e0295079/library/std/src/sys/pal/unix/process/process_unix.rs#L463)), it instead falls back to just calling `fork` [directly](https://github.com/rust-lang/rust/blob/df0c9c37c1d7458d1d06b370912f6595e0295079/library/std/src/sys/pal/unix/process/process_unix.rs#L111). In addition, it also creates a UDS (Unix Domain Socket) pair to exchange some information between the original and the forked process[^uds-motivation], which explains the `socketpair` and `recvfrom` syscalls that we saw earlier.

[^uds-motivation]: I don't really know why that happens, and I was lazy to search `git blame` to find the original motivation. Seems to be related to signal safety. Anyway, this blog post is already long enough without delving deeper into this.

When I saw that, I was pretty sure that this is indeed the source of the problem, since I already had my [share of troubles]({% post_url 2021-05-07-building-rust-binaries-in-ci-that-work-with-older-glibc %}) with old `glibc` versions on HPC clusters before. Sure enough, my local system has `glibc 2.35`, while the cluster still uses `glibc 2.17` (which is actually the [oldest version](https://blog.rust-lang.org/2022/08/01/Increasing-glibc-kernel-requirements.html) supported by Rust today).

Good, now that we at least know why different syscalls are being generated, let's try to find out why is their performance different. After all, shouldn't `fork` be essentially as fast as `vfork` these days?

# `fork` vs `vfork` (are you gonna need that memory?)
To better understand what is happening, and to make sure that the effect is not Rust-specific, I wrote a very simple C++ [program](https://github.com/Kobzol/rust-cmd-spawn-bench/blob/main/benchmark.cpp) that tries to replicate the process spawning syscalls executed by the Rust standard library by executing the `posix_spawn` function. To select between `fork` vs `vfork` "semantics", I use the `POSIX_SPAWN_USEVFORK` flag. Let's see what happens locally vs on the cluster again:

<img src="/assets/posts/process-spawning/spawn-vfork-cpp-local-vs-cluster.png" width="500" alt="Performance comparison of fork vs vfork between my laptop and the cluster. The cluster is slightly slower." />

Okay, it's indeed slower on the cluster, which can be probably attributed to an older kernel (`3.10` vs `5.15`) and/or older `glibc` (`2.17` vs `2.35`), but it's nowhere as slow as before. So what gives? Is it Rust's fault? Well, let's see what happens if we benchmark the spawning of `10000` processes, but this time we will progressively increase the RSS of the original process by allocating some bogus memory up-front:

*[RSS]: Resident set size

<img src="/assets/posts/process-spawning/spawn-vfork-cpp-memory-local-vs-cluster.png" width="500" alt="Performance comparison of fork vs vfork between my laptop and the cluster. The cluster is slightly slower." />

…is it just me or does one of the bars stand out? :laughing: First, let's try to understand why does is `fork` so much slower on the cluster, but not on my local laptop. We can find the answer in the [documentation](https://man7.org/linux/man-pages/man3/posix_spawn.3.html) of the `POSIX_SPAWN_USEVFORK` flag:

```
POSIX_SPAWN_USEVFORK
          Since glibc 2.24, this flag has no effect.  On older
          implementations, setting this flag forces the fork() step
          to use vfork(2) instead of fork(2).  The _GNU_SOURCE
          feature test macro must be defined to obtain the
          definition of this constant.
```

In other words, if you have at least `glibc 2.24`, this flag is basically a no-op, and all your `posix_spawn`-created processes (including those created by Rust's `Command`) will use the fast `vfork` method by default, making process spawning quite fast. This basically shows that there's no point in even trying to debug/profile this issue on my local laptop, since with the newer `glibc` the slow spawning will be basically unreproducible.

> Note that Rust doesn't actually set `POSIX_SPAWN_USEVFORK` manually. It just benefits from the faster spawning by default, as long as you have `glibc 2.24+`.

Now let's get to the elephant in the room. Why does it take 5 seconds to spawn 10 000 processes if I have allocated 1 GiB of memory before in my process, but a whopping 25 seconds when I have already allocated 5 GiB? The almost linear scaling pattern should give it away - it's the "copy-on-write" mechanism of `fork`. While it is true that almost no memory is copied outright, the kernel still has to copy the *page tables* of the previously allocated memory, and mark them as read-only/copy-on-write. This is normally relatively fast, but if you do it ten thousand times per second, it quickly adds up. Of course, I'm far from being the [first](https://github.com/rtomayko/posix-spawn#benchmarks) [one](https://blog.famzah.net/2009/11/20/fork-gets-slower-as-parent-process-use-more-memory/) to notice this phenomenon, but it still surprised me just how big of a performance hit it can be.

Just to double-check that I'm really on the right track, I also checked a third programming language, and tried to benchmark `subprocess.Popen(["sleep", "0"])` in Python 3:

<img src="/assets/posts/process-spawning/spawn-vfork-py-local-vs-cluster.png" width="500" alt="Performance comparison of fork vs vfork in Python between my laptop and the cluster. The cluster is much slower." />

Sure enough, it's again much slower on the cluster. And if we peek inside with `strace` again, we'll find that on the cluster, Python uses `clone` without the `VFORK` flag, so esssentially the same thing as Rust, while locally it uses the `vfork` syscall directly.

Ok, so at this point I knew that some of the slowdown is obviously caused by the usage of `fork` (and some of it is probably also introduced by the Unix sockets, but I didn't want to deal with that). I saw that even on the cluster, I can achieve a much better performance, but I would need to avoid the `fork` slow path in the Rust standard library and also add the `POSIX_SPAWN_USEVFORK` flag to its `posix_spawnp` call.

# Should we use `vfork`?
After I learned about the source of the bottleneck, I created an [issue](https://github.com/rust-lang/rust/issues/87764) about it in the Rust issue tracker[^gh-issue]. This led me to investigate how other languages deal with this issue. We already saw that Python uses the slow method with older `glibc`. I found out that Go (which AFAIK actually doesn't use `glibc` on Linux and basically implements syscalls from scratch) switched to the `vfork` method in `1.9`, which produced some nice wins in [production](https://about.gitlab.com/blog/2018/01/23/how-a-fix-in-go-19-sped-up-our-gitaly-service-by-30x/).

[^gh-issue]: Funnily enough, I basically rediscovered all of this by writing this blog post 2.5 years later, rather than just re-reading my old issue… :laughing:

However, I was also directed to some [sources](https://bugs.python.org/issue34663#msg325765) from people much more knowledgeable about Linux than me, that basically explained that there is a reason why `vfork` wasn't being used for older `glibc` versions, and that reason is because these old `glibc` versions implemented it in a buggy way.

So I decided that it's probably not a worthwhile effort to push this further and risk the option of introducing arcane `glibc` bugs, and I closed the issue. As we'll see later, this wasn't *the only* bottleneck in process spawning on the cluster, though. 

# Aside: modifying the standard library
When I first learned about the issue and saw that the `POSIX_SPAWN_USEVFORK` flag fixes the performance problem on the cluster, I was a bit sad at first that what would have been essentially a one-line change in C or C++ (since they do not really have any high-level standard library API for spawning processes) would require me to either propose a change to, or fork (neither of which is trivial) the Rust standard library.

However, I realized that this line of thinking is misleading. Yes, it would be a one-line change in C or C++, but only because in these languages, I would have to first write the whole process spawning infrastructure myself! Or I would have to use a third-party library, but then I would encounter a similar issue - I would either have to fork it, copy-paste it in my code or get a (potentially controversial) change merged to it. I'm actually really glad that it's so easy to use third-party libraries in Rust and that the standard library allows me to use fundamental functionality (like process spawning) out of the box. But there are trade-offs everywhere - one implementation can never fit all use-cases perfectly, and if you're interacting with an HPC cluster with a 10-year-old kernel, the probability of not fitting within the intended use-case increases rapidly :laughing:.

So why couldn't I just copy-paste the code from the standard library into my own code, modify it and then use the modified version? Well, this would be an option, of course, but the issue is that it would be a lot of work. I need process spawning to be asynchronous, and thus in addition to modifying the single line in the standard library, I would also need to copy-paste the whole of `std::process::Command`, and also `tokio::process::Command`, and who knows what else.

If it was possible to build a custom version of the standard library in an easier way, I could just keep this one-line change on top of the mainline version, and rebuild it as needed, without having to modify all the other Rust code that is built on top of it (like `tokio::process::Command`). And since Rust links to its standard library statically by default, it shouldn't even cause problems with distributing the final built binary. Hopefully, [`build-std`](https://doc.rust-lang.org/cargo/reference/unstable.html#build-std) will be able to help with this use-case one day.

As I already stated in the introduction, it's important to note that the bottleneck that I'm describing here has essentially only been showing in microbenchmarks, and it usually isn't such a big problem in practice. If it was a larger issue for us, I would seriously consider the option of copy-pasting the code, or writing our own process spawning code from scratch (but that would increase our maintenance burden, so I'd like to avoid that if possible).

So, was this all there is to slow process spawning? No, it turns out that there is more.

# It's all in the environment

- 20 vs 200 environment variables
- copying, BTreeMap

# Is spawning blocking?

- spawn and blocking a thread or all threads
- env lock

# Bonus: `sleep` vs `/usr/bin/sleep`
Since I'm focused on micro-benchmarks in this blog post, let's see one more performance effect. What do you think, is there any performance difference between spawning a process that executes `sleep` vs spawning a process that executes `/usr/bin/sleep` (no tricks here, these two paths lead to the same binary) in Rust? It turns out that there is:

<img src="/assets/posts/process-spawning/spawn-sleep-vs-usr-bin-sleep.png" width="500" alt="Performance comparison of spawning sleep vs /usr/bin/sleep. The first is slightly faster." />

The difference is not large, but it is clearly visible. When you specify an absolute path, the binary can be executed directly. However, if you specify just a binary name, then the directories in the `PATH` environment variable have to be iterated and checked if they contain the executed binary. For reference, my `PATH` environment variable has `14` entries and `248` bytes in total, so it's not exactly gargantuan. But again, if you spawn 10 thousand processes, it adds up :)

# Conclusion
I hope that you have learned something new about process spawning on Linux with Rust. Even though I think that the presented bottlenecks won't cause any issues for the vast majority of Rust programs, if you ever needed to spawn a gigantic amount of processes in a short time, perhaps this blog post could serve as a reference on what to watch out for.

If you have any comments or questions, please let me know on [Reddit](TODO).
