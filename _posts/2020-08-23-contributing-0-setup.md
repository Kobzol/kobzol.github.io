---
layout: post
title:  "Contributing to Intellij-Rust #0: Intro & setup"
date:   2020-07-31 15:21:35 +0200
categories: rust intellij
--- 
Hi!

I'm a big fan of [Rust](https://www.rust-lang.org/) and all the various [IntelliJ IDEs](https://www.jetbrains.com/products.html#type=ide)
and so naturally I am also an avid user of the awesome [IntelliJ Rust plugin](https://intellij-rust.github.io/).

While using the plugin, I noticed some small quirks that were bothering me and some useful features
that were missing. I wondered if there was something that I could do to improve that situation,
so I checked out the plugin repository to see if there were some issues that I could help with.

It turned out that the answer was yes - I found an issue in a comment, sent my [first pull request](https://github.com/intellij-rust/intellij-rust/pull/3503)
and it got approved and merged in 4 minutes (!). The friendly response I got from the plugin's maintainers motivated
me to continue improving the plugin and over time I found it to be incredibly enjoyable and rewarding -
as of today, I have opened more than [100 PRs](https://github.com/intellij-rust/intellij-rust/pulls/kobzol)
in the plugin's repository :sweat_smile:. I'd like to thank the plugin's maintainers, mainly
[@Undin](https://github.com/undin), [@vlad20012](https://github.com/vlad20012),
[@mchernyavsky](https://github.com/mchernyavsky) and [@ortem](https://github.com/ortem) for keeping up with
my pull requests :)

*[today]: 24. 08. 2020

Since contributing to a non-trivial open-source project can be daunting at first, I decided to document
some of my experiences in this blog series to provide information for people that might also want to contribute
to this plugin. I was inspired to do this by a similar blog post describing a
[contribution to Rust Analyzer](https://dev.to/bnjjj/what-i-learned-contributing-to-rust-analyzer-4c7e).

My goals are to provide a simple guide that could motivate more people to contribute to this wonderful plugin and
also describe basic open-source contribution workflow.
I plan to write these posts as retrospective descriptions of how I approached my contributions with additional
insights that should help you with making contributions of your own.

In this first blog post, I will show you how to setup a basic environment to test and modify the plugin and
I will also describe its basic architecture. In the next post, I will go through
my first contribution step-by-step, from identifying an issue, through implementing a bug fix
to sending a pull request. In later posts I want to explain more complicated things like
creating new intentions, inspections or annotations, tuning code formatters or even designing whole new 
refactoring actions.

- Next post: [#1 Fixing a simple bug in Nest Use intention]({% post_url 2020-08-23-contributing-1-nest-use-fix %})

*Disclaimer*: I'm not an expert on the IntelliJ API/plugins or Rust itself. It's possible that 
something that I write here is incorrect or incomplete. If you find something like that, please let
me know on [Reddit](https://www.reddit.com/r/rust/comments/ifxr99/contributing_to_the_intellijrust_plugin_a_series/)!

# Prerequisites
There are some prerequisites for this series that are out-of-scope for me to describe in detail:

- **Kotlin**
    The plugin is written almost exclusively in the programming language [Kotlin](https://kotlinlang.org/), so
    you should be familiar with it to follow along. If you know Java, C# or other high-level
    languages based on C, it should look very familiar.
- **Rust**
    The plugin provides Rust integration, so naturally I will talk about Rust a lot. You do not
    have to be deeply familiar with it, however I assume that you know the basics or at least that
    you are familiar with Rust's syntactic rules.
- **IntelliJ IDEA**
    I will be using the IntelliJ IDEA for development of the plugin, since building and modifying
    the plugin works out of the box in this IDE. Nevertheless, the plugin can be built, modified
    and tested using any other IDE or text editor. The plugin is IntelliJ-specific though, so we will
    talk about a lot of IntelliJ concepts.
- (**git**)
    Contributing to open-source projects usually requires using some version control system,
    in this case it's git. I assume some basic familiarity with git, although I will describe briefly
    how to contribute to other repositories on GitHub.
- (**Linux**)
    I will use some command line snippets that assume a Linux (or more specifically Ubuntu) environment.
    However, these commands should look very similar on other operating systems and they're mostly not necessary
    if you use IDEA to work on the plugin.

With that out of the way, let's go set up the plugin so that we can build it and test it!

# Building the plugin
> If you want to use IntelliJ IDEA for working with the plugin, you can download the free community version [here](https://www.jetbrains.com/idea/download/).
I recommend you to use this IDE if you want to work on the plugin.

The [contribution documentation](https://github.com/intellij-rust/intellij-rust/blob/master/CONTRIBUTING.md)
of the plugin already does a great job of advising new contributors on how to build and contribute to the plugin.
I used it heavily when I started to contribute and I encourage you to read it first.
The rest of this blog post will be heavily inspired by this documentation.

Before we download the plugin, you will need to make sure that you have installed 
**git** and a **JDK**. I recommend to install JDK 8, which is
[recommended](https://jetbrains.org/intellij/sdk/docs/basics/getting_started/setting_up_environment.html)
by the IntelliJ documentation.
```bash
$ sudo apt-get install git openjdk-8-jdk
```

**EDIT**: Since [recently](https://github.com/intellij-rust/intellij-rust/pull/6153), the plugin has
switched to **JDK** 11:
```bash
$ sudo apt-get install openjdk-11-jdk
```

*[JDK]: Java Development Kit

Hopefully, JDK and git should be the only dependencies that we need, the rest will be handled by the
plugin's build system.

Now we can clone the repository of the plugin:
```bash
$ git clone https://github.com/intellij-rust/intellij-rust
$ cd intellij-rust
```
The plugin uses the Gradle build system, so building it is very easy, simply invoke the `assemble` task
in the directory of the plugin:
```bash
$ ./gradlew :assemble
```
The command will download a lot of packages and also two IDEs (CLion and IDEA) that will be used as
sandbox environments for testing the plugin, so prepare at least a few gigabytes of disk space for this.
Also prepare a cup of coffee if you are running this on an HDD.

> You can also build the project in IDEA by opening the project directory and building/running the
"Run CLion" or "Run IDEA" configurations.

There are some other useful gradle tasks:
- `./gradlew :plugin:runIde -PbaseIDE=clion` - open CLion with the current version of the plugin
- `./gradlew :plugin:runIde -PbaseIDE=idea` - open IDEA with the current version of the plugin
- `./gradlew :test` - run all tests (takes a LONG time)
- `./gradlew :test --tests *MyFavouriteTest*` - run a specific test 
- `./gradlew :plugin:buildPlugin` - publish the plugin so that it can be installed from disk

You can also invoke all of these directly from IDEA, using the Gradle window.

# Plugin architecture
The plugin basically reimplements most of the [rustc](https://rustc-dev-guide.rust-lang.org/) frontend,
which makes some of its internals relatively complex -- it has its own Rust lexer and parser, it infers types,
resolves names, solves trait impls and understands modules and crates. Even though that may look daunting at first,
when you want to modify the plugin, you usually do not have to dive deep into these subsystems and you can
just use them as black-box APIs. I will comment on things like type inference or name resolution
in later blog posts when we will need them for implementing various features. If you want to know more,
the architecture of the plugin is described very well in the [plugin's documentation](https://github.com/intellij-rust/intellij-rust/blob/master/ARCHITECTURE.md).

However, what we will need to understand right away is the directory hierarchy of the plugin, to know where to
look if we want to modify some code. There are several modules in the plugin's root directory, the most important are:
- `:src` - code of the Rust plugin
- `:intellij-toml` - code of the TOML plugin
- `:toml` - code specific for TOML + Rust integration (think `Cargo.toml`)
- `:common` - common code shared by Rust and TOML plugins
- `:idea` - code specific for IDEA integration
- `:clion` - code specific for CLion integration
- `:debugger` - code specific for Rust debugger

As you can see, there are actually two plugins in the repository - TOML and Rust. Most of my
contributions are targeting the Rust plugin, so we will be mostly dealing with the `src` directory.

That's pretty much all that we need to know right now, we will explore the individual parts of the
plugin when we will need them for a specific feature.

Now you should have a working development environment set up so that you can modify the plugin,
build and test the plugin. In the [next post]({% post_url 2020-08-23-contributing-1-nest-use-fix %}), we will actually implement something and fix a simple :bug:.

You can comment on this post on [Reddit](https://www.reddit.com/r/rust/comments/ifxr99/contributing_to_the_intellijrust_plugin_a_series/).
