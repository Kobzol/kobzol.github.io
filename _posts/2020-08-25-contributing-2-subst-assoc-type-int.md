---
layout: post
title:  "Contributing to Intellij-Rust #2: Intention to substitute an associated type"
date:   2020-08-25 16:03:00 +0200
categories: rust intellij
--- 
This post is part of a [series]({% post_url 2020-08-23-contributing-0-setup %}) in which I describe
my contributions to the [IntelliJ Rust](https://github.com/intellij-rust/intellij-rust) plugin.

- Previous post: [#1 Fixing a simple bug in Nest Use intention]({% post_url 2020-08-23-contributing-1-nest-use-fix %})
- Next post: [#3 Quick fix to attach file to a module]({% post_url 2020-09-04-contributing-3-quick-fix-attach-file-to-mod %})

In this post we'll build a complete intention from scratch, based on one of my recent PRs.
It will be a relatively simple intention because there are a lot of concepts that need to be explained
along the way. In later posts I want to explain more complicated features, but first we need to understand
the basic building blocks of IntelliJ APIs and the general concepts of the plugin. Therefore a lot of
this post will be about explaining useful tips and tricks for writing intentions and working with the
plugin in general.

You can find the original PR that I will go through [here](https://github.com/intellij-rust/intellij-rust/pull/5643) (spoiler alert!).

# Finding an issue
We will be solving [this issue](https://github.com/intellij-rust/intellij-rust/issues/2766) created by
[matklad](https://github.com/matklad) two years ago. He suggested to create an intention that would
substitute (or "inline") an associated type. Here is an example of how it should work:

```rust
impl Iterator for Foo {
    type Item = i32;
    fn next(&mut self) -> Option<<Self as Iterator>::Item/*caret*/> {
        unimplemented!()
    }
}
// ^ turns into v
impl Iterator for Foo {
    type Item = i32;
    fn next(&mut self) -> Option<i32> {
        unimplemented!()
    }
}
```
If you invoke it on a specific use of an associated type, it should replace (inline) the associated type
with its actual value. Later we will see that the same intention will be able to also inline type aliases
because they are represented in the plugin in the same way as associated types.

# Associated types
[Associated types](https://doc.rust-lang.org/stable/rust-by-example/generics/assoc_items/types.html)
is a Rust feature that allows you to declare one or more type placeholders in a trait and use them in the signature
of the trait's methods. Each implementor of the trait then has to choose a concrete type for each type placeholder.
The first place where Rust beginners meet an associated type is usually in the ubiquitous [Iterator](https://doc.rust-lang.org/std/iter/trait.Iterator.html)
trait. I won't go into more detail here, as it's out of scope for this post, but you can find more
information about associated types for example [here](https://doc.rust-lang.org/book/ch19-03-advanced-traits.html).

# Intentions
I already covered this in the last post, but to recap: intention is an action that can be invoked
by the user over some piece of code. If you press `Alt + Enter`, a list of available intentions is
displayed (based on where your caret is located). You can then select some intention from the list and
invoke it. Intentions typically operate in a very localized scope. Larger scale actions that can potentially
change each file in your project are usually handled by refactorings (we will implement one of those in a
later post). For example, the plugin contains intentions that add an `impl` block for a struct, add
an `else` branch to an `if` statement, change a reference to be mutable or nest use statements (we have seen this one
in the [previous post]({% post_url 2020-08-23-contributing-1-nest-use-fix %})). Currently there are about
50 different intentions in the plugin. Now let's see how we can add a new one.

# Bootstrapping an intention
Naming things is the basis of programming, so first we should come up with a name.
I decided to name the intention `SubstituteAssociatedTypeIntention`. I know, stunning :) Now that we
have a name, where should we create a file for the intention? If we search for `*Intention*`, we will
get back a lot of files in the `src/main/kotlin/org/rust/ide/intentions` directory, which looks like
a reasonable place where intentions might live, so let's create a new file named
`SubstituteAssociatedTypeIntention.kt` inside that directory.

Hmm, but what should we put into the file? How does an intention even look like? Well, there are already
over 50 different intentions, so why not copy one of them and modify it? I looked through the intentions
to find some short one, for example `AddElseIntention`, which adds an `else` branch to an `if` statement:

```kotlin
class AddElseIntention : RsElementBaseIntentionAction<RsIfExpr>() {
    override fun getText() = "Add else branch to this if statement"
    override fun getFamilyName(): String = text

    override fun findApplicableContext(
        project: Project,
        editor: Editor,
        element: PsiElement
    ): RsIfExpr? {
        ...
    }

    override fun invoke(project: Project, editor: Editor, ctx: RsIfExpr) {
        ...
    }
}
```
Right, so an intention should inherit from `RsElementBaseIntentionAction`, parametrized with a generic
`Context` argument, which states the type of an object that will be passed from `findApplicableContext` to `invoke`.
I have talked about context and these two methods already in the [previous post]({% post_url 2020-08-23-contributing-1-nest-use-fix %}#understanding-the-existing-code),
but to recap, each intention needs to implement two methods:

- `findApplicableContext` - when you press `Alt + Enter` over some piece of code, the plugin iterates
all intentions and calls this method on each one of them. If the method returns some non-null *context*,
the intention will be offered in an intention list to the user. If the method returns null, the intention
will not be offered.
- `invoke` - if the user selects an intention to be executed from the intention list, this method will be
called to actually perform the intention. It will receive the *context* from `findApplicableContext`
as one of its arguments.

**Aside**: How did I know that these are the important methods and what are they for?
Just click on the upward pointing arrow next to the method to go to the base method in the parent interface,
as it usually has a documentation comment. Intentions are also well documented on the `RsElementBaseIntentionAction` class.
Sadly, sometimes documentation is missing or it's not very descriptive. In such cases, you can try
to search through the IntelliJ [SDK documentation](https://jetbrains.org/intellij/sdk/docs/),
although that's also sometimes pretty terse. If you want to do something, but do not know which IntelliJ API
to use, a useful tactic that often helps is to check the source code of other IntelliJ plugins or IDEs
and search for a similar feature. I recommend to check out the source code of the [Kotlin plugin](https://github.com/JetBrains/kotlin/tree/master/idea)
or the free Java [IntelliJ community edition](https://github.com/JetBrains/intellij-community).

So we will have to implement these two methods for our intention. There are also two additional methods
that must be implemented: `getText` and `getFamilyName`. `getText` Should return a string that will be displayed
as the intention's text in the intention list after the user presses `Alt + Enter`. `getFamilyName` contains
a family name of the intention. Intentions with the same family name can be disabled/enabled in bulk.
Unless the intention has a specialized text based on where it is invoked, these two methods
usually return the same string (as is the case in `AddElseIntention`).

Now that we are wiser, let's create a skeleton of `SubstituteAssociatedTypeIntention` with a reasonable
`text`:

```kotlin
class SubstituteAssociatedTypeIntention
    : RsElementBaseIntentionAction<SubstituteAssociatedTypeIntention.Context>() {
    override fun getText() = "Substitute associated type"
    override fun getFamilyName() = text

    class Context

    override fun findApplicableContext(
        project: Project,
        editor: Editor,
        element: PsiElement
    ): Context? {
        return null
    }

    override fun invoke(project: Project, editor: Editor, ctx: Context) {}
}
```
We don't know what the `Context` type will be, so I just created an empty inner class, we'll change
it later. `findApplicableContext` currently returns `null` anyway, so the intention will never even
be offered!

If you use IDEA, you might notice that there is a warning around the intention's name with the text
`Intention does not have a description`. Each intention is required to have a short description in
HTML format, along with two template files with example code before and after applying the intention to it.
This description and the templates can then be displayed in `Settings`, where you can find a list of all
intentions for a given language. The intention descriptions are located in `src/main/resources/intentionDescriptions`,
each intention has a separate directory named after itself.

To fix this warning, let's copy the description of an existing intention, for example our favourite `AddElseIntention`.
The directory contains three files:
- `description.html` - a short description of the intention
- `before.rs.template` - Rust code sample on which the intention will be applied
- `after.rs.template` - Rust code sample showing how the code looks after the intention runs

Note that instead of `/*caret*/`, the templates use `<spot>` to mark the caret position.
Now we just have to provide some short text describing what our intention does and modify the templates.
I used the code from the original issue for the templates.

> If we forgot to include a description or a template, CI tests would later loudly complain about their absence.
> **EDIT**: turns out that this wasn't the case, as the tests for missing intention descriptions were.. well, missing :smile:.
> But this is now resolved since [this PR](https://github.com/intellij-rust/intellij-rust/pull/6042) got merged.

Now that we have an intention skeleton and its description, let's write the first test for it!

# Writing a failing test
Again, we first have to deal with naming and location of the test. Naming is pretty simple - just
append `Test` after the name of the intention. But where should the test live? Let's use
the same tactic as before - look for existing intention tests. If we open `AddElseIntention` and press
`Ctrl + Shift + T` on it, it will navigate us to its corresponding test, the unexpectedly named 
`AddElseIntentionTest`, located in `src/test/kotlin/org/rust/ide/intentions/AddElseIntentionTest.kt`.
It looks something like this:

```kotlin
class AddElseIntentionTest : RsIntentionTestBase(AddElseIntention()) {
    fun test1() = doUnavailableTest("""
        fn main() {
            42/*caret*/;
        }
    """)

    fun `test simple`() = doAvailableTest("""
        fn foo(a: i32, b: i32) {
            if a == b {
                println!("Equally");/*caret*/
            }
        }
    """, """
        fn foo(a: i32, b: i32) {
            if a == b {
                println!("Equally");
            } else {/*caret*/}
        }
    """)
}
```
This shows us three things:
- Intention tests should inherit from `RsIntentionTestBase` and they should pass an instance of the
tested intention to it.
- We can use the `doUnavailableTest` method to check that the intention is not offered at the specified
caret location. This basically checks that the `findApplicableContext` method of the intention is working properly.
- We can use the `doAvailableTest` method to check that the intention is offered at the specified
caret location and that the code looks as expected after the intention is executed (the first parameter
of the method contains the original code and the second parameter contains
the expected output after the intention is invoked on the original code). The original code has to include a
`/*caret*/` to specify where should the intention be invoked. The expected result code can also include a
caret marker to test where has the caret moved after the intention is invoked, although it is optional.

Now that we know the basic structure, let's create a test class named `SubstituteAssociatedTypeIntentionTest`
and let's write a first test:
```kotlin
class SubstituteAssociatedTypeIntentionTest
    : RsIntentionTestBase(SubstituteAssociatedTypeIntention()) {
fun `test associated type in type context`() = doAvailableTest("""
    trait Trait {
        type Item;
        fn foo(&self) -> Self::Item;
    }
    impl Trait for () {
        type Item = i32;
        fn foo(&self) -> <Self as Trait>::/*caret*/Item { 0 }
    }
""", """
    trait Trait {
        type Item;
        fn foo(&self) -> Self::Item;
    }
    impl Trait for () {
        type Item = i32;
        fn foo(&self) -> i32 { 0 }
    }
""")
}
```

> The plugin names tests with spaces in backticks: `test associated type in type context`, so better
get used to it (I personally quite like it). `doAvailableTest` also calls `trimIndent()` on both of the
passed codes, so don't worry about the indentation.

# Deciding when to offer the intention
Now that we have a test that we can debug, let's start writing the intention. First we have to implement
the `findApplicableContext` method and decide what *context* type it will return. Let's go through the
signature of the method:
```kotlin
override fun findApplicableContext(
    project: Project,
    editor: Editor,
    element: PsiElement
): Context? {}
```
Here is a description of its parameters:
- `project` represents the opened IntelliJ project. This is a very important object from which you can access
everything from the current project - its files, configuration, the `Rust` crate/workspace, etc. Conversely,
without it you do not have access to pretty much anything, so it's often passed as a parameter to various
methods that you need to implement.
- `editor` represents the opened editor tab with source code in which `Alt + Enter` was pressed. Through
it you can for example query and change the caret position and you can also access the file that is currently
opened in the editor.
- `element` represents the PSI element located at the caret when `Alt + Enter` was pressed. This will be the
parameter that interests us the most, because based on it we have to decide if the intention should be offered.

> The basics of PSI have been explained in the [previous post]({% post_url 2020-08-23-contributing-1-nest-use-fix %}#psi).

The intention should be available if `element` **resolves** to an associated type. But what does that mean?

#### Name resolution
In simple terms, `A` resolves to `B` if the caret moves to `B` when you `Ctrl + <click>` on `A`. In such
case we can say that `A` has a reference to `B` and it can **resolve** it to find `B`. However, do not
confuse this term with Rust references like `&x` or `&mut x`. In this context a reference from `A` to
`B` means that `B` is a declaration of something (module, local variable, structure) and
`A` is some usage of `B` that refers to it. An example to make this clear:
```rust
struct S {
    a: u32
}
fn foo(s: S) {
    let x = s.a;
    let y = x + 1;
    let z = std::vec::Vec::<u32>::new();
}
```

- `S` in `s: S` resolves to the struct `struct S`
- `s` in `s.a` resolves to the parameter `s: S`
- `x` in `x + 1` resolves to the local variable `let x`
- `std` in `std::vec::Vec::<u32>::new()` resolves to the `std` module
- `std::vec::Vec` in `std::vec::Vec::<u32>::new()` resolves to the `Vec` struct
- `std::vec::Vec::<u32>::new()` in `std::vec::Vec::<u32>::new()` resolves to the associated method `new` of `Vec`

The system that resolves references from usages of items to their declarations is usually called
**Name resolution** and it is implemented both by `rustc` and the IntelliJ APIs, where it is a first-class
concept. 

So, how do we recognize if `element` is something that resolves to an associated type? In the example
above, maybe you have noticed that all of the references had a similar look and feel: `S`, `s`, `x`,
`std::vec::Vec`, etc. If you [paid attention]({% post_url 2020-08-23-contributing-1-nest-use-fix %}#paths)
in the previous post, this should look familiar - they are all **paths**! If we put a caret on `x`
in the above example and use the `PsiViewer` plugin to examine the PSI, we quickly find out that paths
are represented in the plugin by the `RsPath` class, which (like all PSI elements) inherits from `PsiElement`.

Therefore, we first have to find out if `element` is a `RsPath`. You might be tempted to simply perform
a (safe) cast: `element as? RsPath`, but it is not that simple. It might happen that the caret was located at
an element that is a child of a path (the PSI elements form a tree), and in such case the cast would not succeed.
For example in `std:/*caret*/:vec::Vec<u32>`, the `element` would be `::`, a simple text token that is a child
of the path that we want to resolve.

> Paths are represented hierarchically; in `std::vec::Vec`: `std` is actually a path that is a child
of the `std::vec` path, which is a child of `std::vec::Vec` path, etc. We will see this in action in future
posts, but it's not important for now.

Luckily, the IntelliJ PSI offers a large set of APIs for navigating the PSI tree. You can use them to
search for a parent of a specific PSI type:
```kotlin
val path = element.parentOfType<RsPath>() ?: return null
```
If `element` has some parent that is a path, it will be returned, otherwise we return `null` and
the intention will not be offered.

> There are multiple ways of asking for parents, you can ask for an ancestor, a parent or a context.
To be honest, I do not understand the differences in detail, but so far using parent lookup was usually
the right choice by default.

Now that we have a path, we have to resolve it and check if the result is an associated type. How do you
resolve a path? By implementing a deeply complex logic that iterates over scopes and tries to match items
in each scope to the name/path that is being resolved according to the rules of Rust™. Luckily, we do not have
to implement it by ourselves, as the plugin has an implementation of name resolution. Paths inherit from
`RsReferenceElement`, which provides them with a `reference` attribute that has a `resolve` method which does 
the job. Associated types are represented by `RsTypeAlias` (you can again find this with `PsiViewer`),
so let's use something like this:
```kotlin
val typeAlias = path.reference?.resolve() as? RsTypeAlias ?: return null
```
If the reference cannot be resolved or if it does not resolve to an associated type, return `null` to
disable the intention.

The last thing to check is whether the associated type has some type actually assigned to it. If not,
we do not have anything to substitute, so the intention should not be offered. Let's access the `typeReference`
attribute, which is of type `RsTypeReference` (more on that later):
```kotlin
val type = typeAlias.typeReference ?: return null
```
How did I know that `typeReference` is the correct attribute that contains the assigned type? I opened
`RsTypeAlias` to see what attributes it has, then put a breakpoint in this method to examine the `typeAlias`
variable to see which of its attributes contains something that looks like the assigned type. If you have
some `PsiElement` and you're not sure what is it, read its `text` attribute, which contains the original
raw source text. Then it's usually easy to see what the element represents. In this case:
```rust
type A = u32;
```
`typeAlias.typeReference` would represent the type `u32`.

Now we have a path that resolves to an associated type and the concrete type that should be substituted.
Since we will need those things for the actual functionality of the intention, let's return those two things
as *context* to have them available in the `invoke` method.
This is the final code of the `findApplicableContext` method along with the modified `Context` class:
```kotlin
data class Context(val path: RsPath,
                   val typeAliasReference: RsTypeReference)

override fun findApplicableContext(
    project: Project,
    editor: Editor,
    element: PsiElement
): Context? {
    val path = element.parentOfType<RsPath>() ?: return null
    val typeAlias = path.reference?.resolve() as? RsTypeAlias ?: return null
    val type = typeAlias.typeReference ?: return null
    return Context(path, type)
}
```

> Why do we store `typeAliasReference` in `Context` when we can get it from the `path`? Simply to reduce
code and error handling in the `invoke` method.

# Implementing the `invoke` method
As a reminder, here is the signature of the `invoke` method:
```kotlin
override fun invoke(project: Project, editor: Editor, ctx: Context)
```
We already know `project` and `editor` and `ctx` is exactly the thing that we have returned
from `findApplicableContext`. Easy. Now we just need to replace `ctx.path` with the type
stored in the context. In theory, we could just replace it textually, i.e. literally take the string
containing the `text` of the path and replace it with `text` of the type. However, this is usually
not how it should be done. The proper solution is to manipulate the PSI tree and not the raw text.

There is a very useful utility class for this, `RsPsiFactory`. It allows you to build PSI nodes from
other nodes or from raw strings. We need to create a new path that will represent the type that we are
substituting and then replace the original path with the newly created path.

First, how do we get the type that we want to substitute? In `Context`, we have a `RsTypeReference`,
which represents an element that refers to a Rust type. It has a `type` attribute, which returns the actual
type it's referencing. Note that the classes representing Rust types inherit from the `Ty` class, not from
`PsiElement`, as they live completely outside of the PSI world. `RsTypeReference` simply maps PSI type elements to `Ty`
objects (this mapping is implemented by the **type inference** subsystem).

How do we create a path from a type? `RsPsiFactory` has a method called `tryCreatePath` that takes a string
and tries to build a PSI `RsPath` object out of it. But we don't have a string yet, we have a type, so
first we have to convert it to a string. There is a very customizable type rendering API for this,
you can use it via the `renderInsertionSafe` method, which renders a type to a string in such a way
that it is safe to be inserted into Rust code. Let's combine all of this in `invoke`:
```kotlin
val factory = RsPsiFactory(project)
val typeRef = ctx.typeAliasReference

// if the path couldn't be parsed, do not continue
val createdPath = factory.tryCreatePath(
    typeRef.type.renderInsertionSafe()
) ?: return 
```
Now we just replace the original path with the new one using the `replace` method:
```kotlin
ctx.path.replace(createdPath)
```
And that's it! If we try to run the first test, it passes :rocket:. We have a basic implementation of the
intention in ~15 lines, not bad. Of course in a while we'll see that the implementation will need to grow
somewhat once we'll have to account for the nasty edge cases :)

By the way, have you noticed that the element representing an associated type is called `RsTypeAlias`?
That is because associated types and type aliases are basically the same thing[^1], with the same syntax (`type X = Y`).
The only difference is that associated types are associated with a trait, but that does not really matter to
our intention. Therefore our intention should *just* work also for substituting/inlining type aliases out
of the box!

[^1]: At least from the perspective of PSI.

# Adding more tests
Now that we have a basic implementation of the intention, we should add tests for various edge cases
that could happen. I will just post short snippets and not the whole test methods, since they are quite
repetitive.

What happens if the type has a generic parameter?
```rust
impl<T> Trait<T> for () {
    type Item = S<T>;
    fn foo(&self, item: Self::/*caret*/Item) -> T {}
    // turns into
    fn foo(&self, item: S<T>) -> T {}
}
```
Awesome, both the type rendering and path creation handled the generic type, and we have another
passing test!

What if the type is used in an expression context, i.e. a function call?
```rust
impl Trait for () {
    type Item = S;
    fn foo(&self) {
        <Self as Trait>::/*caret*/Item::bar();
    }
    // turns into
    fn foo(&self) {
        S::bar();
    }
}
```
Also works, nice.

What if it has a generic parameter AND it is used in an expression context? 
```rust
impl Trait for () {
    type Item = S<u32>;
    fn foo(&self) {
        <Self as Trait>::/*caret*/Item::bar();
    }
    // turns into
    fn foo(&self) {
        S<u32>::bar();
    }
}
```
Now although this may look correct, this is in fact not valid Rust code. In an expression context,
the `<` in `S<u32>` is parsed as a comparison operator, so we have to use the turbofish syntax:
```rust
S::<u32>::bar();
```

The test will actually fail because the inserted path could not even be parsed by the plugin.
So how do we handle this in the intention?

We need to find out if the path that we are replacing is in a type or expression context. If you compare
paths used in a type context (e.g. `fn foo(s: <Path>)`) and in an expression context (i.e. `let a = <Path>::new()`)
with the `PsiViewer`, you'll notice that in type contexts the paths have a `RsTypeReference`[^2] as a PSI parent,
which we have already met in `findApplicableContext`. So let's use this knowledge to check if we are
indeed inside a type context or not:
```kotlin
val isTypeContext = ctx.path.parentOfType<RsTypeReference>() != null
```
After that, we have to check if the created path has any generic arguments (if not, we don't need to add
turbofish). You can find that by examining the `typeArgumentList` attribute of a path. If we find that we are indeed
inside expression context and that the created path has some generic arguments, we'll just insert `::` in the
middle of it like it's no big deal:
```kotlin
// identifier: PSI element with the path segment name
// endOffsetInParent: offset where the identifier ends, relative to its parent 
val end = createdPath.identifier?.endOffsetInParent ?: 0
val pathText = createdPath.text

// I'm not even sorry for this
val newPath = pathText.substring(0, end) + "::" + pathText.substring(end)
```
For example in `S<u32>`, the `identifier` is `S` and it ends at offset `1`. Therefore this code will
insert `::` at position `1` and change this path to `S::<u32>`.

With this change, the test passes. This is how the `invoke` method looks now:
```kotlin
val factory = RsPsiFactory(project)
val typeRef = ctx.typeAliasReference
val isTypeContext = ctx.path.parentOfType<RsTypeReference>() != null
val createdPath = factory.tryCreatePath(typeRef.type.renderInsertionSafe())
    ?: return

// S<u32> -> S::<u32> in expression context
val insertedPath: RsPath = if (!isTypeContext &&
                               createdPath.typeArgumentList != null) {
    val end = createdPath.identifier?.endOffsetInParent ?: 0
    val pathText = createdPath.text
    val newPath = pathText.substring(0, end) + "::" + pathText.substring(end)
    val path = factory.tryCreatePath(newPath) ?: return
    ctx.path.replace(path) as RsPath
} else {
    ctx.path.replace(createdPath) as RsPath
}
```

[^2]: Or one of its subclasses, in this case `RsBaseType`.

So, any more edge cases that come to mind? What if you substitute a type that is not available in the
scope where the intention was invoked?
```rust
use foo::B;
mod foo {
    pub struct A;
    pub type B = A;
}
fn foo() -> /*caret*/B { unreachable!() }
// turns into
fn foo() -> A { unreachable!() }
```
Oops! `A` is not available in the scope where we have used the intention. Luckily, the plugin already
contains powerful API to import missing types from a given `PsiElement` or a type reference, so it's enough
to add this one liner to the end of the `invoke` method:
```kotlin
RsImportHelper.importTypeReferencesFromTy(insertedPath, typeRef.type)
```
The first parameter is a context where should the import happen, and the second parameter is the type
to be imported (if necessary). With this change the above the intention auto-imports any necessary types:
```rust
use foo::{B, A};
```

What if the type that is being substituted already has some generic argument?
```rust
type Type<T> = Vec<T>;
fn bar(t: Type<u32>) {}
// turns into
fn bar(t: Vec<T>) {}
```
This also doesn't work properly, as it should generate `Vec<u32>` :disappointed:.
However, I will not show how to implement support for this case, because I only found
about it while writing this blog post and I have yet to send another PR to fix this :sweat_smile:. Also
this post is already pretty long -- but don't worry, we're almost at the end!

**Edit**: it turned out that there are [multiple issues](https://github.com/intellij-rust/intellij-rust/pull/6032)
with this intention being applied to type aliases (mainly because of generics). So for now I have enabled it
only for associated types.

We should also add some tests that check that the intention is not offered on places where it shouldn't be.
Does that mean that we should add a test for each possible Rust element that does not resolve to an associated type?
Probably not a good idea, as that would be a lot of (repetitive) tests.
I generally only tend to include sanity checks and edge cases that I know the intention worries about. Basically for
every `if` condition in the intention that checks some special case, there should be a test that tests if that
special case is handled correctly. We now know that `findApplicableContext` should filter out invalid references
and associated types without an actual assigned type, so let's add a test for the latter situation:
```kotlin
fun `test unavailable on trait associated type`() = doUnavailableTest("""
    trait Trait { type Item; }
    fn foo<T: Trait>() -> T::/*caret*/Item { unimplemented!() }
""")
```

I have also added an additional test that checks if the intention works for associated types in traits that
have a default value. This is currently a `nightly`-only feature, but why not make the intention future-proof?

# Testing the intention in GUI
Great, so now we have an implemented intention, we have test coverage, but before we proclaim victory 
and send a PR, let's test the intention in the GUI first, to experience the satisfaction of seeing it in action.
The repository of the plugin contains an `exampleProject` directory with a trivial Rust project that is
commonly used to test the plugin manually. Let's launch the `RunClion` action to start up CLion, open
the `exampleProject` in it, copy paste the code from the original issue into it and BEHOLD: 

{% include gif.html path="/assets/posts/contributing-2/int-unavailable" w="100%" %}

*Sigh* :pensive:. The intention does not seem to appear in the intention list. By putting a breakpoint
inside the `findApplicableContext` method, we can quickly realize that the method is not even being
called at all. Although it works in tests, tt seems that something else must be done for the intention
to be registered by the IDE.

When working on the plugin, you might often meet this situation where you suspect that there's some
configuration that needs to be added for something to work, but you don't know what or where it is.
There are several ways of tackling this:

1. Look in the [official](https://confluence.jetbrains.com/display/IDEADEV/Creation+of+Intention+Action)
[documentation](https://jetbrains.org/intellij/sdk/docs/tutorials/code_intentions.html). I often find it lacking,
there are some good resources about explaining high-level concepts, but usually it doesn't help me very much.
2. Look how the problem was handled before. This is not the first intention in the plugin, so it might be a good idea
to check some previous PR that authored an intention to see what it had to do to make the intention available in the GUI.
For example let's take our venerable `AddElseIntention`. How do we find out in which PR it was authored?
    - Use `git blame`, which can find the last commit that modified a given file or even a specific line.
    You can find a tutorial for its usage [here](https://linuxhint.com/git_blame).
    - Right click on the column with line numbers in IDEA, click on `Annotate` and it will show you the last commit that modified
    each line in the currently opened file.
    - Look through merged PRs in the project's [repository](https://github.com/intellij-rust/intellij-rust/pulls?q=is%3Apr+is%3Amerged+intention).
3. Often the fastest solution, and the one that I have used, is to take an existing intention and
simply grep for its name. If it is registered in the plugin, its name has to be mentioned somewhere in the project, right?
If we search for files (`Ctrl + Shift + F`) containing the string `AddElseIntention`, we get these three results:
    - `src/.../intentions/AddElseIntention.kt` - the intention itself, no surprise there
    - `src/test/.../intentions/AddElseIntentionTest.kt` - the intention's test, we already know this one
    - `src/main/resources/META-INF/rust-core.xml` - A-HA! We didn't modify this file yet. It looks like some
    XML with configuration of the plugin and amongst other things it contains this record that seems to tell the
    plugin about the existence of the intention:

    ```xml
    <intentionAction>
        <className>org.rust.ide.intentions.AddElseIntention</className>
        <category>Rust</category>
    </intentionAction>
   ```

We have found the missing piece! Now let's just add this:
```xml
<intentionAction>
    <className>org.rust.ide.intentions.SubstituteAssociatedTypeIntention</className>
    <category>Rust</category>
</intentionAction>
```
to `rust-core.xml` and voilà, our intention is offered in the GUI! :tada:

{% include gif.html path="/assets/posts/contributing-2/int-available" w="100%" %}

> After you put the intention into `rust-core.xml`, a little connector icon appears next to the intention
class in IDEA, so that you can go back and forth between the intention and it's registration point. There are
also additional icons for going to the intention's description and templates.

# Wrapping it up
After implementing the intention, I sent a [PR](https://github.com/intellij-rust/intellij-rust/pull/5643)
named `INT: add intention to substitute an associated type` to the plugin (you can find the whole source code
of the intention in that PR). The discussion was fairly short, [mchernyavsky](https://github.com/mchernyavsky)
just noticed that the intention doesn't import types, I fixed that and that was all. Even then,
it took about a month until the PR was merged, as sometimes it takes time for the maintainers to find
bandwidth for reviewing. So have patience and do not despair!

If you're reading this, thanks for sticking with me up until the end of this post. If you have any
comments, let me know on [Reddit](https://www.reddit.com/r/rust/comments/ihkwfc/contributing_to_the_intellijrust_plugin_writing/).
