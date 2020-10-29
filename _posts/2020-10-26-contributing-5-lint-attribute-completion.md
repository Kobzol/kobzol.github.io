---
layout: post
title:  "Contributing to Intellij-Rust #5: Lint attribute completion"
date:   2020-10-26 18:37:00 +0100
categories: rust intellij
--- 
This post is part of a [series]({% post_url 2020-08-23-contributing-0-setup %}) in which I describe
my contributions to the [IntelliJ Rust](https://github.com/intellij-rust/intellij-rust) plugin.

- Previous post: [#4 Introduce constant refactoring]({% post_url 2020-10-19-contributing-4-introduce-constant-refactoring %})
- Next post: [TBD]

So far, we have been talking mostly about IDE actions that
[modify]({% post_url 2020-08-23-contributing-1-nest-use-fix %})
[user]({% post_url 2020-08-25-contributing-2-subst-assoc-type-int %})
[code]({% post_url 2020-10-19-contributing-4-introduce-constant-refactoring %}). We have also seen
some [code analysis]({% post_url 2020-09-04-contributing-3-quick-fix-attach-file-to-mod %}),
but we haven't implemented it from scratch (we'll do that in the next post). This time, we'll try
[something completely different](https://youtu.be/8KwgWqVCPzk?t=10).

In this post we'll implement code completion for both `rustc` and [`clippy`](https://github.com/rust-lang/rust-clippy)
lints inside Rust [attributes](https://doc.rust-lang.org/reference/attributes.html). I'll describe
what completion is and how it works inside the plugin. We will also create a Python script to find
the list of all currently active `rustc` and `clippy` lints and automatically generate source files
containing the lints.

You can find the original PR that I will go through [here](https://github.com/intellij-rust/intellij-rust/pull/5646)
(spoiler alert!). This one is fresh out of the oven -- at the time of writing of this post, it hasn't
even been published yet!

# Finding an issue
[Riateche](https://github.com/Riateche) created a [feature request](https://github.com/intellij-rust/intellij-rust/issues/3720)
in which he asked if the plugin could complete `rustc` and `clippy` lints inside attributes. Lints are
code inspections that warn you of potentially problematic or suboptimal situations in your code. The
Rust compiler has a set of built-in lints (it detects e.g. unused variables or wrong naming
conventions). In addition, you can also use `clippy`, a compiler plugin that provides a much larger
[set of lints](https://rust-lang.github.io/rust-clippy/master/) of various categories like
code complexity or performance.

There are four lint "levels" that specify what happens if the lint matches your code:
- **allow** - the code will be allowed (nothing will happen)
- **warn** - the compiler will produce a warning
- **deny** - the compiler will not compile your code
- **forbid** - like `deny`, but once a lint is forbidden, it cannot be allowed again in the rest
of your code

Each lint has its default level, but Rust also allows you to change the level of a specific lint
(or a group of lints) in certain parts of your code using attributes. For example, if you do not want
the compiler to warn you about unused variables, you can `allow` them:
```rust
#![allow(unused_variables)]

fn foo() {
    let x = 1; // no warning
}
```
Or if you really like naming conventions, you can `deny` breaking them:
```rust
#![deny(non_camel_case_types)]

struct my_struct; // hard error
```

Because there are a lot of lints available (a few hundred) and it's pretty common to allow or deny
specific lints, it would be nice if the plugin could complete them. Therefore, in this situation:
```rust
#![allow(unused_va/*caret*/)]
```
the plugin should complete the code to this:
```rust
#![allow(unused_variables/*caret*/)]
```

# Completion
Code completion is a pretty standard feature of modern IDEs. It can basically "finish your
sentences" inside code -- you start typing something and the IDE offers you a list of entries
that could be completed from the prefix that you have written:

{% include gif.html path="/assets/posts/contributing-5/completion-function" w="100%" %}

If you learn to use code completion, it can make writing code much easier.

The IntelliJ Rust plugin can complete many things: keywords,
[paths]({% post_url 2020-08-23-contributing-1-nest-use-fix %}#paths), types, struct fields, etc. Its
completion is also context-dependent, for example at `let a: /*caret*/` it will offer you types,
while at `let a = /*caret*/` it will offer you potential expressions.

# Bootstrapping code completion
So, how do we find out how to add new completion to the plugin? One way would be to check out
previous PRs that added something related to completion to see what parts of code have they touched.
If we look at the [contributor documentation](https://github.com/intellij-rust/intellij-rust/blob/master/CONTRIBUTING.md#commit-messages)
of the plugin, we'll see that code completion related changes should use the prefix `COMP`. We can
then [search](https://github.com/intellij-rust/intellij-rust/pulls?q=is%3Apr+COMP+is%3Aclosed) for
such PRs in the plugin's GitHub repository. If you look through them, you'll notice one class that
occurs repeatedly, `RsCompletionContributor.kt`, so that's where we'll begin[^grep].

[^grep]:
    We could have also just grepped for `completion` inside the plugin's repository, which would
    also work in this case. But, you know, I'd rather teach you
    [how to fish](https://en.wiktionary.org/wiki/give_a_man_a_fish_and_you_feed_him_for_a_day;_teach_a_man_to_fish_and_you_feed_him_for_a_lifetime) :)

[`RsCompletionContributor`](https://github.com/intellij-rust/intellij-rust/blob/3b2080b973292a6f3aab6cce0e569991c2a166e3/src/main/kotlin/org/rust/lang/core/completion/RsCompletionContributor.kt)
is registered in
[`rust-core.xml`](https://github.com/intellij-rust/intellij-rust/blob/3b2080b973292a6f3aab6cce0e569991c2a166e3/src/main/resources/META-INF/rust-core.xml)
as a "completion contributor":
```xml
<completion.contributor
    language="Rust"
    implementationClass="org.rust.lang.core.completion.RsCompletionContributor" />
```
If we take a look at it, we can see that it contains various "providers", which provide completion
for primitive types, tuple fields, derive attributes, await, etc.:
```kotlin
class RsCompletionContributor : CompletionContributor() {
    init {
        extend(CompletionType.BASIC, RsPrimitiveTypeCompletionProvider)
        extend(CompletionType.BASIC, RsBoolCompletionProvider)
        extend(CompletionType.BASIC, RsFragmentSpecifierCompletionProvider)
        extend(CompletionType.BASIC, RsCommonCompletionProvider)
        extend(CompletionType.BASIC, RsTupleFieldCompletionProvider)
        extend(CompletionType.BASIC, RsDeriveCompletionProvider)
        extend(CompletionType.BASIC, RsAttributeCompletionProvider)
        extend(CompletionType.BASIC, RsMacroCompletionProvider)
        extend(CompletionType.BASIC, RsPartialMacroArgumentCompletionProvider)
        extend(CompletionType.BASIC, RsFullMacroArgumentCompletionProvider)
        extend(CompletionType.BASIC, RsCfgAttributeCompletionProvider)
        extend(CompletionType.BASIC, RsAwaitCompletionProvider)
        extend(CompletionType.BASIC, RsStructPatRestCompletionProvider)
    }
}
```
It seems that to add a new type of completion, we should add a new provider to this list, so that's
exactly what I did by creating a new class called `RsRustcLintCompletionProvider` next to the other
providers and adding it to the list of providers[^basic]:
```kotlin
init {
    ...
    extend(CompletionType.BASIC, RsRustcLintCompletionProvider)
}
```

[^basic]:
    I have no idea what `CompletionType.BASIC` means, but all of the other providers are using it,
    so let's use it too and hope for the best :laughing:.

Before we take a look at `RsRustcLintCompletionProvider`, let's write a test to see what situations
we might encounter in our implementation. 

# Writing a failing test
As usually, let's first write a test so that we can step into the completion provider to see what
arguments does it receive. So, how can we test completions? If we take a look at some existing
completion provider, for example
[`RsDeriveCompletionProvider`](https://github.com/intellij-rust/intellij-rust/blob/3b2080b973292a6f3aab6cce0e569991c2a166e3/src/main/kotlin/org/rust/lang/core/completion/RsDeriveCompletionProvider.kt),
and invoke `Ctrl + Shift + T`, it will lead us to
[`RsDeriveCompletionProviderTest`](https://github.com/intellij-rust/intellij-rust/blob/3b2080b973292a6f3aab6cce0e569991c2a166e3/src/test/kotlin/org/rust/lang/core/completion/RsDeriveCompletionProviderTest.kt):
```kotlin
class RsDeriveCompletionProviderTest : RsCompletionTestBase() {
    fun `test complete on struct`() = doSingleCompletion("""
        #[derive(Debu/*caret*/)]
        struct Test {
            foo: u8
        }
    """, """
        #[derive(Debug/*caret*/)]
        struct Test {
            foo: u8
        }
    """)
    ...
}
```
Cool, so there is already a base class for testing completions,
[`RsCompletionTestBase`](https://github.com/intellij-rust/intellij-rust/blob/3b2080b973292a6f3aab6cce0e569991c2a166e3/src/test/kotlin/org/rust/lang/core/completion/RsCompletionTestBase.kt)!
To test a single completion, we can use the `doSingleCompletion` function. We give it a snippet of
code with a `/*caret*/` placed after some text that should be completed and a second snippet with
the result that we expect to see after the completion is performed. Let's copy-paste this test class
and create a first test for our lint completion:
```kotlin
class RsLintCompletionProviderTest : RsCompletionTestBase() {
    fun `test complete inner attribute`() = doSingleCompletion("""
        #![allow(unused_var/*caret*/)]
    """, """
        #![allow(unused_variables/*caret*/)]
    """)
}
```
The test fails -- as expected, nothing is being completed yet.

Now let's go back to `RsRustcLintCompletionProvider`. I looked at the other completion providers
and they all inherited from
[`RsCompletionProvider`](https://github.com/intellij-rust/intellij-rust/blob/3b2080b973292a6f3aab6cce0e569991c2a166e3/src/main/kotlin/org/rust/lang/core/completion/RsCompletionProvider.kt).
Therefore, I did the same and created the following minimal skeleton:
```kotlin
class RsRustcLintCompletionProvider : RsCompletionProvider() {
    override fun addCompletions(
        parameters: CompletionParameters,
        context: ProcessingContext,
        result: CompletionResultSet
    ) { /*TODO*/ }

    override val elementPattern: ElementPattern<out PsiElement>
        get() { /*TODO*/ }
}
```
To make our completion do something, we have to implement at least two things: the `addCompletions`
function and the `elementPattern` attribute.

# Matching elements for lint completion
Let's begin with `elementPattern`. Before we can complete anything, we have to specify on which Rust
elements we want to perform the completion. It wouldn't make sense to e.g. complete struct
fields when you're calling a function or complete a local variable when you're defining a function
parameter type. The plugin thus requires you to create an *element pattern*, which specifies on which
elements should the completion be performed.

To do that, we have to create an instance of `ElementPattern`, which is an IntelliJ API for querying
(or "matching") PSI elements using a declarative interface. For example, here is a pattern that
matches elements inside a loop:
```kotlin
psiElement().inside(
    psiElement<RsBlock>().withParent(
        or(
            psiElement<RsForExpr>(),
            psiElement<RsLoopExpr>(),
            psiElement<RsWhileExpr>()
        )
    )
)
```
It matches any PSI element (`psiElement()`) that is `inside` a block (`psiElement<RsBlock>()`)
which has a loop (`RsForExpr`/`RsLoopExpr`/`RsWhileExpr`) as its parent (`withParent`). 

As an another example, which will be relevant to our use case, here is a pattern that matches text
inside a `derive(...)` attribute:
```kotlin
psiElement<RsMetaItem>().withSuperParent(
    2,
    psiElement()
        .withSuperParent<RsStructOrEnumItemElement>(2)
        .with("deriveCondition") { e -> e is RsMetaItem && e.name == "derive" }
)
```
It matches any attribute part (`RsMetaItem`) that has a "superparent two levels up" (i.e. a
grandparent), which itself is a PSI element that has a `struct` or `enum` as its grandparent and
is an attribute part with the name `derive`. We'll see what all this means in a moment.

#### Examining PSI of lint attributes
So, how do we find out what pattern should we use for completing lints? First, we have to examine
how does the PSI structure of lint attributes looks like. To do that, we'll use the
[PsiViewer]({% post_url 2020-08-23-contributing-1-nest-use-fix %}#psi) plugin. If I write the
following code in a Rust file:
```rust
#![allow(unused_variables)]
```
the generated PSI tree will look something like this[^psitree]:
```
RsInnerAttr
  PsiElement: #
  PsiElement: !
  PsiElement: [
  RsMetaItem
    RsPath
      PsiElement: allow
    RsMetaItemArgs
      PsiElement: (
      RsMetaItem
        RsPath
          PsiElement: unused_variables
      PsiElement: )
  PsiElement: ]
```

[^psitree]:
    This output was copied from PsiViewer and slightly modified -- I added text content to some PSI
    nodes and removed some things to make the output more readable.

That's a lot of stuff! Let's go through the interesting parts:
- `RsInnerAttr` is the PSI representation of an inner attribute. Rust contains two types
of [attributes](https://doc.rust-lang.org/reference/attributes.html):
    - Inner attributes start with `#![` and apply to the parent of the attribute (like a file or a
    module). They are used e.g. for enabling unstable features:
    ```rust
#![feature(box_syntax)]
    ```
    They are also commonly used for allowing/denying lints.

    - Outer attributes start with `#[` and apply to the thing that directly follows the attribute.
    They are used e.g. for deriving traits on structs:
    ```rust
#[derive(Debug)]
struct MyStruct;
    ```
- `RsMetaItem` represents a part of an attribute. We can see that for the code above, we have a meta
item as a direct child of `RsInnerAttr` and this meta item contains a
[path]({% post_url 2020-08-23-contributing-1-nest-use-fix %}#paths) with the text `allow`, which is
the lint level. Inside this meta item there is another meta item that contains a path with the text
`unused_variables`, which is the name of the lint.

#### Creating patterns for lint attributes
It looks like we first have to match an attribute containing one of the lint levels
(`allow`/`warn`/`deny`/`forbid`) and then match a path containing (a prefix of) some lint name
inside the lint level.

Let's start with the pattern for the lint level. I created a set with the names of valid lint levels
and a pattern that matches them inside
[`RsPsiPattern`](https://github.com/intellij-rust/intellij-rust/blob/3b2080b973292a6f3aab6cce0e569991c2a166e3/src/main/kotlin/org/rust/lang/core/RsPsiPattern.kt),
which contains many useful patterns used by the plugin.
```kotlin
private val LINT_ATTRIBUTES: Set<String> = setOf(
    "allow",
    "warn",
    "deny",
    "forbid"
)

val lintAttributeMetaItem: PsiElementPattern.Capture<RsMetaItem> =
    psiElement<RsMetaItem>()
        .withParent(RsAttr::class.java)
        .with("lintAttributeCondition") { e -> e.name in LINT_ATTRIBUTES }
```
We want a meta item (`psiElement<RsMetaItem>()`) that is a direct child of an attribute
(`RsAttr::class.java`) and that has one of the four allowed names. I used
[`RsAttr`](https://github.com/intellij-rust/intellij-rust/blob/3b2080b973292a6f3aab6cce0e569991c2a166e3/src/main/kotlin/org/rust/lang/core/psi/ext/RsAttr.kt#L12)
as the parent, which is an interface implemented both by inner (`RsInnerAttr`) and outer (`RsOuterAttr`)
attributes. Therefore our pattern will match both attribute types, although inner attributes are
probably much more commonly used for changing lint levels.

Now that we can match attributes with lint levels, let's create our final element pattern inside
`RsRustcLintCompletionProvider`:
```kotlin
override val elementPattern: ElementPattern<out PsiElement> get() =
    PlatformPatterns.psiElement()
        .withLanguage(RsLanguage)
        .withParent(RsPath::class.java)
        .inside(
            psiElement<RsMetaItem>()
                .withSuperParent(2, RsPsiPattern.lintAttributeMetaItem)
        )
```
We want a PSI element that has a path as a parent and that is inside a meta item that is itself
a grandchild of an attribute with a lint level. This matches the location of the `unused_variables`
lint in the PSI tree that we have seen previously.

# Performing the first completion
Now that we can match the proper elements that should be completed, let's add support for some
basic completion. First, we will need to represent each lint:
```kotlin
data class Lint(val name: String, val isGroup: Boolean)
```
The `isGroup` property specifies whether the lint represents a lint group. Lints in `rustc` and
`clippy` are aggregated into groups so that you can enable or disable related lints easily. For
example, the `rustc` lint group `nonstandard-style` contains the lints `non-camel-case-types`,
`non-snake-case` and `non-upper-case-globals`. For our needs, a lint is not very different from a
lint group, but I thought that it would be nice to show a different icon for groups in the list of
completion entries.

Let's create a few lints manually for testing, [later](#generating-the-list-of-lints-automatically)
we will auto-generate them with a Gradle task.
```kotlin
val LINTS = listOf(
    Lint("unused", true),
    Lint("unused_variables", false),
    Lint("deprecated", false)
);
```

Now that we have some lints, let's go back to the `addCompletions` function:
```kotlin
override fun addCompletions(
    parameters: CompletionParameters,
    context: ProcessingContext,
    result: CompletionResultSet
) {
    ...
}
```
It takes three parameters:
- **parameters** contains information about the active completion, for example the file in which the
completion is being performed, and most importantly, the PSI element that is currently being completed.
- **context** is a helper map that can be used to pass some temporary information between completion
providers and element patterns. We will not use it.
- **result** is used to populate the completion entries that will be shown to the user. 

Let's go through our list of lints in the function and create a completion entry for each lint:
```kotlin
LINTS.forEach {
    addLintToCompletion(result, it)
}
```
I know, not very exciting. I put the actual implementation into a separate function, because we will
use it later in another place. This is the interesting stuff:
```kotlin
protected fun addLintToCompletion(
    result: CompletionResultSet,
    lint: Lint,
    completionText: String? = null
) {
    val text = completionText ?: lint.name
    val element = LookupElementBuilder.create(text)
        .withPresentableText(lint.name)
        .withIcon(getIcon(lint))
        .withPriority(getPriority(lint))
    result.addElement(element)
}
```
We use `LookupElementBuilder` to create a completion entry. The `create` method takes the actual
text that will be inserted into the file if the user chooses this completion entry. To specify how
will this entry present itself in the completion list, we use `withPresentableText` and give it the
name of the lint. In most cases, these two things will be the same, except for a single `clippy`
completion entry, which we will see in a moment. After that we simply choose an icon and a priority
for the entry. Entries with a higher priority will appear higher in the completion entry list.

The functions for getting an icon and priority are rather dull:
```kotlin
private fun getIcon(lint: Lint): Icon = if (lint.isGroup) {
        GROUP_ICON
    } else {
        RsIcons.ATTRIBUTE
    }

private fun getPriority(lint: Lint): Double = if (lint.isGroup) {
        GROUP_PRIORITY
    } else {
        LINT_PRIORITY
    }

companion object {
    private const val LINT_PRIORITY = 5.0
    private const val GROUP_PRIORITY = 4.0

    private val GROUP_ICON = RsIcons.ATTRIBUTE.multiple()
}
```
I used the plugin's icon for attributes, because I was too lazy to create a new one. For group lint
icons, I used the handy
[`multiple`](https://github.com/intellij-rust/intellij-rust/blob/3b2080b973292a6f3aab6cce0e569991c2a166e3/src/main/kotlin/org/rust/ide/icons/RsIcons.kt#L106)
function which takes an icon and adds its copy to itself with a slight offset, which should signify
that there are multiple items in the group. As for priority, I decided that group lints should have
smaller priority than normal lints[^priority].

[^priority]: This choice was rather arbitrary on my part. If you think it should be reversed, let me know.

After we create the entry, we add it to the `CompletionResultSet` to make it visible for the user.
And with these few lines of code, the first test passes!

Notice that we did not have to filter the set of offered lints based on what prefix has the user
already entered. We simply added all of them to the result set and let IntelliJ took care of the
rest. For example, if we add `unused`, `unused_variables` and `deprecated` to the result set and the
user writes `unus`, the IDE will only display the first two variants in the completion list. You can
see that in effect here:

{% include gif.html path="/assets/posts/contributing-5/completion-lint-basic" w="100%" %}

I used the `Ctrl + Space` keybind to display the completion list without writing anything.

Let's add a few more tests that check if our basic completion also works in outer attributes and
for other lint levels:
```kotlin
fun `test complete outer attribute`() = doSingleCompletion("""
    #[allow(unused_var/*caret*/)]
    fn foo() {}
""", """
    #[allow(unused_variables/*caret*/)]
    fn foo() {}
""")

fun `test warn`() = doSingleCompletion("""
    #![warn(unused_var/*caret*/)]
""", """
    #![warn(unused_variables/*caret*/)]
""")

fun `test deny`() = doSingleCompletion("""
    #![deny(unused_var/*caret*/)]
""", """
    #![deny(unused_variables/*caret*/)]
""")

fun `test forbid`() = doSingleCompletion("""
    #![forbid(unused_var/*caret*/)]
""", """
    #![forbid(unused_variables/*caret*/)]
""")
```
These tests all pass out of the box, thanks to our [lint element pattern](#creating-patterns-for-lint-attributes).

# Clippy lints
We are not done yet though, because we also need to complete `clippy` lints. These begin with the
`clippy::` prefix. So let's modify the completion logic a bit. On the "root" level (when there is
no `::` in the lint name), the completion list will contain `rustc` lints and also a special `clippy`
entry that will insert the text `clippy::` when selected[^different]. If the lint name contains
the `clippy::` prefix, we will only offer `clippy` lints (`rustc` lints will be ignored here).

[^different]:
    This is an example of a completion entry that inserts different text than what it displays
    in the completion entry list, as mentioned before.

If that sounded confusing, check out the following tests, which should make it clear:
```kotlin
fun `test complete clippy group at root`() = doSingleCompletion("""
    #[allow(clip/*caret*/)]
    fn foo() {}
""", """
    #[allow(clippy::/*caret*/)]
    fn foo() {}
""")

fun `test do not complete clippy lints at root`()
    = checkNotContainsCompletion("borrow_interior_mutable_const", """
    #[allow(borr/*caret*/)]
    fn foo() {}
""")

fun `test complete inside clippy`() = checkContainsCompletion(
    listOf("identity_op", "flat_map_identity", "map_identity"), """
    #[allow(clippy::ident/*caret*/)]
    fn foo() {}
""")
```
We want to complete the special `clippy` entry at the root level, do not offer `clippy` lints at
the root level and offer `clippy` lints with the `clippy::` prefix. The `checkNotContainsCompletion`
function can be used to assert that a specific completion will not be offered, while
`checkContainsCompletion` checks that all of the passed completions will be offered.

To clean things up a bit, let's create a separate provider for `rustc` and for `clippy` lints.
First, we will turn `RsRustcLintCompletionProvider` into a shared base class for these two providers:
```kotlin
abstract class RsLintCompletionProvider : RsCompletionProvider() {
    protected open val prefix: String = ""
    protected abstract val lints: List<Lint>
```
The provider will require its derived classes to implement two things -- a list of lints that
should be completed and a lint name (path) prefix. If the currently entered lint name will not have
the corresponding prefix, the lints of the provider will not be offered:
```kotlin
override fun addCompletions(
    parameters: CompletionParameters,
    context: ProcessingContext,
    result: CompletionResultSet
) {
    val path = parameters.position.parentOfType<RsPath>() ?: return
    val currentPrefix = getPathPrefix(path)
    if (currentPrefix != prefix) return

    lints.forEach {
        addLintToCompletion(result, it)
    }
}
```
We get the element that is participating in the completion (`parameters.position`), find its parent
path, calculate its prefix and if it matches the prefix of our provider, we add its completions to
the result set. The path prefix is calculated with the following method:
```kotlin
protected fun getPathPrefix(path: RsPath): String {
    val qualifier = path.qualifier ?: return path.coloncolon?.text ?: ""
    return "${getPathPrefix(qualifier)}${qualifier.referenceName.orEmpty()}::"
}
```
To understand this function, we'll have to understand paths a bit more. Paths are represented in the
plugin hierarchically, for example `foo::bar` is represented with this PSI:
```
RsPath
    RsPath
        PsiElement: foo
    PsiElement: ::
    PsiElement: bar
```
The `qualifier` of the `bar` path is `foo`. This is exactly the prefix that we are interested in.
If there is no qualifier, we return an empty string[^coloncolon]. This will represent the "root level"
path that has no prefix. If there is a qualifier, we recurse into the same method for the qualifier
and append the name of the qualifier to the result. For example, for the path `unused`, this function
will return an empty prefix. For the path `clippy::unus`, this function will return the prefix
`clippy::`. We will use this to distinguish situations where we should complete `rustc` vs
`clippy` lints.

[^coloncolon]:
    If the path starts with `::`, we have to return `::` instead of an empty string. Otherwise we
    would complete `rustc` lints even if the user wrote e.g. `#![allow(::)]`, which is incorrect.
    This was found out by [Undin](https://github.com/Undin) in this
    [issue](https://github.com/intellij-rust/intellij-rust/issues/6311) and I then fixed it in a
    follow-up [PR](https://github.com/intellij-rust/intellij-rust/pull/6313).

Now that we have the base class, let's create a class for `rustc` lints:
```kotlin
object RsRustcLintCompletionProvider : RsLintCompletionProvider() {
    override val lints: List<Lint> = RUSTC_LINTS
}
```
This one is pretty simple. Its prefix should be an empty string (which is the default), so we just
specify the list of lints. We will define these lints in a moment.

Then we create a class for `clippy` lints:
```kotlin
object RsClippyLintCompletionProvider : RsLintCompletionProvider() {
    override val prefix: String = "clippy::"
    override val lints: List<Lint> = CLIPPY_LINTS

    override fun addCompletions(
        parameters: CompletionParameters,
        context: ProcessingContext,
        result: CompletionResultSet
    ) {
        super.addCompletions(parameters, context, result)

        val path = parameters.position.parentOfType<RsPath>() ?: return
        if (getPathPrefix(path).isEmpty()) {
            addLintToCompletion(result, Lint("clippy", true), prefix)
        }
    }
}
```
In addition to using a different list of lints, we also specify the prefix (`clippy::`) and override
the `addCompletions` function. If we find that the current prefix is empty (i.e. we are completing
`rustc` lints at the top level), we add a "fake" lint to the completion entry. It will be displayed
with the name `clippy`, it will insert the string `clippy::` when selected and it will act like a
group[^clippy-group].

[^clippy-group]: There are a lot of `clippy` lints, so this made sense to me.

And finally, we add both of these new providers to `RsCompletionContributor`:
```kotlin
class RsCompletionContributor : CompletionContributor() {
    init {
        ...
        extend(CompletionType.BASIC, RsClippyLintCompletionProvider)
        extend(CompletionType.BASIC, RsRustcLintCompletionProvider)
    }
```

With these changes, we can now complete both `rustc` and `clippy` lints! :tada:

{% include gif.html path="/assets/posts/contributing-5/completion-lint-clippy" w="100%" %}

There is only one thing left to do -- generate the list of lints automatically!

# Generating the list of lints automatically
Originally, I hard-coded the list of lints into the source code. But [Undin](https://github.com/Undin)
[pointed out](https://github.com/intellij-rust/intellij-rust/pull/5646#discussion_r495045350) to me
that it would be nice to automatically fetch them from `rustc` and `clippy`, so that they can be
updated easily in future versions of the plugin.

The general idea is to create a (Gradle) task that will fetch the current lint list and generate
two Kotlin files (one for `rustc` and one for `clippy`), each with the corresponding lists stored in
Kotlin `List`. Using this task, a plugin contributor can easily refresh the lint list with a single
command from time to time, to keep the plugin actual.

The plugin already uses a similar approach for downloading and code generating
[compiler features](https://github.com/intellij-rust/intellij-rust/blob/3b2080b973292a6f3aab6cce0e569991c2a166e3/build.gradle.kts#L477)
and [Cargo options](https://github.com/intellij-rust/intellij-rust/blob/3b2080b973292a6f3aab6cce0e569991c2a166e3/build.gradle.kts#L502).
These things (same as lints) change regularly, so it is useful to have the option to regenerate them
with a single command. On the other hand, they do not change so often and so much to justify more
complex updating methods -- for example updating them dynamically during plugin initialization on the
user's machine.

# Creating a Python script to download lints
In order to create this task, we need a way of programmatically getting the set of lints of both
`rustc` and `clippy`. I decided to write a Python script for this, as I found that implementing this
in Kotlin inside the Gradle task file ([`build.gradle.kts`](https://github.com/intellij-rust/intellij-rust/blob/3b2080b973292a6f3aab6cce0e569991c2a166e3/build.gradle.kts))
it a bit cumbersome. I created the script at `scripts/fetch_lints.py`.

Let's start with `rustc` lints. Luckily, `rustc` provides a command that prints out the list of
all lints and lint groups:
```bash
$ rustc -W help
```
What's not so nice is that the output is not exactly "machine readable" :sweat_smile::
```
Available lint options:
    -W <foo>           Warn about <foo>
    -A <foo>           Allow <foo>
    -D <foo>           Deny <foo>
    -F <foo>           Forbid <foo> (deny <foo> and all attempts to override)

Lint checks provided by rustc:

                                   name  default  meaning
                                   ----  -------  -------
 absolute-paths-not-starting-with-crate  allow    fully qualified paths that start with...
                   anonymous-parameters  allow    detects anonymous parameters
                           box-pointers  allow    use of owned (Box type) heap memory
                                            ...

Lint groups provided by rustc:
                       name  sub-lints
                       ----  ---------
                   warnings  all lints that are set to issue warnings
        future-incompatible  keyword-idents, anonymous-parameters, ...
                                            ...
```
Do not despair though, we should be able to tame this output with a little bit of regex-fu in Python:
```python
class LintParsingMode:
    Start = 0
    ParsingLints = 1
    LintsParsed = 2
    ParsingGroups = 3


def get_rustc_lints():
    result = subprocess.run(["rustc", "-W", "help"],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            stdin=subprocess.DEVNULL,
                            check=True)
    output = result.stdout.decode()

    def normalize(name):
        return name.replace("-", "_")

    lint_regex = re.compile(r"^([a-z0-9]+-)*[a-z0-9]+$")
    parsing = LintParsingMode.Start
    lints = []
    for line in output.splitlines():
        line_parts = [part.strip() for part in line.strip().split()]
        if len(line_parts) == 0:
            if parsing == LintParsingMode.ParsingLints:
                parsing = LintParsingMode.LintsParsed
            continue
        if "----" in line_parts[0]:
            if parsing == LintParsingMode.Start:
                parsing = LintParsingMode.ParsingLints
            elif parsing == LintParsingMode.LintsParsed:
                parsing = LintParsingMode.ParsingGroups
            continue
        if parsing == LintParsingMode.ParsingLints and lint_regex.match(line_parts[0]):
            lints.append((normalize(line_parts[0]), False))
        if parsing == LintParsingMode.ParsingGroups and lint_regex.match(line_parts[0]):
            lints.append((normalize(line_parts[0]), True))
    return lints
```
First we run `rustc` and capture its output. Then we go through it line by line and parse the
individual lints and lint groups. The code is pretty fragile and it will probably break in the next
version of `rustc` :laughing:. So I won't explain it in detail.

There is no corresponding command to get all lints for `clippy`. After exploring a few options, I
decided to clone the `clippy` repository using `git` and use one of its Python scripts which can
parse the lints out of the `clippy` source code[^whypython]. This worked, but it was a bit cumbersome.

[^whypython]: This was also one of the reasons why I decided to use Python to write the lint fetching script.

A few days after my PR with lint completion got merged, I noticed that
[Rust Analyzer](https://github.com/rust-analyzer/rust-analyzer) also
[added](https://github.com/rust-analyzer/rust-analyzer/pull/6109) lint completion (what a concidence!
:laughing:). I noticed that they found a [URL](http://rust-lang.github.io/rust-clippy/master/lints.json)
which contains a JSON object with all of the `clippy` lints, which was exactly what I needed. So
almost immediately after my PR got merged I created [another one](https://github.com/intellij-rust/intellij-rust/pull/6305)
that removes the repository cloning and instead just downloads the lints from the magic URL[^urllib]:
```python
from urllib import request

def get_clippy_lints():
    data = request.urlopen(
        "http://rust-lang.github.io/rust-clippy/master/lints.json"
    )
    clippy_lints = json.loads(data.read())

    groups = set()
    lints = []
    for lint in clippy_lints:
        lints.append((lint["id"], False))
        groups.add(lint["group"])
    return lints + [(group, True) for group in groups]
```

[^urllib]:
    I use `urllib` here instead of the more popular `requests` library to avoid a third-party
    dependency. Normally using `requests` wouldn't be a problem, but since the Python script will
    be used from a Gradle task, it could be a bit cumbersome to setup Gradle to use e.g. a Python
    virtual environment. Once again, a great [review](https://github.com/intellij-rust/intellij-rust/pull/6305#discussion_r513365167)
    by [Undin](https://github.com/Undin), thanks!

And finally, when the script is executed, we call both of the functions, merge the lints together
with a flag that specifies their type (`rustc`/`clippy`) and output them as JSON:
```python
if __name__ == "__main__":
    output = [{"name": l[0], "group": l[1], "rustc": True} for l in get_rustc_lints()] + \
             [{"name": l[0], "group": l[1], "rustc": False} for l in get_clippy_lints()]

    print(json.dumps(output))
```

# Using the script to generate code with the lints
With the Python script done, we can create a Gradle task inside `build.gradle.kts`:
```kotlin
task("updateLints") {
    doLast {
        val lints = JsonSlurper().parseText("python3 fetch_lints.py"
            .execute("scripts", print = false)) as List<Map<String, *>>

        fun Map<String, *>.isGroup(): Boolean = get("group") as Boolean
        fun Map<String, *>.isRustcLint(): Boolean = get("rustc") as Boolean
        fun Map<String, *>.getName(): String = get("name") as String

        writeLints(
            "src/main/kotlin/org/rust/lang/core/completion/lint/RustcLints.kt",
            lints.filter { it.isRustcLint() },
            "RUSTC_LINTS"
        )
        writeLints(
            "src/main/kotlin/org/rust/lang/core/completion/lint/ClippyLints.kt",
            lints.filter { !it.isRustcLint() },
            "CLIPPY_LINTS"
        )
    }
}
```
We run the Python script and parse its output as JSON. Then we create a `RUSTC_LINTS` variable with
the `rustc` lints, write it to the `RustcLints.kt` file and do a similar thing for the `clippy` lints.

The `writeLints` function creates the content of these two files:
```kotlin
fun writeLints(
    path: String,
    lints: List<Map<String, *>>,
    variableName: String
) {
    val file = File(path)
    val items = lints.sortedWith(
        compareBy({ !it.isGroup() }, { it.getName() })
    ).joinToString(
        separator = ",\n    "
    ) {
        val name = it.getName()
        val isGroup = it.isGroup()
        "Lint(\"$name\", $isGroup)"
    }
    file.bufferedWriter().use {
        it.writeln("""
/*
* Use of this source code is governed by the MIT license that can be
* found in the LICENSE file.
*/

package org.rust.lang.core.completion.lint

val $variableName: List<Lint> = listOf(
$items
)
""".trim())
    }
}
```
It sorts the lints so that groups are at the top, creates a `Lint` instance for each lint and writes
each lint on a single line into the target file. We also can't forget to include the MIT license
header :smile:.

# Wrapping it up
And that's it folks! Even though it was a bit complicated to automatically generate the lints, the
core logic of the completion consists of just a few lines of code, which is pretty nice for such a
useful feature.

The lint completion was introduced in this [PR](https://github.com/intellij-rust/intellij-rust/pull/5646).
The review process was pretty standard, even though the implementation was rewritten from scratch
due to some well-deserved refactoring and the automatic lint generation, which was originally written
purely in Kotlin and not in Python. It took a few months to merge it.

If you're reading this, thanks for sticking with me until the end of this post. If you have any
comments, let me know on [Reddit](TODO).

# Footnotes
