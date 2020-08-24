---
layout: post
title:  "Contributing to Intellij-Rust #1: Fixing bug in Nest Use intention"
date:   2020-07-31 15:21:35 +0200
categories: rust intellij
--- 
This post is part of a [series]({% post_url 2020-08-23-contributing-0-setup %}) in which I describe
my contributions to the [IntelliJ Rust](https://github.com/intellij-rust/intellij-rust) plugin.

- Previous post: [#0 Intro & setup]({% post_url 2020-08-23-contributing-0-setup %})
- Current post: [#1 Fixing a simple bug in Nest Use intention](#)
- Next post: [TBD]

In this post I will go through [my very first contribution](https://github.com/intellij-rust/intellij-rust/pull/3503)
(don't click if you want to avoid spoilers!) to the plugin. Not because
it is especially interesting, but it's simple enough that I can explain the complete contribution process.
I'll go through the process of finding an issue, locating code that is relevant to it, writing a test,
implementing a fix and sending a PR.

Because this is the first post of this series describing an actual contribution, I will talk about
the contribution workflow in addition to explaining some basic concepts of the IntelliJ Rust plugin.
In later posts I will focus more on explaining the implemented features and the plugin's inner workings,
since the contribution process will be mostly the same.

# Finding a problem
The first thing that you have to do if you want to contribute to an open-source project is
to decide what do you want to implement. This is actually harder than it sounds and often it is
the hardest part of the whole process. Do you want to fix an issue? Implement new functionality that you
miss? Resurrect an old PR that was forgotten by the maintainers and/or by its author?
Is the issue that you're trying to solve still relevant? Is no one else working on it concurrently?
Which issue should you choose so that it's not too hard to demotivate you?

A good start is to look through issues with labels like "good first issue", "help wanted" or "easy".
The IntelliJ Rust plugin uses the `help wanted` issue label for issues that could be
solved by outside contributors. You can find such issues
[here](https://github.com/intellij-rust/intellij-rust/labels/help%20wanted). Additionally, some of the issues
are marked with difficulty tags that tell you approximately how hard it will be to fix the issue:

- `E-easy` - usually bug fixes or small modifications to existing features
- `E-medium` - implementation of a new straightforward feature or improvement of an existing feature
- `E-hard` - implementation of a new, complex feature or large-scale rewrite of some existing feature

There is also the `E-mentor` tag, which marks that mentoring instructions may be available for contributors
that want to tackle issues with this tag.

Another place that you can use to find potential issues to solve or to chat with the maintainers
and users of the plugin is its [gitter](https://gitter.im/intellij-rust/intellij-rust) page.

# The first issue
While looking through the plugin's issues, I found a [comment](https://github.com/intellij-rust/intellij-rust/issues/2577#issuecomment-469150465)
that mentioned a bug that seemed relatively easy to fix (even though I had no idea how the plugin works at that time).
The bug was in the `Nest use statements` intention. **Intentions** are simple code-modifying actions
that you can invoke on a piece of code via `Alt + Enter`. This specific intention is offered on `use` statements
and when invoked, it groups (nests) several use statements together:

```rust
use foo::bar/*caret*/;
use foo::baz;

// when invoked, the intention transforms the above code to:
use foo::{
    bar,
    baz
};
```

The `/*caret*/` comment is a notation used by the plugin's tests to mark the location of the user's caret,
I will be using it often in further code snippets.

The bug that was mentioned in the issue was that given this code:
```rust
use foo/*caret*/;
use foo::bar;
```
The intention would nest the imports like this: 
```rust
use foo::{foo, bar};
```
which is not equivalent to the original imports -- the following code should be generated instead[^1]:
```rust
use foo::{self, bar};
```
Because `foo` originally referred to the `foo` module (therefore it referred to itself),
so after nesting it should refer to `self`.

[^1]: Although at the end of this post we will see that even this transformation is not fully correct!

This looked like a simple bug that could be fixed with a few lines of code and a good first issue for me to try to solve.

# Finding the relevant code
So now that I knew what was the problem that I wanted to fix, the next step was to find the code that
implements this transformation. This is sometimes very difficult -- large projects can have thousands
of files and even worse, the functionality that you want to change might be spread over several of them.
In later posts I will describe some tricks that can help with this process when dealing with IntelliJ plugins,
however in this case it was pretty easy. I knew the name of the intention that I needed to fix, so it was just
a matter of grepping for `nest.*use.*intention` which led me to `src/main/kotlin/org/rust/ide/intentions/NestUseStatementsIntention.kt`
(yes, a bit of a mouthful, but that's Kotlin/Java for you).

# Finding out what is going on
After locating the relevant code, I had to find out why it failed in the mentioned case.
I quickly realized that using a debugger to examine the behaviour of the intention is the fastest way
to understand what exactly is it doing. At first, I tried to open up the IDE[^2], place a
breakpoint inside the intention and then invoke it manually on a piece of code. That worked, but it was
not pretty -- starting the IDE is slow and when a breakpoint is hit, its GUI freezes.

That led me to search for tests that were testing the functionality of this specific intention, in hope
that they would provide a faster debugging workflow.

[^2]: Using the `RunClion` or `RunIDEA` actions in IDEA or the `:plugin:runIde` Gradle task described in the previous post.

# Writing a failing test
Finding tests for some piece of code in a large open-source repository is not always easy[^3]. Luckily,
by glancing over the existing tests, I realized that the IntelliJ Rust plugin uses a simple naming convention
-- a test for a feature residing in some class has the same name as the tested class with `Test` appended at the end. 
So I searched (`Ctrl + Shift + F` in IDEA) for `NestUseStatementsIntentionTest`
and found it in `src/test/kotlin/org/rust/ide/intentions/NestUseStatementsIntentionTest.kt`.

[^3]: As described [here](https://matklad.github.io/2018/06/18/a-trick-for-test-maintenance.html) by matklad, one of the previous maintainers of the plugin, who now works on [Rust Analyzer](https://rust-analyzer.github.io/).

> Sticking to TDD with automated tests is a really good idea while working on IntelliJ plugins, as it is
much faster than starting the IDE up manually after every code change.

*[TDD]: Test-driven development

Writing a failing test before you even start to implement a fix or a feature is quite useful here, because it will help
you understand the current behaviour of the code (by debugging the execution of the test) and it may
also help guide your implementation. When I'm creating a new complex feature, I often write a ton
of tests upfront. This helps me avoid scenarios where I implement a part of a feature, then I realize
that my current solution is too simple and that I need to refactor the code to handle more cases.
Generating all edge cases and possible situations that I can think of upfront helps me think about edge cases that
I need to handle in the code from the beginning of the development.

There is also an additional reason to write tests -- if you want to merge your changes back into the plugin
with a Pull Request, the maintainers will most likely ask you to include at least one test to check that
your code is working and (mainly) to avoid future regressions. The plugin is heavily tested (currently it has over 6 thousand tests!),
so generally the more tests, the merrier.

I started with writing a test that demonstrates the issue so that I could debug it and find out
where is the problem. Intention tests use a method called `doAvailableTest` which takes code on which the intention is performed
(along with a caret position so that the test knows where to invoke the intention) and expected code that should
be produced after the intention is performed. Let's add such test to the end of `NestUseStatementsIntentionTest`:

```kotlin
fun `test converts module to self`() = doAvailableTest("""
    use foo/*caret*/;
    use foo::foo;
    use foo::bar;
""", """
    use foo::{
        self,
        foo,
        bar
    };
""")
```

Now let's run the test to see if it indeed fails. This can be done either by clicking on the green triangle
next to the test in IDEA or by using the command line:

```bash
$ ./gradlew :test --tests "*test converts module to self"
```

The command spitted out this:
```
junit.framework.ComparisonFailure: TEXT expected:<use foo::{
        [self],
        foo,
        bar
    }...> but was:<use foo::{
        [foo],
        foo,
        bar
    }...>
```
Great, this was exactly what I was expecting, instead of `self` the intention generated `foo`. Now
we can move to actually fixing the bug.

# Understanding the existing code
Intentions in this plugin are usually self-contained within a single file, therefore it's usually
not that hard to see what's going on. Each intention has two important methods:

- `findApplicableContext` - when you press `Alt + Enter` over some piece of code, the plugin iterates
all intentions and calls this method on each one of them. If the method returns some non-null *context*,
the intention will be offered in an intention list to the user. If the method returns null, the intention
will not be offered.
- `invoke` - if the user selects an intention to be executed from the intention list, this method will be
called to actually perform the intention. It will receive the *context* from `findApplicableContext`
as one of its arguments.

The bug that I wanted to fix was in the code transformation performed by the intention. It doesn't really
matter when was the intention offered, so I could ignore `findApplicationContext` and look at `invoke`.

Here is the full code of the `invoke` method:

```kotlin
override fun invoke(project: Project, editor: Editor, ctx: Context) {
    val path = makeGroupedPath(ctx.basePath, ctx.useSpecks)

    val inserted = ctx.root.addAfter(ctx.createElement(path, project), ctx.firstOldElement)

    for (prevElement in ctx.oldElements) {
        prevElement.delete()
    }

    val nextUseSpeckExists = inserted.rightSiblings.filterIsInstance<RsUseSpeck>().count() > 0
    if (nextUseSpeckExists) {
        ctx.root.addAfter(RsPsiFactory(project).createComma(), inserted)
    }

    editor.caretModel.moveToOffset(inserted!!.startOffset + ctx.cursorOffset)
}
```

I won't be explaining the signature of the method or its behaviour in detail, we'll talk about them
in a later post where we will create an intention from scratch.

The first line seems to create something called a path. A [path](https://doc.rust-lang.org/reference/paths.html)
in Rust is a sequence of identifiers separated by `::` which can be resolved to some named Rust element,
for example a struct or a module.
`foo`, `foo::bar` or `crate::foo::bar::Baz` are examples of simple paths.
There are also more complicated path variants, but we don't need to concern ourselves with those for now.

*[AST]: Abstract syntax tree

The rest of the method looks like it inserts and deletes things into the user's source file and the
last line seems to do something with the user's caret. Since we want to modify what is inserted
(`self` instead of the module name), and not how it's inserted, we'll look more closely at the `makeGroupedPath`
method and ignore the rest.

> We'll talk about how insertions, deletions and modifications of text in user's source files
work in later posts.

Here's the source code of it:
```kotlin
private fun makeGroupedPath(basePath: String, useSpecks: List<RsUseSpeck>): String {
    val useSpecksInGroup = useSpecks.flatMap {
        // Remove first group
        val useGroup = it.useGroup
        if (it.path?.referenceName == basePath && useGroup != null) {
            useGroup.useSpeckList.map { it.text }
        } else {
            listOf(deleteBasePath(it.text, basePath))
        }
    }
    return useSpecksInGroup.joinToString(",\n", "$basePath::{\n", "\n}")
}
```
The method receives some initial path and a list of `RsUseSpeck`s and returns
a string. So, what is a `RsUseSpeck`? To explain that, we will first have to talk about the way
IntelliJ represents parsed source code.
 
After IntelliJ parses source code, it is represented with a so-called *[Program Structure Interface](https://jetbrains.org/intellij/sdk/docs/basics/architectural_overview/psi.html)
(PSI) tree*, which is a fancy name for an enhanced AST. Rust code is parsed by the plugin into a tree of
PSI nodes that all inherit from a base `PsiElement` class. There are tens of various Rust elements
that can be parsed - `RsPath` represents a parsed path, `RsFunction` represents a function, etc.
These elements contain attributes essential for providing further analyses performed by the plugin,
for example `RsFunction` provides access to the function's name, its return type, parameters, etc.

The individual Rust PSI node types are automatically generated from a BNF grammar describing Rust syntax
located at `src/main/grammars/RustParser.bnf`. This makes it a bit difficult to understand which PSI node type
corresponds to individual Rust syntax elements. Luckily, there is a very useful tool for discovering the Rust PSI
node types called -- a plugin available in IntelliJ IDEA called `PsiViewer`. It allows you to display the parsed PSI tree of (Rust) code that you
have opened in your editor, which makes exploring the various PSI nodes much easier. We will talk about PSI more in later posts,
where we will learn how to manipulate it and create new PSI nodes from scratch.

Now back to use specks. `RsUseSpeck` basically represents a (potentially nested) part of a `use` statement.
For example, in the following snippet:

```rust
use foo::{self, foo, bar};
```

`foo::{self, foo, bar}`, `self`, `foo` and `bar` are use specks.

*[BNF]: Backus-Naur form

Cool. So what use specks does the method work with in our (still failing) test?
Let's try to put a breakpoint at the first line of the method and debug the test to find out.
All PSI elements have a very useful `text` attribute, which returns their verbatim string content
as it was parsed from the source code. I used that to print the contents of the use speck list.
These are the values of the arguments:

- `basePath` - `foo`
- `useSpecks` - `[foo, foo::foo, foo::bar]`

As a reminder, this is the test source code on which the intention was invoked:
```rust
use foo/*caret*/;
use foo::foo;
use foo::bar;
```

A-ha! It looks like `basePath` contains the base path (d'uh) that will be the parent of the generated
use group and `useSpecks` contains the use specks that should be nested inside the group. The problem
is that when a use speck has the same name as the base path (`foo` in this example), the nested
use speck should be renamed to `self` instead, but the intention didn't handle this special case.

So how do we handle it? The `makeGroupedPath` method calls another method, `deleteBasePath`:

```kotlin
private fun deleteBasePath(fullPath: String, basePath: String): String {
    return when {
        fullPath.startsWith(basePath) -> fullPath.removePrefix("$basePath::")
        else -> fullPath
    }
}
```
It receives a base path (in this case `foo`) and some other path (named `fullPath`) and removes the
base path prefix from the full path. For example it turns `foo::bar` into just `bar` so that it can
be nested as a standalone element inside a use group - we want `foo::{bar}` and not `foo::{foo::bar}`.

When I found this method, the fix became clear: if the `fullPath` is equal to the `basePath`,
we need to return `"self"`. And indeed, adding this one line fixed my failing test! :tada:
```kotlin
...
    fullPath == basePath -> "self"
    fullPath.startsWith(basePath) -> fullPath.removePrefix("$basePath::")
...
```

Phew. That was a very long journey to do a very small edit (13 lines for the test and one line for the
intention change) to the plugin's source code.
I hope that you were able to follow my ramblings, as it was a lot of new information
about the IntelliJ APIs combined with modifying existing code written by someone else, which is always
difficult. I did not explain everything, but hopefully it was detailed enough to explain the process
I went through when implementing this fix. Now that the code is ready, let's go merge it into the plugin!

# Contributing the change back to the plugin
The first thing that we have to do is commit our changes. The plugin contains a great [guide](https://github.com/intellij-rust/intellij-rust/blob/master/CONTRIBUTING.md)
describing its contribution rules, which also contain a list of tags that should be used when modifying various
part of the plugin. It says that `INT` should be the tag used for changes related to intentions, therefore
I named my commit `INT: handle conversion of module to self in nest use intention`. A bit of a mouthful,
but hopefully it gets the point across. I also recommend to name branches in an intuitive way. My branch was named
`int-2577`, because it dealt with an intention and it fixed issue #2577… yeah, not a great name, but in my defence,
it was my first PR to this repository.

The next thing that you have to do if you are contributing to the plugin for the first time is to include
your GitHub nickname into the contributors list. It is located in the `CONTRIBUTORS.txt` file in the root
of the repository and it already contains over one hundred names! Simply insert your GitHub nickname into the list
in alphabetical order in another commit.

Now that we have our changes committed to git, we need to create a Pull Request (PR), which is a way for contributors
to ask for their code to be merged into someone else's repository. Because you are not allowed to push your
branch directly to the plugin's repository (you need a permission from the maintainers for this), you have to
create your own copy of the repository. The easiest way to do this is to go to the [GitHub](https://github.com/intellij-rust/intellij-rust)
page of the plugin and click on the `Fork` button in the upper right corner. This will create a copy of the
repository at `https://github.com/<your username>/intellij-rust`. Then you can add it as a `git` remote
and push your branch to it!

```bash
git remote add myfork https://github.com/<your username>/intellij-rust
git push myfork -u <my-branch>:<my-branch>
```

After that, go to [https://github.com/intellij-rust/intellij-rust/pulls](https://github.com/intellij-rust/intellij-rust/pulls).
If GitHub picked up the push to your fork, it should show you a special button for creating a PR
directly from your recently pushed branch. If not, click on `New pull request`, click on `compare across forks`,
select your fork for `head repository` and your branch name for `compare`. Then fill the description of your
PR - what it tries to accomplish, how the implementation works and what are its possible edge cases.
If your PR fixes a specific issue, link it in the description with a `Fixes: ` or `Closes: ` prefix,
this will instruct GitHub to automatically close the issue if your PR gets merged. Finally click on
`Create pull request` and hope for the best!

The plugin uses automatic CI infrastructure, so after some time (~25 minutes) you should see if your branch
passed all of the tests on the PR's page.

After you send the PR, the only thing that you can do is wait. This part is sometimes a bit frustrating,
as maintainers are usually pretty busy and it might take some time before they can review your PR.
In my case I was lucky, as the PR got merged in just four minutes (!), but sometimes it can also take weeks
or even months. If you are really desperate and do not receive any feedback after several weeks, try to
ping one of the maintainers in a follow-up comment on the PR.

If the maintainers agree with your change, they will instruct the [BORS](https://github.com/bors-ng/bors-ng)
bot with a command to try to merge your PR into `master` and run all of the tests. If they pass,
congratulations, your PR was successfully merged!

However, often there is a fair bit of discussion and review comments that need to be solved before
your PR is accepted. Remember that you are trying to merge your changes into someone else's project.
Even though you are doing work for them for free, they still have the right to refuse your contribution
or ask for changes that you might not like. The ultimate goal is to improve the quality-of-life of
the project's users, so sometimes it's necessary to let go of your personal goals and do what's best for the project
as a whole.

I hope that this post has inspired you to try to contribute to IntelliJ Rust (or other open-source
project that you are using). If you have read the whole post up until this point, I salute you!
Leave me a comment on [Reddit](https://www.reddit.com/r/rust/comments/ifxr99/contributing_to_the_intellijrust_plugin_a_series/) if you have any remarks. And that's it for today… or not?

# Was my fix correct?
Sometime later after the PR with my fix got merged, I stumbled upon an [issue](https://github.com/rust-lang/rustfmt/issues/3362)
in the `rustfmt` repository. It mentions that the use statements `A` and `B` are in fact not
semantically equivalent:

```rust
use foo::bar;               // A
use foo::bar::baz;          // A
// vs
use foo::bar::{self, baz};  // B
```
because `B` would not import a macro named `bar!` in the `foo` module (if such macro exists).

Users of the plugin expect (and rightfully so) that this intention should not change the meaning
of the modified use statements, and therefore using the intention should not break user code.
The issue that I linked clearly states this is in fact not the case, as the described
transformation (which can be executed by this intention) simply does not produce equivalent semantics
in ALL cases.

So, was my fix incorrect? Well, maybe. But even though this transformation is not valid in ALL cases,
it is valid in MOST common cases. The plugin is not perfect, as it uses many heuristics, but its main
goal is to be useful for its users, not to handle all possible edge cases that could arise (although
it usually tries to handle as many as it can). My PR solved a concrete user's bug report, so I consider
it a success.

**Fun fact**: because `rustfmt` tries to be perfect (and in its case I think it actually should be), it didn't
stabilize the `merge_imports` feature to this day, amongst other things because of this single semantics
changing transformation.
