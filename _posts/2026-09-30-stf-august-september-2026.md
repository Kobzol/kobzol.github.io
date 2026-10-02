---
layout: "post"
title: "Upstream Rust maintenance report (August-September 2026)"
date: "2026-09-30 15:00:00 +0200"
categories: rust
month_range: August and September 2026
reddit_link: https://www.reddit.com/r/rust/comments/1wu5l6y/upstream_rust_maintenance_report_augustseptember/
---

As noted in my [previous report]({% post_url 2026-08-03-stf-june-july-2026 %}), I am currently working on the open source Rust toolchain as a [Sovereign Tech Fellow][stf-fellowship-2026]. Every two months, I'm putting out a report of my open source work done in that period. This is the second installment of this series. Same as the last time, I'll try to pick a few highlights, summarize the rest of the stuff that I worked on, and also provide contribution statistics and a raw list of opened PRs.

This post details my open source Rust work done in {{ page.month_range }}.

Here's an index for simpler navigation:

- [Reducing target directory size](#reducing-target-directory-size)
- [Compile time improvements](#compile-time-improvements)
  - [Trying to optimize the Rust parser](#trying-to-optimize-the-rust-parser)
  - [Making Polonius faster](#making-polonius-faster)
  - [Shipping the parallel frontend](#shipping-the-parallel-frontend)
  - [Measuring compiler performance on ARM](#measuring-compiler-performance-on-arm)
  - [Investigating incremental recompilation](#investigating-incremental-recompilation)
- [Improving the Rust compiler merge queue](#improving-the-rust-compiler-merge-queue)
- [Josh subtree migration](#josh-subtree-migration)
- [Tracking `rust-lang` crates on crates.io](#tracking-rust-lang-crates-on-cratesio)
- [Reviving unmaintained repositories](#reviving-unmaintained-repositories)
  - [thanks.rust-lang.org](#thanksrust-langorg)
  - [rustup-components-history](#rustup-components-history)
- [Funding team activities](#funding-team-activities)
- [Other things I worked on](#other-things-i-worked-on)
- [Contribution statistics and PR list](#contribution-statistics-and-pull-requests)

## Reducing target directory size

I already wrote in my [previous report]({% post_url 2026-08-03-stf-june-july-2026 %}), and also earlier [on this blog]({% post_url 2025-06-02-reduce-cargo-target-dir-size-with-z-no-embed-metadata %}), about the initiative to reduce the size of the `target` directory by removing duplicated metadata of Rust crates, which can make it smaller in real-world projects by 5-35%, so it can be quite significant.

Last time, I noted that we are waiting for Cargo's new build dir layout nightly experiment to conclude, before we enable yet another experiment on nightly by default. This happened during August, so I [enabled][embed-metadata-cargo-nightly] the usage of `-Zembed-metadata=no` on the nightly channel by default, and [announced][embed-metadata-post] it on the Rust blog post.

The good news is that we haven't really heard any large complaints or issues about it since then, and several build systems already successfully updated to the new mechanism, where the metadata is kept only in `.rmeta` files, which then have to be passed explicitly to `rustc` via the `--extern` flag.

Thanks to that experiment, I discussed moving forward with the Cargo team, and opened a [stabilization report][embed-metadata-rust-stabilization-report] for the compiler side of the feature (turning the unstable `-Zembed-metadata` flag into a stable `-Cembed-metadata` flag), which is now in [FCP vote](https://github.com/rust-lang/rust/pull/163436#issuecomment-5889363144) :tada:. Soon after, [Weihang Lo][weihanglo] opened a separate [Cargo stabilization report][embed-metadata-cargo-stabilization-report] for the Cargo side of the feature (passing `-Cembed-metadata=no` to `rustc` by default). There are some remaining [questions](https://rust-lang.zulipchat.com/#narrow/channel/246057-t-cargo/topic/Usage.20of.20-Zno-embed-metadata/near/627845724) about how does this affect Cargo's stability story about `.rlib`, `.dylib` and `.rmeta` artifacts, but I think that this should not block the compiler side of the stabilization.

Since Cargo is already using the unstable `-Zembed-metadata` flag *by default* on nightly, and Rust's own build system is also making use of that flag, simply moving `-Zembed-metadata` to `-Cembed-metadata`, which is what we would normally do, would immediately break nightly users, unless we managed to synchronize that change across both `rustc` and Cargo atomically, which is not trivial at the moment. The plan is thus to keep supporting both `-Zembed-metadata` and `-Cembed-metadata` for some time, to allow users to migrate to the stable version of the flag, and then finally remove the unstable flag.

This is quite exciting, because it looks like we might be finally close to removing the duplication of Rust metadata on disk, which existed in Rust for almost 10 years, and was unnecessarily inflating the size of the `target` directory.

By the way, it seems that a [Project Goal](https://goals.rust-lang.org/) focused on reducing the size of the `target` directory further is in the works. Maybe don't go buying another disk drive just yet!

[embed-metadata-cargo-nightly]: https://github.com/rust-lang/cargo/pull/17267
[embed-metadata-rust-stabilization-report]: https://github.com/rust-lang/rust/pull/163436
[embed-metadata-cargo-stabilization-report]: https://github.com/rust-lang/cargo/pull/17533
[embed-metadata-post]: https://blog.rust-lang.org/inside-rust/2026/08/18/reducing-target-dir-size-on-nightly/
[weihanglo]: https://github.com/weihanglo

## Compile time improvements

Same as in the previous period, I tried to spend some time on improving the performance of the Rust compiler, though this time I don't have that much to show for it. My experiments were mostly focused on trying to apply arena allocation to various parts of the compiler. I must admit that I did not achieve much success, partly because of my own unfamiliarity with arenas (though I learned a lot during my experiments!), partly due to the way the compiler codebase is structured, and partly because I now think that the design of Rust is sort of hostile towards arena allocation. Though with the upcoming [stabilization][allocator-stabilization] of the `Allocator` trait, it should become better.

Apart from the high-level areas that I describe below, I also worked on some random small performance improvements:
- Added a fast path to string escaping in the compiler in [rust#160453] (thanks [@matthieu-m][matthieu-m] for the [suggestion](https://github.com/rust-lang/rust/pull/159916#issuecomment-5145000967)). Surprisingly, escaping strings can be quite hot, and the standard library's escaping code is currently [not very fast][escape-std].
- Removed an unnecessary `.clone()` call from the macro expansion system in [rust#162004]. It would be nice if Clippy's [redundant_clone](https://rust-lang.github.io/rust-clippy/master/#redundant_clone) lint could catch this, but unfortunately it is currently not very smart.
- Resolved a performance regression from a previously merged PR in [rust#162371].
- Applied LTO to Cranelift in [rust#163412]. This didn't help all that much. I also want to try to apply PGO to Cranelift, which I hope will help more.
- Tried to reduce the size of macro-generated code in the `tracing` crate in [tokio-rs/tracing#3603], because I saw a lot of unnecessary generated code duplication there in bors. But it seems that `tracing` has been unmaintained for some time, so I'm not sure if anyone will take a look at it.

[escape-std]: https://github.com/rust-lang/rust/pull/159916
[remove-clone-perf]: https://perf.rust-lang.org/compare.html?start=3cabe36ceb022e2f56d4d330b1e2886f31117f18&end=70a39cfb7b741e95fcb6af8b15f5f694a3c2b271&stat=instructions:u
[allocator-stabilization]: https://github.com/rust-lang/rust/pull/156882
[matthieu-m]: https://github.com/matthieu-m

### Trying to optimize the Rust parser

I like reading about how other programming languages and communities implement their compilers. In particular, I always enjoy seeing the [tricks][zig-parsing] that the Zig compiler pulls off. It implements parsing very efficiently, using a Data Oriented Design/Entity Component System approach, and I find that quite cool.

I wanted to try using a similar approach for tokenization and parsing also in the Rust compiler. Now, it should be noted that parsing Zig or C is a *very* different discipline than parsing Rust. It's not necessarily that Rust's grammar is that complicated to parse, but some of the language's design, where parsing is interwoven with macro expansion and name resolution, and its focus on providing *great* diagnostics, makes its parsing logic much more complicated than one might think.

Today, the Rust lexer and parser represent tokens using essentially a tree representation. [Token trees][token-tree] are stored in a `Vec`, where each tree can either be a leaf token (like `+`) or a delimited group of nested trees (like `(1 + 2)`), which is stored in a separate `Vec`. In other words, everytime the parser encounters parentheses, braces or brackets in a Rust file, it will allocate a new `Vec` on the heap. As you might imagine, this is not terribly efficient, neither time-wise, nor memory-wise.

I tried to change that to use a flat representation, where all tokens, including delimited sequences, are stored in one single `Vec`, to avoid all those tiny allocations. Changing the lexer was very simple, and locally produced ~30% wins in terms of lexing performance, which was nice. However, moving this change up to the parser, macro expansion and AST handling was quite… involved[^lexer-only]. It was not really feasible to change the representation everywhere at once, because there is *a lot* of code that accesses the [`TokenStream`][token-stream] type, which abstracts the `Vec` of token trees. So I had to create a second implementation on the side (using the flat `Vec` of tokens), reimplement all the old functionality using the flat token structure and implement conversion functions in both directions (from flat to nested trees and from nested to flat trees). Then I had to incrementally migrate usages of `TokenStream` in the compiler to the new representation, by moving the conversions to higher and higher-level call-sites, until all conversions were gone.

[^lexer-only]: Note that it doesn't work to keep this change local *only* to the lexer, because it produces the same tokens that the parser and the AST then works with. Using the flat representation in the lexer, and another representation in the parser, requires converting between them, which makes compilation slower overall, even if lexing is sped up (I tried).

After a lot of work, I managed to get quite far in [rust#159378][flat-tokens]. However, the performance results are not [very impressive](https://perf.rust-lang.org/compare.html?start=a8a1e6fd9df2e094d6f09c0d57991508680acc1c&end=270a6702b0cd5877ec2a39d3fa823beb31b1e9a0&stat=instructions:u) so far: the compiler is actually slower with the flat token representation. The best result I achieved was [this](https://perf.rust-lang.org/compare.html?start=fd7ed57dfd3bdebb745a1d8158638727b0e7047a&end=41bfd27447b6da2214d1c73b14037a50d34b84c3&stat=instructions:u), but then once I started moving more stuff into the new representation, it actually regressed even more. The reason is mostly macro expansion. The nested tree representation with every delimited group being a separate allocation is actually quite useful when you want to do a lot of modifications of the parsed list of tokens, which is exactly what happens during the expansion of both declarative and proc macros, and also in a few other parts of the parser, usually around attributes, where we currently do a bunch of in-place modifications of the input token stream (which is kind of terrifying, and a hack).

I think that it should be possible to either modify that code to be more friendly to the flat representation, or somehow use a hybrid representation that would combine the performance benefits of the flat representation with the ability to be easily modified of the nested representation. Not sure how that would look like though.

Some further performance wins might also be gained by:
- Reducing the size of individual tokens. Each token has ~40B at the moment, which is kinda ludicrous.
- Using a chunked `Vec`, so that appending to the end of the flat list doesn't require reallocating and copying the whole token list when the `Vec` runs out of memory.
- Migrating [`AttrTokenStream`][attr-token-stream] to the flat representation too, so that we don't have to convert between the flat and separately allocated token trees when dealing with attributes[^attr-token-stream].

[^attr-token-stream]: Yes, there is a second representation of token streams in the compiler that also uses the separately allocated `Vec`s, which is used for attributes. It is quite similar, but not *quite* the same, as `TokenStream`. Don't ask me why.

I think that this might be a situation where the performance results keep being red until the last bottleneck/conversion point is removed, and at that point it could jump to being green a lot. But so far it looks like getting to that point is quite difficult :)

While staring into the token parsing code for many weeks, I noticed that there are other sources of inefficiencies. For example, the parser snapshots its state before parsing certain constructs, so that it can reparse some parts of the code lazily at a later stage. This snapshotting happens quite often (on bors I measured over 250 thousand snapshots being made), and it is a bit expensive. That might sound surprising; isn't the parser state essentially just a single number with a position pointing into an input string? Well, I wish :) The issue is that because of how the delimited groups are represented, we actually have to remember a stack of currently active parent delimited groups, so that when we encounter the end of a delimited group, we know where to backtrack in the parser. As an example, when we are parsing `(1 + array[0<pos>] + 2)`, and the parser is at `<pos>`, where the `[0]` group ends, it has to be able to go back to its parent delimited group (`(1 + ...)`), so that it can access its data.

What makes this a bit infuriating is that most times, I suspect that we don't even end up using most of the parents at all, but we still pay the cost for cloning the whole parent stack. This is kinda stupid, so I tried to figure out some ways of not cloning a `Vec` of several items everytime a snapshot is made in [rust#162593][collect-pos]. I tried:
- Storing intrusive pointers in the delimited group stack items, so that snapshotting only clones at most one parent item, and I can find its parent by following the pointer. But this trades snapshotting performance for adding yet another allocation when encountering each delimited group (so that we can store the parent somewhere), which resulted in performance regressions.
- Using immutable datastructures (using crates like [`im`][im]) to reduce the overhead of cloning. This also resulted in performance regressions.
- I considered using an `Arc` inside the delimited groups to remember their parents, but I quickly ditched this idea, because it would be a lot of work to make this work, and would likely run into reference cycles (though that would be resolvable via using `Weak` pointers), and would inflate the size of each token tree even more.
- Only clone the immediate parent, not the whole parent stack. I *suspect* that this is enough, because I don't think that we ever need to recurse back into grandparents when restoring the snapshotted parser, and it produces relatively [nice][collect-pos-perf] performance results. The problem is that so far I haven't been able to convince myself that this works in 100% of the cases or find someone who would be confident enough about how the parser works to confirm this for me.

In the flat representation, I removed the need to remember the parent stack by storing an index into the start of a parent into each delimited group. That makes snapshot cloning essentially free. But everything is a trade-off, because this increases the size of each token, which has a negative effect on performance.

Anyway, I might return to this work sometime later, though [rust#159378][flat-tokens] will require a lot of conflict fixes, because it modifies many files in the compiler.

[token-tree]: https://github.com/Kobzol/rust/blob/80a4f6cdbdc30afa1f27c830386361d22b161286/compiler/rustc_ast/src/tokenstream.rs#L30
[token-stream]: https://github.com/Kobzol/rust/blob/80a4f6cdbdc30afa1f27c830386361d22b161286/compiler/rustc_ast/src/tokenstream.rs#L639
[attr-token-stream]: https://github.com/Kobzol/rust/blob/80a4f6cdbdc30afa1f27c830386361d22b161286/compiler/rustc_ast/src/tokenstream.rs#L349
[zig-parsing]: https://mitchellh.com/zig/parser#anatomy-of-the-parser
[flat-tokens]: https://github.com/rust-lang/rust/pull/159378
[collect-pos]: https://github.com/rust-lang/rust/pull/162593
[collect-pos-perf]: https://perf.rust-lang.org/compare.html?start=c4c4a576936e9e67717d0deb8e74e02dd5dd10de&end=bc1920c34c4073325a5bc1e76f871d8dd3909660&stat=instructions:u
[im]: https://docs.rs/im/latest/im/

### Making Polonius faster

Since August, the Rust compiler uses the Polonius borrow checker implementation on the nightly channel [by default][polonius-blog-post] :tada: This was a long time coming and I'm very excited by it. Compared to the previous borrow checker implementation (NLL), it is currently slower in some cases though. When it originally [landed][polonius-pr] at the start of August, `check` builds of `serde` had a ~15% instruction count [regression][polonius-perf] (end-to-end) vs NLL.

Since then, [Jack Huey][jackh726] and [Rémy Rakic][lqd], who drive the whole Polonius effort, did a lot of great work to speed up Polonius. Now, the [regression][polonius-perf-today] of Polonius vs NLL on `serde` is just around ~3-5%. Since this is an end-to-end measurement, and borrow checking is usually a relatively modest fraction of the work performed by the compiler, this means that Polonius itself likely became several times faster.

I tried to help with the Polonius optimization effort, by attempting to use arena allocation for some of the data structures that Polonius allocates, but I was unable to find a good speed-up. Then I tried to parallelize Polonius, which took a non-trivial amount of work. After I finally got it to compile, I triumphantly [opened a PR][polonius-parallel]… only to find out that Polonius was [already parallelized](https://github.com/rust-lang/rust/pull/162485#issuecomment-5598356055), and all I managed was to implement another *nested* parallelization, which was usually "parallelizing" work across (almost always) only 1 or 2 items :see_no_evil: This was yet another reminder and a cautionary tale against trying to "micro-optimize" something before I properly understand how it works. Nevertheless, I did learn a bunch of things and found some possible improvements to the parallelization machinery for the future. I also gained some experience with how to apply arena allocation to the Rust compiler, which should come in handy later.

In the end, my experiments at least led to [rust#162488][polonius-dense-bit], which replaced one data structure in the Polonius implementation, which led to a ~2% instruction count [win][polonius-dense-bit-perf] on a `check` build of `serde`. It was a relatively modest win, and just a tiny fraction of the Polonius performance improvements done in the past few weeks, but hey, I'll take it.

[polonius-blog-post]: https://blog.rust-lang.org/2026/08/04/enabling-polonius-alpha-on-nightly/
[polonius-pr]: https://github.com/rust-lang/rust/pull/159343
[polonius-perf]: https://perf.rust-lang.org/compare.html?start=87212cef77e7bfa92ba0c4850be1d089745ba6fc&end=7608eb7b07eaf93f16d7cf5bcb2098eca87503df&stat=instructions%3Au&secondary=false&clippy=false&debug=false&opt=false&doc=false&doc-json=false
[polonius-perf-today]: https://perf.rust-lang.org/compare.html?start=67e5ad9cdc09753a0bc5da690db2edbe39e294bd&end=6bb1652a020e80cef79332741d89e996d71933c9&stat=cycles%3Au&clippy=false&debug=false&opt=false&doc=false&doc-json=false&frontendThreads=1&secondary=false
[lqd]: https://github.com/lqd
[jackh726]: https://github.com/jackh726
[polonius-parallel]: https://github.com/rust-lang/rust/pull/162485
[polonius-dense-bit]: https://github.com/rust-lang/rust/pull/162488
[polonius-dense-bit-perf]: https://perf.rust-lang.org/compare.html?start=0d31508599a7814a7044e9a7a871e3dc5f037753&end=1edd55dcfcd573872c727fa3e086369a71661ee0&stat=instructions:u

### Shipping the parallel frontend

Making the frontend of the Rust compiler parallel is an initiative that has been in progress for many many years. This sentence was also true in 2023, where we [hoped](https://blog.rust-lang.org/2023/11/09/parallel-rustc/) to stabilize the parallel frontend within the following few months. Oh well.

Now, it finally looks like we are on the verge of enabling it on nightly by default, thanks to the efforts of [Vadim Petrochenkov][petrochenkov] and several other contributors. I still have only very basic understanding of how the parallelism inside the compiler's frontend works, and thus wasn't involved in fixing the myriad of bugs and reproducibility issues with the parallel frontend itself. However, I thought that I might at least help with driving the actual nightly switch forward.

In [rust#162848][parallel-nightly], I'm currently working on doing just that. Mostly it comes down to performing some changes to our testing infrastructure. And I also prepared a [blog post][parallel-blog-post] to announce this change.

Hopefully, we will be able to land the parallel frontend on nightly in October, to start gathering data from users in the wild.

[petrochenkov]: https://github.com/petrochenkov
[parallel-blog-post]: https://github.com/rust-lang/blog.rust-lang.org/pull/1942
[parallel-nightly]: https://github.com/rust-lang/rust/pull/162848

### Measuring compiler performance on ARM

Over the course of 2025, I worked on a [Rust Project Goal][arm-perf-project-goal] together with [James Barford][jamesbarford], where we extended [`rustc-perf`][rustc-perf], the Rust compiler benchmarking suite[^rustc-perf-post], to support running benchmarks on multiple machines in parallel, which made our benchmarks much faster to execute, and also to support running benchmarks on other architectures than `x64`. Even though this work got concluded by the end of 2025, we have been actually still running compiler benchmarks only on `x64` throughout 2026.

[^rustc-perf-post]: I previously wrote about this suite [here]({% post_url 2023-08-18-rustc-benchmark-suite %}).

This changed in the last month, where we got access to a cloud ARM machine, and started running `rustc-perf` benchmarks on it by default. We still don't yet *look* at the ARM results that much though, that will require some more tooling and policy changes. 

[arm-perf-project-goal]: https://goals.rust-lang.org/2025h1/perf-improvements.html
[jamesbarford]: https://github.com/Jamesbarford
[rustc-perf]: https://github.com/rust-lang/rustc-perf

### Investigating incremental recompilation

I spent some time to continue my investigations into why incrementally rebuilding [bors][bors] tests is so damn slow. I [found out][cgu-reuse] that the compiler currently doesn't handle incremental recompilation of async closures very well, and this is a problem for bors, because it is full of them. Essentially, what happens is that everytime you modify code within an async closure, the compiler will recompile a much larger part of your crate than it would necessarily have to. I hacked together a small compiler change that avoids this behavior, which reduced the incremental recompilation time of bors from 14s to 8s (!). However, I don't know if this is the proper fix, and whether it would have an adverse effect in other benchmarks. I also found out that enabling debuginfo causes more incremental recompilations in bors than when debuginfo is disabled. This is highly suspicious, and I suspect that there is much more to uncover here.

Doing this work will require some sustained focus, and other things came up in the meantime, so I didn't get to it yet. Maybe I'll find some time to work on it in the next two months. In the meantime, I tried to nerd-snipe the illustrious [nnethercote] to take a look at bors, so maybe this won't be an issue soon :laughing:

[cgu-reuse]: https://rust-lang.zulipchat.com/#narrow/channel/131828-t-compiler/topic/Diagnosing.20CGU.20reuse/near/621817368
[bors]: https://github.com/rust-lang/bors
[nnethercote]: https://github.com/nnethercote

## Improving the Rust compiler merge queue

Speaking of bors, there were some exciting updates to the merge queue of the Rust compiler in the past few weeks.

In my [previous report]({% post_url 2026-08-03-stf-june-july-2026 %}##other-things-i-worked-on), I noted that [@Mark-Simulacrum][mark-simulacrum] started looking into running some of our more expensive and latency-sensitive CI jobs on EC2 runners. This is cool in that it both makes the jobs much faster, but also much cheaper, than running on CodeBuild, which we did previously. I'm happy that we finished this work with Mark in August :tada: which means that our `x64` try jobs, which we have to run before starting each compiler performance benchmark, now take only ~1 hour, so they are essentially twice as fast as before. We also started using the EC2 instances for ARM jobs that build compiler artifacts, which is what enabled us to run ARM benchmarks (as noted [above](#measuring-compiler-performance-on-arm)) on every merged PR.

We also landed one long-standing feature request and one infrastructure improvement in bors.

The long-standing feature request is the automation of something that we call "r=me after PR CI passes". When approving PRs in the `rust-lang/rust` repository, it was quite common for the reviewer to want to approve a PR for which the PR CI hasn't finished yet. We didn't have any automation for that, because we use our own merge queue implementation (bors), so we cannot use GitHub's built-in tooling for this. So the PR author had to wait until PR CI became green, and then approve the PR on behalf of the approver. This was annoying; people sometimes forgot to approve the PR or had to keep a tab open until the CI finished. There was an [open issue][homu-issue] about this from 2019 in [homu], the previous merge queue implementation.

Since we finally [switched][bors-talk] from homu to bors at the start of this year, it finally became realistic to implement this feature, though it took us a few months before we figured out the right design for it and found the time to implement it. [Sakibul Islam][sakib-25800], my former GSoC mentee, who is now a member of the [bors team], single-handedly [implemented][bors-tentative-approvals] and tested the feature (I have to say that it was a joy to review this PR!). Reviewers can thus now simply write `@bors r+` and let bors worry about PR CI passing or failing, without having to babysit the PR.

The infrastructure improvement that I mentioned is that rollups are now unrolled by bors. Oh wow, what a sentence! Rollups are
PRs that batch multiple other PRs together to amortize the cost of running CI. After they are merged, we "unroll" them by producing compiler artifacts for each separate PR merged with the previous `main` commit, so that we can run performance benchmarks on each PR separately, to determine which rolled-up PR caused a performance regression (if there are any)[^rollup-ci-cost].

[^rollup-ci-cost]: If you're wondering how it makes sense to run CI on each rolled-up PR when we wanted to avoid that cost in the first place, the difference is that the full CI runs ~90 jobs, while for the perf. test we only need a single job for each PR.

Previously, this unrolling was performed by the [`rustc-perf`][rustc-perf] bot. This worked relatively well, but it was implemented in a "fire-and-forget" way, so if the unrolling failed, we had no way to retry or even properly learn about the failure, and it required the `rustc-perf` bot to have permissions for pushing into the `rust-lang/rust` repository. Moving this feature from `rustc-perf` to bors was something that I wanted to do for a long time, to make it much more robust, make it possible to implement some cool new features related to triaging the rolled-up performance benchmarks, and also to remove the unnecessary `push` permissions from the `rustc-perf` account, thus making our CI safer overall. Merging the `rustc-perf` [PR][rustc-perf-unroll-rollups] with almost 450 removed lines was a pretty nice feeling[^bors-pr]. A lot of this work was initially performed by Sakibul again, I just picked it up and moved it over the finish line.

[^bors-pr]: Yes, I am aware that the sibling [bors PR](https://github.com/rust-lang/bors/pull/817) actually added almost 3 thousand lines :laughing: But a lot of that were generated `.sqlx` metadata changes, and also now we actually have proper tests for this rather complex feature.

[homu-issue]: https://github.com/rust-lang/homu/issues/39
[homu]: https://github.com/rust-lang/homu
[bors-talk]: https://www.youtube.com/watch?v=NhTwLwznok8
[bors team]: https://rust-lang.org/governance/teams/infra/#team-infra-bors
[bors-tentative-approvals]: https://github.com/rust-lang/bors/pull/849
[bors-unroll-rollups]: https://github.com/rust-lang/bors/pull/817
[rustc-perf-unroll-rollups]: https://github.com/rust-lang/rustc-perf/pull/2524
[sakib-25800]: https://github.com/Sakib25800
[mark-simulacrum]: https://github.com/Mark-Simulacrum

## Josh subtree migration

The `rust-lang/rust` repository leverages several other git repositories with which it has to be periodically synchronized in both directions. For some of them, we are using `git subtree`, while for others, we use the awesome [Josh][josh] tool, about which I [previously][josh-post] wrote on the Rust blog.

For several years, we have been trying to migrate the remaining subtrees using `git subtree` (which is *very* painful to use) to Josh. Lately, we made a lot of progress on that, and it seems that we are nearing the finish line. The Josh tool received some updates that make it much better in managing our repositories and we implemented some improvements to our [josh-sync] tool, which wraps Josh to provide `rust-lang`-specific functionality.

This allowed us to move forward with the five remaining subtrees still managed by `git subtree`:
- `rustc_codegen_cranelift`: [migrated][rustc_codegen_cranelift-migration] to Josh :tada:.
- `rustfmt`: [migrated][rustfmt-migration] to Josh :tada:.
- `portable-simd`: has an open [migration PR][portable-simd-migration], which is currently stuck on resolving some CI failures.
- `rustc_codegen_gcc`: we attempted to perform a migration, but ran into some issues. We will try again after the next sync.
- `clippy`: we resolved several missing features in `josh-sync` that should enable the Clippy repository to migrate, though there are still some things left to resolve. Hopefully we will be able to migrate to it soon.

I would (finally!) like to get this over the finish line, so that we can stop using custom patched versions of `git subtree` to even be able to handle our subtree repositories, and to have all the subtree logic be performed in a unified manner via `josh-sync` and Josh.

In addition, we are also currently discussing whether it would make sense to move Cargo from a git submodule to a Josh subtree.

[rustc_codegen_cranelift-migration]: https://github.com/rust-lang/rustc_codegen_cranelift/pull/1700
[rustfmt-migration]: https://github.com/rust-lang/rustfmt/pull/7134
[portable-simd-migration]: https://github.com/rust-lang/portable-simd/pull/550
[josh-sync]: https://github.com/rust-lang/josh-sync
[josh]: https://github.com/josh-project/josh
[josh-post]: https://blog.rust-lang.org/inside-rust/2026/06/04/how-josh-helps-rust-manage-code-across-multiple-repositories/

## Tracking `rust-lang` crates on crates.io

There are hundreds of "official" or semi-official crates on crates.io that are somehow associated with the Rust Project. Either they are deployed from repositories living under the `rust-lang` GitHub organization or they are owned by some Rust Project teams. Historically, we did not do a very good job of categorizing and tracking which crates are actually owned by the Rust Project, and which teams should own them though. So many of those crates are currently owned by individual GitHub users, some of which are no longer contributing to Rust anymore.

The Infrastructure team would like to clean that up, first so that we don't have such a mess in it, but also for improved security. Our goal is to force using [Trusted publishing][trusted-publishing], to ensure that all crate releases happen from CI, so that we at least have some audit trail when releases are made, and make all Rust Project crates owned by the special [`rust-lang-owner`][rust-lang-owner] account, which is only accessible to our infrastructure admins, so that it won't be possible to disable Trusted publishing and perform *silent* "rogue publishes" of crates, for example if the GitHub account of some Rust Project member would be compromised.

To achieve that, we have to:
1. Actually find out which crates should be owned by `rust-lang-owner`. This is mostly manual work. Luckily, [Eric Huss][ehuss] did a lot of the work already, and put most of the crates that we should own into a big Excel table, so this part is mostly done.
2. For those crates that are currently not owned by `rust-lang-owner`, ask their current owners to invite the special account, so that we can start managing the crate. I started doing this cat herding recently, and it was surprisingly successful. The owner account now owns over 250 crates, vs (I think) less than a hundred that it owned when I started this effort a few weeks ago. People have been very responsive to my crate ownership requests, thank you![^identity]
3. Associate the crates that we manage to specific Rust teams that should (virtually) own them, and repositories from which they should be deployed, in the [`team`][team] database. This is an ongoing effort, right now we only track a few tens of those crates. We did not have owners for some crates that we already tracked in the `team` database, so I backfilled them in [team#2742] and made it mandatory to have at least one team owner for each publishable crate in [team#2743].
4. For the crates that are still expected to have some releases, and are not yet completely deprecated, configure Trusted publishing for them, and configure them to be publishable from GitHub Actions (e.g. using [`release-plz`][release-plz]). This is the hardest part, because it is not fully automatable, and different teams have different ideas on how they want their crates to be published/released. To make this a bit simpler and avoid doing unnecessary work, I implemented support for tracking crates that are not expected to be published anymore without configuring Trusted publishing for them in [team#2775]. 
5. Provide a way for Rust teams to yank and unyank crates that they own, without those teams actually being owners of the crate on crates.io (as noted earlier, we want to avoid this to reduce the fallout of compromised accounts). I implemented this in `triagebot` ([team#2725], [triagebot#2497]), so now Rust team members can yank and unyank crates on the Rust Zulip server using some chat commands.

Steps 2., 3. and 4. are still ongoing, but they made a lot of progress in the past few weeks. Thanks to that, we were able to go forward with our plan and ensure that `rust-lang-owner` is the sole owner of all the crates that we track, which I implemented in [team#2726].

Now, "all that's left" to do is to incrementally backfill all the Rust Project crates into the `team` DB, along with figuring out which team should own them, and configuring Trusted publishing for them if needed. 

[^identity]: There was one person who initially didn't trust my request to invite the owner account to own their crate. Fair enough, you shouldn't trust random internet strangers! Luckily I was able to prove on Zulip that I am who I claimed to be :)

[ehuss]: http://github.com/ehuss
[trusted-publishing]: https://crates.io/docs/trusted-publishing
[rust-lang-owner]: https://crates.io/users/rust-lang-owner
[team]: https://github.com/rust-lang/team
[release-plz]: https://github.com/release-plz/release-plz

## Reviving unmaintained repositories

In the past two months, I participated in a "revival" of two codebases that were neglected and unmaintained for quite some time, and made substantial improvements to one of them.

### thanks.rust-lang.org

The [thanks] website shows contribution statistics for individual Rust releases, as a way of thanking all the people who contribute to Rust. This tool was created several years ago, and since then it has been mostly chugging along fine. However, we wanted to make some improvements to it, which was quite difficult, because it was implemented in a way where it was counting the contributions for each Rust release starting all the way from the first Rust release. In other words, it was `O(n^2)`, which meant that it took over 10 minutes to generate the contents of the website. That wasn't really a problem on CI, because it only ran once per day, but it was super annoying for any local experiments and further development.

We wanted to move to a [faster algorithm](https://github.com/rust-lang/thanks/pull/37), but it was producing some differences in output. So as a pre-requisite, we first wanted to add tests. [Daniel Scherzer][daniel-scherzer] implemented end-to-end tests in [thanks#99], but it was a bit cumbersome to store snapshots of the generated HTML pages in the repository. So I first implemented a CSV output mode in [thanks#105] and [thanks#110], which only outputs the contribution statistics into a CSV file, rather than the full HTML page. Then we realized that some of the tests were not deterministic, which turned out to be an issue with missed sorting of git submodules, which I fixed in [thanks#111]. After that, we could finally merge the snapshot tests. Thanks, Daniel!

After we had some initial tests, I set out to reimplement the contribution counting logic. Originally, I wanted to just modify the original algorithm to avoid the duplicated work, but after some experiments, I decided to reimplement the whole thing from scratch, to make it amenable for parallelization. First, we gather a set of all commits for individual Rust releases and tags, then we remove duplicates and assert that we have counted all commits in the git history. The duplicate check was actually missing in the original implementation, so this rewrite actually fixed a bug, where some commits were previously counted multiple times. After that, we go through all the commits and extract the commit author and reviewer out of it, while taking the mailmap of the `rust-lang/rust` repository into account. This work was performed multiple times for each commit before, while now it is only performed once per commit. Splitting the work into two explicit stages also made it much easier to parallelize it.

This new algorithm was implemented in [thanks#116]. The performance results were very nice. Gathering the statistics for all (~100) Rust releases originally took more than 10 minutes, but with my PR it only took ~20 seconds on my laptop. I further made it even faster in [thanks#123] by checking out git submodules in parallel. This huge performance improvement actually finally made it possible to experiment with the tool locally, and make improvements to it. It also made CI much faster, which is nice. Sometimes, improving performance is not just about metrics, but it unlocks completely new opportunities.

The main improvement that this allowed us to do was adding support for multiple projects. While the tool already counted contributions from all submodules and subtrees of the main `rust-lang/rust` repository, it did not take into account other important projects in the Rust toolchain, such as Rustup. In [thanks#125], I did some preparatory work to support multiple projects and then in [thanks#126] I added support for counting contributions from the `rust-lang/rustup` repository. Since we now had more than a single project, I also added an overview page in [thanks#130], to see all the projects at one place, and a [new page][all-projects-all-time] that combines all-time contributions from all the tracked projects. Once we added Rustup, I reached out to the `crates.io` and `docs.rs` maintainers, and they were fine with also including those projects in `thanks`, so I did that in [thanks#131]. And finally, I made the project overview page be the default homepage in [thanks#138], so that now that you go to [thanks.rust-lang.org][thanks], you will see all the tracked projects at one place.

I am quite happy that we finally made the `thanks` tool not take 10 minutes to execute, I considered that as an affront. We actually wanted to do this for a long time, but the reason why it didn't happen is that no one felt like they were really owning the tool, so reviews fell through the cracks and nothing moved forward. In July, I finally decided that there is no point in waiting years for someone else to review changes in this repository. I asked a fellow Infrastructure team member if they would be fine if I took over the maintenance of the tool, and they said yes. So I took it upon myself to review and merge changes to this tool, even if it sometimes meant approving a bunch of my PRs myself, without much review. Once I embraced this mindset, I was able to move forward with the improvements at light speed :) And I think that it was overall a good thing for this codebase.

[thanks-rust]: https://thanks.rust-lang.org/rust/
[thanks]: https://thanks.rust-lang.org/
[daniel-scherzer]: https://github.com/DanielEScherzer
[all-projects-all-time]: https://thanks.rust-lang.org/all-time.html

### rustup-components-history

The second repository that I picked up after it not being maintained for a long time was [`rustup-components-history`][rustup-components-history], which powers [this page][rustup-components-history-page] that shows which Rustup components were available for individual Rust targets in the past few days.

It was a similar story as `thanks`; no one felt like they owned the repository, so no reviews were being made. I found out about this when I was approached by [@rami3l][rami3l], the lead of the Rustup team, if I could help him find a reviewer for his [PR](https://github.com/rust-lang/rustup-components-history/pull/54) that was opened over two years ago. I realized that as a member of the Infrastructure team, that reviewer can simply be me, so I reviewed their PR and finally merged it. Then, by coincidence just a week later, an unrelated [change](https://github.com/rust-lang/blog.rust-lang.org/pull/1941) to one Rust target actually [broke](https://github.com/rust-lang/rustup/issues/5085#issuecomment-5694734804) the components website. I thus went and [fixed](https://github.com/rust-lang/rustup-components-history/pull/60) it, and also gave [permissions](https://github.com/rust-lang/team/pull/2758) to the Rustup team to manage this repository. You would think that a tool called `rustup-components-history` would allow the Rustup team to merge changes to it, but it wasn't actually configured as such before.

Once I fixed the tool, I spent a bit of effort on doing the usual facelift of Rust repositories:
- Switched the default branch to `main` ([rustup-components-history#61]).
- Cleaned up CI ([rustup-components-history#62], [rustup-components-history#65], [rustup-components-history#66]).
- Removed unused code and updated the codebase to Edition 2024 ([rustup-components-history#63]).

This didn't take much time and it rejuvenated the codebase a bit, which is always nice.

[rustup-components-history]: https://github.com/rust-lang/rustup-components-history
[rustup-components-history-page]: https://rust-lang.github.io/rustup-components-history/
[rami3l]: https://github.com/rami3l
[rustup-components-history-rustup]: https://github.com/rust-lang/team/pull/2758

## Funding team activities

As a part of the Rust funding team, I helped bootstrap the Maintainer in Residence (MiR) program, by helping to categorize the maintenance needs of various Rust teams and matching them with the funding needs of Rust maintainers. We were able to support 7 people right from the start, which is awesome! You can find out more about them in these two blog posts:
- [Announcing our first Maintainers in Residence][mir-post-1]
- [Announcing a Maintainer in Residence: Scott Schafer for the Cargo team][mir-post-2]

Apart from that, I finished the [MiR page][mir-page] on the Rust website (implemented in [www.rust-lang.org#2323]), and worked on some tooling to help us track the contributions of funded maintainers. I also prepared a [charter][funding-charter] for the Funding team, to be approved by the Rust Leadership Council.

[mir-page]: https://rust-lang.org/funding/mir.html
[funding-charter]: https://github.com/rust-lang/funding/pull/10

There is a lot more work to do in the Funding team, but I think that we got off to a good start.

## Other things I worked on

- I resumed my refactoring spree of `bootstrap`, the Rust compiler build system, this time with a [set of PRs][bootstrap-llvm] that refactored how the build system builds and downloads LLVM from our CI. This continues a long series of refactoring that tries to make bootstrap easier to understand, modify and maintain, and unlocked some further cleanups ([rust#161853], [rust#161691], [rust#160631]).
- I started working on renaming the [`rust-clippy`](https://github.com/rust-lang/rust-clippy) repository simply to `clippy` and also renaming its default branch to `main` ([rust-clippy#17541], [rust-clippy#17552]).
- As usually, I did lots of tiny fixes and improvements to CI, infrastructure, tooling of various `rust-lang` repositories, and to our bots.
- As usually, I participated in the Rust Compiler [performance triage](https://github.com/rust-lang/rustc-perf/tree/main/triage#rust-compiler-performance-triage).
- Together with my co-mentors, [Jieyou Xu][jieyou-xu] and [Folkert de Vries][folkertdev], we concluded the two Rust GSoC 2026 projects that we were mentoring. I think that both of them were quite successful, and we were very excited to work with our mentees, [Walnut356] and [xonx4l]. I will share more details about the projects in my next report, once Rust GSoC 2026 has completely finished.
- I analysed the results of a [survey](https://github.com/rust-lang/surveys/pull/409) about the performance of the Rust Leadership Council and shared it with members of the Rust Project.
- I wrote a bunch of blog posts on the official Rust blog:
  - Together with [Lori Lorusso][lorilorusso], we prepared another entry of the maintainer spotlight series, this time with [@blyxyas](https://blog.rust-lang.org/inside-rust/2026/09/21/maintainer-spotlight-alejandra-gonzalez-blyxyas/).
  - Posted an [update][lc-update-post] on the activity of the Leadership Council.
  - [Announced](https://blog.rust-lang.org/inside-rust/2026/08/18/leadership-council-repr-selection/) the Leadership Council elections.
  - [Announced][embed-metadata-post] the nightly experiment to default to `-Zembed-metadata=no` in Cargo.
  - Together with [Lori Lorusso][lorilorusso], we prepared two announcements ([1][mir-post-1], [2][mir-post-2]) about our first Maintainers in Residence :tada:
- I was [re-elected][lc-update-post] as the [Infrastructure team][infra-team]'s representative in the Leadership Council. Yay! I hope to continue being useful to the Rust Project in the Leadership Council.

[bootstrap-llvm]: https://github.com/rust-lang/rust/pulls?q=is%3Apr+state%3Amerged+author%3Akobzol+assorted+bootstrap+LLVM+refactor
[jieyou-xu]: https://github.com/jieyouxu
[folkertdev]: https://github.com/folkertdev
[Walnut356]: https://github.com/Walnut356
[xonx4l]: https://github.com/xonx4l
[blyxyas]: https://github.com/blyxyas
[lorilorusso]: https://github.com/lorilorusso
[mir-post-1]: https://blog.rust-lang.org/2026/08/26/announcing-our-first-maintainers-in-residence/
[mir-post-2]: https://blog.rust-lang.org/2026/09/22/announcing-a-maintainer-in-residence-scott-schafer-for-the-cargo-team/
[lc-update-post]: https://blog.rust-lang.org/inside-rust/2026/09/28/leadership-council-update/
[infra-team]: https://rust-lang.org/governance/teams/infra/

## Contribution statistics and pull requests

Below you can find some statistics and a list of PRs that I opened during {{ page.month_range }}.

<!-- stats -->

- Opened **262** pull requests in Rust-related repositories.
  - With a median of **20** modified lines per pull request.
- Reviewed **214** pull requests in Rust-related repositories.
- Sent **889** comments in the `rust-lang` GitHub organization.
- Sent **2282** public and **1942** private messages on the [Rust Zulip](https://rust-lang.zulipchat.com).

<!-- commentary -->

I want to provide a bit of context regarding the statistics above. After my [previous report]({% post_url 2026-08-03-stf-june-july-2026 %}), where I wrote that I opened 162 PRs in two months, some people reached out to me and essentially asked me whether I am OK :laughing: And that I shouldn't overwork myself. Given that in this report, that number is (exactly!) 100 PRs higher, I thought that I should explain it a bit.

Those numbers of PRs are not produced by me using LLMs (as I explained [previously]({% post_url 2026-08-03-stf-june-july-2026 %}#conclusion), I almost never use them for code that gets committed to git) nor by me being a 10x engineer working 24/7.  I simply open a large number of usually very small PRs across many projects, given the nature of work that I do in the Rust Project, which often deals with fixing CI, improving infrastructure and tooling, improving docs, etc. I don't push out 5 big new features every day. That's why I included the median[^average] of modified lines in my PR, to get across the idea that most of my PRs are very small. So take the numbers above with a grain of salt. I mostly put them here for my own historical record.

[^average]: I used a median, rather than an average, because I opened [one PR](https://github.com/rust-lang/rustc-perf/pull/2522) recently that had 1.6 million modified lines :laughing: And only after it was merged I realized that most of that was some accidentally committed leftover profiling data. We force-pushed the changes away, but this PR skewed the average to over 8000 lines :laughing: That's why it's hard to take similar statistics at face value :)

<!-- pr-list -->

<details markdown="1">
<summary>List of opened PRs</summary>

### rust-lang/rust (71 PRs)
- [#160421](https://github.com/rust-lang/rust/pull/160421): Do not use -Werror when building rustc_llvm with GCC (<span style="color: red;">closed</span>)
- [#160427](https://github.com/rust-lang/rust/pull/160427): Run try builds on EC2 by default (<span style="color: #8250DF;">merged</span>)
- [#160434](https://github.com/rust-lang/rust/pull/160434): Avoid Docker push when the image did not change (<span style="color: #8250DF;">merged</span>)
- [#160449](https://github.com/rust-lang/rust/pull/160449): Fix lookup of object files (<span style="color: #8250DF;">merged</span>)
- [#160451](https://github.com/rust-lang/rust/pull/160451): Deduplicate target and host filesearch (<span style="color: #8250DF;">merged</span>)
- [#160453](https://github.com/rust-lang/rust/pull/160453): Add fast path to `escape_string_symbol` (<span style="color: #8250DF;">merged</span>)
- [#160493](https://github.com/rust-lang/rust/pull/160493): Rollup of 29 pull requests (<span style="color: #8250DF;">merged</span>)
- [#160501](https://github.com/rust-lang/rust/pull/160501): Add bootstrap CLI snapshot test for testing miri (<span style="color: #8250DF;">merged</span>)
- [#160502](https://github.com/rust-lang/rust/pull/160502): Reduce number of miri tests executed on PR CI (<span style="color: #8250DF;">merged</span>)
- [#160573](https://github.com/rust-lang/rust/pull/160573): [perf test] Revert "Rollup merge of #159339 - LorrensP-2158466:extract-use-injections, r=petrochenkov" (<span style="color: red;">closed</span>)
- [#160574](https://github.com/rust-lang/rust/pull/160574): Update rustc-perf submodule (<span style="color: #8250DF;">merged</span>)
- [#160579](https://github.com/rust-lang/rust/pull/160579): Do not download GCC from CI in PR CI jobs (<span style="color: red;">closed</span>)
- [#160631](https://github.com/rust-lang/rust/pull/160631): Do not eagerly download rustfmt in bootstrap (<span style="color: #8250DF;">merged</span>)
- [#160645](https://github.com/rust-lang/rust/pull/160645): Assorted bootstrap LLVM refactors (part 1/N) (<span style="color: #8250DF;">merged</span>)
- [#160681](https://github.com/rust-lang/rust/pull/160681): Respect `--all-targets` flag when checking the compiler (<span style="color: #8250DF;">merged</span>)
- [#160693](https://github.com/rust-lang/rust/pull/160693): Add branch config for perf. unrolling in bors (<span style="color: #8250DF;">merged</span>)
- [#160839](https://github.com/rust-lang/rust/pull/160839): Stop updating npm lockfile by Renovatebot (<span style="color: #8250DF;">merged</span>)
- [#160894](https://github.com/rust-lang/rust/pull/160894): Allow running an arbitrary number of try jobs per PR (<span style="color: #8250DF;">merged</span>)
- [#160916](https://github.com/rust-lang/rust/pull/160916): Assorted bootstrap LLVM refactors (part 2/N) (<span style="color: #8250DF;">merged</span>)
- [#160970](https://github.com/rust-lang/rust/pull/160970): Fix handling of relative paths starting with a dot in bootstrap (<span style="color: #8250DF;">merged</span>)
- [#161046](https://github.com/rust-lang/rust/pull/161046): Enable unrolling feature of bors (<span style="color: #8250DF;">merged</span>)
- [#161102](https://github.com/rust-lang/rust/pull/161102): Explicitly pass run_make_support rlib/rmeta paths to compiletest (<span style="color: #8250DF;">merged</span>)
- [#161111](https://github.com/rust-lang/rust/pull/161111): Take bors try-perf branch into account in verify-channel.sh (<span style="color: #8250DF;">merged</span>)
- [#161145](https://github.com/rust-lang/rust/pull/161145): Remove references to the obsolete `try-perf` branch (<span style="color: #8250DF;">merged</span>)
- [#161235](https://github.com/rust-lang/rust/pull/161235): Compute job time in post-merge-report from the actual GitHub duration (<span style="color: #8250DF;">merged</span>)
- [#161236](https://github.com/rust-lang/rust/pull/161236): Download auto jobs in citool in parallel (<span style="color: #8250DF;">merged</span>)
- [#161237](https://github.com/rust-lang/rust/pull/161237): Remove jdno from infra-ci rotation (<span style="color: #8250DF;">merged</span>)
- [#161247](https://github.com/rust-lang/rust/pull/161247): Assorted bootstrap LLVM refactors (part 3/N) (<span style="color: #8250DF;">merged</span>)
- [#161290](https://github.com/rust-lang/rust/pull/161290): Assorted bootstrap LLVM refactors (part 4/N) (<span style="color: #8250DF;">merged</span>)
- [#161344](https://github.com/rust-lang/rust/pull/161344): Update the `rustc-perf` submodule (<span style="color: #8250DF;">merged</span>)
- [#161384](https://github.com/rust-lang/rust/pull/161384): Bust sccache's cache (<span style="color: #8250DF;">merged</span>)
- [#161393](https://github.com/rust-lang/rust/pull/161393): Configure LLM policy URL for triagebot (<span style="color: #8250DF;">merged</span>)
- [#161438](https://github.com/rust-lang/rust/pull/161438): Change triagebot backport to ping T-libs-fcp (<span style="color: #8250DF;">merged</span>)
- [#161460](https://github.com/rust-lang/rust/pull/161460): Add a `size_hint` function to `Display` (<span style="color: green;">open</span>)
- [#161475](https://github.com/rust-lang/rust/pull/161475): Fix checking of LLVM prebuilt status (<span style="color: #8250DF;">merged</span>)
- [#161483](https://github.com/rust-lang/rust/pull/161483): Warn about running ui-fulldeps tests in stage 1 (<span style="color: #8250DF;">merged</span>)
- [#161516](https://github.com/rust-lang/rust/pull/161516): Revert #161236 (Download auto jobs in citool in parallel) (<span style="color: #8250DF;">merged</span>)
- [#161641](https://github.com/rust-lang/rust/pull/161641): Check for missing rustfmt in the stdarch intrinsic test step sooner (<span style="color: #8250DF;">merged</span>)
- [#161663](https://github.com/rust-lang/rust/pull/161663): Reduce dependency on implicit paths in bootstrap (<span style="color: #8250DF;">merged</span>)
- [#161666](https://github.com/rust-lang/rust/pull/161666): Print vendor instructions in `x vendor` (<span style="color: #8250DF;">merged</span>)
- [#161691](https://github.com/rust-lang/rust/pull/161691): Assorted bootstrap config refactors (part 1/N) (<span style="color: #8250DF;">merged</span>)
- [#161853](https://github.com/rust-lang/rust/pull/161853): Consolidate LLVM skip in check builds in bootstrap (<span style="color: #8250DF;">merged</span>)
- [#161992](https://github.com/rust-lang/rust/pull/161992): [do not merge] ARM perf experiments (<span style="color: red;">closed</span>)
- [#161995](https://github.com/rust-lang/rust/pull/161995): [perf] Use SmallVec in `smart_resolve_path` (<span style="color: red;">closed</span>)
- [#162004](https://github.com/rust-lang/rust/pull/162004): Remove unneeded clone in macro deriving (<span style="color: #8250DF;">merged</span>)
- [#162006](https://github.com/rust-lang/rust/pull/162006): Use a simple arena for annotatable items (<span style="color: red;">closed</span>)
- [#162053](https://github.com/rust-lang/rust/pull/162053): Add bootstrap command to check all Tier 2+ targets (<span style="color: green;">open</span>)
- [#162092](https://github.com/rust-lang/rust/pull/162092): Implement test- naming convention for CI jobs (<span style="color: #8250DF;">merged</span>)
- [#162111](https://github.com/rust-lang/rust/pull/162111): Update mailmap for Will Crichton and Petr Hosek (<span style="color: #8250DF;">merged</span>)
- [#162328](https://github.com/rust-lang/rust/pull/162328): Allow overriding filecheck even if LLVM is built or downloaded (<span style="color: #8250DF;">merged</span>)
- [#162371](https://github.com/rust-lang/rust/pull/162371): Cache sanitizer set in `Session` (<span style="color: #8250DF;">merged</span>)
- [#162413](https://github.com/rust-lang/rust/pull/162413): Unconditionally invalidate the library when the compiler changes (<span style="color: #8250DF;">merged</span>)
- [#162428](https://github.com/rust-lang/rust/pull/162428): Pin the number of frontend threads while gathering PGO to 1 (<span style="color: #8250DF;">merged</span>)
- [#162473](https://github.com/rust-lang/rust/pull/162473): Small `x perf` improvements (<span style="color: #8250DF;">merged</span>)
- [#162480](https://github.com/rust-lang/rust/pull/162480): Mono item collection microoptimizations (<span style="color: red;">closed</span>)
- [#162485](https://github.com/rust-lang/rust/pull/162485): Parallelize gathering constraints in the borrow checker (<span style="color: red;">closed</span>)
- [#162488](https://github.com/rust-lang/rust/pull/162488): Use `DenseBit` for `drop_live_at` in liveness tracing (<span style="color: #8250DF;">merged</span>)
- [#162512](https://github.com/rust-lang/rust/pull/162512): Implement `ExactSizeIterator` for `Chain` (<span style="color: red;">closed</span>)
- [#162524](https://github.com/rust-lang/rust/pull/162524): Use `SmallVec` in `TokenCursor` (<span style="color: red;">closed</span>)
- [#162533](https://github.com/rust-lang/rust/pull/162533): Use `share-generics` for libstd (<span style="color: red;">closed</span>)
- [#162593](https://github.com/rust-lang/rust/pull/162593): [perf] Try to optimize `collect_pos` (<span style="color: green;">open</span>)
- [#162777](https://github.com/rust-lang/rust/pull/162777): Remove allocation from `mbe::quoted::parse` (<span style="color: red;">closed</span>)
- [#162780](https://github.com/rust-lang/rust/pull/162780): Use `-Clinker-plugin-lto` in bootstrap (<span style="color: red;">closed</span>)
- [#162848](https://github.com/rust-lang/rust/pull/162848): Use 2 parallel frontend threads by default on the nightly and dev channel (<span style="color: green;">open</span>)
- [#163212](https://github.com/rust-lang/rust/pull/163212): rustfmt subtree update (<span style="color: red;">closed</span>)
- [#163412](https://github.com/rust-lang/rust/pull/163412): Apply LTO to Cranelift and GCC codegen backends (<span style="color: green;">open</span>)
- [#163433](https://github.com/rust-lang/rust/pull/163433): Support also `try-jobs:` to specify custom try jobs (<span style="color: #8250DF;">merged</span>)
- [#163436](https://github.com/rust-lang/rust/pull/163436): Stabilize `-Zembed-metadata` (<span style="color: green;">open</span>)
- [#163444](https://github.com/rust-lang/rust/pull/163444): Add `stable_rustc` helper in `run-make-support` (<span style="color: #8250DF;">merged</span>)
- [#163452](https://github.com/rust-lang/rust/pull/163452): Use newtype enums for representing frontend and backend jobs (<span style="color: green;">open</span>)
- [#163533](https://github.com/rust-lang/rust/pull/163533): Run cg_gcc tests with the correct compiler (<span style="color: green;">open</span>)

### rust-lang/team (36 PRs)
- [#2648](https://github.com/rust-lang/team/pull/2648): Move inactive t-triage members to alumni (<span style="color: #8250DF;">merged</span>)
- [#2649](https://github.com/rust-lang/team/pull/2649): Add Zulip topic for the funding team and MiRs (<span style="color: #8250DF;">merged</span>)
- [#2662](https://github.com/rust-lang/team/pull/2662): Configure branches for unrolled perf builds for bors (<span style="color: #8250DF;">merged</span>)
- [#2669](https://github.com/rust-lang/team/pull/2669): Add first batch of Maintainers in Residence (<span style="color: #8250DF;">merged</span>)
- [#2670](https://github.com/rust-lang/team/pull/2670): Add Tyler Mandry to funding advisors (<span style="color: #8250DF;">merged</span>)
- [#2674](https://github.com/rust-lang/team/pull/2674): Change default branch of `rust-clippy` to `main` (<span style="color: green;">open</span>)
- [#2679](https://github.com/rust-lang/team/pull/2679): Add ruleset for the `thanks` repo (<span style="color: #8250DF;">merged</span>)
- [#2680](https://github.com/rust-lang/team/pull/2680): Remove `rust-timer` branches from `rust-lang/rust` (<span style="color: #8250DF;">merged</span>)
- [#2681](https://github.com/rust-lang/team/pull/2681): Remove obsolete merge bot variants (<span style="color: #8250DF;">merged</span>)
- [#2682](https://github.com/rust-lang/team/pull/2682): Archive the `rustc-rayon` repository (<span style="color: #8250DF;">merged</span>)
- [#2696](https://github.com/rust-lang/team/pull/2696): Rename the default branch of `triagebot` to `main` (<span style="color: #8250DF;">merged</span>)
- [#2697](https://github.com/rust-lang/team/pull/2697): Change default branch of the `forge` repository to `main` (<span style="color: #8250DF;">merged</span>)
- [#2700](https://github.com/rust-lang/team/pull/2700): Add check for duplicated alumnis and remove them (<span style="color: #8250DF;">merged</span>)
- [#2713](https://github.com/rust-lang/team/pull/2713): Add lcnr and Joel Marcey to funding advisors (<span style="color: #8250DF;">merged</span>)
- [#2725](https://github.com/rust-lang/team/pull/2725): Add crates to the v1 API (<span style="color: #8250DF;">merged</span>)
- [#2726](https://github.com/rust-lang/team/pull/2726): Ensure that only `rust-lang-owner` owns our tracked crates (<span style="color: #8250DF;">merged</span>)
- [#2727](https://github.com/rust-lang/team/pull/2727): Track Cargo crates (<span style="color: green;">open</span>)
- [#2735](https://github.com/rust-lang/team/pull/2735): Point the `funding@rust-lang.org` e-mail list to the funding team (<span style="color: #8250DF;">merged</span>)
- [#2742](https://github.com/rust-lang/team/pull/2742): Assign owner teams to crates.io crates (<span style="color: #8250DF;">merged</span>)
- [#2743](https://github.com/rust-lang/team/pull/2743): Force team ownership of crates (<span style="color: #8250DF;">merged</span>)
- [#2744](https://github.com/rust-lang/team/pull/2744): Set compiler team as co-owners of `annotate-snippets` (<span style="color: #8250DF;">merged</span>)
- [#2751](https://github.com/rust-lang/team/pull/2751): Add branch protection for the `goals` repo (<span style="color: #8250DF;">merged</span>)
- [#2758](https://github.com/rust-lang/team/pull/2758): Give the Rustup team access to `rustup-components-history` (<span style="color: #8250DF;">merged</span>)
- [#2759](https://github.com/rust-lang/team/pull/2759): Change the default branch of portable-simd to main (<span style="color: #8250DF;">merged</span>)
- [#2767](https://github.com/rust-lang/team/pull/2767): Add Scott Schafer to the Maintainers in Residence team (<span style="color: #8250DF;">merged</span>)
- [#2772](https://github.com/rust-lang/team/pull/2772): Give security response merge rights to the blog (<span style="color: red;">closed</span>)
- [#2775](https://github.com/rust-lang/team/pull/2775): Allow managing unpublishable crates (<span style="color: #8250DF;">merged</span>)
- [#2777](https://github.com/rust-lang/team/pull/2777): Process crates without trusted publishing (<span style="color: #8250DF;">merged</span>)
- [#2778](https://github.com/rust-lang/team/pull/2778): Manage `rustup-available-packages` crate (<span style="color: green;">open</span>)
- [#2786](https://github.com/rust-lang/team/pull/2786): Add homepage to the funding team repo (<span style="color: #8250DF;">merged</span>)
- [#2787](https://github.com/rust-lang/team/pull/2787): Archive the `pin-utils` repository (<span style="color: green;">open</span>)
- [#2788](https://github.com/rust-lang/team/pull/2788): Update Council libs rep (<span style="color: #8250DF;">merged</span>)
- [#2789](https://github.com/rust-lang/team/pull/2789): Manage Council private Zulip stream (<span style="color: #8250DF;">merged</span>)
- [#2792](https://github.com/rust-lang/team/pull/2792): Sort bypass actors (<span style="color: #8250DF;">merged</span>)
- [#2793](https://github.com/rust-lang/team/pull/2793): Create `trusted-contributors` team (<span style="color: #8250DF;">merged</span>)
- [#2795](https://github.com/rust-lang/team/pull/2795): Add Predrag to trusted-contributors (<span style="color: green;">open</span>)

### rust-lang/bors (34 PRs)
- [#799](https://github.com/rust-lang/bors/pull/799): Tag EC2 instances launched by bors (<span style="color: #8250DF;">merged</span>)
- [#800](https://github.com/rust-lang/bors/pull/800): Add web page with EC2 instance list (<span style="color: #8250DF;">merged</span>)
- [#801](https://github.com/rust-lang/bors/pull/801): Add links to the queue page (<span style="color: #8250DF;">merged</span>)
- [#802](https://github.com/rust-lang/bors/pull/802): Implement backfilling of EC2 instances (<span style="color: #8250DF;">merged</span>)
- [#803](https://github.com/rust-lang/bors/pull/803): Improve layout of pending builds table (<span style="color: #8250DF;">merged</span>)
- [#804](https://github.com/rust-lang/bors/pull/804): Strip auto/try job prefixes (<span style="color: #8250DF;">merged</span>)
- [#806](https://github.com/rust-lang/bors/pull/806): Try to start EC2 instances on any branch (<span style="color: #8250DF;">merged</span>)
- [#807](https://github.com/rust-lang/bors/pull/807): Reload in-memory job cache when bors starts (<span style="color: #8250DF;">merged</span>)
- [#808](https://github.com/rust-lang/bors/pull/808): Document Zulip posting and EC2 instance spawning (<span style="color: #8250DF;">merged</span>)
- [#809](https://github.com/rust-lang/bors/pull/809): Only consider workflow run webhooks with the `push` event (<span style="color: #8250DF;">merged</span>)
- [#812](https://github.com/rust-lang/bors/pull/812): Allow opting out of the maximum try job limit (<span style="color: #8250DF;">merged</span>)
- [#813](https://github.com/rust-lang/bors/pull/813): Add hint about `@bors try nolimit` (<span style="color: #8250DF;">merged</span>)
- [#815](https://github.com/rust-lang/bors/pull/815): Add a hint about retrying PR CI when someone uses `@bors retry` in an invalid state (<span style="color: #8250DF;">merged</span>)
- [#816](https://github.com/rust-lang/bors/pull/816): Store `pr_number` field in the `build` table (<span style="color: #8250DF;">merged</span>)
- [#817](https://github.com/rust-lang/bors/pull/817): Add rollup unrolling (<span style="color: #8250DF;">merged</span>)
- [#818](https://github.com/rust-lang/bors/pull/818): Add a hint to `@bors try cancel` (<span style="color: #8250DF;">merged</span>)
- [#819](https://github.com/rust-lang/bors/pull/819): Trigger the merge queue when the priority of a PR changes (<span style="color: #8250DF;">merged</span>)
- [#820](https://github.com/rust-lang/bors/pull/820): Correctly parse unrolled member build kind from EC2 instance tags (<span style="color: #8250DF;">merged</span>)
- [#821](https://github.com/rust-lang/bors/pull/821): Fix termination of multiple EC2 instances (<span style="color: #8250DF;">merged</span>)
- [#823](https://github.com/rust-lang/bors/pull/823): Close PRs in DB that disappear from GitHub (<span style="color: #8250DF;">merged</span>)
- [#827](https://github.com/rust-lang/bors/pull/827): Ignore homu-ignore blocks in squashed commit messages (<span style="color: #8250DF;">merged</span>)
- [#833](https://github.com/rust-lang/bors/pull/833): Add a sanity check for valid bors config before merging a PR (<span style="color: #8250DF;">merged</span>)
- [#834](https://github.com/rust-lang/bors/pull/834): Fix decoding base64 GitHub contents (<span style="color: #8250DF;">merged</span>)
- [#837](https://github.com/rust-lang/bors/pull/837): Check that EC2 instance is in `allowed_instances` (<span style="color: #8250DF;">merged</span>)
- [#838](https://github.com/rust-lang/bors/pull/838): Add in-memory cache of spawned EC2 instances (<span style="color: #8250DF;">merged</span>)
- [#839](https://github.com/rust-lang/bors/pull/839): Check config validity post merge (<span style="color: #8250DF;">merged</span>)
- [#850](https://github.com/rust-lang/bors/pull/850): Do not link to GitHub PRs when doing rollup mergeability check (<span style="color: #8250DF;">merged</span>)
- [#854](https://github.com/rust-lang/bors/pull/854): Add a test for not merging a tentatively approved PR (<span style="color: #8250DF;">merged</span>)
- [#858](https://github.com/rust-lang/bors/pull/858): Upgrade tentative approvals if the PR was already fully approved (<span style="color: #8250DF;">merged</span>)
- [#859](https://github.com/rust-lang/bors/pull/859): Make tentative approvals less obtrusive (<span style="color: #8250DF;">merged</span>)
- [#862](https://github.com/rust-lang/bors/pull/862): Apply approval labels eagerly when a PR is tentatively approved (<span style="color: #8250DF;">merged</span>)
- [#863](https://github.com/rust-lang/bors/pull/863): Support also the `try-jobs` custom try job marker (<span style="color: #8250DF;">merged</span>)
- [#864](https://github.com/rust-lang/bors/pull/864): Set `approval_tentative` to `FALSE` in `unapprove_pull_request_if_sha_changed` (<span style="color: #8250DF;">merged</span>)
- [#865](https://github.com/rust-lang/bors/pull/865): Hotfix database state (<span style="color: red;">closed</span>)

### rust-lang/rustc-perf (33 PRs)
- [#2520](https://github.com/rust-lang/rustc-perf/pull/2520): Add support for bare rustc invocation with `--print-sysroot` (<span style="color: #8250DF;">merged</span>)
- [#2521](https://github.com/rust-lang/rustc-perf/pull/2521): Temporarily fix the `serde` 4 threads benchmark (<span style="color: #8250DF;">merged</span>)
- [#2522](https://github.com/rust-lang/rustc-perf/pull/2522): Create three NLL benchmarks (<span style="color: #8250DF;">merged</span>)
- [#2524](https://github.com/rust-lang/rustc-perf/pull/2524): Remove unrolling functionality (<span style="color: #8250DF;">merged</span>)
- [#2526](https://github.com/rust-lang/rustc-perf/pull/2526): Remove accidentally committed files (<span style="color: red;">closed</span>)
- [#2533](https://github.com/rust-lang/rustc-perf/pull/2533): Fix handling of try builds that were not enqueued (<span style="color: #8250DF;">merged</span>)
- [#2534](https://github.com/rust-lang/rustc-perf/pull/2534): Ignore comments from bors (<span style="color: #8250DF;">merged</span>)
- [#2535](https://github.com/rust-lang/rustc-perf/pull/2535): Read bors try build completed comments (<span style="color: #8250DF;">merged</span>)
- [#2538](https://github.com/rust-lang/rustc-perf/pull/2538): Add 2026-08-18 triage (<span style="color: #8250DF;">merged</span>)
- [#2539](https://github.com/rust-lang/rustc-perf/pull/2539): Add crate metadata to compare page quick links (<span style="color: #8250DF;">merged</span>)
- [#2541](https://github.com/rust-lang/rustc-perf/pull/2541): Include profile in error message about unavailable artifacts (<span style="color: #8250DF;">merged</span>)
- [#2550](https://github.com/rust-lang/rustc-perf/pull/2550): Improve support for ARM benchmarks (<span style="color: #8250DF;">merged</span>)
- [#2551](https://github.com/rust-lang/rustc-perf/pull/2551): Correctly store targets of benchmark requests into the database (<span style="color: #8250DF;">merged</span>)
- [#2555](https://github.com/rust-lang/rustc-perf/pull/2555): Respect optional job attribute when checking parent jobs (<span style="color: #8250DF;">merged</span>)
- [#2556](https://github.com/rust-lang/rustc-perf/pull/2556): Separate artifact size records by target (<span style="color: #8250DF;">merged</span>)
- [#2560](https://github.com/rust-lang/rustc-perf/pull/2560): Ignore runtime benchmarks when a benchmark filter is set (<span style="color: #8250DF;">merged</span>)
- [#2564](https://github.com/rust-lang/rustc-perf/pull/2564): Fix duration estimation (<span style="color: #8250DF;">merged</span>)
- [#2565](https://github.com/rust-lang/rustc-perf/pull/2565): Speed up triage command (<span style="color: #8250DF;">merged</span>)
- [#2566](https://github.com/rust-lang/rustc-perf/pull/2566): Run ARM benchmarks by default (<span style="color: #8250DF;">merged</span>)
- [#2567](https://github.com/rust-lang/rustc-perf/pull/2567): Fetch GitHub commits concurrently in the triage command (<span style="color: #8250DF;">merged</span>)
- [#2568](https://github.com/rust-lang/rustc-perf/pull/2568): Add support for frontend threads to the UI (<span style="color: #8250DF;">merged</span>)
- [#2571](https://github.com/rust-lang/rustc-perf/pull/2571): Add `tokio-1.53.1` benchmark (<span style="color: #8250DF;">merged</span>)
- [#2572](https://github.com/rust-lang/rustc-perf/pull/2572): Share target directory for different values of frontend threads (<span style="color: #8250DF;">merged</span>)
- [#2573](https://github.com/rust-lang/rustc-perf/pull/2573): UI improvements related to frontend threads (<span style="color: #8250DF;">merged</span>)
- [#2574](https://github.com/rust-lang/rustc-perf/pull/2574): Allow benchmark to opt into different values of frontend threads (<span style="color: #8250DF;">merged</span>)
- [#2575](https://github.com/rust-lang/rustc-perf/pull/2575): Remove the `serde-1.0.219-threads4` benchmark (<span style="color: #8250DF;">merged</span>)
- [#2579](https://github.com/rust-lang/rustc-perf/pull/2579): Fix normalization of profiles and scenario in the frontend (<span style="color: #8250DF;">merged</span>)
- [#2580](https://github.com/rust-lang/rustc-perf/pull/2580): Add 2026-09-14 triage (<span style="color: #8250DF;">merged</span>)
- [#2581](https://github.com/rust-lang/rustc-perf/pull/2581): Run `apt update` before installing Valgrind (<span style="color: #8250DF;">merged</span>)
- [#2585](https://github.com/rust-lang/rustc-perf/pull/2585): Allow filtering Clippy benchmarks in the compare page (<span style="color: #8250DF;">merged</span>)
- [#2586](https://github.com/rust-lang/rustc-perf/pull/2586): Use `--jobs-frontend` instead of `-Zthreads` (<span style="color: green;">open</span>)
- [#2594](https://github.com/rust-lang/rustc-perf/pull/2594): Make `parse_benchmarks` infallible (<span style="color: #8250DF;">merged</span>)
- [#2596](https://github.com/rust-lang/rustc-perf/pull/2596): Improve support for different codegen backends (<span style="color: #8250DF;">merged</span>)

### rust-lang/thanks (26 PRs)
- [#109](https://github.com/rust-lang/thanks/pull/109): Run Clippy and rustfmt on CI (<span style="color: #8250DF;">merged</span>)
- [#110](https://github.com/rust-lang/thanks/pull/110): Write all-time data in CSV output mode (<span style="color: #8250DF;">merged</span>)
- [#111](https://github.com/rust-lang/thanks/pull/111): Sort submodules to fix non-deterministic commit iteration (<span style="color: #8250DF;">merged</span>)
- [#112](https://github.com/rust-lang/thanks/pull/112): Add conclusion CI job (<span style="color: #8250DF;">merged</span>)
- [#113](https://github.com/rust-lang/thanks/pull/113): Force handling of submodules (<span style="color: #8250DF;">merged</span>)
- [#114](https://github.com/rust-lang/thanks/pull/114): Sort also by e-mail author while deduplicating (<span style="color: #8250DF;">merged</span>)
- [#115](https://github.com/rust-lang/thanks/pull/115): Update to edition 2024 (<span style="color: #8250DF;">merged</span>)
- [#116](https://github.com/rust-lang/thanks/pull/116): Change processing of commits to walk all commits only once (<span style="color: #8250DF;">merged</span>)
- [#117](https://github.com/rust-lang/thanks/pull/117): [perf] checkout submodules in parallel (<span style="color: red;">closed</span>)
- [#118](https://github.com/rust-lang/thanks/pull/118): Set `line-tables-only` debuginfo in release mode (<span style="color: #8250DF;">merged</span>)
- [#119](https://github.com/rust-lang/thanks/pull/119): Refresh repositories using an environment variable, not using a CLI flag (<span style="color: #8250DF;">merged</span>)
- [#120](https://github.com/rust-lang/thanks/pull/120): Use cache in CI (<span style="color: #8250DF;">merged</span>)
- [#121](https://github.com/rust-lang/thanks/pull/121): Add all-time snapshot (<span style="color: #8250DF;">merged</span>)
- [#122](https://github.com/rust-lang/thanks/pull/122): Make tests self-contained (<span style="color: #8250DF;">merged</span>)
- [#123](https://github.com/rust-lang/thanks/pull/123): Checkout submodules in parallel (<span style="color: #8250DF;">merged</span>)
- [#124](https://github.com/rust-lang/thanks/pull/124): Allow overriding the mailmap (<span style="color: #8250DF;">merged</span>)
- [#125](https://github.com/rust-lang/thanks/pull/125): Prepare for multiple projects (<span style="color: #8250DF;">merged</span>)
- [#126](https://github.com/rust-lang/thanks/pull/126): Add support for Rustup (<span style="color: #8250DF;">merged</span>)
- [#130](https://github.com/rust-lang/thanks/pull/130): Add page with all tracked projects (<span style="color: #8250DF;">merged</span>)
- [#131](https://github.com/rust-lang/thanks/pull/131): Track crates.io and docs.rs (<span style="color: #8250DF;">merged</span>)
- [#132](https://github.com/rust-lang/thanks/pull/132): Ignore bots in docs.rs (<span style="color: #8250DF;">merged</span>)
- [#133](https://github.com/rust-lang/thanks/pull/133): Ensure that deploys are never executed concurrently (<span style="color: #8250DF;">merged</span>)
- [#138](https://github.com/rust-lang/thanks/pull/138): Make the projects page be the homepage (<span style="color: #8250DF;">merged</span>)
- [#141](https://github.com/rust-lang/thanks/pull/141): Make the regression test optional (<span style="color: #8250DF;">merged</span>)
- [#143](https://github.com/rust-lang/thanks/pull/143): Use deduplicated scores for people and commit count (<span style="color: #8250DF;">merged</span>)
- [#144](https://github.com/rust-lang/thanks/pull/144): Ignore dependabot and renovatebot by default (<span style="color: #8250DF;">merged</span>)

### rust-lang/blog.rust-lang.org (10 PRs)
- [#1910](https://github.com/rust-lang/blog.rust-lang.org/pull/1910): Add post about using `-Zembed-metadata=no` by default on nightly (<span style="color: #8250DF;">merged</span>)
- [#1911](https://github.com/rust-lang/blog.rust-lang.org/pull/1911): Add Leadership Council September 2026 announcement post (<span style="color: #8250DF;">merged</span>)
- [#1913](https://github.com/rust-lang/blog.rust-lang.org/pull/1913): Clarify that `-Zembed-metadata=no` is an experiment (<span style="color: #8250DF;">merged</span>)
- [#1914](https://github.com/rust-lang/blog.rust-lang.org/pull/1914): Add `Announcing our first Maintainers in Residence` blog post (<span style="color: #8250DF;">merged</span>)
- [#1927](https://github.com/rust-lang/blog.rust-lang.org/pull/1927): Build Zola in debug mode (<span style="color: #8250DF;">merged</span>)
- [#1931](https://github.com/rust-lang/blog.rust-lang.org/pull/1931): Fix placeholder date validation for Inside Rust posts (<span style="color: #8250DF;">merged</span>)
- [#1942](https://github.com/rust-lang/blog.rust-lang.org/pull/1942): Add Enabling the parallel frontend on nightly post (<span style="color: green;">open</span>)
- [#1943](https://github.com/rust-lang/blog.rust-lang.org/pull/1943): Add Leadership Council September 2026 update post (<span style="color: #8250DF;">merged</span>)
- [#1947](https://github.com/rust-lang/blog.rust-lang.org/pull/1947): Add Maintainer spotlight interview with blyxyas (<span style="color: #8250DF;">merged</span>)
- [#1948](https://github.com/rust-lang/blog.rust-lang.org/pull/1948): Add `Announcing a Maintainer in Residence: Scott Schafer for the Cargo team` post (<span style="color: #8250DF;">merged</span>)

### rust-lang/triagebot (8 PRs)
- [#2484](https://github.com/rust-lang/triagebot/pull/2484): Run CI on `main` branch (<span style="color: #8250DF;">merged</span>)
- [#2485](https://github.com/rust-lang/triagebot/pull/2485): Deny warnings on CI (<span style="color: #8250DF;">merged</span>)
- [#2486](https://github.com/rust-lang/triagebot/pull/2486): Add LLM policy URL config (<span style="color: #8250DF;">merged</span>)
- [#2487](https://github.com/rust-lang/triagebot/pull/2487): Fix sending of Zulip DMs (<span style="color: #8250DF;">merged</span>)
- [#2492](https://github.com/rust-lang/triagebot/pull/2492): Fix sending of Zulip DMs (take 2) (<span style="color: #8250DF;">merged</span>)
- [#2497](https://github.com/rust-lang/triagebot/pull/2497): Implement crate yanking/unyanking on Zulip (<span style="color: #8250DF;">merged</span>)
- [#2498](https://github.com/rust-lang/triagebot/pull/2498): Fix channel name in yank check (<span style="color: #8250DF;">merged</span>)
- [#2510](https://github.com/rust-lang/triagebot/pull/2510): Stop trusting Zulip custom profile fields in the `lookup` command (<span style="color: #8250DF;">merged</span>)

### rust-lang/josh-sync (7 PRs)
- [#56](https://github.com/rust-lang/josh-sync/pull/56): Update josh-sync version (<span style="color: #8250DF;">merged</span>)
- [#57](https://github.com/rust-lang/josh-sync/pull/57): Fix CI check (<span style="color: #8250DF;">merged</span>)
- [#59](https://github.com/rust-lang/josh-sync/pull/59): Load nightly commit SHA from CI instead of from `rustc` (<span style="color: #8250DF;">merged</span>)
- [#60](https://github.com/rust-lang/josh-sync/pull/60): Include nightly version in merge commit message (<span style="color: #8250DF;">merged</span>)
- [#62](https://github.com/rust-lang/josh-sync/pull/62): Allow specifying nightly date in `pull --upstream-commit` (<span style="color: #8250DF;">merged</span>)
- [#63](https://github.com/rust-lang/josh-sync/pull/63): Allow pushing commits with the SSH protocol (<span style="color: green;">open</span>)
- [#64](https://github.com/rust-lang/josh-sync/pull/64): Allow continuing with a pull when a merge conflict happens (<span style="color: #8250DF;">merged</span>)

### rust-lang/rustup-components-history (7 PRs)
- [#60](https://github.com/rust-lang/rustup-components-history/pull/60): Parse tier tables by their ID, not position (<span style="color: #8250DF;">merged</span>)
- [#61](https://github.com/rust-lang/rustup-components-history/pull/61): Switch default branch to main (<span style="color: #8250DF;">merged</span>)
- [#62](https://github.com/rust-lang/rustup-components-history/pull/62): Update CI (<span style="color: #8250DF;">merged</span>)
- [#63](https://github.com/rust-lang/rustup-components-history/pull/63): Remove unused code (<span style="color: #8250DF;">merged</span>)
- [#64](https://github.com/rust-lang/rustup-components-history/pull/64): Reduce rightward drift (<span style="color: #8250DF;">merged</span>)
- [#65](https://github.com/rust-lang/rustup-components-history/pull/65): Deploy GitHub Pages from the workflow (<span style="color: #8250DF;">merged</span>)
- [#66](https://github.com/rust-lang/rustup-components-history/pull/66): Build the repo on CI in release mode (<span style="color: #8250DF;">merged</span>)

### rust-lang/rust-clippy (4 PRs)
- [#17541](https://github.com/rust-lang/rust-clippy/pull/17541): Build docs into the `main` directory (<span style="color: #8250DF;">merged</span>)
- [#17543](https://github.com/rust-lang/rust-clippy/pull/17543): First add files to git before checking diff in the deploy script (<span style="color: red;">closed</span>)
- [#17552](https://github.com/rust-lang/rust-clippy/pull/17552): Modify doc links to point to `main` instead of `master` (<span style="color: #8250DF;">merged</span>)
- [#17556](https://github.com/rust-lang/rust-clippy/pull/17556): Rename default branch from `master` to `main` (<span style="color: green;">open</span>)

### rust-lang/rust-forge (4 PRs)
- [#1098](https://github.com/rust-lang/rust-forge/pull/1098): Rename the default branch to `main` (<span style="color: #8250DF;">merged</span>)
- [#1099](https://github.com/rust-lang/rust-forge/pull/1099): Document `llm_policy_url` (<span style="color: #8250DF;">merged</span>)
- [#1105](https://github.com/rust-lang/rust-forge/pull/1105): Switch governance owner from ehuss to LC (<span style="color: #8250DF;">merged</span>)
- [#1106](https://github.com/rust-lang/rust-forge/pull/1106): Document crate yanking in triagebot (<span style="color: #8250DF;">merged</span>)

### rust-lang/cargo (2 PRs)
- [#17413](https://github.com/rust-lang/cargo/pull/17413): Micro-optimize two package dir functions (<span style="color: #8250DF;">merged</span>)
- [#17426](https://github.com/rust-lang/cargo/pull/17426): Use trusted publishing for Cargo crates (<span style="color: green;">open</span>)

### rust-lang/portable-simd (2 PRs)
- [#549](https://github.com/rust-lang/portable-simd/pull/549): Switch the default branch to main (<span style="color: #8250DF;">merged</span>)
- [#550](https://github.com/rust-lang/portable-simd/pull/550): First rust-lang/rust pull using Josh (<span style="color: green;">open</span>)

### rust-lang/rustc-dev-guide (2 PRs)
- [#3027](https://github.com/rust-lang/rustc-dev-guide/pull/3027): Note that cg-clif is using Josh now (<span style="color: #8250DF;">merged</span>)
- [#3032](https://github.com/rust-lang/rustc-dev-guide/pull/3032): Mark `rustfmt` as being managed by Josh (<span style="color: #8250DF;">merged</span>)

### rust-lang/rustc_codegen_cranelift (2 PRs)
- [#1700](https://github.com/rust-lang/rustc_codegen_cranelift/pull/1700): Initial Josh pull (<span style="color: #8250DF;">merged</span>)
- [#1702](https://github.com/rust-lang/rustc_codegen_cranelift/pull/1702): Update `rustup.sh` to use `rustc-josh-sync` (<span style="color: #8250DF;">merged</span>)

### rust-lang/rustfmt (2 PRs)
- [#7132](https://github.com/rust-lang/rustfmt/pull/7132): Rename `rust-toolchain` to `rust-toolchain.toml` (<span style="color: #8250DF;">merged</span>)
- [#7134](https://github.com/rust-lang/rustfmt/pull/7134): Initial Josh pull (<span style="color: #8250DF;">merged</span>)

### rust-lang/simpleinfra (2 PRs)
- [#1204](https://github.com/rust-lang/simpleinfra/pull/1204): Configure rustc-perf Ansible for Aarch64 (<span style="color: #8250DF;">merged</span>)
- [#1222](https://github.com/rust-lang/simpleinfra/pull/1222): Increase CPU allocation for triagebot to one full CPU (<span style="color: #8250DF;">merged</span>)

### rust-lang/stdarch (2 PRs)
- [#2225](https://github.com/rust-lang/stdarch/pull/2225): Refactor generation to use a unified formatting approach (<span style="color: #8250DF;">merged</span>)
- [#2231](https://github.com/rust-lang/stdarch/pull/2231): Pull from rust-lang/rust (<span style="color: #8250DF;">merged</span>)

### rust-lang/www.rust-lang.org (2 PRs)
- [#2330](https://github.com/rust-lang/www.rust-lang.org/pull/2330): Fix button overflow on funding page on mobile (<span style="color: #8250DF;">merged</span>)
- [#2335](https://github.com/rust-lang/www.rust-lang.org/pull/2335): Add Scott Schafer to the MiR page (<span style="color: #8250DF;">merged</span>)

### rust-lang/crater (1 PR)
- [#851](https://github.com/rust-lang/crater/pull/851): Add MIT/Apache2 license files (<span style="color: green;">open</span>)

### rust-lang/funding (1 PR)
- [#10](https://github.com/rust-lang/funding/pull/10): Add Funding team charter (<span style="color: green;">open</span>)

### rust-lang/funding-private (1 PR)
- [#1](https://github.com/rust-lang/funding-private/pull/1): Add MiR check-in script and contribution analysis script (<span style="color: #8250DF;">merged</span>)

### rust-lang/goals (1 PR)
- [#755](https://github.com/rust-lang/goals/pull/755): Fix website link in README (<span style="color: #8250DF;">merged</span>)

### rust-lang/rustc_codegen_gcc (1 PR)
- [#983](https://github.com/rust-lang/rustc_codegen_gcc/pull/983): Rename rust-toolchain to rust-toolchain.toml (<span style="color: #8250DF;">merged</span>)

### tokio-rs/tracing (1 PR)
- [#3603](https://github.com/tokio-rs/tracing/pull/3603): Use a function to convert from `Level` to `log::Level` to reduce the amount of generated code (<span style="color: green;">open</span>)


</details>

## Conclusion

These two months felt pretty nice again. I keep worrying about the direction the IT world, and our society, is heading in with the advent of LLMs, and this sometimes makes me feel under the weather, but being funded for open source Rust work is usually enough to get my mood up. I also met a bunch of Rust enthusiasts at a Rust meetup in Prague where I had a talk about how Rust makes parallelism safe(r), and I started [teaching Rust][rust-course-fei] again, because the university semester has just started, so that is nice.

As always, I'd like to thank other members of the Rust Project and other Rust contributors, who collaborated with me, discussed various things with me, and reviewed my code in this time period. Thank you very much!

I would also like to thank the [Sovereign Tech Agency](https://www.sovereign.tech/) for funding my open source maintenance work! I am really grateful for this opportunity.

As noted in my [previous report]({% post_url 2026-08-03-stf-june-july-2026 %}#conclusion), I am currently enrolled in [GitHub Sponsors](https://github.com/sponsors/kobzol). I did not advertise it much, because I currently have funding for my open source work through the Sovereign Tech Fellowship. However, that is for one year (and it also isn't full-time), and it is hard to say whether I will be able to find the next source of funding after that. So it is good to have at least some backup. If you'd like to support my open source Rust work, I would really appreciate it! You can find more ways of supporting Rust Project maintainers [here](https://rust-lang.org/funding/).

If you have any questions regarding my upstream Rust work, feel free to ask on [Reddit]({{ page.reddit_link }}).

[bors]: https://github.com/rust-lang/bors
[stf-fellowship]: https://www.sovereign.tech/programs/fellowship
[stf-fellowship-2026]: https://www.sovereign.tech/news/meet-the-2026-sovereign-tech-fellows
[rust-course-fei]: https://github.com/Kobzol/rust-course-fei
