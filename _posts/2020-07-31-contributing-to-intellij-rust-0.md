---
layout: post
title:  "Contributing to Intellij-Rust #0: Intro & setup"
date:   2020-07-31 15:21:35 +0200
categories: rust intellij
--- 
Hi!

I'm a big fan of [Rust](https://www.rust-lang.org/) and all the various [IntelliJ IDEs](https://www.jetbrains.com/products.html#type=ide)
and so naturally I am also an avid user of the [IntelliJ Rust plugin](https://intellij-rust.github.io/), which is awesome.

However, last year, when I was using the plugin, I noticed some quirks that were bothering me
and some features that I would love to have but that were missing. I wondered if there was something that
I could do to improve that situation, so I looked at the plugin repository to see if there were some issues
that I could help with.

It turned out that the answer was yes - I found an issue in a comment, sent my [first pull request](https://github.com/intellij-rust/intellij-rust/pull/3503)
and it got approved and merged in 4 minutes (!). The friendly response I got from the plugin's maintainers motivated
me to continue improving the plugin as I found it incredibly enjoyable and rewarding. Since then, it got slightly
out of hand - as of today, I have opened more than [100 PRs](https://github.com/intellij-rust/intellij-rust/pulls/kobzol)
in the plugin's repository :sweat_smile:.

*[today]: 31. 07. 2020

Since contributing to a non-trivial open-source project can be daunting at first, I decided to document
some of my experiences in this blog series to provide useful information for people that might also want to contribute
to this plugin. I was inspired by a similar blog post describing a [contribution to Rust Analyzer](https://dev.to/bnjjj/what-i-learned-contributing-to-rust-analyzer-4c7e).

In this first blog post, I will show you how to setup a basic environment to test and modify the plugin and
I will also describe its basic architecture. In the following parts, I will go through
some of my contributions step-by-step, from identifying an issue, through writing a fix or a new feature
to sending and pushing through a pull request.

# Intro
There are some prerequisites for this series that are out-of-scope for me to describe in detail in this blog post,
I list them below.

- **Kotlin**
    The plugin is written almost exclusively in the programming language [Kotlin](https://kotlinlang.org/),
    therefore I assume that you can read and understand Kotlin code. However, even if you do not know it,
    do not despair - if you know Java, C# or other high-level languages based on C, it should look very familiar.
    I will not explain Kotlin syntax in this series, but I will occasionally have some
    remarks about the code style used in the plugin's codebase.
- **IntelliJ IDEA**
    Even though it's not strictly necessary, I will be using IntelliJ IDEA as a development environment
    for modifying the plugin. It has out-of-the-box support for building and testing the plugin and
    it also has various built-in tools that help with its development, so it's a natural choice.
    Nevertheless, the plugin can be built, modified and tested using any other IDE or text editor.
- **git**
    Contributing to open-source projects usually requires using some version control system,
    in this case it's git. I assume some basic familiarity with git, however I will describe
    in detail how to contribute to other repositores on GitHub, which is important for this series.
- **Linux**
    I will show some command line examples (mostly in this first blog post) that will assume a Linux
    environment. However, they shouldn't be OS specific, so you should be fine on other operating systems.

With that out of the way, let's go set up the plugin so that we can build it and test it!

# Building the plugin
> If you want to use IntelliJ IDEA for working with the plugin, you can download the free community version [here](https://www.jetbrains.com/idea/download/).

Before we download the plugin, you will need to make sure that you have installed 
**git** and some **JDK**. I recommend to install JDK 11, which can be done with the following command on
Ubuntu:
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
sandboxes for the plugin, so prepare at least a few gigabytes of disk space for this. Also prepare a
cup of :coffee: if you are running this on an HDD :smile:.

> You can also build the project in IDEA by opening the project directory and building the
> "Run CLion" or "Run IDEA" configuration (click on the green hammer icon).

Now that the plugin is built, you can install it from disk **TODO*.
You can also run the test suite, but I wouldn't recommend it, since there are several thousand tests
and it takes a while to execute all of them.

# Architecture
Now that we have downloaded and compiled the plugin, let's take a look at the plugin's directory structure
to know what we are dealing with. There are several modules:
