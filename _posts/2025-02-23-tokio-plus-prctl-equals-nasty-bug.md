---
layout: "post"
title: "Tokio + prctl = nasty bug"
date: "2025-02-23 18:00:00 +0100"
categories: rust
#reddit_link: TODO
---

Recently I encountered a bug so cute that I immediately knew that I will want to share it on my blog. It was one of those bugs that even Rust can't save you from. It occurred in [HyperQueue](https://github.com/It4innovations/hyperqueue) (HQ), a distributed task scheduler written in Rust that I work on.

Despite the fact that HyperQueue is a pretty non-trivial distributed application, and it has long been developed mostly only by two people that only have a limited time available for it, it has so far been very reliable, which always fascinates me[^Rust]. But since we have released version [0.21.0](https://github.com/It4innovations/hyperqueue/releases/tag/v0.21.0), we have received several issue reports about a major problem, where tasks spawned by HyperQueue were getting terminated after a few seconds, apparently without any obvious reason. One [reported issue](https://github.com/It4innovations/hyperqueue/discussions/815) was even weirder, as tasks were executing normally, but the very last executed task was *always* failing, no matter what task it was. This was quite unusual to us, as HQ usually works pretty well, and our CI test suite was green, so what gives? Let's dive in.

[^Rust]: A large contributing factor to the reliability is the fact that is written in Rust. There were some similar previous tools in our lab written in C++… and it has not been so wonderful.

## Origin of the bug
Luckily, we had a pretty good reproducer from one of our users that has reliably reproduced the bug on my machine. When HyperQueue spawned a task that executed this simple Python function:

```python
def work():
    time.sleep(10)
    print("hello world")
```

the task would fail after approximately ten seconds (just before the print), without producing any output. A funny thing was that if I changed the sleep to `2` seconds, it worked. If I changed it to `5` seconds, it also worked. But once the sleep time reached `10` seconds, the task would fail. That was quite… weird, to say the least.

Thanks to this reproducer, I was able to find the commit that introduced this bug using [`git bisect run`](https://lwn.net/Articles/317154/) in just a few minutes. The commit was actually created quite some time ago, back in summer of 2024, when I was doing a frankly unhealthy amount of HyperQueue benchmarking for my [PhD]({% post_url 2024-11-12-phd-postmortem %})[^phd], but it was only merged recently, which is why the issues have only started appearing now. The [commit](https://github.com/It4innovations/hyperqueue/commit/b7effa3946162817874f99a661ea87562b10b80f) slightly changed the way we spawn tasks (external processes) in HyperQueue:

```diff
- let mut child = command.spawn();
+ let mut child = tokio::task::spawn_blocking(move || command.spawn())
+        .await
+        .expect("Command spawning failed");
```

[^phd]: Oh, I'm *so* happy that I can talk about my PhD in past tense now…

The change looks quite innocent! Note that it only changes where the command is spawned (so where the `fork`/`clone`/`exec` syscall is executed), otherwise the process is then polled in the same way as before (`spawn` doesn't block until the process finishes, just until it starts executing). Therefore, I was confused as to why it should cause this weird task killing behavior. But first, I should probably explain why I even made this change in the first place.

Spawning processes on Linux sounds like something that is so cheap that you don't have to worry about it. Well, that is mostly true… until it isn't :laughing:. HyperQueue needs to be able to spawn thousands of processes per second, and do it on HPC clusters and supercomputers that can use quite ancient versions of the Linux kernel and glibc (the *C* standard library implementation), which means that just the act of spawning a process itself can become a large [bottleneck]({% post_url 2024-01-25-process-spawning-performance-in-rust %}).

To achieve concurrency, HyperQueue uses tokio, and more specifically its single-threaded runtime[^single-threaded]. But notice that the [`spawn`](https://docs.rs/tokio/latest/tokio/process/struct.Command.html#method.spawn) method of tokio's [`Command`](https://docs.rs/tokio/latest/tokio/process/struct.Command.html) is blocking! This makes sense, of course, because there's not exactly an asynchronous version of `fork`. If you thus try to spawn a very large number of processes very quickly, the spawning costs will add up, and thus the tokio runtime thread might get blocked and other tasks might starve (I found this with my PhD benchmarking experiments). Well, since spawning a process is a blocking operation, why not offload it to a different (worker) thread using the [`spawn_blocking`](https://docs.rs/tokio/latest/tokio/task/fn.spawn_blocking.html) function? I tried that, and it seemed to have a positive effect on HyperQueue's performance. So that's how the 
commit was born.

[^single-threaded]: It is for good reasons, [trust me]({% post_url 2025-01-15-async-rust-is-about-concurrency %}#why-not-use-async).

Funnily enough, this commit was added to HyperQueue in an *enormous* [pull request](https://github.com/It4innovations/hyperqueue/pull/798) that essentially backported most of my benchmarking experiments that I have done over the summer. The PR almost exclusively contained changes only to benchmarks, so it should have been safe to merge without a lot of scrutiny[^last-words]. But it also contained two *teeny tiny* changes. The PR description that I wrote is quite funny in retrospect:

[^last-words]: Yes, you can probably already see that this was one of those "famous last words" situations.

> This backports the benchmarks that I prepared for my PhD thesis back into the HQ repository. Almost all changes are to the benchmarks repository, and they thus shouldn't need a lot of review. There are a few changes in HQ though: command spawning optimization and the option to disable authentication for benchmarking.

Well, guess what, the "command spawning optimization" managed to break HyperQueue's primary functionality for a bunch of users. That's what I get for sending `+3,458 -601` diff pull requests, sigh…

## Figuring out the cause
Now that I knew which commit caused the bug, I "only" had to figure out *why*. I didn't understand why moving a blocking operation to a tokio's threadpool should cause this kind of problem. If there was a deadlock or something like that, then sure, but tasks being randomly killed after approximately ten seconds? That was super weird. I wasn't used to these kinds of heisenbugs in HyperQueue. Therefore, my first instinct was to blame tokio :laughing: I thought that maybe the spawning of the command has to happen on the same thread where the command is then polled for completion, or something like that. But I didn't find anything related to that in tokio's issue tracker. And when I created a standalone program outside HQ trying to reproduce this behavior, it worked fine:

```rust
use tokio::process::Command;

#[tokio::main(flavor = "current_thread")]
async fn main() {
    let mut cmd = Command::new("sleep");
    cmd.arg("10");

    let mut child = tokio::task::spawn_blocking(move || {
        cmd.spawn().unwrap()
    }).await.unwrap();

    let res = child.wait().await.unwrap();
    assert_eq!(res.code(), Some(0));
}
```

What was also confusing me was the fact that the task did not produce any output, and apparently ended without an exit code. This is how we were checking the exit code of the task process in HQ:

```rust
let status_to_result = |status: ExitStatus| {
    if !status.success() {
        let code = status.code().unwrap_or(-1);
        ...
        Err(tako::Error::GenericError(format!(
            "Program terminated with exit code {code}"
        )))
    } else {
        Ok(TaskResult::Finished)
    }
};
```
The exit code was -1, so apparently it was missing. Something was killing our tasks after a few seconds, without them producing any output nor exit code. What could it be? Well, that sounded like a [signal](https://man7.org/linux/man-pages/man7/signal.7.html)! At first, I didn't see how to get information about a signal that could have been sent to the task process from [`ExitStatus`](https://doc.rust-lang.org/std/process/struct.ExitStatus.html), but then I realized that it has to be OS-specific. And indeed, there is [`ExitStatusExt`](https://doc.rust-lang.org/std/os/unix/process/trait.ExitStatusExt.html) on Linux, which provides a way to get the [`signal`](https://doc.rust-lang.org/std/os/unix/process/trait.ExitStatusExt.html#tymethod.signal) that was received by the spawned process.

And sure enough, after logging the received signal, I found out that the tasks are being killed with `SIGTERM`. But who (or what) could be sending this signal, and why is it not being sent without `spawn_blocking`?! Now we get to the fun part.

HyperQueue is essentially a process manager that runs in user space. The user space part provides many advantages, but it also introduces limitations. In particular, it is not always possible for HQ to ensure that when a process that spawns tasks (called *worker*) quits unexpectedly (e.g. when it receives `SIGKILL`), its spawned tasks will be cleaned up. Sadly, Linux does not seem to provide any way of implementing perfect structured process management in user space. In other words, when a parent process dies, it is possible for its (grand)children to continue executing. There is a solution for this called [PID namespaces](https://man7.org/linux/man-pages/man7/pid_namespaces.7.html), but it requires elevated privileges, and also seems a bit too heavyweight for HyperQueue.

However, some time ago, I found a partial solution for this problem, which is able to at least clean up direct children (although sadly not grandchildren) when the HQ worker dies. It is called [`PR_SET_DEATHSIG`](https://man7.org/linux/man-pages/man2/pr_set_pdeathsig.2const.html), and we configure it when spawning tasks using the `prctl` syscall like this[^unsafe]:

```rust
unsafe {
    command.pre_exec(|| {
        // Send SIGTERM to this task when the parent (worker) dies.
        libc::prctl(libc::PR_SET_PDEATHSIG, libc::SIGTERM);
    });
}
```

[^unsafe]: By the way, this is the *only* usage of `unsafe` in HyperQueue, a ~40k line codebase that implements high-performance task scheduling on supercomputers, which amazes me. Although we will need to add one additional `unsafe` block once we migrate to the [2024 edition](https://blog.rust-lang.org/2025/02/20/Rust-1.85.0.html) because we use [`std::env::set_var`](https://doc.rust-lang.org/std/env/fn.set_var.html) in `main` :laughing:

You probably realized by now that I'm not talking about `PR_SET_PDEATHSIG` by accident, and that the `SIGTERM` signal that we configure to be sent to the task when the worker dies looks like the culprit that has been killing the tasks. And indeed, when I commented out the `prctl` call, the bug was gone.

But this still doesn't explain the bug, because the worker doesn't die. So why is `SIGTERM` being sent to the task?? Let's examine the description of `PR_SET_PDEATHSIG`:

> Set the parent-death signal of the calling process to sig (either
a signal value in the range [1, NSIG - 1], or 0 to clear).  This
is the signal that the calling process will get when its parent
dies.

Ok, that seems to make sense. When the parent (the worker process) dies, the task receives `SIGTERM`, that's what I want. Or, at least that's what I thought would happen…

…

The problem is the word *parent*. I automatically assumed that it means the "parent process". But now that I have examined the very next sentence of the description again, I saw this:

>  The parent-death signal is sent upon subsequent termination of the
parent thread and also upon termination of…

Wait, did it say *thread*? Crap. Suddenly, everything clicked -- do you see it?

By moving the spawning of the command into a different (tokio worker) thread, suddenly I told the kernel to send `SIGTERM` to the spawned process when *that worker thread* dies, instead of when the parent process (or rather its main thread) dies. Perhaps that wouldn't be an issue on its own, but it looked like the worker thread was being killed after approximately ten seconds of inactivity. Probably tokio reaps these threads in the background periodically when they have no work left to do? I tried to count the number of active threads in my reproducer program using the [`num_threads`](https://docs.rs/num_threads/latest/num_threads/) crate:

```rust
let mut cmd = Command::new("sleep");
cmd.arg("10");
unsafe {
    cmd.pre_exec(|| {
        libc::prctl(libc::PR_SET_PDEATHSIG, libc::SIGTERM);
        Ok(())
    });
}

let mut child = tokio::task::spawn_blocking(move || {
    cmd.spawn().unwrap()
}).await.unwrap();
eprintln!("Thread count: {}", num_threads::num_threads().unwrap());

let res = child.wait().await.unwrap();
eprintln!("Thread count: {}", num_threads::num_threads().unwrap());
eprintln!("{:?}", res.signal());
```

and sure enough, it printed this:
```rust
Thread count: 2
Thread count: 1
Some(15)
```

So tokio was clearly terminating the worker thread after a few seconds of inactivity, which caused the kernel to terminate the spawned process with `SIGTERM`. This was also the reason why tasks would actually finish successfully if you submitted more of them (as shown in [#815](https://github.com/It4innovations/hyperqueue/discussions/815)), because the worker thread would receive more work to do (more commands to spawn), so it took more time for tokio to terminate it. Only the last task would then fail, because the worker thread had nothing else to do, so it ended and that killed the last task abruptly. Just incredible.

Therefore, the case was closed. The problem was a very unlucky interaction of us starting a process in a different thread than the main thread, using `PR_SET_PDEATHSIG` and tokio reaping worker threads in the background. Note that tokio is not to be blamed here, as reaping of idle threads is a reasonable thing to do. This was just one of those unfortunate cases where a combination of several things that otherwise worked well did not in fact work well together.

## Fixing the bug
This might be a bit disappointing, but I "fixed" the bug simply by [reverting](https://github.com/It4innovations/hyperqueue/pull/823) the commit with the task spawning optimization. I don't want to give up the cleanup functionality offered by `PR_SET_PDEATHSIG`[^pre-exec], and I don't know how to tell it to only send the signal when the parent process (not thread) dies (if you do, please let me know!), nor how to do achieve this functionality in any other way in user space.

[^pre-exec]: Even though in benchmarks it seemed like setting it has a small overhead on its own, because the [`pre_exec`](https://doc.rust-lang.org/std/os/unix/process/trait.CommandExt.html#tymethod.pre_exec) call prevents some command spawning optimizations.

It's quite sad that our test suite hasn't caught this bug; apparently there was no test that would execute a task for longer than a few seconds :laughing: In general, it's quite tricky to test something like this[^tigerbeetle], but I didn't want to leave it completely without a regression test, so I at least implemented [this](https://github.com/It4innovations/hyperqueue/pull/823/commits/9c20bd83cf085c9419fc18c194586b0a9799335e) test. Yeah, testing if a task can run for `20` seconds isn't great, but hey, at least it's something.

[^tigerbeetle]: Sadly, HQ doesn't have a fully deterministic test suite like e.g. [TigerBeetle](https://docs.tigerbeetle.com/about/vopr/) does.

## Conclusion
In the end, it took me probably less than an hour to find, diagnose and fix this bug, so it wasn't *that bad*, as far as bughunting stories go. But I found the bug to be sort of beautiful, so I wanted to share it anyway.

I hope that you found this bughunt case interesting, and that you perhaps also learnt something new along the way. If you have any comments, let me know on [Reddit]({{ page.reddit_link }}).
