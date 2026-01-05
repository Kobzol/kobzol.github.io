---
layout: "post"
title: "1160 PRs to improve Rust in 2025"
date: "2026-01-05 15:00:00 +0100"
categories: rust rustc
reddit_link: https://www.reddit.com/r/rust/comments/1q4srtz/1160_prs_to_improve_rust_in_2025
---

The end of the year is a time for reflection, so I thought that I should take a look back at the
previous year. And since my main job is currently contributing to open-source, what better way to do
that than enumerating all the Rust pull requests that I opened in 2025. In this post, I'll share
stats about my Rust contributions from the past year and also some thoughts about open-source (Rust)
maintenance, as this topic is [highly relevant](https://rustfoundation.org/media/announcing-the-rust-foundation-maintainers-fund/) right now.

First, some statistics. The GitHub GraphQL API claims that:
- I opened `1497` PRs in 2025 (+98% from 755 opened PRs in 2024).
  - `1160` (77.49%) out of those were relevant to the `rust-lang` organization or other upstream Rust work[^ecosystem]. I only consider these in this post.
  - I contributed to `50` different upstream-Rust-related repositories in the past year.
- I reviewed `976` PRs in 2025 (+131% from 421 reviewed PRs in 2024).
  - `753` (77.15%) out of those were relevant to upstream Rust[^ratio].

[^ecosystem]: It also includes a handful of contributions to the "Rust ecosystem", i.e. Rust crates on crates.io that are outside the `rust-lang` organization. But there are not many of those, and I did not include PRs to my own crates, such as [delegate](https://github.com/Kobzol/rust-delegate) or [cargo-pgo](https://github.com/Kobzol/cargo-pgo).

[^ratio]: It's a bit funny how similar is the ratio of upstream Rust work in both my opened *and* reviewed PRs.

> I used [this script](https://gist.github.com/Kobzol/076b5c7096bfc675e73d52227d341d66) to calculate these statistics.

When I saw these numbers, I was quite surprised. It felt like too much, and I had to go double-check the script I used to compute it. But after examining the list of my opened PRs, and thinking a bit more about my Rust contributions, it started making sense. The high number of PRs that I open(ed) stems from the fact that the kind of work I usually do in Rust is quite maintenance-heavy[^maintenance-blog]. As a member of the Rust [Infrastructure team](https://rust-lang.org/governance/teams/infra/), I do many small and drive-by contributions to various repositories to fix CI, update configs or docs, set up some tooling, etc.
I definitely couldn't open a thousand PRs in a year if they were all implementations of new
compiler/languages features or something like that[^compiler-errors].

[^maintenance-blog]: I plan to blog Soon™ about my definition of software maintenance, either on this blog or on the official Rust blog. Stay tuned.

[^compiler-errors]: Although I know [people](https://github.com/rust-lang/rust/pulls?q=is%3Amerged+is%3Apr+author%3Acompiler-errors+created%3A2024-01-01..2025-01-01+) who can :grin:.

A lot of that work can be quite unglamorous, like doing house chores. There are probably less than `50` pull requests from the past year that I could show to someone and say "here, I did something cool". The rest is mostly work that "had to be done". And there's a lot of that work! Even though `1160` PRs might sound like a lot, it is just a drop in the ocean in the
upstream Rust world. In 2025, just the [`rust-lang/rust`](https://github.com/rust-lang/rust) repository
received `10483` (!) pull requests[^first-pr-2025]. I personally opened only `307` out of those PRs. That shows just
how much work goes into maintaining Rust (and note that this is just a single repository, although the most important and extensive one that we have). I try to help this effort by often (but not always) prioritizing unblocking other Rust Project contributors, rather than pushing my own work forward, as that tends to have a larger effect down the line.

[^first-pr-2025]: The first one was [#134988](https://github.com/rust-lang/rust/pull/134988). On average, it is more than `28` PRs opened per day.

It should also be noted that opening pull requests is just a [fraction](https://youtu.be/6n2eDcRjSsk?t=1046) of the work that a typical open-source contributor/maintainer does. There are certainly many other activities that *I* do, such as code reviews, writing and reading design docs, discussing various ideas with other people on Zulip and GitHub, reading and writing blog posts, triaging issues, governing and making decisions, listening to podcasts to find inspiration, attending
  and talking at conferences, watching recordings of conference talks that I didn't see live or
  thinking about compiler optimizations while walking my dog :) Open-source is about communication as
  much as it is about writing code (and even that is a form of communication). So quantifying work based
  on just the number of opened pull requests does not paint the whole picture.

It can be quite hard to demonstrate the value of work like this, especially to companies. That is something that we are trying to improve with the [Rust Foundation Maintainer Fund](https://rustfoundation.org/media/announcing-the-rust-foundation-maintainers-fund/) (and other similar efforts). Maintaining Rust so that it keeps working as well today as it did yesterday is a lot of work. And moving it forward by adding new features is even harder[^100-engineers]. That is why I think that it is crucial to support contributors that maintain and develop Rust. Without them, Rust could not thrive and evolve.

[^100-engineers]: I [like to say]({% post_url 2025-06-09-why-doesnt-rust-care-more-about-compiler-performance %}) that if you gave me a hundred full-time engineers, I would find all of them something to work on in the Rust toolchain immediately.

While I am currently one of the lucky people who are funded for their upstream Rust work[^fulltime], many
Rust contributors do not have access to stable funding. While the Rust Foundation (together with the Rust Project)
is currently trying to figure out how we can build a sustainable mechanism for funding full-time Rust maintainers,
there are also more targeted ways to help fund individual contributors "in the small". If you are feeling generous,
consider [sponsoring individuals](https://rust-lang.org/funding/) who make Rust better on a daily basis.

[^fulltime]: On average, I spend around 70% of my work time on Rust, and I am funded for all that.

## Summary

Here is a short summary of a few things from 2025 that stand out (in no particular order). In 2025, I:
- Was elected to the [Leadership Council](https://rust-lang.org/governance/teams/leadership-council/) and invited to the [compiler team](https://blog.rust-lang.org/inside-rust/2025/05/30/compiler-team-new-members/).
- Oversaw the Rust GSoC program again, this year with 19 (!) projects. I think that we did [pretty well](https://blog.rust-lang.org/2025/11/18/gsoc-2025-results/)!
- Attended [RustWeek](https://2025.rustweek.org/) and the Rust [All Hands](https://blog.rust-lang.org/inside-rust/2025/09/30/all-hands-2026/), quite possibly the best conference/event I have ever been to.
  - Inspired by RustWeek, I wrote a [blog post]({% post_url 2025-05-16-evolution-of-rustc-errors %}) that shows the evolution Rust compiler error messages. I'm quite proud of that one, if I do say so myself :)
- Helped move the initiative to use the [LLD linker by default on Linux](https://blog.rust-lang.org/2025/09/01/rust-lld-on-1.90.0-stable/) over the finish line, finally getting the great work of [@lqd](https://github.com/lqd) and others to a large fraction of Rust users.
- Made a lot of progress on improving the [Rust Compiler Benchmark Suite](https://github.com/rust-lang/rustc-perf) together with [James Barford](https://github.com/Jamesbarford) from ARM, as a part of one of Rust's [Project Goals](https://rust-lang.github.io/rust-project-goals/2025h2/rustc-perf-improvements.html). This reduced the time needed to wait for compiler benchmarks on our CI and opened the doors to benchmarking on more hardware architectures (e.g. ARM).
- Spent an unhealthy amount of time peeking into the abyss of [bootstrap](https://rustc-dev-guide.rust-lang.org/building/bootstrapping/what-bootstrapping-does.html) (the Rust toolchain build system),
  refactoring it and making it at least somewhat consistent again after the [Great stage0 redesign](https://blog.rust-lang.org/inside-rust/2025/05/29/redesigning-the-initial-bootstrap-sequence/) has landed. Much more work remains to be done there, though.
- Helped prepare several surveys ([Rust Compiler Performance survey](https://blog.rust-lang.org/2025/09/10/rust-compiler-performance-survey-2025-results/), [Rust Contributor survey](https://github.com/rust-lang/surveys/pull/350), [Leadership Council survey](https://github.com/rust-lang/surveys/pull/338), [Variadic Generics survey](https://blog.rust-lang.org/inside-rust/2025/09/22/variadic-generics-micro-survey/), [Safety-critical survey](https://github.com/rust-lang/surveys/pull/384) and of course the [State of Rust survey](https://blog.rust-lang.org/2025/11/17/launching-the-2025-state-of-rust-survey/)).
- Made a lot of little improvements and reduced tech debt somewhat in our infrastructure and CI. By creating a [tool](https://github.com/rust-lang/josh-sync) to make git subtree synces easier and more robust, helping move our CI off the `rust-lang-ci/rust` repository (finally!), syncing crates.io [crate owners](https://github.com/rust-lang/team/pull/2151) in the [`team`](https://github.com/rust-lang/team) repo, moving the Rust web to a [static website](https://github.com/rust-lang/www.rust-lang.org/pull/2174) and adding some [cool](https://rust-lang.org/governance/people/) [things](https://rust-lang.org/governance/people/Kobzol/) to it, and implementing many improvements to our bots (mostly [triagebot](https://github.com/rust-lang/triagebot) and [bors](https://github.com/rust-lang/bors)).
- Was able to make small progress on compiler performance. In addition to the already mentioned LLD linker stabilization, Compiler Performance survey and rustc-perf improvements, I made [some](https://github.com/rust-lang/cargo/pull/15923) [improvements](https://github.com/rust-lang/cargo/pull/15780) to visualizing what takes time in Rust builds, bootstrapped an official [Cargo build performance guide](https://github.com/rust-lang/cargo/pull/15924), made a few [drive-by](https://github.com/rust-lang/rust/pull/145408) [performance](https://github.com/rust-lang/rust/pull/145358) improvements, and restarted important work on [proc-macro caching](https://github.com/rust-lang/rust/pull/145354)[^proc-macro-stuck]. I also had some big ideas for building tooling for better diagnostics of compiler performance and build times, but sadly did not have time to work on these since ~June. Lots of other things got in the way!
- Made Rustup *start* ~3x faster by [adding 6 lines](https://github.com/rust-lang/rustup/pull/4350) to it. Kinda proud of that one :laughing:.
- Made Rust Analyzer ~20% faster by implementing [PGO](https://github.com/rust-lang/rust-analyzer/pull/19582) for it and Clippy ~5% faster by switching it to use [Jemalloc](https://github.com/rust-lang/rust/pull/142286).
- Implemented [visualization of linking times](https://github.com/rust-lang/cargo/pull/15923) in `cargo build --timings` output (not stabilized yet).
- Wrote my first [RFC](https://github.com/rust-lang/rfcs/pull/3809) (for the `#[derive(From)]` feature), got it accepted :tada: and [implemented](https://github.com/rust-lang/rust/pull/144922) it. Although it will need to be landed over an edition due to some backwards incompatible name resolution issues, so it might take some time before it gets stabilized.
- Participated in various funding discussions, helped prepare a [design document](https://github.com/rust-lang/funding/pull/1) for the [Rust Foundation Maintainer Fund](https://rustfoundation.org/media/announcing-the-rust-foundation-maintainers-fund/) and created a dedicated [Funding](https://rust-lang.org/funding/) page on the Rust website, to make it easier to sponsor Rust Project contributors.
- Had a talk about how Rust does open-source governance/maintenance at a local tech conference, gave some Rust talks at a few Rust [meetups](https://www.meetup.com/rust-prague/events/311846118/), led two Rust trainings and taught Rust at my university [again](https://github.com/Kobzol/rust-course-fei).

[^proc-macro-stuck]: Which is sadly kind of stuck on finding more people that understand this part of the compiler (or on becoming such a person myself).

It goes without saying that everything mentioned above was team work that couldn't be done without the help of the awesome [people](https://rust-lang.org/governance/people/) who *are* Rust :heart:.

## My 2025 Rust PRs

And here is the promised list of the Rust PRs that I opened in 2025. They are categorized by repository (repos are ordered by PR count in descending order) and within each repo they are ordered by creation time in ascending order. Unless otherwise noted, the pull request was merged, although I also kept the opened and closed ones, just to show the open/close/merge ratio.

[Below the list](#a-few-more-thoughts-on-my-2025-contributions) you can find a few more thoughts on my 2025 Rust contributions and the conclusion.

<!-- pr-list -->

### rust-lang/rust (307 PRs)
- [#135001](https://github.com/rust-lang/rust/pull/135001): Allow using self-contained LLD in bootstrap
- [#135127](https://github.com/rust-lang/rust/pull/135127): rustc-dev-guide subtree update
- [#135164](https://github.com/rust-lang/rust/pull/135164): Add test for checking used glibc symbols
- [#135303](https://github.com/rust-lang/rust/pull/135303): CI: fix name of jobs
- [#135478](https://github.com/rust-lang/rust/pull/135478): Run clippy for rustc_codegen_gcc on CI
- [#135638](https://github.com/rust-lang/rust/pull/135638): Make it possible to build GCC on CI
- [#135658](https://github.com/rust-lang/rust/pull/135658): Do not include GCC source code in source tarballs
- [#135810](https://github.com/rust-lang/rust/pull/135810): Add Kobzol on vacation
- [#135829](https://github.com/rust-lang/rust/pull/135829): Rustc dev guide subtree update
- [#135832](https://github.com/rust-lang/rust/pull/135832): Apply LTO config to rustdoc
- [#135950](https://github.com/rust-lang/rust/pull/135950): Tidy Python improvements
- [#136530](https://github.com/rust-lang/rust/pull/136530): Implement `x perf` directly in bootstrap
- [#136586](https://github.com/rust-lang/rust/pull/136586): Only apply LTO to rustdoc at stage 2
- [#136864](https://github.com/rust-lang/rust/pull/136864): Rewrite the `ci.py` script in Rust
- [#136911](https://github.com/rust-lang/rust/pull/136911): Add documentation URL to selected jobs
- [#136913](https://github.com/rust-lang/rust/pull/136913): Put kobzol back on review rotation
- [#136921](https://github.com/rust-lang/rust/pull/136921): Build GCC on CI
- [#136924](https://github.com/rust-lang/rust/pull/136924): Add profiling of bootstrap commands using Chrome events
- [#136941](https://github.com/rust-lang/rust/pull/136941): Move `llvm.ccache` to `build.ccache`
- [#136942](https://github.com/rust-lang/rust/pull/136942): Use ccache for stage0 tool builds
- [#136977](https://github.com/rust-lang/rust/pull/136977): Upload Datadog metrics with citool
- [#137023](https://github.com/rust-lang/rust/pull/137023): Bump sccache in CI to 0.9.1
- [#137044](https://github.com/rust-lang/rust/pull/137044): [CRATER] Detect presence of .ctors/.dtors in linked objects (<span style="color: red;">closed</span>)
- [#137070](https://github.com/rust-lang/rust/pull/137070): Do not generate invalid links in job summaries
- [#137077](https://github.com/rust-lang/rust/pull/137077): Postprocess bootstrap metrics into GitHub job summary
- [#137189](https://github.com/rust-lang/rust/pull/137189): Update host LLVM to 20.1 on CI
- [#137340](https://github.com/rust-lang/rust/pull/137340): Add a notice about missing GCC sources into source tarballs
- [#137362](https://github.com/rust-lang/rust/pull/137362): Add build step log for `run-make-support`
- [#137373](https://github.com/rust-lang/rust/pull/137373): Compile run-make-support and run-make tests with the bootstrap compiler
- [#137535](https://github.com/rust-lang/rust/pull/137535): Introduce `-Zembed-metadata` to allow omitting full metadata from rlibs and dylibs
- [#137610](https://github.com/rust-lang/rust/pull/137610): Revert "Auto merge of #135726 - jdonszelmann:attr-parsing, r=oli-obk" (<span style="color: red;">closed</span>)
- [#137612](https://github.com/rust-lang/rust/pull/137612): Update bootstrap to edition 2024
- [#137660](https://github.com/rust-lang/rust/pull/137660): Update gcc submodule
- [#137665](https://github.com/rust-lang/rust/pull/137665): Update sccache to 0.10.0
- [#137667](https://github.com/rust-lang/rust/pull/137667): Add `dist::Gcc` build step
- [#137683](https://github.com/rust-lang/rust/pull/137683): Add a tidy check for GCC submodule version
- [#137718](https://github.com/rust-lang/rust/pull/137718): Use original command for showing sccache stats
- [#137732](https://github.com/rust-lang/rust/pull/137732): Use Windows 2019 for 32-bit MSVC CI jobs (<span style="color: red;">closed</span>)
- [#137746](https://github.com/rust-lang/rust/pull/137746): [do not merge] Another attempt to fix 32-bit MSVC CI (<span style="color: red;">closed</span>)
- [#137749](https://github.com/rust-lang/rust/pull/137749): Fix 32-bit MSVC CI
- [#137926](https://github.com/rust-lang/rust/pull/137926): Add a test for `-znostart-stop-gc` usage with LLD
- [#137945](https://github.com/rust-lang/rust/pull/137945): Skip Rust for Linux in CI temporarily
- [#137947](https://github.com/rust-lang/rust/pull/137947): Do not install rustup on Rust for Linux job
- [#138013](https://github.com/rust-lang/rust/pull/138013): Add post-merge analysis CI workflow
- [#138051](https://github.com/rust-lang/rust/pull/138051): Add support for downloading GCC from CI
- [#138053](https://github.com/rust-lang/rust/pull/138053): Increase the max. custom try jobs requested to `20`
- [#138066](https://github.com/rust-lang/rust/pull/138066): [WIP] Enable automatic cross-compilation in run-make tests (<span style="color: red;">closed</span>)
- [#138223](https://github.com/rust-lang/rust/pull/138223): Fix post-merge workflow
- [#138232](https://github.com/rust-lang/rust/pull/138232): Reduce verbosity of GCC build log
- [#138268](https://github.com/rust-lang/rust/pull/138268): Handle empty test suites in GitHub job summary report
- [#138307](https://github.com/rust-lang/rust/pull/138307): Allow specifying glob patterns for try jobs
- [#138348](https://github.com/rust-lang/rust/pull/138348): Rollup of 11 pull requests (<span style="color: red;">closed</span>)
- [#138350](https://github.com/rust-lang/rust/pull/138350): Rollup of 10 pull requests
- [#138395](https://github.com/rust-lang/rust/pull/138395): Download GCC from CI on test builders
- [#138396](https://github.com/rust-lang/rust/pull/138396): Enable metrics and verbose tests in PR CI
- [#138451](https://github.com/rust-lang/rust/pull/138451): Build GCC on CI with GCC, not Clang
- [#138452](https://github.com/rust-lang/rust/pull/138452): Remove `RUN_CHECK_WITH_PARALLEL_QUERIES`
- [#138454](https://github.com/rust-lang/rust/pull/138454): Improve post-merge workflow
- [#138487](https://github.com/rust-lang/rust/pull/138487): Pass `CI_JOB_DOC_URL` to Docker
- [#138507](https://github.com/rust-lang/rust/pull/138507): Mirror NetBSD sources
- [#138531](https://github.com/rust-lang/rust/pull/138531): Store test diffs in job summaries and improve analysis formatting
- [#138533](https://github.com/rust-lang/rust/pull/138533): Only use `DIST_TRY_BUILD` for try jobs that were not selected explicitly
- [#138591](https://github.com/rust-lang/rust/pull/138591): Refactor git change detection in bootstrap
- [#138597](https://github.com/rust-lang/rust/pull/138597): [do not merge] beta test for git change detection (#138591) (<span style="color: red;">closed</span>)
- [#138645](https://github.com/rust-lang/rust/pull/138645): [do not merge] Preparation for LLD stabilization (<span style="color: red;">closed</span>)
- [#138655](https://github.com/rust-lang/rust/pull/138655): rustc-dev-guide sync
- [#138656](https://github.com/rust-lang/rust/pull/138656): Remove double nesting in post-merge workflow
- [#138704](https://github.com/rust-lang/rust/pull/138704): Simplify CI LLVM checks in bootstrap
- [#138706](https://github.com/rust-lang/rust/pull/138706): Improve bootstrap git modified path handling
- [#138709](https://github.com/rust-lang/rust/pull/138709): Update GCC submodule
- [#138792](https://github.com/rust-lang/rust/pull/138792): Rollup of 10 pull requests (<span style="color: red;">closed</span>)
- [#138834](https://github.com/rust-lang/rust/pull/138834): Group test diffs by stage in post-merge analysis
- [#138930](https://github.com/rust-lang/rust/pull/138930): Add bootstrap step diff to CI job analysis
- [#139015](https://github.com/rust-lang/rust/pull/139015): Remove unneeded LLVM CI test assertions
- [#139016](https://github.com/rust-lang/rust/pull/139016): Add job duration changes to post-merge analysis report
- [#139130](https://github.com/rust-lang/rust/pull/139130): Revert "Auto merge of #129827 - bvanjoi:less-decoding, r=petrochenkov"
- [#139322](https://github.com/rust-lang/rust/pull/139322): Add helper function for checking LLD usage to `run-make-support`
- [#139378](https://github.com/rust-lang/rust/pull/139378): Use target-agnostic LLD flags in bootstrap for `use-lld`
- [#139473](https://github.com/rust-lang/rust/pull/139473): Rollup of 5 pull requests
- [#139481](https://github.com/rust-lang/rust/pull/139481): Add job summary links to post-merge report
- [#139588](https://github.com/rust-lang/rust/pull/139588): Use LTO to optimize Rust tools (cargo, miri, rustfmt, clippy, Rust Analyzer)
- [#139597](https://github.com/rust-lang/rust/pull/139597): Do not run per-module late lints if they can be all skipped
- [#139648](https://github.com/rust-lang/rust/pull/139648): Optimize Rust Analyzer with BOLT (<span style="color: red;">closed</span>)
- [#139678](https://github.com/rust-lang/rust/pull/139678): Gate advanced features of `citool` to reduce compilation time (<span style="color: red;">closed</span>)
- [#139691](https://github.com/rust-lang/rust/pull/139691): Document that `opt-dist` requires metrics to be enabled
- [#139707](https://github.com/rust-lang/rust/pull/139707): Fix comment in bootstrap
- [#139807](https://github.com/rust-lang/rust/pull/139807): Improve wording of post-merge report
- [#139819](https://github.com/rust-lang/rust/pull/139819): Use `rust-cache` to speed-up `citool` compilation
- [#139853](https://github.com/rust-lang/rust/pull/139853): Disable combining LLD with external llvm-config
- [#139894](https://github.com/rust-lang/rust/pull/139894): Fix `opt-dist` CLI flag and make it work without LLD
- [#139978](https://github.com/rust-lang/rust/pull/139978): Add citool command for generating a test dashboard
- [#140063](https://github.com/rust-lang/rust/pull/140063): Remove stray newline from post-merge report
- [#140191](https://github.com/rust-lang/rust/pull/140191): Remove git repository from git config
- [#140394](https://github.com/rust-lang/rust/pull/140394): Make bootstrap git tests more self-contained
- [#140703](https://github.com/rust-lang/rust/pull/140703): Handle PR not found in post-merge workflow
- [#140786](https://github.com/rust-lang/rust/pull/140786): Do not deny warnings in "fast" try builds
- [#140889](https://github.com/rust-lang/rust/pull/140889): WIP: test PR for triagebot (<span style="color: red;">closed</span>)
- [#140901](https://github.com/rust-lang/rust/pull/140901): Fix download of GCC from CI on non-nightly channels
- [#141280](https://github.com/rust-lang/rust/pull/141280): Use Docker cache from the current repository
- [#141323](https://github.com/rust-lang/rust/pull/141323): Add bors environment to CI
- [#141335](https://github.com/rust-lang/rust/pull/141335): [do not merge] Triagebot test (<span style="color: red;">closed</span>)
- [#141384](https://github.com/rust-lang/rust/pull/141384): Enable review queue tracking
- [#141388](https://github.com/rust-lang/rust/pull/141388): Move `dist-x86_64-linux` CI job to GitHub temporarily
- [#141423](https://github.com/rust-lang/rust/pull/141423): [do not merge] Test PR for moving off rust-lang-ci (<span style="color: red;">closed</span>)
- [#141458](https://github.com/rust-lang/rust/pull/141458): [do not merge] Try build test for beta (<span style="color: red;">closed</span>)
- [#141459](https://github.com/rust-lang/rust/pull/141459): [do not merge] Try build for stable (<span style="color: red;">closed</span>)
- [#141634](https://github.com/rust-lang/rust/pull/141634): Fix CI for unrolled builds on the `try-perf` branch
- [#141678](https://github.com/rust-lang/rust/pull/141678): Revert "increase perf of charsearcher for single ascii characters"
- [#141723](https://github.com/rust-lang/rust/pull/141723): Provide secrets to try builds with new bors
- [#141771](https://github.com/rust-lang/rust/pull/141771): Increase timeout for new bors try builds
- [#141777](https://github.com/rust-lang/rust/pull/141777): Do not run PGO/BOLT in x64 Linux alt builds
- [#141897](https://github.com/rust-lang/rust/pull/141897): Fix citool tests when executed locally
- [#141899](https://github.com/rust-lang/rust/pull/141899): Turn `stdarch` into a Josh subtree
- [#141910](https://github.com/rust-lang/rust/pull/141910): Fix `create-docs-artifacts.sh` with new bors
- [#141912](https://github.com/rust-lang/rust/pull/141912): Rollup of 5 pull requests
- [#141948](https://github.com/rust-lang/rust/pull/141948): Allow PR builds to read sccache entries from S3 (<span style="color: red;">closed</span>)
- [#142076](https://github.com/rust-lang/rust/pull/142076): Check documentation of bootstrap in PR CI
- [#142123](https://github.com/rust-lang/rust/pull/142123): Implement initial support for timing sections (`--json=timings`)
- [#142199](https://github.com/rust-lang/rust/pull/142199): Do not free disk space in the `mingw-check-tidy` job
- [#142210](https://github.com/rust-lang/rust/pull/142210): Run `mingw-check-tidy` on auto builds
- [#142211](https://github.com/rust-lang/rust/pull/142211): Do not checkout GCC submodule for the tidy job
- [#142231](https://github.com/rust-lang/rust/pull/142231): Run `calculate_matrix` job on `master` to cache citool builds
- [#142235](https://github.com/rust-lang/rust/pull/142235): Build rustc with assertions in `dist-alt` jobs
- [#142241](https://github.com/rust-lang/rust/pull/142241): Disable download-rustc on CI
- [#142282](https://github.com/rust-lang/rust/pull/142282): Only run `citool` tests on the `auto` branch
- [#142286](https://github.com/rust-lang/rust/pull/142286): Use jemalloc for Clippy
- [#142303](https://github.com/rust-lang/rust/pull/142303): Assorted bootstrap cleanups (step 1)
- [#142344](https://github.com/rust-lang/rust/pull/142344): Revert "add `Cargo.lock` to CI-rustc allowed list for non-CI env"
- [#142357](https://github.com/rust-lang/rust/pull/142357): Simplify LLVM bitcode linker in bootstrap and add tests for it
- [#142364](https://github.com/rust-lang/rust/pull/142364): Do not warn on `rust.incremental` when using download CI rustc
- [#142374](https://github.com/rust-lang/rust/pull/142374): Fix missing newline trim in bootstrap
- [#142395](https://github.com/rust-lang/rust/pull/142395): Cache all crates for citool (<span style="color: red;">closed</span>)
- [#142407](https://github.com/rust-lang/rust/pull/142407): Remove bootstrap adhoc group
- [#142416](https://github.com/rust-lang/rust/pull/142416): Assorted bootstrap cleanups (step 2)
- [#142431](https://github.com/rust-lang/rust/pull/142431): Add initial version of snapshot tests to bootstrap
- [#142434](https://github.com/rust-lang/rust/pull/142434):  Pre-install JS dependencies in tidy Dockerfile
- [#142566](https://github.com/rust-lang/rust/pull/142566): Fix `-nopt` CI jobs
- [#142574](https://github.com/rust-lang/rust/pull/142574): Rollup of 12 pull requests
- [#142581](https://github.com/rust-lang/rust/pull/142581): Enforce in bootstrap that build must have stage at least 1
- [#142589](https://github.com/rust-lang/rust/pull/142589): Rollup of 8 pull requests
- [#142624](https://github.com/rust-lang/rust/pull/142624): Actually take `--build` into account in bootstrap
- [#142627](https://github.com/rust-lang/rust/pull/142627): Add `StepMetadata` to describe steps
- [#142629](https://github.com/rust-lang/rust/pull/142629): Add config builder for bootstrap tests
- [#142665](https://github.com/rust-lang/rust/pull/142665): Rollup of 12 pull requests (<span style="color: red;">closed</span>)
- [#142672](https://github.com/rust-lang/rust/pull/142672): Clarify bootstrap tools description
- [#142679](https://github.com/rust-lang/rust/pull/142679): Rollup of 12 pull requests (<span style="color: red;">closed</span>)
- [#142685](https://github.com/rust-lang/rust/pull/142685): Rollup of 11 pull requests
- [#142692](https://github.com/rust-lang/rust/pull/142692): Assorted bootstrap cleanups (step 3)
- [#142703](https://github.com/rust-lang/rust/pull/142703): Rollup of 3 pull requests (<span style="color: red;">closed</span>)
- [#142719](https://github.com/rust-lang/rust/pull/142719): Rollup of 6 pull requests (<span style="color: red;">closed</span>)
- [#142781](https://github.com/rust-lang/rust/pull/142781): Rollup of 11 pull requests (<span style="color: red;">closed</span>)
- [#142784](https://github.com/rust-lang/rust/pull/142784): Add codegen timing section
- [#142795](https://github.com/rust-lang/rust/pull/142795): Rollup of 10 pull requests
- [#142912](https://github.com/rust-lang/rust/pull/142912): [perf] Try to skip some early lints with `--cap-lints` (<span style="color: red;">closed</span>)
- [#142963](https://github.com/rust-lang/rust/pull/142963): Skip unnecessary components in x64 try builds
- [#142978](https://github.com/rust-lang/rust/pull/142978): Add new self-profiling event to cheaply aggregate query cache hit counts
- [#143041](https://github.com/rust-lang/rust/pull/143041): Remove cache for citool
- [#143048](https://github.com/rust-lang/rust/pull/143048): Enforce in bootstrap that check must have stage at least 1
- [#143175](https://github.com/rust-lang/rust/pull/143175): Make combining LLD with external LLVM config a hard error
- [#143255](https://github.com/rust-lang/rust/pull/143255): Do not enable LLD by default in the dist profile
- [#143285](https://github.com/rust-lang/rust/pull/143285): Add `stdarch` bootstrap smoke test (<span style="color: green;">open</span>)
- [#143316](https://github.com/rust-lang/rust/pull/143316): Add bootstrap check snapshot tests
- [#143325](https://github.com/rust-lang/rust/pull/143325): Use non-global interner in `test_string_interning` in bootstrap
- [#143412](https://github.com/rust-lang/rust/pull/143412): Move `std_detect` into stdlib
- [#143420](https://github.com/rust-lang/rust/pull/143420): rustc-dev-guide subtree update
- [#143421](https://github.com/rust-lang/rust/pull/143421): [do not merge] rustc-dev-guide subtree update (<span style="color: red;">closed</span>)
- [#143452](https://github.com/rust-lang/rust/pull/143452): Fix CLI completion check in `tidy`
- [#143581](https://github.com/rust-lang/rust/pull/143581): Implement `ToolTarget` and port `RemoteTestServer` and `WasmComponentLd` to it (<span style="color: red;">closed</span>)
- [#143586](https://github.com/rust-lang/rust/pull/143586): Fix wrong cache event query key
- [#143615](https://github.com/rust-lang/rust/pull/143615): Fix handling of no_std targets in `doc::Std` step
- [#143639](https://github.com/rust-lang/rust/pull/143639): [do not merge] stdarch subtree update (<span style="color: red;">closed</span>)
- [#143641](https://github.com/rust-lang/rust/pull/143641): Add `ToolTarget` to bootstrap
- [#143642](https://github.com/rust-lang/rust/pull/143642): stdarch subtree update
- [#143644](https://github.com/rust-lang/rust/pull/143644): Add triagebot stdarch mention ping
- [#143676](https://github.com/rust-lang/rust/pull/143676): Rollup of 6 pull requests (<span style="color: red;">closed</span>)
- [#143707](https://github.com/rust-lang/rust/pull/143707): Fix `--skip-std-check-if-no-download-rustc`
- [#143816](https://github.com/rust-lang/rust/pull/143816): Implement `check` for compiletest and RA using tool macro
- [#143817](https://github.com/rust-lang/rust/pull/143817): Access `wasi_sdk_path` instead of reading environment variable in bootstrap
- [#143887](https://github.com/rust-lang/rust/pull/143887): Run bootstrap tests sooner in the `x test` pipeline
- [#143919](https://github.com/rust-lang/rust/pull/143919): Rollup of 10 pull requests
- [#143946](https://github.com/rust-lang/rust/pull/143946): Rollup of 14 pull requests (<span style="color: red;">closed</span>)
- [#143947](https://github.com/rust-lang/rust/pull/143947): Rollup of 7 pull requests (<span style="color: red;">closed</span>)
- [#144053](https://github.com/rust-lang/rust/pull/144053): Remove install Rust script from CI
- [#144056](https://github.com/rust-lang/rust/pull/144056): Copy GCC sources into the build directory even outside CI
- [#144085](https://github.com/rust-lang/rust/pull/144085): Rollup of 10 pull requests (<span style="color: red;">closed</span>)
- [#144176](https://github.com/rust-lang/rust/pull/144176): Add approval blocking labels for new bors
- [#144177](https://github.com/rust-lang/rust/pull/144177): Rollup of 8 pull requests (<span style="color: red;">closed</span>)
- [#144193](https://github.com/rust-lang/rust/pull/144193): Suggest adding `Fn` bound when calling a generic parameter (<span style="color: green;">open</span>)
- [#144222](https://github.com/rust-lang/rust/pull/144222): stdarch subtree update
- [#144252](https://github.com/rust-lang/rust/pull/144252): Do not copy .rmeta files into the sysroot of the build compiler during check of rustc/std
- [#144303](https://github.com/rust-lang/rust/pull/144303): Consolidate staging for `rustc_private` tools
- [#144437](https://github.com/rust-lang/rust/pull/144437): Rollup of 10 pull requests (<span style="color: red;">closed</span>)
- [#144462](https://github.com/rust-lang/rust/pull/144462): Allow pretty printing paths with `-Zself-profile-events=args`
- [#144464](https://github.com/rust-lang/rust/pull/144464): Only run bootstrap tests in `x test` on CI
- [#144639](https://github.com/rust-lang/rust/pull/144639): Update rustc-perf submodule
- [#144730](https://github.com/rust-lang/rust/pull/144730): Create a typed wrapper for codegen backends in bootstrap
- [#144779](https://github.com/rust-lang/rust/pull/144779): Implement debugging output of the bootstrap Step graph into a DOT file
- [#144787](https://github.com/rust-lang/rust/pull/144787): Refactor codegen backends in bootstrap
- [#144899](https://github.com/rust-lang/rust/pull/144899): Print CGU reuse statistics in `-Zprint-mono-items`
- [#144906](https://github.com/rust-lang/rust/pull/144906): Require approval from t-infra instead of t-release on tier bumps
- [#144922](https://github.com/rust-lang/rust/pull/144922): Implement `#[derive(From)]`
- [#144943](https://github.com/rust-lang/rust/pull/144943): Rollup of 15 pull requests (<span style="color: red;">closed</span>)
- [#144950](https://github.com/rust-lang/rust/pull/144950): Rollup of 11 pull requests (<span style="color: red;">closed</span>)
- [#145000](https://github.com/rust-lang/rust/pull/145000): Remove unneeded `stage` parameter when setting up stdlib Cargo
- [#145003](https://github.com/rust-lang/rust/pull/145003): Rollup of 12 pull requests
- [#145007](https://github.com/rust-lang/rust/pull/145007): Fix build/doc/test of error index generator
- [#145011](https://github.com/rust-lang/rust/pull/145011): Enforce in bootstrap that doc must have stage at least 1
- [#145083](https://github.com/rust-lang/rust/pull/145083): Fix cross-compilation of Cargo
- [#145089](https://github.com/rust-lang/rust/pull/145089): Improve error output when a command fails in bootstrap
- [#145116](https://github.com/rust-lang/rust/pull/145116): Revert #143906
- [#145131](https://github.com/rust-lang/rust/pull/145131): Enforce in bootstrap that clippy must have stage at least 1
- [#145156](https://github.com/rust-lang/rust/pull/145156): Override custom Cargo `build-dir` in bootstrap
- [#145207](https://github.com/rust-lang/rust/pull/145207): Ship correct Cranelift library in its dist component
- [#145215](https://github.com/rust-lang/rust/pull/145215): Enable RUST_BACKTRACE=1 on CI
- [#145221](https://github.com/rust-lang/rust/pull/145221): Fix Cargo cross-compilation (take two)
- [#145253](https://github.com/rust-lang/rust/pull/145253): Document compiler and stdlib in stage1 in `pr-check-2` CI job
- [#145261](https://github.com/rust-lang/rust/pull/145261): Improve tracing in bootstrap
- [#145295](https://github.com/rust-lang/rust/pull/145295): Consolidate stage directories and group logs in bootstrap
- [#145310](https://github.com/rust-lang/rust/pull/145310): Reduce usage of `compiler_for` in bootstrap
- [#145315](https://github.com/rust-lang/rust/pull/145315): Rollup of 6 pull requests (<span style="color: red;">closed</span>)
- [#145320](https://github.com/rust-lang/rust/pull/145320): Allow cross-compiling the Cranelift dist component
- [#145324](https://github.com/rust-lang/rust/pull/145324): Rename and document `ONLY_HOSTS` in bootstrap
- [#145334](https://github.com/rust-lang/rust/pull/145334): Rollup of 11 pull requests
- [#145340](https://github.com/rust-lang/rust/pull/145340): Split codegen backend check step into two and don't run it with `x check compiler`
- [#145341](https://github.com/rust-lang/rust/pull/145341): Install libgccjit into the compiler's sysroot when cg_gcc is enabled
- [#145343](https://github.com/rust-lang/rust/pull/145343): Dogfood `-Zno-embed-metadata` in the standard library (<span style="color: green;">open</span>)
- [#145354](https://github.com/rust-lang/rust/pull/145354): Cache derive proc macro expansion with incremental query (<span style="color: green;">open</span>)
- [#145358](https://github.com/rust-lang/rust/pull/145358): Sort mono items by symbol name
- [#145406](https://github.com/rust-lang/rust/pull/145406): Rollup of 12 pull requests (<span style="color: red;">closed</span>)
- [#145407](https://github.com/rust-lang/rust/pull/145407): Rollup of 11 pull requests
- [#145408](https://github.com/rust-lang/rust/pull/145408): Deduplicate -L search paths
- [#145450](https://github.com/rust-lang/rust/pull/145450): Rollup of 11 pull requests
- [#145452](https://github.com/rust-lang/rust/pull/145452): Do not strip binaries in bootstrap everytime if they are unchanged
- [#145453](https://github.com/rust-lang/rust/pull/145453): Remove duplicated tracing span in bootstrap
- [#145454](https://github.com/rust-lang/rust/pull/145454): Fix tracing debug representation of steps without arguments in bootstrap
- [#145455](https://github.com/rust-lang/rust/pull/145455): Do not copy files in `copy_src_dirs` in dry run
- [#145460](https://github.com/rust-lang/rust/pull/145460): Speedup `copy_src_dirs` in bootstrap
- [#145472](https://github.com/rust-lang/rust/pull/145472): Enforce in bootstrap that dist and install must have stage at least 1
- [#145490](https://github.com/rust-lang/rust/pull/145490): Trace some basic I/O operations in bootstrap
- [#145557](https://github.com/rust-lang/rust/pull/145557): Fix uplifting in `Assemble` step
- [#145560](https://github.com/rust-lang/rust/pull/145560): Remove unused `PartialOrd`/`Ord` from bootstrap
- [#145563](https://github.com/rust-lang/rust/pull/145563): Remove the `From` derive macro from prelude
- [#145565](https://github.com/rust-lang/rust/pull/145565): Improve context of bootstrap errors in CI
- [#145645](https://github.com/rust-lang/rust/pull/145645): Fix rustc uplifting (take two)
- [#145654](https://github.com/rust-lang/rust/pull/145654): Download CI GCC into the correct directory
- [#145663](https://github.com/rust-lang/rust/pull/145663): Enforce in bootstrap that test must have stage at least 1 (except for compiletest)
- [#145763](https://github.com/rust-lang/rust/pull/145763): Ship LLVM tools for the correct target when cross-compiling
- [#145780](https://github.com/rust-lang/rust/pull/145780): Do not warn about missing change ID in tarball builds (<span style="color: red;">closed</span>)
- [#145781](https://github.com/rust-lang/rust/pull/145781): Remove profile section from Clippy
- [#145841](https://github.com/rust-lang/rust/pull/145841): Always build miri for the host in `x run miri`
- [#145845](https://github.com/rust-lang/rust/pull/145845): Make `x test distcheck` self-contained
- [#145848](https://github.com/rust-lang/rust/pull/145848): Slightly optimize reading of source files
- [#145874](https://github.com/rust-lang/rust/pull/145874): Remove unnecessary stage2 host builds from cross-compiled dist builders
- [#145875](https://github.com/rust-lang/rust/pull/145875): Make bootstrap command caching opt-in
- [#145876](https://github.com/rust-lang/rust/pull/145876): Enable building/disting standard library in stage 0
- [#145902](https://github.com/rust-lang/rust/pull/145902): Avoid more rustc rebuilds in cross-compilation scenarios
- [#145904](https://github.com/rust-lang/rust/pull/145904): Move `riscv64-gc-unknown-linux-musl` from Tier 2 with Host tools to Tier 2
- [#146076](https://github.com/rust-lang/rust/pull/146076): Consolidate staging for compiletest steps in bootstrap
- [#146090](https://github.com/rust-lang/rust/pull/146090): Derive `PartialEq` for `InvisibleOrigin`
- [#146124](https://github.com/rust-lang/rust/pull/146124): Test `rustc-dev` in `distcheck`
- [#146127](https://github.com/rust-lang/rust/pull/146127): Rename `ToolRustc` to `ToolRustcPrivate`
- [#146199](https://github.com/rust-lang/rust/pull/146199): Document Cargo with in-tree rustdoc
- [#146203](https://github.com/rust-lang/rust/pull/146203): Do not copy rustc rlibs into the sysroot of the build compiler (<span style="color: green;">open</span>)
- [#146253](https://github.com/rust-lang/rust/pull/146253): Optimize Cargo with LTO
- [#146435](https://github.com/rust-lang/rust/pull/146435): Change the default value of `gcc.download-ci-gcc` to `true`
- [#146449](https://github.com/rust-lang/rust/pull/146449): Fix `libgccjit` symlink when we build GCC locally
- [#146582](https://github.com/rust-lang/rust/pull/146582): Only run Cranelift dist test on nightly
- [#146592](https://github.com/rust-lang/rust/pull/146592): Implement a simple diagnostic system for tidy
- [#146771](https://github.com/rust-lang/rust/pull/146771): Simplify default value of `download-ci-llvm`
- [#146774](https://github.com/rust-lang/rust/pull/146774): Allow running `x <cmd> <path>` from a different directory
- [#146884](https://github.com/rust-lang/rust/pull/146884): Fix modification check of `rustdoc-json-types`
- [#146920](https://github.com/rust-lang/rust/pull/146920): Rollup of 8 pull requests (<span style="color: red;">closed</span>)
- [#146927](https://github.com/rust-lang/rust/pull/146927): Make it possible to `x install` Cranelift and LLVM bitcode linker
- [#147038](https://github.com/rust-lang/rust/pull/147038): Rename verbosity functions in bootstrap
- [#147039](https://github.com/rust-lang/rust/pull/147039): [DO NOT MERGE] Test PR for new rustc-perf (<span style="color: red;">closed</span>)
- [#147046](https://github.com/rust-lang/rust/pull/147046): Rename `rust.use-lld` to `rust.bootstrap-override-lld`
- [#147157](https://github.com/rust-lang/rust/pull/147157): Generalize configuring LLD as the default linker in bootstrap (<span style="color: red;">closed</span>)
- [#147188](https://github.com/rust-lang/rust/pull/147188): Remove usage of `compiletest-use-stage0-libtest` from CI
- [#147515](https://github.com/rust-lang/rust/pull/147515): Update rustc-perf submodule
- [#147625](https://github.com/rust-lang/rust/pull/147625): Add a warning when running tests with the GCC backend and debug assertions are enabled
- [#147626](https://github.com/rust-lang/rust/pull/147626): Generalize configuring LLD as the default linker in bootstrap
- [#147698](https://github.com/rust-lang/rust/pull/147698): Do not enable LLD if we don't build host code for targets that opt into it
- [#147816](https://github.com/rust-lang/rust/pull/147816): Do not error out for `download-rustc` if LTO is configured
- [#148395](https://github.com/rust-lang/rust/pull/148395): Generalize branch references
- [#148500](https://github.com/rust-lang/rust/pull/148500): Update git index before running diff-index
- [#148564](https://github.com/rust-lang/rust/pull/148564): Change default branch references
- [#148675](https://github.com/rust-lang/rust/pull/148675): Remove eslint-js from npm dependencies
- [#148896](https://github.com/rust-lang/rust/pull/148896): Revert "Rollup merge of #146627 - madsmtm:jemalloc-simplify, r=jdonszelmann"
- [#149605](https://github.com/rust-lang/rust/pull/149605): Use branch name instead of HEAD when unshallowing
- [#149612](https://github.com/rust-lang/rust/pull/149612): Apply the `bors` environment also to the `outcome` job
- [#149657](https://github.com/rust-lang/rust/pull/149657): Revert "Rollup merge of #149147 - chenyukang:yukang-fix-unused_assignments-macro-gen-147648, r=JonathanBrouwer"
- [#149724](https://github.com/rust-lang/rust/pull/149724): Fix off-by-one staging output when testing the library
- [#149734](https://github.com/rust-lang/rust/pull/149734): Mirror GCC 9.5.0
- [#149806](https://github.com/rust-lang/rust/pull/149806): Mirror `ubuntu:24.04` on ghcr
- [#149807](https://github.com/rust-lang/rust/pull/149807): Use ubuntu:24.04 for the `x86_64-gnu-miri` job
- [#149808](https://github.com/rust-lang/rust/pull/149808): WIP: Try to reuse PGO profiles in `opt-dist` (<span style="color: green;">open</span>)
- [#149921](https://github.com/rust-lang/rust/pull/149921): Add new source component that includes GPL-licensed source
- [#150070](https://github.com/rust-lang/rust/pull/150070): Partially revert #147888 and print warning if LLVM CMake dir is missing when building Enzyme
- [#150071](https://github.com/rust-lang/rust/pull/150071): Add dist step for Enzyme (<span style="color: green;">open</span>)
- [#150308](https://github.com/rust-lang/rust/pull/150308): Update bors configuration
- [#150478](https://github.com/rust-lang/rust/pull/150478): Fix new bors config
- [#150489](https://github.com/rust-lang/rust/pull/150489): Disable debuginfo when building GCC
- [#150490](https://github.com/rust-lang/rust/pull/150490): Specify bug URL when building GCC
- [#150534](https://github.com/rust-lang/rust/pull/150534): Run rustdoc tests in opt-dist tests (<span style="color: green;">open</span>)
- [#150535](https://github.com/rust-lang/rust/pull/150535): Rename the gcc component to ci-gcc (<span style="color: green;">open</span>)
- [#150538](https://github.com/rust-lang/rust/pull/150538): Add a dist component for cg_gcc (<span style="color: green;">open</span>)
- [#150541](https://github.com/rust-lang/rust/pull/150541): Add a dist component for libgccjit (<span style="color: green;">open</span>)

### rust-lang/rustc-perf (167 PRs)
- [#2029](https://github.com/rust-lang/rustc-perf/pull/2029): Triage 2025 01 07
- [#2030](https://github.com/rust-lang/rustc-perf/pull/2030): Change what we check in CI profiling test
- [#2035](https://github.com/rust-lang/rustc-perf/pull/2035): Triage 2025 01 27
- [#2040](https://github.com/rust-lang/rustc-perf/pull/2040): Update bitmaps to 3.2.1
- [#2042](https://github.com/rust-lang/rustc-perf/pull/2042): Bump MSRV to 1.81
- [#2044](https://github.com/rust-lang/rustc-perf/pull/2044): Triage 2025 02 18
- [#2045](https://github.com/rust-lang/rustc-perf/pull/2045): Make compare page slightly less misleading when there are no relevant results
- [#2046](https://github.com/rust-lang/rustc-perf/pull/2046): Pin the rustc version used to compile collector
- [#2049](https://github.com/rust-lang/rustc-perf/pull/2049): Add manual deploy workflow
- [#2050](https://github.com/rust-lang/rustc-perf/pull/2050): Fix gather data test
- [#2051](https://github.com/rust-lang/rustc-perf/pull/2051): Fix bootstrap rustc benchmark
- [#2053](https://github.com/rust-lang/rustc-perf/pull/2053): Fix stable benchmarks
- [#2055](https://github.com/rust-lang/rustc-perf/pull/2055): Increase the number of finished runs shown in the status page
- [#2056](https://github.com/rust-lang/rustc-perf/pull/2056): Revert "Increase the number of finished runs shown in the status page"
- [#2058](https://github.com/rust-lang/rustc-perf/pull/2058): Triage 2025 03 11
- [#2069](https://github.com/rust-lang/rustc-perf/pull/2069): Update html5ever to 0.31.0
- [#2071](https://github.com/rust-lang/rustc-perf/pull/2071): Update cargo to 0.87.1
- [#2073](https://github.com/rust-lang/rustc-perf/pull/2073): Add clap_derive 4.5.32 benchmark
- [#2075](https://github.com/rust-lang/rustc-perf/pull/2075): Remove bitmaps-3.1.0 benchmark
- [#2076](https://github.com/rust-lang/rustc-perf/pull/2076): Remove html5ever-0.26.0 benchmark
- [#2077](https://github.com/rust-lang/rustc-perf/pull/2077): Update cranelift codegen to 0.119.0
- [#2078](https://github.com/rust-lang/rustc-perf/pull/2078): Add support for selecting workspace package
- [#2079](https://github.com/rust-lang/rustc-perf/pull/2079): Remove cargo 0.60.0 benchmark
- [#2082](https://github.com/rust-lang/rustc-perf/pull/2082): Update diesel to 2.2.10
- [#2084](https://github.com/rust-lang/rustc-perf/pull/2084): Add `eza 0.21.2` benchmark
- [#2089](https://github.com/rust-lang/rustc-perf/pull/2089): Remove `cranelift-codegen-0.82.1` benchmark
- [#2090](https://github.com/rust-lang/rustc-perf/pull/2090): Remove `diesel-1.4.8` benchmark
- [#2091](https://github.com/rust-lang/rustc-perf/pull/2091): Update `hyper` to 1.6.0
- [#2092](https://github.com/rust-lang/rustc-perf/pull/2092): Move typenum-1.18.0 patch file to the correct directory
- [#2093](https://github.com/rust-lang/rustc-perf/pull/2093): Fix category value case
- [#2095](https://github.com/rust-lang/rustc-perf/pull/2095): Update image to 0.25.6
- [#2102](https://github.com/rust-lang/rustc-perf/pull/2102): Remove `clap-3.1.6` benchmark
- [#2103](https://github.com/rust-lang/rustc-perf/pull/2103): Remove `exa-0.10.1` benchmark
- [#2104](https://github.com/rust-lang/rustc-perf/pull/2104): Benchmark update 2025 libc 0.2.172
- [#2109](https://github.com/rust-lang/rustc-perf/pull/2109): Add `regex-automata-0.4.8` benchmark
- [#2111](https://github.com/rust-lang/rustc-perf/pull/2111): Remove `hyper-0.14.18`
- [#2112](https://github.com/rust-lang/rustc-perf/pull/2112): Remove `image-0.24.1`
- [#2120](https://github.com/rust-lang/rustc-perf/pull/2120): Remove `libc-0.2.124`
- [#2121](https://github.com/rust-lang/rustc-perf/pull/2121): Remove `regex-1.5.5`
- [#2122](https://github.com/rust-lang/rustc-perf/pull/2122): Remove `ripgrep-13.0.0`
- [#2123](https://github.com/rust-lang/rustc-perf/pull/2123): Remove `ripgrep-13.0.0-tiny`
- [#2124](https://github.com/rust-lang/rustc-perf/pull/2124): Add `diesel-2.2.10 -new-solver` benchmark (<span style="color: red;">closed</span>)
- [#2125](https://github.com/rust-lang/rustc-perf/pull/2125): Add `nalgebra-0.33.0-new-solver` benchmark
- [#2126](https://github.com/rust-lang/rustc-perf/pull/2126): Add `syn-2.0.101-new-solver`
- [#2127](https://github.com/rust-lang/rustc-perf/pull/2127): Add `serde-1.0.219-new-solver`
- [#2128](https://github.com/rust-lang/rustc-perf/pull/2128): Add `bitmaps-3.2.1-new-solver`
- [#2129](https://github.com/rust-lang/rustc-perf/pull/2129): Add `html5ever-0.31.0-new-solver`
- [#2135](https://github.com/rust-lang/rustc-perf/pull/2135): Triage 2025 05 20
- [#2138](https://github.com/rust-lang/rustc-perf/pull/2138): Update performance triage roster
- [#2139](https://github.com/rust-lang/rustc-perf/pull/2139): Add `--exact-match` CLI argument to allow exact matching of benchmarks
- [#2141](https://github.com/rust-lang/rustc-perf/pull/2141): Add `serde-1.0.219-threads4` benchmark for the parallel frontend
- [#2142](https://github.com/rust-lang/rustc-perf/pull/2142): Improve error message when `perf-config.json` is not found
- [#2143](https://github.com/rust-lang/rustc-perf/pull/2143): Add `large-workspace` stress test benchmark
- [#2144](https://github.com/rust-lang/rustc-perf/pull/2144): Add a test for existence of `[workspace]` in compile benchmarks
- [#2145](https://github.com/rust-lang/rustc-perf/pull/2145): Add `triagebot` benchmark (<span style="color: red;">closed</span>)
- [#2146](https://github.com/rust-lang/rustc-perf/pull/2146): Add `crates.io` benchmark (<span style="color: red;">closed</span>)
- [#2147](https://github.com/rust-lang/rustc-perf/pull/2147): Use `--exact-match` instead of `--include` on the website
- [#2150](https://github.com/rust-lang/rustc-perf/pull/2150): Use async closures in collector
- [#2152](https://github.com/rust-lang/rustc-perf/pull/2152): Run DB tests against SQLite too
- [#2154](https://github.com/rust-lang/rustc-perf/pull/2154): Fix Clippy benchmarks
- [#2155](https://github.com/rust-lang/rustc-perf/pull/2155): Only invoke the Clippy wrapper for the leaf crate
- [#2156](https://github.com/rust-lang/rustc-perf/pull/2156): Add `DocJson` profile for benchmarking JSON rustdoc output
- [#2158](https://github.com/rust-lang/rustc-perf/pull/2158): Do not compile extended tools in bootstrap benchmark
- [#2160](https://github.com/rust-lang/rustc-perf/pull/2160): Use stable compiler for compiling the `collector`
- [#2161](https://github.com/rust-lang/rustc-perf/pull/2161): Check test cases with measurements
- [#2162](https://github.com/rust-lang/rustc-perf/pull/2162): Triage 2025 06 17
- [#2165](https://github.com/rust-lang/rustc-perf/pull/2165): Port the detailed query page to Vue
- [#2168](https://github.com/rust-lang/rustc-perf/pull/2168): Add query cache hits to detailed query table
- [#2172](https://github.com/rust-lang/rustc-perf/pull/2172): Temporarily disable release artifact benchmarking
- [#2173](https://github.com/rust-lang/rustc-perf/pull/2173): Add new `cargo` stable benchmark
- [#2174](https://github.com/rust-lang/rustc-perf/pull/2174): Remove the `style-servo` stable benchmark
- [#2175](https://github.com/rust-lang/rustc-perf/pull/2175): Add `include-blob` secondary benchmark
- [#2176](https://github.com/rust-lang/rustc-perf/pull/2176): Fix incr patch of `include-blob`
- [#2179](https://github.com/rust-lang/rustc-perf/pull/2179): Make `cargo` compilable with modern rustc and re-enable stable benchmarks
- [#2180](https://github.com/rust-lang/rustc-perf/pull/2180): Do not show patch release data in the dashboard
- [#2182](https://github.com/rust-lang/rustc-perf/pull/2182): Update benchmarking server specs
- [#2183](https://github.com/rust-lang/rustc-perf/pull/2183): Fix compilation of the stable cargo benchmark on latest beta
- [#2185](https://github.com/rust-lang/rustc-perf/pull/2185): Stream bootstrap log when running the rustc benchmark
- [#2186](https://github.com/rust-lang/rustc-perf/pull/2186): Remove unused dev dependency
- [#2187](https://github.com/rust-lang/rustc-perf/pull/2187): Revert #2161
- [#2188](https://github.com/rust-lang/rustc-perf/pull/2188): Do not panic on S3 file upload failures
- [#2189](https://github.com/rust-lang/rustc-perf/pull/2189): Log duration of self-profile parsing
- [#2194](https://github.com/rust-lang/rustc-perf/pull/2194): Revert "Do not panic on S3 file upload failures"
- [#2201](https://github.com/rust-lang/rustc-perf/pull/2201): Refactor benchmark requests
- [#2202](https://github.com/rust-lang/rustc-perf/pull/2202): Add 2025-07-15 triage
- [#2204](https://github.com/rust-lang/rustc-perf/pull/2204): Implement benchmark comparison TUI using Ratatui
- [#2206](https://github.com/rust-lang/rustc-perf/pull/2206): Add basic benchmark set implementation
- [#2209](https://github.com/rust-lang/rustc-perf/pull/2209): Add changes filter to compare page
- [#2210](https://github.com/rust-lang/rustc-perf/pull/2210): Make missing test case check more granular
- [#2216](https://github.com/rust-lang/rustc-perf/pull/2216): Preparation for collector job queue integration
- [#2218](https://github.com/rust-lang/rustc-perf/pull/2218): Do not exit website if there is no data
- [#2219](https://github.com/rust-lang/rustc-perf/pull/2219): Add 2025-08-12 triage
- [#2226](https://github.com/rust-lang/rustc-perf/pull/2226): Add job benchmark loop
- [#2229](https://github.com/rust-lang/rustc-perf/pull/2229): Track stdlib artifact size
- [#2230](https://github.com/rust-lang/rustc-perf/pull/2230): Check latest commit SHA in the collector
- [#2231](https://github.com/rust-lang/rustc-perf/pull/2231): Purge toolchain cache directory if it gets too large
- [#2232](https://github.com/rust-lang/rustc-perf/pull/2232): Fix duration formatting on the status page
- [#2234](https://github.com/rust-lang/rustc-perf/pull/2234): Refactor new status page
- [#2237](https://github.com/rust-lang/rustc-perf/pull/2237): Add 2025-09-02 triage
- [#2239](https://github.com/rust-lang/rustc-perf/pull/2239): Check if collector is active when starting it
- [#2240](https://github.com/rust-lang/rustc-perf/pull/2240): Stop hardcoding the master branch of rust-lang/rust
- [#2250](https://github.com/rust-lang/rustc-perf/pull/2250): Estimate when requests will end in the new status page
- [#2251](https://github.com/rust-lang/rustc-perf/pull/2251): Change `./target/release` example commands to `cargo run --release`
- [#2252](https://github.com/rust-lang/rustc-perf/pull/2252): Do not use the benchmark index when computing benchmark request queue
- [#2253](https://github.com/rust-lang/rustc-perf/pull/2253): Reload benchmark request and DB index after a request is completed
- [#2256](https://github.com/rust-lang/rustc-perf/pull/2256): Add 2025-09-23 triage
- [#2259](https://github.com/rust-lang/rustc-perf/pull/2259): Partially enable job queue in production
- [#2261](https://github.com/rust-lang/rustc-perf/pull/2261): Do not update collector progress when the job queue is used
- [#2262](https://github.com/rust-lang/rustc-perf/pull/2262): Fix rustc benchmark when the `rust` directory does not exist
- [#2265](https://github.com/rust-lang/rustc-perf/pull/2265): Remove benchmark request and jobs when an artifact is purged
- [#2266](https://github.com/rust-lang/rustc-perf/pull/2266): Fix job queue migration
- [#2270](https://github.com/rust-lang/rustc-perf/pull/2270): Use merge queue on CI
- [#2271](https://github.com/rust-lang/rustc-perf/pull/2271): Allow running the website with SQLite
- [#2272](https://github.com/rust-lang/rustc-perf/pull/2272): Render target in compile-time compare page
- [#2273](https://github.com/rust-lang/rustc-perf/pull/2273): Bump MSRV to 1.88.0
- [#2274](https://github.com/rust-lang/rustc-perf/pull/2274): Show stderr when an `eprintln` profiler invocation fails
- [#2275](https://github.com/rust-lang/rustc-perf/pull/2275): Fix Windows support
- [#2276](https://github.com/rust-lang/rustc-perf/pull/2276): Get host tuple from rustc used for benchmarking/profiling, if possible
- [#2277](https://github.com/rust-lang/rustc-perf/pull/2277): Add kind to job queue unique constraint
- [#2278](https://github.com/rust-lang/rustc-perf/pull/2278): Make `html5ever` compilable on beta
- [#2279](https://github.com/rust-lang/rustc-perf/pull/2279): Test stable benchmarks with the beta toolchain
- [#2280](https://github.com/rust-lang/rustc-perf/pull/2280): Add 2025-10-13 triage
- [#2284](https://github.com/rust-lang/rustc-perf/pull/2284): Make job queue handler more resilient against panics
- [#2285](https://github.com/rust-lang/rustc-perf/pull/2285): Add target to runtime benchmarks
- [#2289](https://github.com/rust-lang/rustc-perf/pull/2289): Add total accumulated change to the Aggregations tab
- [#2290](https://github.com/rust-lang/rustc-perf/pull/2290): Update Parcel version and re-enable Hot Module Reload
- [#2292](https://github.com/rust-lang/rustc-perf/pull/2292): Update design of the new status page
- [#2293](https://github.com/rust-lang/rustc-perf/pull/2293): Update job queue loop to avoid early exit
- [#2294](https://github.com/rust-lang/rustc-perf/pull/2294): Remove cutoff dates for inserting benchmark requests
- [#2295](https://github.com/rust-lang/rustc-perf/pull/2295): Fix stable benchmarks CI
- [#2296](https://github.com/rust-lang/rustc-perf/pull/2296): Ensure that deploys are not concurrent
- [#2299](https://github.com/rust-lang/rustc-perf/pull/2299): Sort jobs of in-progress benchmark requests by their creation date
- [#2300](https://github.com/rust-lang/rustc-perf/pull/2300): Ensure that compilation sections are always present
- [#2301](https://github.com/rust-lang/rustc-perf/pull/2301): Make rustc-perf example Cargo commands more bulletproof
- [#2303](https://github.com/rust-lang/rustc-perf/pull/2303): Create master benchmark requests in the new system if they are not in the old system
- [#2304](https://github.com/rust-lang/rustc-perf/pull/2304): Re-enable backfilling
- [#2305](https://github.com/rust-lang/rustc-perf/pull/2305): Switch new and old status pages
- [#2306](https://github.com/rust-lang/rustc-perf/pull/2306): Show collector jobs by default
- [#2307](https://github.com/rust-lang/rustc-perf/pull/2307): Improve error UI in status page
- [#2308](https://github.com/rust-lang/rustc-perf/pull/2308): Rename CI jobs to make them more accurate
- [#2309](https://github.com/rust-lang/rustc-perf/pull/2309): Use the new job queue for request duration estimation
- [#2310](https://github.com/rust-lang/rustc-perf/pull/2310): Add 2025-11-03 triage
- [#2311](https://github.com/rust-lang/rustc-perf/pull/2311): Add more error logs
- [#2312](https://github.com/rust-lang/rustc-perf/pull/2312): Do not send "commit queued" comments after every try build completes
- [#2313](https://github.com/rust-lang/rustc-perf/pull/2313): Change error handling for creating parent jobs
- [#2314](https://github.com/rust-lang/rustc-perf/pull/2314): Improve error reporting in status page and logs
- [#2315](https://github.com/rust-lang/rustc-perf/pull/2315): Treat in-progress requests as completed when computing queue order
- [#2316](https://github.com/rust-lang/rustc-perf/pull/2316): Always load the benchmark request index
- [#2320](https://github.com/rust-lang/rustc-perf/pull/2320): Correctly pass backend when computing benchmark detail graph
- [#2321](https://github.com/rust-lang/rustc-perf/pull/2321): Fix benchmarking of stable/beta releases
- [#2325](https://github.com/rust-lang/rustc-perf/pull/2325): Add stable benchmarks to the compile-time benchmark set
- [#2327](https://github.com/rust-lang/rustc-perf/pull/2327): Fix endless comment loop
- [#2328](https://github.com/rust-lang/rustc-perf/pull/2328): Add comment send error logging and handle empty commands
- [#2329](https://github.com/rust-lang/rustc-perf/pull/2329): Validate codegen backends in bot commands and mention them in help
- [#2330](https://github.com/rust-lang/rustc-perf/pull/2330): Parse profiles in GitHub commands
- [#2334](https://github.com/rust-lang/rustc-perf/pull/2334): Handle non-default benchmark parameters in the graphs endpoint
- [#2335](https://github.com/rust-lang/rustc-perf/pull/2335): Add 2025-11-25 triage
- [#2337](https://github.com/rust-lang/rustc-perf/pull/2337): Do not enqueue rustc job for release benchmark requests
- [#2338](https://github.com/rust-lang/rustc-perf/pull/2338): Improve queue ordering when bootstrapping the system
- [#2339](https://github.com/rust-lang/rustc-perf/pull/2339): Modify UI of the status page
- [#2340](https://github.com/rust-lang/rustc-perf/pull/2340): Make benchmark set and job operations a bit more robust
- [#2341](https://github.com/rust-lang/rustc-perf/pull/2341): Split the x64 benchmark set into two
- [#2343](https://github.com/rust-lang/rustc-perf/pull/2343): Do not consider completed requests with errors for request duration estimation
- [#2350](https://github.com/rust-lang/rustc-perf/pull/2350): Fix release benchmark with multiple collectors
- [#2351](https://github.com/rust-lang/rustc-perf/pull/2351): Update job queue documentation
- [#2355](https://github.com/rust-lang/rustc-perf/pull/2355): Add 2025-12-16 triage
- [#2357](https://github.com/rust-lang/rustc-perf/pull/2357): Fix cyclic dependency in frontend

### rust-lang/team (164 PRs)
- [#1635](https://github.com/rust-lang/team/pull/1635): Add branch protection for the `master-old` branch in `rustc-dev-guide`
- [#1644](https://github.com/rust-lang/team/pull/1644): Remove mentions of the bors-rs organization
- [#1657](https://github.com/rust-lang/team/pull/1657): Extend the triagebot team
- [#1663](https://github.com/rust-lang/team/pull/1663): Add dry run workflow for testing the applied changes
- [#1670](https://github.com/rust-lang/team/pull/1670): Add `mentorship-programs` team
- [#1677](https://github.com/rust-lang/team/pull/1677): PR 2 (<span style="color: red;">closed</span>)
- [#1679](https://github.com/rust-lang/team/pull/1679): Fix cargo build in dry run workflow
- [#1680](https://github.com/rust-lang/team/pull/1680): [do not merge] Test PR for dry run (<span style="color: red;">closed</span>)
- [#1681](https://github.com/rust-lang/team/pull/1681): Fix dry run workflow for PR from forks
- [#1682](https://github.com/rust-lang/team/pull/1682): Add explicit `--repo` argument in dry-run workflow
- [#1683](https://github.com/rust-lang/team/pull/1683): Fix concurrency group in dry-run
- [#1684](https://github.com/rust-lang/team/pull/1684): Redirect stderr to file in dry-run workflow
- [#1686](https://github.com/rust-lang/team/pull/1686): Also print sync-team output to CI logs
- [#1688](https://github.com/rust-lang/team/pull/1688): Use pipefail in dry-run workflow
- [#1689](https://github.com/rust-lang/team/pull/1689): Add infra-admins explicitly to sync-team
- [#1690](https://github.com/rust-lang/team/pull/1690): Add validation for `allowed-merge-teams`
- [#1696](https://github.com/rust-lang/team/pull/1696): Add CODEOWNERS
- [#1697](https://github.com/rust-lang/team/pull/1697): Import sync team into team
- [#1701](https://github.com/rust-lang/team/pull/1701): Disable sending dry-run PR comments temporarily
- [#1702](https://github.com/rust-lang/team/pull/1702): Add basic threat model
- [#1705](https://github.com/rust-lang/team/pull/1705): Update CODEOWNERS
- [#1710](https://github.com/rust-lang/team/pull/1710): Re-enable dry run comments
- [#1712](https://github.com/rust-lang/team/pull/1712): Use local `sync-team` code for performing dry runs
- [#1713](https://github.com/rust-lang/team/pull/1713): Migrate `team` to `clap`
- [#1715](https://github.com/rust-lang/team/pull/1715): Switch to merge queues
- [#1717](https://github.com/rust-lang/team/pull/1717): Upload GitHub Pages using the standard action
- [#1718](https://github.com/rust-lang/team/pull/1718): No-op change to retrigger pages (<span style="color: red;">closed</span>)
- [#1719](https://github.com/rust-lang/team/pull/1719): Disable dry-run in merge queue
- [#1721](https://github.com/rust-lang/team/pull/1721): Run sync-team in merge queue
- [#1722](https://github.com/rust-lang/team/pull/1722): Backport sync team changes
- [#1723](https://github.com/rust-lang/team/pull/1723): Run sync every four hours and allow manual execution
- [#1725](https://github.com/rust-lang/team/pull/1725): Pin Rust version used on CI
- [#1726](https://github.com/rust-lang/team/pull/1726): Use `sync-team` from `team` directly
- [#1727](https://github.com/rust-lang/team/pull/1727): Remove individual bors permissions
- [#1728](https://github.com/rust-lang/team/pull/1728): Forbid admin permissions
- [#1737](https://github.com/rust-lang/team/pull/1737): Add aws-runners-test repository under automation
- [#1738](https://github.com/rust-lang/team/pull/1738): Fix name of binary in dry-run CI workflow
- [#1739](https://github.com/rust-lang/team/pull/1739): Add Urgau to t-triagebot
- [#1741](https://github.com/rust-lang/team/pull/1741): Fix sync-team link in README
- [#1742](https://github.com/rust-lang/team/pull/1742): Sync GitHub App branch protection push allowances
- [#1743](https://github.com/rust-lang/team/pull/1743): Run dry-run with code from PR if it is not from a fork
- [#1745](https://github.com/rust-lang/team/pull/1745): Work around missing permissions for rust-lang/rust branch protections
- [#1746](https://github.com/rust-lang/team/pull/1746): Add bots needed for rust-lang/rust
- [#1747](https://github.com/rust-lang/team/pull/1747): Remove unused bors repos from permission allowlist
- [#1748](https://github.com/rust-lang/team/pull/1748): Change repository sync order to handle archiving
- [#1749](https://github.com/rust-lang/team/pull/1749): Make it possible to run sync-team against local data
- [#1750](https://github.com/rust-lang/team/pull/1750): Add required CI check for triagebot merge queue
- [#1751](https://github.com/rust-lang/team/pull/1751): Do not require PRs for branches managed by homu
- [#1752](https://github.com/rust-lang/team/pull/1752): Add debug logging of team and repo diffs during actual sync
- [#1755](https://github.com/rust-lang/team/pull/1755): Revert "Merge pull request #1752 from Kobzol/debug-log"
- [#1756](https://github.com/rust-lang/team/pull/1756): Use destructuring in diffs to make it harder to forget to include diff fields
- [#1761](https://github.com/rust-lang/team/pull/1761): Add kobzol to relnotes-interest-group
- [#1762](https://github.com/rust-lang/team/pull/1762): [WIP] Add all unmanaged repos (<span style="color: red;">closed</span>)
- [#1772](https://github.com/rust-lang/team/pull/1772): Backport archived Rust Analyzer repos
- [#1773](https://github.com/rust-lang/team/pull/1773): Backport archived rust-dev-tools repos
- [#1774](https://github.com/rust-lang/team/pull/1774): Backport archived rust-lang-deprecated repos (batch 1)
- [#1775](https://github.com/rust-lang/team/pull/1775): Backport archived rust-lang-deprecated repos (batch 2)
- [#1776](https://github.com/rust-lang/team/pull/1776): Backport archived rust-lang-nursery repos (batch 1)
- [#1777](https://github.com/rust-lang/team/pull/1777): Backport archived rust-lang-nursery repos (batch 2)
- [#1788](https://github.com/rust-lang/team/pull/1788): Backport rust-dev-tools repos (batch 1)
- [#1789](https://github.com/rust-lang/team/pull/1789): Backport rust-dev-tools repos (batch 2)
- [#1796](https://github.com/rust-lang/team/pull/1796): Backport rustc-perf-collector repo
- [#1797](https://github.com/rust-lang/team/pull/1797): Backport rust-lang-nursery repos (batch 1)
- [#1798](https://github.com/rust-lang/team/pull/1798): Backport rust-lang-nursery repos (batch 2)
- [#1799](https://github.com/rust-lang/team/pull/1799): Backport rust-lang-nursery repos (batch 3)
- [#1800](https://github.com/rust-lang/team/pull/1800): Backport rust-cookbook repo
- [#1801](https://github.com/rust-lang/team/pull/1801): Backport rust-lang-ci/rust repo (<span style="color: red;">closed</span>)
- [#1802](https://github.com/rust-lang/team/pull/1802): Backport archived rls-vfs repo
- [#1803](https://github.com/rust-lang/team/pull/1803): Backport archived rust-embedded repos (batch 1)
- [#1804](https://github.com/rust-lang/team/pull/1804): Backport archived rust-embedded repos (batch 2)
- [#1805](https://github.com/rust-lang/team/pull/1805): Backport rust-analyzer repos (batch 1)
- [#1806](https://github.com/rust-lang/team/pull/1806): Backport rust-analyzer repos for archival
- [#1807](https://github.com/rust-lang/team/pull/1807): Backport rust-analyzer repos (batch 2)
- [#1813](https://github.com/rust-lang/team/pull/1813): Allow automatically fetching Zulip ID for newly added users
- [#1814](https://github.com/rust-lang/team/pull/1814): Add Google Summer of Code 2025 contributors to the `gsoc-contributors` team
- [#1816](https://github.com/rust-lang/team/pull/1816): Add branch protection to rust-log-analyzer
- [#1819](https://github.com/rust-lang/team/pull/1819): Add Karan Janthe to `gsoc-contributors`
- [#1820](https://github.com/rust-lang/team/pull/1820): Add website entry for GSoC contributors
- [#1821](https://github.com/rust-lang/team/pull/1821): Add GSoC 2025 mentors to the `mentors` team
- [#1823](https://github.com/rust-lang/team/pull/1823): Add `gsoc-contributors` as a subteam of `launching-pad`
- [#1828](https://github.com/rust-lang/team/pull/1828): Add support for `rust-timer` merge bot and `try-perf`/`perf-tmp` branch protections
- [#1835](https://github.com/rust-lang/team/pull/1835): Update rustlings homepage URL
- [#1836](https://github.com/rust-lang/team/pull/1836): Remove mentions of rust-lang-ci
- [#1843](https://github.com/rust-lang/team/pull/1843): Make homu permissions more strict
- [#1847](https://github.com/rust-lang/team/pull/1847): Simplify comment implementation in dry-run
- [#1851](https://github.com/rust-lang/team/pull/1851): Remove homu from `a-mir-formality`
- [#1852](https://github.com/rust-lang/team/pull/1852): Add back two removed homepages
- [#1853](https://github.com/rust-lang/team/pull/1853): Add back branch protection for `expect-test`
- [#1854](https://github.com/rust-lang/team/pull/1854): Add `expect-test` team
- [#1859](https://github.com/rust-lang/team/pull/1859): Add `vscode-themes` under automation and archive it
- [#1866](https://github.com/rust-lang/team/pull/1866): Sync organization members (<span style="color: red;">closed</span>)
- [#1869](https://github.com/rust-lang/team/pull/1869): Fixup links in README
- [#1870](https://github.com/rust-lang/team/pull/1870): Add required CI check to Forge
- [#1873](https://github.com/rust-lang/team/pull/1873): Add panstromek and James Barford into the compiler performance working area
- [#1879](https://github.com/rust-lang/team/pull/1879): Unify dependency versions between team and sync-team
- [#1891](https://github.com/rust-lang/team/pull/1891): Add more blocking CI checks to rustc-perf
- [#1893](https://github.com/rust-lang/team/pull/1893): Add `josh-sync` repository
- [#1896](https://github.com/rust-lang/team/pull/1896): Require tests to pass on `josh-sync`
- [#1900](https://github.com/rust-lang/team/pull/1900): Add dev desktop permissions to wg-gcc-backend
- [#1906](https://github.com/rust-lang/team/pull/1906): Add `infra-admins` to the `bors` repo
- [#1907](https://github.com/rust-lang/team/pull/1907): Fix rustc-perf CI checks
- [#1912](https://github.com/rust-lang/team/pull/1912): Change cron to only run once per day
- [#1972](https://github.com/rust-lang/team/pull/1972): Add reference expansion repo
- [#1978](https://github.com/rust-lang/team/pull/1978): Lock down permissions on `promote-release`
- [#1986](https://github.com/rust-lang/team/pull/1986): Add archived teams to v1 API
- [#1988](https://github.com/rust-lang/team/pull/1988): Make the output of the static API deterministic
- [#1992](https://github.com/rust-lang/team/pull/1992): Ensure that Zulip user IDs are unique
- [#1997](https://github.com/rust-lang/team/pull/1997): Rename community survey team to survey team
- [#1998](https://github.com/rust-lang/team/pull/1998): Change branch protection of rustc-dev-guide to `main`
- [#1999](https://github.com/rust-lang/team/pull/1999): Add a few website descriptions to archived teams
- [#2002](https://github.com/rust-lang/team/pull/2002): Give permission to do try builds to wg-triage (<span style="color: red;">closed</span>)
- [#2004](https://github.com/rust-lang/team/pull/2004): Change default branch of www.rust-lang.org to `main`
- [#2005](https://github.com/rust-lang/team/pull/2005): Update configuration of the website repo
- [#2010](https://github.com/rust-lang/team/pull/2010): Rename default branch of rustup to `main`
- [#2011](https://github.com/rust-lang/team/pull/2011): Add Sakibul to the bors team
- [#2012](https://github.com/rust-lang/team/pull/2012): Add Zalathar to the bootstrap team
- [#2013](https://github.com/rust-lang/team/pull/2013): Use merge queue on rustc-perf
- [#2015](https://github.com/rust-lang/team/pull/2015): Update Project directors based on 2025 election results
- [#2035](https://github.com/rust-lang/team/pull/2035): Remove website entry for the alumni team
- [#2039](https://github.com/rust-lang/team/pull/2039): Backfill missing Zulip IDs
- [#2040](https://github.com/rust-lang/team/pull/2040): Make Zulip IDs required
- [#2043](https://github.com/rust-lang/team/pull/2043): Remove Discord roles and website Discord info
- [#2049](https://github.com/rust-lang/team/pull/2049): Fix GitHub username of iownrena
- [#2050](https://github.com/rust-lang/team/pull/2050): Backfill missing Zulip IDs based on GitHub account association and user comments
- [#2051](https://github.com/rust-lang/team/pull/2051): Archive the `rust-analyzer/countme` repository
- [#2052](https://github.com/rust-lang/team/pull/2052): Backfill Zulip IDs based on Zulip name and GitHub username match
- [#2053](https://github.com/rust-lang/team/pull/2053): Backfill Zulip IDs based on Zulip name and team name match
- [#2054](https://github.com/rust-lang/team/pull/2054): Backfill Zulip IDs based on Zulip name and GitHub name match
- [#2055](https://github.com/rust-lang/team/pull/2055): Change branch protection for `rust-lang/rust`
- [#2056](https://github.com/rust-lang/team/pull/2056): Change branch protection of `rustfmt`
- [#2058](https://github.com/rust-lang/team/pull/2058): Add `t-website` Zulip stream to t-website website entry
- [#2061](https://github.com/rust-lang/team/pull/2061): Update how often is the website updated
- [#2071](https://github.com/rust-lang/team/pull/2071): Make it possible to document usage of GitHub Sponsors
- [#2072](https://github.com/rust-lang/team/pull/2072): Configure a `T-website` zulip group for the website team
- [#2078](https://github.com/rust-lang/team/pull/2078): Sync crates.io Trusted Publishing configs
- [#2082](https://github.com/rust-lang/team/pull/2082): Add triagebot to glob
- [#2084](https://github.com/rust-lang/team/pull/2084): Create a private channel that contains all team members
- [#2090](https://github.com/rust-lang/team/pull/2090): Add trusted publishing for the `annotate-snippets` crate
- [#2091](https://github.com/rust-lang/team/pull/2091): Add trusted publishing for the `measureme` crates
- [#2096](https://github.com/rust-lang/team/pull/2096): Add trusted publishing to `thorin`
- [#2102](https://github.com/rust-lang/team/pull/2102): Make validation error messages more verbose
- [#2114](https://github.com/rust-lang/team/pull/2114): Add trusted publishing to mdbook
- [#2115](https://github.com/rust-lang/team/pull/2115): Fix script for finding publishable package
- [#2118](https://github.com/rust-lang/team/pull/2118): Add trusted publishing to `cc-rs`
- [#2133](https://github.com/rust-lang/team/pull/2133): Add Zulip ID for U007D
- [#2134](https://github.com/rust-lang/team/pull/2134): Allow configuring "trusted publishing only" config for crates
- [#2139](https://github.com/rust-lang/team/pull/2139): Add environment to `annotate-snippets`
- [#2151](https://github.com/rust-lang/team/pull/2151): Sync crate owners on crates.io
- [#2154](https://github.com/rust-lang/team/pull/2154): Fix outputs of `generate-tokens` reusable action
- [#2156](https://github.com/rust-lang/team/pull/2156): Run crates.io sync in dry run
- [#2157](https://github.com/rust-lang/team/pull/2157): Test crates.io dry-run (<span style="color: red;">closed</span>)
- [#2158](https://github.com/rust-lang/team/pull/2158): Actually run crates-io sync in dry run workflow
- [#2160](https://github.com/rust-lang/team/pull/2160): Batch load trusted publishing configs and remove unused ones
- [#2161](https://github.com/rust-lang/team/pull/2161): Add a `funding` repository
- [#2162](https://github.com/rust-lang/team/pull/2162): Backfill all crates.io crates (<span style="color: green;">open</span>)
- [#2172](https://github.com/rust-lang/team/pull/2172): Set `CRATES_IO_USERNAME` environment variable in dry-run
- [#2173](https://github.com/rust-lang/team/pull/2173): Add crates.io trusted publishing back to `ar_archive_writer`
- [#2174](https://github.com/rust-lang/team/pull/2174): Add crates.io trusted publishing back to `crates_io_og_image`
- [#2175](https://github.com/rust-lang/team/pull/2175): Print crate name in deleting TP diff
- [#2178](https://github.com/rust-lang/team/pull/2178): Create a GitHub team and a Zulip group for the RFMF design committee
- [#2179](https://github.com/rust-lang/team/pull/2179): Do not panic when a person is not found
- [#2180](https://github.com/rust-lang/team/pull/2180): Track `gll` repository
- [#2202](https://github.com/rust-lang/team/pull/2202): Add bors merge bot
- [#2203](https://github.com/rust-lang/team/pull/2203): Configure bors for rust-lang/rust

### rust-lang/bors (142 PRs)
- [#204](https://github.com/rust-lang/bors/pull/204): Respect lockfile of `sqlx-cli` in CI
- [#216](https://github.com/rust-lang/bors/pull/216): Add universal synchronization in tests
- [#225](https://github.com/rust-lang/bors/pull/225): Refactoring
- [#228](https://github.com/rust-lang/bors/pull/228): Refactor storage of `TreeState` in the DB
- [#229](https://github.com/rust-lang/bors/pull/229): Improve compilation performance
- [#232](https://github.com/rust-lang/bors/pull/232): Use `sqlx::Encode` implementation for `GithubRepoName`
- [#237](https://github.com/rust-lang/bors/pull/237): Refactor tests
- [#249](https://github.com/rust-lang/bors/pull/249): Update PR status in upsert query
- [#251](https://github.com/rust-lang/bors/pull/251): Fix column migrations without `DEFAULT` clause and add a test for it
- [#252](https://github.com/rust-lang/bors/pull/252): Update deps
- [#253](https://github.com/rust-lang/bors/pull/253): Deduplicate some dependencies
- [#261](https://github.com/rust-lang/bors/pull/261): Add helper methods for waiting for a PR condition
- [#271](https://github.com/rust-lang/bors/pull/271): Add `IF NOT EXISTS` to repository creation migration
- [#272](https://github.com/rust-lang/bors/pull/272): Remove redundant colon from "Not approved" PR info comment
- [#273](https://github.com/rust-lang/bors/pull/273): Make check for cancelled workflows deterministic
- [#278](https://github.com/rust-lang/bors/pull/278): Split refresh handlers
- [#282](https://github.com/rust-lang/bors/pull/282): Update README
- [#293](https://github.com/rust-lang/bors/pull/293): Make try build comments more compact
- [#296](https://github.com/rust-lang/bors/pull/296): Update docs
- [#297](https://github.com/rust-lang/bors/pull/297): Make `help` and `info` command output nicer
- [#299](https://github.com/rust-lang/bors/pull/299): Use correct bot prefix in try build in progress comment
- [#300](https://github.com/rust-lang/bors/pull/300): Parse PR comments as Markdown and ignore code and links
- [#302](https://github.com/rust-lang/bors/pull/302): Upsert PRs into the database in the command handler, rather than in each command separately
- [#307](https://github.com/rust-lang/bors/pull/307): Cancel previously running try build on `@bors try`
- [#308](https://github.com/rust-lang/bors/pull/308): Reload PR state from DB after each executed command
- [#310](https://github.com/rust-lang/bors/pull/310): Drain previously seen notifications in `TestSyncMarker`
- [#311](https://github.com/rust-lang/bors/pull/311): Show parent commit SHA in try build completed message
- [#313](https://github.com/rust-lang/bors/pull/313): Add http to link printed by bors
- [#320](https://github.com/rust-lang/bors/pull/320): Add test for parsing try jobs with a comma and glob
- [#335](https://github.com/rust-lang/bors/pull/335): Support Markdown emphasis (`*`) in the command parser
- [#336](https://github.com/rust-lang/bors/pull/336): Disallow approving non open PRs
- [#341](https://github.com/rust-lang/bors/pull/341): Add yet another test for MarkDown asterisk parsing
- [#342](https://github.com/rust-lang/bors/pull/342): Add bot web URL to README
- [#344](https://github.com/rust-lang/bors/pull/344): Handle Markdown paragraphs
- [#345](https://github.com/rust-lang/bors/pull/345): Add suggestion to run help command when command parsing fails
- [#346](https://github.com/rust-lang/bors/pull/346): Temporarily partially revert 338
- [#347](https://github.com/rust-lang/bors/pull/347): Re-enable PR checks
- [#348](https://github.com/rust-lang/bors/pull/348): Remove multi-line logs
- [#352](https://github.com/rust-lang/bors/pull/352): Parse `@bors try` commands to replace homu for try builds
- [#354](https://github.com/rust-lang/bors/pull/354): Add tests for empty reviewer in approval command
- [#359](https://github.com/rust-lang/bors/pull/359): Add more logging around check suites
- [#360](https://github.com/rust-lang/bors/pull/360): Improve delegate comments
- [#362](https://github.com/rust-lang/bors/pull/362): Refactor test suite to handle timeouts in a more robust way
- [#363](https://github.com/rust-lang/bors/pull/363): Detect completed builds based only on workflow completion events
- [#364](https://github.com/rust-lang/bors/pull/364): Strip PR description from merge message in try builds
- [#365](https://github.com/rust-lang/bors/pull/365): Show a sample of failed jobs when a build fails
- [#366](https://github.com/rust-lang/bors/pull/366): Do not allow approving WIP PRs
- [#367](https://github.com/rust-lang/bors/pull/367): Forbid approving PRs with labels blocking approval
- [#368](https://github.com/rust-lang/bors/pull/368): Remove repository name from merge commit message
- [#372](https://github.com/rust-lang/bors/pull/372): Show information about auto build in `@bors info`
- [#373](https://github.com/rust-lang/bors/pull/373): Include timeout duration in `Test timed out` comment
- [#374](https://github.com/rust-lang/bors/pull/374): Configure web URL for bors and show it in approved commit message
- [#375](https://github.com/rust-lang/bors/pull/375): Forbid unapproving closed PRs
- [#376](https://github.com/rust-lang/bors/pull/376): Improve web redirect
- [#377](https://github.com/rust-lang/bors/pull/377): Reduce log clutter when there are no PRs for mergeability check
- [#378](https://github.com/rust-lang/bors/pull/378): Run refresh handlers and merge queue after starting the bot
- [#379](https://github.com/rust-lang/bors/pull/379): Make error message nicer when bors service panics in tests
- [#380](https://github.com/rust-lang/bors/pull/380): Generalize bors prefix override
- [#390](https://github.com/rust-lang/bors/pull/390): Improve logging around build cancellation
- [#391](https://github.com/rust-lang/bors/pull/391): Clarify deployment instructions
- [#392](https://github.com/rust-lang/bors/pull/392): Handle build cancellation errors properly
- [#393](https://github.com/rust-lang/bors/pull/393): Unify logic for unapproving a DB
- [#394](https://github.com/rust-lang/bors/pull/394): Run Clippy on tests in CI and fix test Clippy lints
- [#398](https://github.com/rust-lang/bors/pull/398): Ignore `bors build finished` failed jobs
- [#399](https://github.com/rust-lang/bors/pull/399): Remove unused .sqlx file
- [#400](https://github.com/rust-lang/bors/pull/400): Include commit SHA in build failed comment
- [#401](https://github.com/rust-lang/bors/pull/401): Fix flakiness of `enqueue_prs_on_pr_opened`
- [#402](https://github.com/rust-lang/bors/pull/402): Refactor test suite
- [#407](https://github.com/rust-lang/bors/pull/407): Implement general retry mechanism
- [#412](https://github.com/rust-lang/bors/pull/412): Ignore cancelled jobs in build failed comment
- [#417](https://github.com/rust-lang/bors/pull/417): Make bors info build status more accurate
- [#418](https://github.com/rust-lang/bors/pull/418): Hide previous try build started comment(s) on try build restart
- [#419](https://github.com/rust-lang/bors/pull/419): Do not warn about pushes to approved PRs that have a failed auto build
- [#420](https://github.com/rust-lang/bors/pull/420): Synchronize labels with homu
- [#421](https://github.com/rust-lang/bors/pull/421): Add tests for `min_ci_time`
- [#422](https://github.com/rust-lang/bors/pull/422): Refeactor merge queue tests and change how the merge queue is executed
- [#423](https://github.com/rust-lang/bors/pull/423): Document and refactor mergeability queue
- [#424](https://github.com/rust-lang/bors/pull/424): Tiny merge queue improvements
- [#427](https://github.com/rust-lang/bors/pull/427): Remove hardcoded master branch reference
- [#433](https://github.com/rust-lang/bors/pull/433): Correctly finish successful auto builds when the tree is closed
- [#437](https://github.com/rust-lang/bors/pull/437): Fix merge queue PR query
- [#438](https://github.com/rust-lang/bors/pull/438): Reduce space taken by workflow URLs in try build started comment
- [#443](https://github.com/rust-lang/bors/pull/443): Add a contributing section to README
- [#444](https://github.com/rust-lang/bors/pull/444): Ensure that Cargo.lock is up-to-date on CI
- [#447](https://github.com/rust-lang/bors/pull/447): Rename "extended logs" to "enhanced plaintext logs"
- [#460](https://github.com/rust-lang/bors/pull/460): Check the correct mergeable state in merge queue sanity checks
- [#461](https://github.com/rust-lang/bors/pull/461): Remove unneeded wrap in reapproval comment message
- [#462](https://github.com/rust-lang/bors/pull/462): Sort PRs on the queue page
- [#463](https://github.com/rust-lang/bors/pull/463): Make the queue PR table striped
- [#470](https://github.com/rust-lang/bors/pull/470): Add test for making sure that example config is valid
- [#471](https://github.com/rust-lang/bors/pull/471): Remove mention of LLD for faster compilation
- [#475](https://github.com/rust-lang/bors/pull/475): Update development docs
- [#476](https://github.com/rust-lang/bors/pull/476): Update Octocrab to 0.48
- [#478](https://github.com/rust-lang/bors/pull/478): Allow leading hyphen in private key argument
- [#481](https://github.com/rust-lang/bors/pull/481): Make refresh checks more robust
- [#482](https://github.com/rust-lang/bors/pull/482): Add simple API JSON endpoint for merge queue pull requests
- [#483](https://github.com/rust-lang/bors/pull/483): Unify help between GitHub comments and the webpage
- [#488](https://github.com/rust-lang/bors/pull/488): Tag auto build started comments
- [#489](https://github.com/rust-lang/bors/pull/489): Rename `stalled` to `failed`
- [#490](https://github.com/rust-lang/bors/pull/490): Add priority to mergeability queue
- [#491](https://github.com/rust-lang/bors/pull/491): Add conflict reporting on PRs
- [#492](https://github.com/rust-lang/bors/pull/492): Update Ubuntu to 24.04 in Docker and build with Rust 1.92
- [#496](https://github.com/rust-lang/bors/pull/496): Restructure tests to split GitHub state and mocks better
- [#497](https://github.com/rust-lang/bors/pull/497): Add initial infrastructure for rollup tests
- [#498](https://github.com/rust-lang/bors/pull/498): Finish test infrastructure for rollups
- [#499](https://github.com/rust-lang/bors/pull/499): Recover from more PR sanity checks in merge queue
- [#500](https://github.com/rust-lang/bors/pull/500): Apply unapprove labels when unapproving a PR in the mergeability queue
- [#501](https://github.com/rust-lang/bors/pull/501): Move some code around
- [#502](https://github.com/rust-lang/bors/pull/502): Add a build completion queue
- [#503](https://github.com/rust-lang/bors/pull/503): Reconcile DB and GitHub workflow state when completing try/auto builds
- [#504](https://github.com/rust-lang/bors/pull/504): Test refactorings
- [#505](https://github.com/rust-lang/bors/pull/505): Do not re-schedule mergeability check if a PR is not open anymore
- [#507](https://github.com/rust-lang/bors/pull/507): Make less items public in tests and clean up some test APIs
- [#508](https://github.com/rust-lang/bors/pull/508): Sort rollup PRs by priority
- [#509](https://github.com/rust-lang/bors/pull/509): Post a notice that the tree is closed when approving PRs
- [#511](https://github.com/rust-lang/bors/pull/511): Add more rollup tests
- [#513](https://github.com/rust-lang/bors/pull/513): Synchronize waiting for open PRs
- [#514](https://github.com/rust-lang/bors/pull/514): Add test for rolling up PRs with different base branches
- [#515](https://github.com/rust-lang/bors/pull/515): Add test for rolling up too many rollups
- [#516](https://github.com/rust-lang/bors/pull/516): Fetch rolled up PRs concurrently
- [#517](https://github.com/rust-lang/bors/pull/517): Fix workflow result URL shown in try/auto build completed comments
- [#518](https://github.com/rust-lang/bors/pull/518): Do not add or remove labels on PRs unnecessarily
- [#520](https://github.com/rust-lang/bors/pull/520): Set rollup label manually, rather than depending on rustbot
- [#521](https://github.com/rust-lang/bors/pull/521): Filter out duplicate PRs when making a rollup
- [#522](https://github.com/rust-lang/bors/pull/522): Add "Create similar rollup" functionality
- [#524](https://github.com/rust-lang/bors/pull/524): Add test for label optimization
- [#525](https://github.com/rust-lang/bors/pull/525): Implement homu-compatible ignore blocks
- [#526](https://github.com/rust-lang/bors/pull/526): Thank contributors in README
- [#529](https://github.com/rust-lang/bors/pull/529): Implement pause/resume functionality
- [#530](https://github.com/rust-lang/bors/pull/530): Require review permissions for pausing and resuming
- [#531](https://github.com/rust-lang/bors/pull/531): Require review permissions for creating rollups
- [#532](https://github.com/rust-lang/bors/pull/532): Fix some tracing spans
- [#533](https://github.com/rust-lang/bors/pull/533): Increase global event interval periods
- [#534](https://github.com/rust-lang/bors/pull/534): Improve design of queue page
- [#535](https://github.com/rust-lang/bors/pull/535): Optimize queue page
- [#536](https://github.com/rust-lang/bors/pull/536): Add a function to prepare Octocrab client
- [#537](https://github.com/rust-lang/bors/pull/537): Do not show try build status in queue page
- [#538](https://github.com/rust-lang/bors/pull/538): Return error instead of panicking when GitHub returns inconsistent state
- [#539](https://github.com/rust-lang/bors/pull/539): Increase timeout for fetching non-closed PRs
- [#540](https://github.com/rust-lang/bors/pull/540): Update required webhook events in docs
- [#542](https://github.com/rust-lang/bors/pull/542): Update reqwest to 0.13
- [#543](https://github.com/rust-lang/bors/pull/543): Update test snapshots to newer insta format

### rust-lang/triagebot (60 PRs)
- [#1874](https://github.com/rust-lang/triagebot/pull/1874): Remove rustc-dev-guide as a submodule
- [#1891](https://github.com/rust-lang/triagebot/pull/1891): Improve query for getting users for review (<span style="color: red;">closed</span>)
- [#1892](https://github.com/rust-lang/triagebot/pull/1892): Add simple test infrastructure for testing DB queries
- [#1905](https://github.com/rust-lang/triagebot/pull/1905): Handle open/close PR events in PR tracking
- [#1906](https://github.com/rust-lang/triagebot/pull/1906): Store assigned PRs in memory
- [#1908](https://github.com/rust-lang/triagebot/pull/1908): Extend user loading from the DB
- [#1918](https://github.com/rust-lang/triagebot/pull/1918): Make pull request assignment loading more robust
- [#1919](https://github.com/rust-lang/triagebot/pull/1919): Implement setting review assignment limit
- [#1921](https://github.com/rust-lang/triagebot/pull/1921): Switch CI to use a merge queue
- [#1923](https://github.com/rust-lang/triagebot/pull/1923): Require `test` job to succeed before starting `deploy` job
- [#1925](https://github.com/rust-lang/triagebot/pull/1925): Use GitHub Actions cache to make deploys faster
- [#1930](https://github.com/rust-lang/triagebot/pull/1930): Revert "Use GitHub Actions cache to make deploys faster"
- [#1935](https://github.com/rust-lang/triagebot/pull/1935): Refactor assignment logic slightly
- [#1937](https://github.com/rust-lang/triagebot/pull/1937): Allow using r? even without the owners table
- [#1938](https://github.com/rust-lang/triagebot/pull/1938): Unify `@rustbot assign` and `r?` behavior on PRs (<span style="color: red;">closed</span>)
- [#1939](https://github.com/rust-lang/triagebot/pull/1939): Refactor and unify assignment logic
- [#1943](https://github.com/rust-lang/triagebot/pull/1943): Allow review requesting ghost
- [#1946](https://github.com/rust-lang/triagebot/pull/1946): Run migrations after loading the workqueue
- [#1947](https://github.com/rust-lang/triagebot/pull/1947): Take review preferences into account when determining reviewers
- [#1952](https://github.com/rust-lang/triagebot/pull/1952): Only consider PRs with certain labels to be in the reviewer workqueue
- [#1961](https://github.com/rust-lang/triagebot/pull/1961): Fix assigned PR count in Zulip message
- [#1963](https://github.com/rust-lang/triagebot/pull/1963): Do not perform PR assignment for draft PRs without r?
- [#1968](https://github.com/rust-lang/triagebot/pull/1968): Do not apply labels in autolabel when opening a draft PR
- [#1969](https://github.com/rust-lang/triagebot/pull/1969): Handle drafts better in PR tracking and do not consider self-assigned PRs for the workqueue
- [#1970](https://github.com/rust-lang/triagebot/pull/1970): Store vacation status in the database
- [#1972](https://github.com/rust-lang/triagebot/pull/1972): Determine whether reviewers were requested directly or not
- [#1975](https://github.com/rust-lang/triagebot/pull/1975): Do not write `IssueData` to the DB when it is unchanged
- [#1976](https://github.com/rust-lang/triagebot/pull/1976): Add test for parsing `assign.review_prefs`
- [#1977](https://github.com/rust-lang/triagebot/pull/1977): Take rotation mode into account when performing assignments
- [#1984](https://github.com/rust-lang/triagebot/pull/1984): Refactor PR detection in autolabel
- [#2014](https://github.com/rust-lang/triagebot/pull/2014): Always allow direct review requests
- [#2015](https://github.com/rust-lang/triagebot/pull/2015): Add `whoami` Zulip command
- [#2023](https://github.com/rust-lang/triagebot/pull/2023): Only post suppressed assignment warning when assignment succeeds
- [#2025](https://github.com/rust-lang/triagebot/pull/2025): Add `lookup [github|zulip] <username>` command for determining the GitHub/Zulip username mapping
- [#2028](https://github.com/rust-lang/triagebot/pull/2028): Simplify implementation of `lookup zulip`
- [#2029](https://github.com/rust-lang/triagebot/pull/2029): Fix Zulip username formatting in `lookup github`
- [#2039](https://github.com/rust-lang/triagebot/pull/2039): Add possibility to skip workqueue loading
- [#2040](https://github.com/rust-lang/triagebot/pull/2040): Do not post welcome message when no reviewer is found without fallback
- [#2044](https://github.com/rust-lang/triagebot/pull/2044): Add a Zulip client API
- [#2046](https://github.com/rust-lang/triagebot/pull/2046): Replace structopt with clap
- [#2047](https://github.com/rust-lang/triagebot/pull/2047): Update dependencies
- [#2049](https://github.com/rust-lang/triagebot/pull/2049): Parse Zulip commands with `clap`
- [#2050](https://github.com/rust-lang/triagebot/pull/2050): Do not notify users when a non-sensitive command is executed on their behalf
- [#2052](https://github.com/rust-lang/triagebot/pull/2052): Remove unused code
- [#2053](https://github.com/rust-lang/triagebot/pull/2053): Store PR title in the workqueue and output it in `work show`
- [#2054](https://github.com/rust-lang/triagebot/pull/2054): Put review capacity into backticks
- [#2055](https://github.com/rust-lang/triagebot/pull/2055): Add team API client and cache team API calls
- [#2057](https://github.com/rust-lang/triagebot/pull/2057): Improve formatting of `work show`
- [#2059](https://github.com/rust-lang/triagebot/pull/2059): Fix command impersonation on Zulip
- [#2060](https://github.com/rust-lang/triagebot/pull/2060): Fix self-assign fast path
- [#2061](https://github.com/rust-lang/triagebot/pull/2061): Add `team-stats` Zulip command
- [#2063](https://github.com/rust-lang/triagebot/pull/2063): Make it possible to run `docs-update` and `ping-goals` also through DMs
- [#2081](https://github.com/rust-lang/triagebot/pull/2081): Return JSON content type in Zulip webhook responses
- [#2132](https://github.com/rust-lang/triagebot/pull/2132): Allow opting out of workqueue tracking with a label
- [#2142](https://github.com/rust-lang/triagebot/pull/2142): Log axum anyhow errors using `Debug` impl
- [#2174](https://github.com/rust-lang/triagebot/pull/2174): Do not hardcode the "master" branch
- [#2219](https://github.com/rust-lang/triagebot/pull/2219): Add `@rustbot reroll` command
- [#2231](https://github.com/rust-lang/triagebot/pull/2231): Store tokens as secret strings
- [#2238](https://github.com/rust-lang/triagebot/pull/2238): Update `team`
- [#2240](https://github.com/rust-lang/triagebot/pull/2240): Modify no reviewer available error

### rust-lang/rustc-dev-guide (35 PRs)
- [#2193](https://github.com/rust-lang/rustc-dev-guide/pull/2193): Update (<span style="color: red;">closed</span>)
- [#2195](https://github.com/rust-lang/rustc-dev-guide/pull/2195): Perform the first josh pull
- [#2197](https://github.com/rust-lang/rustc-dev-guide/pull/2197): Add rustc-dev-guide to the list of repositories managed by josh
- [#2200](https://github.com/rust-lang/rustc-dev-guide/pull/2200): Rustc pull
- [#2201](https://github.com/rust-lang/rustc-dev-guide/pull/2201): Rustc pull (<span style="color: red;">closed</span>)
- [#2202](https://github.com/rust-lang/rustc-dev-guide/pull/2202): Add a CI workflow for performing rustc-pull automatically
- [#2214](https://github.com/rust-lang/rustc-dev-guide/pull/2214): Add portable SIMD to list of subtrees
- [#2215](https://github.com/rust-lang/rustc-dev-guide/pull/2215): rustc pull
- [#2216](https://github.com/rust-lang/rustc-dev-guide/pull/2216): Send a message to Zulip when a sync finishes
- [#2217](https://github.com/rust-lang/rustc-dev-guide/pull/2217): Add `@bors rollup=never` to rustc-push PR body
- [#2220](https://github.com/rust-lang/rustc-dev-guide/pull/2220): Revert "Add `@bors rollup=never` to rustc-push PR body"
- [#2226](https://github.com/rust-lang/rustc-dev-guide/pull/2226): Fix rustc-pull CI's bash commands
- [#2234](https://github.com/rust-lang/rustc-dev-guide/pull/2234): Make rustc pulls on CI more frequent
- [#2235](https://github.com/rust-lang/rustc-dev-guide/pull/2235): Rewrite section on executing Docker tests
- [#2237](https://github.com/rust-lang/rustc-dev-guide/pull/2237): Pass `GITHUB_TOKEN` to Zulip CI step
- [#2239](https://github.com/rust-lang/rustc-dev-guide/pull/2239): Checkout repository sources in rustc-pull CI action
- [#2243](https://github.com/rust-lang/rustc-dev-guide/pull/2243): Make the rustc-pull workflow run less often
- [#2262](https://github.com/rust-lang/rustc-dev-guide/pull/2262): Fix posting message to Zulip
- [#2286](https://github.com/rust-lang/rustc-dev-guide/pull/2286): Fix MCP links
- [#2294](https://github.com/rust-lang/rustc-dev-guide/pull/2294): Add Fuchsia ping group page and mention Fuchsia and RfL ping groups in integration test pages
- [#2405](https://github.com/rust-lang/rustc-dev-guide/pull/2405): Remove mentions of rust-lang-ci/rust
- [#2489](https://github.com/rust-lang/rustc-dev-guide/pull/2489): Rustc pull update
- [#2490](https://github.com/rust-lang/rustc-dev-guide/pull/2490): Rustc pull update (old tooling) (<span style="color: red;">closed</span>)
- [#2491](https://github.com/rust-lang/rustc-dev-guide/pull/2491): Finish transition to `rustc-josh-sync`
- [#2495](https://github.com/rust-lang/rustc-dev-guide/pull/2495): Mention that stdarch is managed by josh-sync
- [#2501](https://github.com/rust-lang/rustc-dev-guide/pull/2501): Mention that compiler-builtins is now using `rustc-josh-sync`
- [#2502](https://github.com/rust-lang/rustc-dev-guide/pull/2502): Migrate rustc-pull to CI workflow from `josh-sync`
- [#2517](https://github.com/rust-lang/rustc-dev-guide/pull/2517): Update josh sync documentation
- [#2521](https://github.com/rust-lang/rustc-dev-guide/pull/2521): Authenticate using GitHub app for the sync workflow
- [#2523](https://github.com/rust-lang/rustc-dev-guide/pull/2523): Use main branch of josh-sync for CI workflow
- [#2525](https://github.com/rust-lang/rustc-dev-guide/pull/2525): Remove outdated ci.py reference
- [#2540](https://github.com/rust-lang/rustc-dev-guide/pull/2540): Only run the pull workflow once per week
- [#2589](https://github.com/rust-lang/rustc-dev-guide/pull/2589): Clarify that backtick escaping doesn't work for `@bors try jobs`
- [#2609](https://github.com/rust-lang/rustc-dev-guide/pull/2609): Add debug assertions flag to `cg_gcc` invocation
- [#2611](https://github.com/rust-lang/rustc-dev-guide/pull/2611): Overhaul GCC codegen backend section

### rust-lang/this-week-in-rust (33 PRs)
- [#6260](https://github.com/rust-lang/this-week-in-rust/pull/6260): Add 2025-01-07 perf triage
- [#6289](https://github.com/rust-lang/this-week-in-rust/pull/6289): Add link to `Async Rust is about concurrency, not (just) performance` blog post
- [#6327](https://github.com/rust-lang/this-week-in-rust/pull/6327): Add 2025-01-27 perf triage
- [#6392](https://github.com/rust-lang/this-week-in-rust/pull/6392): Add 2025-02-18 perf triage
- [#6407](https://github.com/rust-lang/this-week-in-rust/pull/6407): Fold list of merged pull requests (<span style="color: red;">closed</span>)
- [#6408](https://github.com/rust-lang/this-week-in-rust/pull/6408): Add blog post about nasty bug (<span style="color: red;">closed</span>)
- [#6456](https://github.com/rust-lang/this-week-in-rust/pull/6456): Add 2025-03-11 perf triage
- [#6498](https://github.com/rust-lang/this-week-in-rust/pull/6498): Add a "Just write a test for it" blog post
- [#6576](https://github.com/rust-lang/this-week-in-rust/pull/6576): Add `Two ways of interpreting visibility in Rust` blog post (<span style="color: red;">closed</span>)
- [#6648](https://github.com/rust-lang/this-week-in-rust/pull/6648): Add `Evolution of Rust compiler errors` blog post
- [#6657](https://github.com/rust-lang/this-week-in-rust/pull/6657): Add 2025-05-20 perf triage
- [#6658](https://github.com/rust-lang/this-week-in-rust/pull/6658): Add `Disable debuginfo to improve Rust compile times` blog post
- [#6697](https://github.com/rust-lang/this-week-in-rust/pull/6697): Add Reducing Cargo target directory size with -Zno-embed-metadata blog post link
- [#6722](https://github.com/rust-lang/this-week-in-rust/pull/6722): Add `Why doesn't Rust care more about compiler performance?` blog post (<span style="color: red;">closed</span>)
- [#6740](https://github.com/rust-lang/this-week-in-rust/pull/6740): Add Rust Compiler Performance Survey 2025
- [#6748](https://github.com/rust-lang/this-week-in-rust/pull/6748): Add 2025-06-17 perf triage
- [#6818](https://github.com/rust-lang/this-week-in-rust/pull/6818): Add 2025-07-15 perf triage
- [#6890](https://github.com/rust-lang/this-week-in-rust/pull/6890): Add 2025-08-12 perf triage
- [#6966](https://github.com/rust-lang/this-week-in-rust/pull/6966): Add `Combining struct literal syntax with read-only field access` blog post
- [#6972](https://github.com/rust-lang/this-week-in-rust/pull/6972): Add 2025-09-02 perf triage
- [#6973](https://github.com/rust-lang/this-week-in-rust/pull/6973): Add `Adding #[derive(From)] to Rust` blog post
- [#6999](https://github.com/rust-lang/this-week-in-rust/pull/6999): Add `Rust compiler performance survey 2025 results` blog post
- [#7048](https://github.com/rust-lang/this-week-in-rust/pull/7048): Add `Reducing binary size of (Rust) programs with debuginfo` blog post
- [#7049](https://github.com/rust-lang/this-week-in-rust/pull/7049): Add `Variadic Generics Micro Survey` official Inside Rust blog post
- [#7055](https://github.com/rust-lang/this-week-in-rust/pull/7055): Add 2025-09-23 perf triage
- [#7130](https://github.com/rust-lang/this-week-in-rust/pull/7130): Add 2025-10-13 perf triage
- [#7222](https://github.com/rust-lang/this-week-in-rust/pull/7222): Add 2025-11-03 perf triage
- [#7278](https://github.com/rust-lang/this-week-in-rust/pull/7278): Add `Launching the 2025 State of Rust Survey` Rust blog post
- [#7280](https://github.com/rust-lang/this-week-in-rust/pull/7280): Add `Google Summer of Code 2025 results` blog post
- [#7313](https://github.com/rust-lang/this-week-in-rust/pull/7313): Add 2025-11-25 perf triage
- [#7364](https://github.com/rust-lang/this-week-in-rust/pull/7364): Add `Making it easier to sponsor Rust contributors` blog post
- [#7395](https://github.com/rust-lang/this-week-in-rust/pull/7395): Add 2025-12-16 perf triage
- [#7435](https://github.com/rust-lang/this-week-in-rust/pull/7435): Add `Investigating and fixing a nasty clone bug` blog post

### rust-lang/www.rust-lang.org (25 PRs)
- [#2152](https://github.com/rust-lang/www.rust-lang.org/pull/2152): Include marker and unknown teams with a website section
- [#2174](https://github.com/rust-lang/www.rust-lang.org/pull/2174): Add rendering of the web into a directory
- [#2189](https://github.com/rust-lang/www.rust-lang.org/pull/2189): Fix CI trigger condition
- [#2190](https://github.com/rust-lang/www.rust-lang.org/pull/2190): Fix endless redirect in index page
- [#2192](https://github.com/rust-lang/www.rust-lang.org/pull/2192): Fix community redirect loop
- [#2193](https://github.com/rust-lang/www.rust-lang.org/pull/2193): Remove Heroku/Rocket config and update docs
- [#2194](https://github.com/rust-lang/www.rust-lang.org/pull/2194): Allow deploying the website manually and add cron job for deploy
- [#2198](https://github.com/rust-lang/www.rust-lang.org/pull/2198): Disable Jekyll on Github Pages
- [#2201](https://github.com/rust-lang/www.rust-lang.org/pull/2201): Install Clippy on CI
- [#2202](https://github.com/rust-lang/www.rust-lang.org/pull/2202): Add archived teams to the website
- [#2208](https://github.com/rust-lang/www.rust-lang.org/pull/2208): Make logos available under `/logos`
- [#2211](https://github.com/rust-lang/www.rust-lang.org/pull/2211): Add a page with everyone in the Rust Project, including alumni
- [#2213](https://github.com/rust-lang/www.rust-lang.org/pull/2213): Add a separate page for each Rust team member
- [#2226](https://github.com/rust-lang/www.rust-lang.org/pull/2226): Unify logic for showing all Project Members and generating individual pages for each person
- [#2227](https://github.com/rust-lang/www.rust-lang.org/pull/2227): Sort team members on the website
- [#2229](https://github.com/rust-lang/www.rust-lang.org/pull/2229): Change what does an "active team" mean
- [#2230](https://github.com/rust-lang/www.rust-lang.org/pull/2230): Use nicer URL for all project members page
- [#2231](https://github.com/rust-lang/www.rust-lang.org/pull/2231): Extend the final section of a page to avoid white space
- [#2233](https://github.com/rust-lang/www.rust-lang.org/pull/2233): Fix passing Zulip domain to team pages
- [#2236](https://github.com/rust-lang/www.rust-lang.org/pull/2236): Add GitHub Sponsors link to person profile page
- [#2237](https://github.com/rust-lang/www.rust-lang.org/pull/2237): Add a funding page that lists Project members with GitHub Sponsors
- [#2244](https://github.com/rust-lang/www.rust-lang.org/pull/2244): Shuffle fundable people on the server
- [#2245](https://github.com/rust-lang/www.rust-lang.org/pull/2245): Add Funding page navbar link (<span style="color: green;">open</span>)
- [#2249](https://github.com/rust-lang/www.rust-lang.org/pull/2249): Generalize funding page
- [#2251](https://github.com/rust-lang/www.rust-lang.org/pull/2251): Remove extra characters

### rust-lang/blog.rust-lang.org (24 PRs)
- [#1455](https://github.com/rust-lang/blog.rust-lang.org/pull/1455): Add 2024 Annual Rust survey announcement blog post
- [#1478](https://github.com/rust-lang/blog.rust-lang.org/pull/1478): Add 2024 State of Rust results link to the announcement post
- [#1493](https://github.com/rust-lang/blog.rust-lang.org/pull/1493): Add blog post about our participation in GSoC 2025
- [#1599](https://github.com/rust-lang/blog.rust-lang.org/pull/1599): Add GSoC 2025 selected projects blog post
- [#1600](https://github.com/rust-lang/blog.rust-lang.org/pull/1600): Fix auto completion of username from git
- [#1601](https://github.com/rust-lang/blog.rust-lang.org/pull/1601): Add autocompletion for team names and URLs
- [#1606](https://github.com/rust-lang/blog.rust-lang.org/pull/1606): Let people choose team label in blog generation
- [#1622](https://github.com/rust-lang/blog.rust-lang.org/pull/1622): Add Rust compiler performance 2025 survey blog post
- [#1671](https://github.com/rust-lang/blog.rust-lang.org/pull/1671): Make links in 1.89.0 blog post clickable
- [#1672](https://github.com/rust-lang/blog.rust-lang.org/pull/1672): Fix submodule path (<span style="color: red;">closed</span>)
- [#1690](https://github.com/rust-lang/blog.rust-lang.org/pull/1690): Make build of the blog much faster by only fetching section metadata
- [#1692](https://github.com/rust-lang/blog.rust-lang.org/pull/1692): Add Rust Compiler Performance 2025 Survey results
- [#1693](https://github.com/rust-lang/blog.rust-lang.org/pull/1693): Add link to the results to the original Compiler Performance Survey post
- [#1697](https://github.com/rust-lang/blog.rust-lang.org/pull/1697): Update compiler performance charts to render better without JS
- [#1699](https://github.com/rust-lang/blog.rust-lang.org/pull/1699): Add variadic generics survey announcement blog post
- [#1717](https://github.com/rust-lang/blog.rust-lang.org/pull/1717): Add blog post announcing the 2025 State of Rust survey
- [#1727](https://github.com/rust-lang/blog.rust-lang.org/pull/1727): Use correct image link in Clippy feature freeze end post
- [#1734](https://github.com/rust-lang/blog.rust-lang.org/pull/1734): Recommend users to rename their fork's default branch
- [#1736](https://github.com/rust-lang/blog.rust-lang.org/pull/1736): Update instructions for renaming rust-lang/rust default branch
- [#1739](https://github.com/rust-lang/blog.rust-lang.org/pull/1739): Add a note that the rust-lang/rust default branch has happened
- [#1742](https://github.com/rust-lang/blog.rust-lang.org/pull/1742): Add GSoC 2025 results blog post
- [#1750](https://github.com/rust-lang/blog.rust-lang.org/pull/1750): Update team dependency
- [#1751](https://github.com/rust-lang/blog.rust-lang.org/pull/1751): Add blog post about the new Funding page
- [#1773](https://github.com/rust-lang/blog.rust-lang.org/pull/1773): Add a post about what is maintenance (<span style="color: green;">open</span>)

### rust-lang/josh-sync (22 PRs)
- [#1](https://github.com/rust-lang/josh-sync/pull/1): Implement pull and push synchronization scripts
- [#2](https://github.com/rust-lang/josh-sync/pull/2): Rename tool to `rustc-josh-sync` and add a few fixes
- [#3](https://github.com/rust-lang/josh-sync/pull/3): Add CI workflow and fix compilation
- [#4](https://github.com/rust-lang/josh-sync/pull/4): Handle newline in `rust-version` and mention this repo in merge commit message
- [#6](https://github.com/rust-lang/josh-sync/pull/6): Stream output of certain commands to the terminal
- [#7](https://github.com/rust-lang/josh-sync/pull/7): Improve commit message of pushes
- [#8](https://github.com/rust-lang/josh-sync/pull/8): Make `gh` PR creation prompt more accurate
- [#9](https://github.com/rust-lang/josh-sync/pull/9): Add reusable workflow for performing rustc-pull on CI
- [#10](https://github.com/rust-lang/josh-sync/pull/10): Handle empty diff more precisely
- [#11](https://github.com/rust-lang/josh-sync/pull/11): Fix README CI example
- [#12](https://github.com/rust-lang/josh-sync/pull/12): Allow configuring upstream repository for `pull`
- [#14](https://github.com/rust-lang/josh-sync/pull/14): Fix push command in README
- [#15](https://github.com/rust-lang/josh-sync/pull/15): Allow overriding upstream commit to pull from
- [#16](https://github.com/rust-lang/josh-sync/pull/16): Add a flag to exit with status code 0 if there is nothing to pull
- [#19](https://github.com/rust-lang/josh-sync/pull/19): Use GitHub app for PR authentication
- [#20](https://github.com/rust-lang/josh-sync/pull/20): Implement verbose flag
- [#21](https://github.com/rust-lang/josh-sync/pull/21): Do not rollback branch state in case of a merge failure
- [#23](https://github.com/rust-lang/josh-sync/pull/23): Add uptream diff link to pull merge commit message
- [#28](https://github.com/rust-lang/josh-sync/pull/28): Implement post-pull commands
- [#29](https://github.com/rust-lang/josh-sync/pull/29): Keep intermediate git state if `--allow-noop` was passed
- [#30](https://github.com/rust-lang/josh-sync/pull/30): Keep all intermediate state with `--allow-noop`
- [#32](https://github.com/rust-lang/josh-sync/pull/32): Use more qualified git ref when pushing branch to josh (<span style="color: green;">open</span>)

### rust-lang/surveys (19 PRs)
- [#327](https://github.com/rust-lang/surveys/pull/327): State of Rust 2024 report
- [#328](https://github.com/rust-lang/surveys/pull/328): Add a guide for what to do after the State of Rust survey finishes
- [#331](https://github.com/rust-lang/surveys/pull/331): Flip angle of bar chart text in mobile layout
- [#332](https://github.com/rust-lang/surveys/pull/332): Add State of Rust 2024 results to FAQ
- [#337](https://github.com/rust-lang/surveys/pull/337): Add compiler performance survey
- [#339](https://github.com/rust-lang/surveys/pull/339): Allow using survey verifier for more survey kinds
- [#340](https://github.com/rust-lang/surveys/pull/340): Add support for rating scale question
- [#343](https://github.com/rust-lang/surveys/pull/343): Bootstrap questions for the 2025 annual survey
- [#344](https://github.com/rust-lang/surveys/pull/344): Compiler performance survey analysis
- [#347](https://github.com/rust-lang/surveys/pull/347): Add declarative macros attributes and derives to features to be stabilized
- [#348](https://github.com/rust-lang/surveys/pull/348): Add question about error codes to the annual survey
- [#349](https://github.com/rust-lang/surveys/pull/349): Change Windows 8 to Windows 8.1
- [#350](https://github.com/rust-lang/surveys/pull/350): Add Rust Project contributor survey 2025
- [#351](https://github.com/rust-lang/surveys/pull/351): Add Zed to editor question in annual survey
- [#356](https://github.com/rust-lang/surveys/pull/356): Update translation guide
- [#360](https://github.com/rust-lang/surveys/pull/360): Bootstrap State of Rust 2025 translations from SurveyHero
- [#365](https://github.com/rust-lang/surveys/pull/365): Add support for ranking questions on SurveyHero
- [#367](https://github.com/rust-lang/surveys/pull/367): Add support for input list questions
- [#384](https://github.com/rust-lang/surveys/pull/384): Add safety critical survey

### rust-lang/rust-forge (18 PRs)
- [#807](https://github.com/rust-lang/rust-forge/pull/807): Add link to State of Rust FAQ to the surveys repo
- [#819](https://github.com/rust-lang/rust-forge/pull/819): Remove mention of IP allowlist for bastion
- [#835](https://github.com/rust-lang/rust-forge/pull/835): Clarify what enables r? in triagebot
- [#853](https://github.com/rust-lang/rust-forge/pull/853): Document triagebot review queue tracking
- [#877](https://github.com/rust-lang/rust-forge/pull/877): Document Zulip commands
- [#882](https://github.com/rust-lang/rust-forge/pull/882): Fix link to MCP
- [#885](https://github.com/rust-lang/rust-forge/pull/885): Add link checking on CI
- [#891](https://github.com/rust-lang/rust-forge/pull/891): Extend guide for configuring legacy AWS access
- [#893](https://github.com/rust-lang/rust-forge/pull/893): Make blacksmith optional
- [#894](https://github.com/rust-lang/rust-forge/pull/894): Increase max width of content to 1000px
- [#896](https://github.com/rust-lang/rust-forge/pull/896): Add "How to start contributing" page
- [#946](https://github.com/rust-lang/rust-forge/pull/946): Replace hardcoded references to master
- [#972](https://github.com/rust-lang/rust-forge/pull/972): Document `@rustbot reroll`
- [#973](https://github.com/rust-lang/rust-forge/pull/973): Update triagebot reroll docs
- [#974](https://github.com/rust-lang/rust-forge/pull/974): Clarify maximum duration to invite members into a team
- [#976](https://github.com/rust-lang/rust-forge/pull/976): Document that Zulip is the primary communication channel of the Project
- [#978](https://github.com/rust-lang/rust-forge/pull/978): Document the t-all/private channel
- [#983](https://github.com/rust-lang/rust-forge/pull/983): Remove outdated services from service infrastructure page

### rust-lang/rust-analyzer (14 PRs)
- [#19582](https://github.com/rust-lang/rust-analyzer/pull/19582): Distribute x64 and aarch64 Linux builds with PGO optimizations
- [#19583](https://github.com/rust-lang/rust-analyzer/pull/19583): Do not perform PGO on Linux CI
- [#19585](https://github.com/rust-lang/rust-analyzer/pull/19585): Allow training PGO on a custom crate and enable it Windows on CI
- [#19586](https://github.com/rust-lang/rust-analyzer/pull/19586): Use a Docker container instead of Zig for building with old(er) glibc on x64 Linux
- [#19595](https://github.com/rust-lang/rust-analyzer/pull/19595): Use PGO on Linux x64 builds
- [#19597](https://github.com/rust-lang/rust-analyzer/pull/19597): Build aarch64 builds on CI with PGO
- [#19600](https://github.com/rust-lang/rust-analyzer/pull/19600): Pin rustc used for the `proc-macro-src` CI job
- [#19602](https://github.com/rust-lang/rust-analyzer/pull/19602): Use PGO for 32-bit ARM builds (<span style="color: red;">closed</span>)
- [#19988](https://github.com/rust-lang/rust-analyzer/pull/19988): Fix link to good first issues
- [#20280](https://github.com/rust-lang/rust-analyzer/pull/20280): Switch to using josh-sync
- [#20282](https://github.com/rust-lang/rust-analyzer/pull/20282): Add CI workflow for periodically performing josh pulls
- [#20330](https://github.com/rust-lang/rust-analyzer/pull/20330): Configure triagebot to reopen bot PRs
- [#20335](https://github.com/rust-lang/rust-analyzer/pull/20335): Use GH app for authenticating sync PRs
- [#20638](https://github.com/rust-lang/rust-analyzer/pull/20638): Add a FAQ entry about RA and Cargo build lock/cache conflicts

### rust-lang/stdarch (14 PRs)
- [#1828](https://github.com/rust-lang/stdarch/pull/1828): Remove stabilized features (<span style="color: red;">closed</span>)
- [#1829](https://github.com/rust-lang/stdarch/pull/1829): Add lockfile
- [#1833](https://github.com/rust-lang/stdarch/pull/1833): Add triagebot config for subtree syncs
- [#1835](https://github.com/rust-lang/stdarch/pull/1835): Add Josh sync scripts
- [#1842](https://github.com/rust-lang/stdarch/pull/1842): Rustc pull update (<span style="color: red;">closed</span>)
- [#1843](https://github.com/rust-lang/stdarch/pull/1843): Remove `std_detect` dev dependency in `core_arch`
- [#1844](https://github.com/rust-lang/stdarch/pull/1844): Perform first rustc pull
- [#1850](https://github.com/rust-lang/stdarch/pull/1850): Document that stdarch is managed by josh-sync
- [#1853](https://github.com/rust-lang/stdarch/pull/1853): Perform the first rustc pull.. for the second time
- [#1870](https://github.com/rust-lang/stdarch/pull/1870): Add rustc-pull CI automation workflow
- [#1873](https://github.com/rust-lang/stdarch/pull/1873): [do not merge] Remove std_detect from CI (<span style="color: red;">closed</span>)
- [#1883](https://github.com/rust-lang/stdarch/pull/1883): Rustc pull update
- [#1891](https://github.com/rust-lang/stdarch/pull/1891): Use GitHub app for authenticating sync workflows
- [#1950](https://github.com/rust-lang/stdarch/pull/1950): rustc-pull

### rust-lang/sync-team (13 PRs)
- [#100](https://github.com/rust-lang/sync-team/pull/100): Improve CLI and make it possible to run on directory with JSON files
- [#101](https://github.com/rust-lang/sync-team/pull/101): Only run the dry-run workflow in the rust-lang organization
- [#103](https://github.com/rust-lang/sync-team/pull/103): [WIP] Refactor token generation logic (<span style="color: red;">closed</span>)
- [#104](https://github.com/rust-lang/sync-team/pull/104): Refactor token generation logic (<span style="color: red;">closed</span>)
- [#105](https://github.com/rust-lang/sync-team/pull/105): Change repository description to not be optional
- [#106](https://github.com/rust-lang/sync-team/pull/106): Normalize order of branch protection checks
- [#107](https://github.com/rust-lang/sync-team/pull/107): Fix deserialization of repository description
- [#109](https://github.com/rust-lang/sync-team/pull/109): Switch CI to use a merge queue
- [#112](https://github.com/rust-lang/sync-team/pull/112): [WIP] Testing GitHub deploy (<span style="color: red;">closed</span>)
- [#113](https://github.com/rust-lang/sync-team/pull/113): Synchronization from GitHub (<span style="color: red;">closed</span>)
- [#119](https://github.com/rust-lang/sync-team/pull/119): Store tokens as secret strings
- [#127](https://github.com/rust-lang/sync-team/pull/127): Fix Zulip API request
- [#132](https://github.com/rust-lang/sync-team/pull/132): Generalize organization handling in tests

### rust-lang/simpleinfra (10 PRs)
- [#689](https://github.com/rust-lang/simpleinfra/pull/689): Give kobzol access to bastion
- [#696](https://github.com/rust-lang/simpleinfra/pull/696): Allow access to the new bors DB from bastion
- [#738](https://github.com/rust-lang/simpleinfra/pull/738): Add configuration for the rustc-perf collector machine
- [#743](https://github.com/rust-lang/simpleinfra/pull/743): Disable swap on rustc-perf
- [#744](https://github.com/rust-lang/simpleinfra/pull/744): Install AWS CLI on the rustc-perf collector machines
- [#745](https://github.com/rust-lang/simpleinfra/pull/745): Replace AWS CLI v2 with v1 on rustc-perf
- [#748](https://github.com/rust-lang/simpleinfra/pull/748): Set default boot target to `multi-user`
- [#752](https://github.com/rust-lang/simpleinfra/pull/752): Pass web URL to bors
- [#795](https://github.com/rust-lang/simpleinfra/pull/795): Add RDS access to the rustc-perf-two collector
- [#869](https://github.com/rust-lang/simpleinfra/pull/869): Use `@bors` prefix for new bors (<span style="color: green;">open</span>)

### rust-lang/cargo (9 PRs)
- [#15378](https://github.com/rust-lang/cargo/pull/15378): Add support for `-Zembed-metadata`
- [#15494](https://github.com/rust-lang/cargo/pull/15494): Fix tracking issue template link
- [#15766](https://github.com/rust-lang/cargo/pull/15766): Make timings graphs scalable to user's window
- [#15780](https://github.com/rust-lang/cargo/pull/15780): Add initial integration for `--json=timings` behing `-Zsection-timings`
- [#15923](https://github.com/rust-lang/cargo/pull/15923): Render individual compilation sections in `--timings` pipeline graph
- [#15924](https://github.com/rust-lang/cargo/pull/15924): Add "Optimizing Build Performance" section to the Cargo book
- [#15970](https://github.com/rust-lang/cargo/pull/15970): Add parallel frontend to the build performance guide
- [#15991](https://github.com/rust-lang/cargo/pull/15991): Add alternative linker to the build performance guide
- [#16142](https://github.com/rust-lang/cargo/pull/16142): Mention cargo wizard in build performance guide (<span style="color: green;">open</span>)

### rust-lang/measureme (9 PRs)
- [#244](https://github.com/rust-lang/measureme/pull/244): Add support for reading aggregated query cache hit counts
- [#245](https://github.com/rust-lang/measureme/pull/245): Use merge queues for the repository
- [#246](https://github.com/rust-lang/measureme/pull/246): Check `master` branch instead of `stable` in CI
- [#247](https://github.com/rust-lang/measureme/pull/247): Document the release process
- [#248](https://github.com/rust-lang/measureme/pull/248): Bump version to 12.0.2
- [#249](https://github.com/rust-lang/measureme/pull/249): Configure crates.io publish using OIDC
- [#250](https://github.com/rust-lang/measureme/pull/250): Add missing `id-token` permission
- [#252](https://github.com/rust-lang/measureme/pull/252): Fix query cache hit aggregation
- [#253](https://github.com/rust-lang/measureme/pull/253): Bump version to 12.0.3

### rust-lang/google-summer-of-code (8 PRs)
- [#13](https://github.com/rust-lang/google-summer-of-code/pull/13): Add AI notice
- [#19](https://github.com/rust-lang/google-summer-of-code/pull/19): Remove obsolete projects
- [#20](https://github.com/rust-lang/google-summer-of-code/pull/20): Update mentor of "Modernize libc" project
- [#23](https://github.com/rust-lang/google-summer-of-code/pull/23): Add Zulip idea discussion links for new project ideas
- [#27](https://github.com/rust-lang/google-summer-of-code/pull/27): Add idea about porting `stdarch` test suite
- [#30](https://github.com/rust-lang/google-summer-of-code/pull/30): Add concurrent Rustup project idea
- [#35](https://github.com/rust-lang/google-summer-of-code/pull/35): Add information about Google Summer of Code 2025 accepted projects
- [#36](https://github.com/rust-lang/google-summer-of-code/pull/36): Add script for computing GSoC mentor reward distribution

### rust-lang/rustup (7 PRs)
- [#4154](https://github.com/rust-lang/rustup/pull/4154): Use ARM based runners for ARM CI targets
- [#4344](https://github.com/rust-lang/rustup/pull/4344): Store dist manifest in JSON to improve load performance (<span style="color: red;">closed</span>)
- [#4350](https://github.com/rust-lang/rustup/pull/4350): Skip manifest loading if there are no components/targets to check
- [#4368](https://github.com/rust-lang/rustup/pull/4368): Fix CI image names for downloading ARM and PowerPC artifacts
- [#4405](https://github.com/rust-lang/rustup/pull/4405): Bump `toml` to 0.9
- [#4470](https://github.com/rust-lang/rustup/pull/4470): Remove hardcoded dependency to the master branch
- [#4511](https://github.com/rust-lang/rustup/pull/4511): Move the default branch from `master` to `main`

### rust-lang/compiler-builtins (5 PRs)
- [#966](https://github.com/rust-lang/compiler-builtins/pull/966): Switch to `rustc-josh-sync`
- [#973](https://github.com/rust-lang/compiler-builtins/pull/973): Add CI workflow for automatically performing subtree sync pulls
- [#975](https://github.com/rust-lang/compiler-builtins/pull/975): Tell triagebot to reopen bot PRs to run CI on them
- [#978](https://github.com/rust-lang/compiler-builtins/pull/978): Update `no-merges` PR title
- [#996](https://github.com/rust-lang/compiler-builtins/pull/996): Switch to using a GH app for authenticating sync PRs

### rust-lang/miri (5 PRs)
- [#4198](https://github.com/rust-lang/miri/pull/4198): Remove GitHub job summaries
- [#4490](https://github.com/rust-lang/miri/pull/4490): Use `josh-sync` instead of `miri-script` for Josh synchronization
- [#4493](https://github.com/rust-lang/miri/pull/4493): Fix cronjob Zulip message
- [#4505](https://github.com/rust-lang/miri/pull/4505): Use GH app for authenticating pull PRs
- [#4602](https://github.com/rust-lang/miri/pull/4602): Use `rustc-josh-sync` merge commit message for pull PR description

### rust-lang/ci-mirrors (4 PRs)
- [#4](https://github.com/rust-lang/ci-mirrors/pull/4): Validate that TOML files don't contain name/URL/hash duplicates
- [#9](https://github.com/rust-lang/ci-mirrors/pull/9): Add a command for adding entries to TOML files
- [#23](https://github.com/rust-lang/ci-mirrors/pull/23): Mirror GCC 9.2.0 sources
- [#26](https://github.com/rust-lang/ci-mirrors/pull/26): Mirror GCC 9.5.0 and add validation against paths starting with a slash

### rust-lang/homu (4 PRs)
- [#233](https://github.com/rust-lang/homu/pull/233): Move bors CI jobs from rust-lang-ci to rust-lang
- [#234](https://github.com/rust-lang/homu/pull/234): Fix pinned dependencies on CI
- [#236](https://github.com/rust-lang/homu/pull/236): Disable try builds
- [#238](https://github.com/rust-lang/homu/pull/238): Generalize merge conflict message

### rust-lang/infra-team (4 PRs)
- [#228](https://github.com/rust-lang/infra-team/pull/228): Rename `master` to `main`
- [#237](https://github.com/rust-lang/infra-team/pull/237): Document triagebot and some smaller services
- [#238](https://github.com/rust-lang/infra-team/pull/238): Fix toolstate link
- [#241](https://github.com/rust-lang/infra-team/pull/241): Update rustc-perf deployment docs link (<span style="color: green;">open</span>)

### rust-lang/cargo-bisect-rustc (3 PRs)
- [#381](https://github.com/rust-lang/cargo-bisect-rustc/pull/381): Use `rust-lang/rust` instead of `rust-lang-ci/rust` for unrolled rollup build commit URLs
- [#388](https://github.com/rust-lang/cargo-bisect-rustc/pull/388): Clarify documentation around usage of merge-base
- [#392](https://github.com/rust-lang/cargo-bisect-rustc/pull/392): Remove hardcoded dependency on master

### rust-lang/promote-release (3 PRs)
- [#95](https://github.com/rust-lang/promote-release/pull/95): Remove hardcoded master references for rust-lang/rust
- [#96](https://github.com/rust-lang/promote-release/pull/96): Do not hardcode the default branch of the blog repository
- [#98](https://github.com/rust-lang/promote-release/pull/98): Trigger website redeploy after a stable version is published

### rust-lang/rustc_codegen_cranelift (3 PRs)
- [#1614](https://github.com/rust-lang/rustc_codegen_cranelift/pull/1614): Rustc pull update (<span style="color: red;">closed</span>)
- [#1617](https://github.com/rust-lang/rustc_codegen_cranelift/pull/1617): Integrate with Josh (<span style="color: green;">open</span>)
- [#1618](https://github.com/rust-lang/rustc_codegen_cranelift/pull/1618): Update `rustup.sh` to use `rustc-josh-sync` (<span style="color: green;">open</span>)

### rust-lang/thanks (3 PRs)
- [#81](https://github.com/rust-lang/thanks/pull/81): Ignore enzyme submodule
- [#83](https://github.com/rust-lang/thanks/pull/83): Normalize repository names
- [#86](https://github.com/rust-lang/thanks/pull/86): Adapt to new rust-lang/rust default branch

### tikv/jemallocator (3 PRs)
- [#119](https://github.com/tikv/jemallocator/pull/119): Remove build directory once build of `jemalloc-sys` finishes
- [#120](https://github.com/tikv/jemallocator/pull/120): Respect jobserver set by Cargo
- [#152](https://github.com/tikv/jemallocator/pull/152): Reverse order of MAKEFLAGS priority

### rust-lang/calendar (2 PRs)
- [#88](https://github.com/rust-lang/calendar/pull/88): Add panstromek to Performance triage rotation
- [#95](https://github.com/rust-lang/calendar/pull/95): Remove rylev from performance triage rotation

### rust-lang/cc-rs (2 PRs)
- [#1447](https://github.com/rust-lang/cc-rs/pull/1447): Use `std::thread::available_parallelism` for determining the default number of jobs
- [#1619](https://github.com/rust-lang/cc-rs/pull/1619): Add publish environment for publishing crate

### rust-lang/rustc_codegen_gcc (2 PRs)
- [#614](https://github.com/rust-lang/rustc_codegen_gcc/pull/614): Add CI success job
- [#619](https://github.com/rust-lang/rustc_codegen_gcc/pull/619): Remove duplicated CI triggers

### XAMPPRocky/octocrab (1 PR)
- [#842](https://github.com/XAMPPRocky/octocrab/pull/842): Send body for retried requests

### kennytm/rustup-toolchain-install-master (1 PR)
- [#64](https://github.com/kennytm/rustup-toolchain-install-master/pull/64): Do not hardcode master branch name

### release-plz/release-plz (1 PR)
- [#2493](https://github.com/release-plz/release-plz/pull/2493): Clarify how to use trusted publishing

### rust-cross/cargo-zigbuild (1 PR)
- [#334](https://github.com/rust-cross/cargo-zigbuild/pull/334): Ignore `-znostart-stop-gc` linker flag

### rust-lang-ci/rust (1 PR)
- [#5](https://github.com/rust-lang-ci/rust/pull/5): Mention rust-lang-ci/rust being unused

### rust-lang/compiler-team (1 PR)
- [#852](https://github.com/rust-lang/compiler-team/pull/852): Fix link in MCP issue template

### rust-lang/funding (1 PR)
- [#1](https://github.com/rust-lang/funding/pull/1): Add Rust Foundation Maintainer Fund exploration document

### rust-lang/gcc (1 PR)
- [#66](https://github.com/rust-lang/gcc/pull/66): Use rust-lang mirror for downloading GCC dependencies

### rust-lang/glob (1 PR)
- [#181](https://github.com/rust-lang/glob/pull/181): Cache filename for sorting in `fill_todo`

### rust-lang/leadership-council (1 PR)
- [#248](https://github.com/rust-lang/leadership-council/pull/248): Add Rust Foundation Maintainer Fund Design committee

### rust-lang/mdBook (1 PR)
- [#2965](https://github.com/rust-lang/mdBook/pull/2965): Add publish environment to deploy job

### rust-lang/rfcs (1 PR)
- [#3809](https://github.com/rust-lang/rfcs/pull/3809): RFC: enable `derive(From)` for single-field structs

### rust-lang/rust-clippy (1 PR)
- [#15542](https://github.com/rust-lang/rust-clippy/pull/15542): Remove profile from Cargo.toml (<span style="color: red;">closed</span>)

### rust-lang/rust-log-analyzer (1 PR)
- [#88](https://github.com/rust-lang/rust-log-analyzer/pull/88): Extract job documentation URL from logs

### rust-lang/rustc-demangle (1 PR)
- [#83](https://github.com/rust-lang/rustc-demangle/pull/83): Do not publish the `native-c` crate

### rust-lang/rustfmt (1 PR)
- [#6720](https://github.com/rust-lang/rustfmt/pull/6720): Rename default branch to main

### rust-lang/thorin (1 PR)
- [#44](https://github.com/rust-lang/thorin/pull/44): Add publish environment

## A few more thoughts on my 2025 contributions

Looking back at the above list, I think I managed to do a lot of work. Even though after finally [finishing my PhD]({% post_url 2024-11-12-phd-postmortem %}) I had a lot of energy and time to work on Rust at the beginning of the year, due to some new family responsibilities, teaching at a university, and doing a lot of "non-technical" work (like surveys, mentoring or governance), I felt a bit unproductive in the second half of the year. At least in terms of actual coding, which is still something that I enjoy the most and that "feels" the best, even though other
 kinds of work are also important.

In fact, my personal Rust TODO list *grew* (not *shrank*) in 2025, which is a bit depressing. A large part of that was likely caused by me trying to finish initiatives already started year(s) ago, which I didn't have the bandwidth to drive forward during my PhD studies, and so new ideas had to wait.

It is also clear that I maintain ~~perhaps~~ *definitely* too many projects and initiatives. I think that is a good
thing for the Rust Project, because I'm able to help maintain some things that would probably otherwise
be unmaintained or stuck. However, I'm not sure if it's such a good thing for myself. Even though I think
that I'm relatively good at handling many initiatives at once[^context-switching] and I'm used to context-switching many times per ~~day~~ hour, that doesn't mean that I wouldn't be (or at least feel) more productive and less stressed if I was working on a smaller set of projects at once. It is my short-to-medium-term goal to reduce
the number of Rust projects that I contribute to, so that I can focus on things that I find the most
impactful and most enjoyable for me to work on, such as compiler performance, which I didn't get to
at all for the past few months. The hard part, as always, is to find people that would continue to
pass the torch so that things I "leave behind" don't get stuck again.

One area where I'm thinking of scaling down my contributions is the [Rust survey team](https://rust-lang.org/governance/teams/launching-pad/#team-survey). I mostly only joined it because it seemed like no one else would do it at the time. And even though I created some scripts to partly automate survey analysis, doing surveys doesn't exactly spark joy to me, so I would like to pass the torch to others. But it's [tricky](https://rust-lang.zulipchat.com/#narrow/channel/392734-council/topic/Onboarding.20people.20to.20teams.20with.20elevated.20privileges/with/558022595)…

[^context-switching]: In reality, I probably suck at it the same as everyone else does, but I don't know how to operate in any other way, so I don't have a baseline to compare to. I also kind of suck at working on a single thing for a long time, which is probably why I cling to context switching so much, almost as a form of procrastination.

## Conclusion

I hope you found this post interesting. I'm thinking of making this a regular yearly "look back" post
(for as long as I'm able to work on Rust), so maybe see you here in a year :)

And in case anyone is wondering, none of the PRs listed above were vibe-coded. I don't use AI much
for normal development, although sometimes it is quite useful for creating one-off scripts, such as
those I used for gathering my GitHub statistics.

If you found some other interesting new year open-source data visualizations, let me know on [Reddit]({{ page.reddit_link }}).
