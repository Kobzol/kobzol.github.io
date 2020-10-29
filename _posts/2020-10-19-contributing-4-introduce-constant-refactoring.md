---
layout: post
title:  "Contributing to Intellij-Rust #4: Introduce constant refactoring"
date:   2020-10-19 17:29:00 +0200
categories: rust intellij
--- 
This post is part of a [series]({% post_url 2020-08-23-contributing-0-setup %}) in which I describe
my contributions to the [IntelliJ Rust](https://github.com/intellij-rust/intellij-rust) plugin.

- Previous post: [#3 Quick fix to attach file to a module]({% post_url 2020-09-04-contributing-3-quick-fix-attach-file-to-mod %})
- Next post: [#5 Lint attribute completion]({% post_url 2020-10-26-contributing-5-lint-attribute-completion %})

In this post we'll take a look at the holy grail of IDEs: automated refactoring. We will implement a
refactoring action that allows you to extract (or "introduce") a constant from an expression, and then
optionally replace all occurrences of such expression with the newly introduced constant. I'll explain
how automated refactoring works and show you some common examples of refactoring actions available in
the IntelliJ IDEs. Then we'll take a look at how you can actually implement some refactoring action
from scratch.

You can find the original PR that I will go through [here](https://github.com/intellij-rust/intellij-rust/pull/4985)
(spoiler alert!).

> From this post onward, I will try to make references to some classes and functions of
> the plugin clickable (where applicable, to avoid some spoilers) so that you can check out their
> source code if you want.

# Finding an issue
We will be solving [this issue](https://github.com/intellij-rust/intellij-rust/issues/4246), in which
[alexander-irbis](https://github.com/alexander-irbis) asked for a refactoring that could extract a
constant from an expression. Constant extraction is one of several refactorings that are built-in into
the IntelliJ IDEs and it is definitely useful, so I decided to take a shot at solving this issue.

The refactoring should be able to take an expression, create a constant with this expression and
replace (optionally all) occurrences of the expression with the newly created constant. Here is an
example:
```rust
fn foo() {
    let a = /*caret*/1 + 1;
    let b = 1 + 1;
}
// ^ turns into v
fn foo() {
    const CONST/*caret*/: i32 = 1 + 1;
    let a = CONST;
    let b = CONST;
}
```
It should work similarly as the `Introduce variable` refactoring, although with a few twists, as we
will see in a moment.

# Refactoring actions
Refactoring is the act of restructuring your source code without (hopefully) changing its runtime
behaviour. There are several common refactoring scenarios, such as renaming a class, moving a function
from one file to another, inlining a function or a variable, introducing a new variable etc. Performing
the refactoring itself is usually not so difficult, even without an IDE. The hard part is what comes
after -- you have to modify the rest of the code to match your changes. You renamed a class? Great,
now you have to update all of its usages to the new name. You moved a function to a new file/module?
Now you need to change all of its imports/uses in other files.

This is where automated refactorings come in. They are the ultimate code transformation tools of
(IntelliJ) IDEs, because not only can they perform the refactoring itself, more importantly they can
(mostly) automate the boring and repetitive task of updating all places in your codebase that use the
refactored code.

Refactoring actions are basically similar to
[intentions]({% post_url 2020-08-25-contributing-2-subst-assoc-type-int %}), as they are invoked
explicitly over some piece of code. Unlike intentions though, they are intended for possibly
large-scale code changes that can take some time, so their API is accustomed to that. For example,
some refactorings are split into two parts. The first searches for all occurrences of the refactored
code. This can take a long time, so it is performed asynchronously in a background thread. The
second part then performs the refactoring itself and updates all of the previously found occurrences.
The refactoring that we will implement in this post is rather simple, so it will not use this API,
but we may see it in a future post.

IntelliJ IDEs allow language plugins to define common refactoring actions that are almost ubiquitous
amongst languages, like introducing a variable or extracting a function out of a block of code. The
refactoring that we will be implementing in this post, `Introduce constant`, is one of them. You can
also implement your own custom refactoring actions from scratch, as we will see in a future post.

# Designing the refactoring
Since refactorings can be quite complex, we should think about how should our refactoring actually
behave before we start to implement it. `Introduce constant` is quite similar to `Introduce variable`,
so first I'll describe how that one works and then we'll see what differences we have to make to
introduce a constant instead of a variable.

If you run the `Introduce variable` refactoring on a Rust expression, a new variable will be
created in the corresponding function. This variable will be initialized with your selected expression,
and the expression itself will be replaced by a usage of the new variable:
```rust
fn foo() {
    let a = /*caret*/1;
}
// ^ turns into v
fn foo() {
    let i = 1;
    let a = i;
}
```
On top of this basic functionality, the refactoring lets you:
- **Select the expression to be extracted** - when you invoke the refactoring on a complex expression,
you can select which part of the expression should be extracted:

    {% include gif.html path="/assets/posts/contributing-4/introduce-variable-expression" w="100%" %}

    > Fun fact: currently, for expressions like `1 * 2 * 3`, you cannot extract the subexpression `2 * 3`, 
    > because of the way the plugin's Rust parser works. You can only extract `1`, `2`, `3`, `1 * 2` or
    > `1 * 2 * 3`. You can be find more information about this issue
    > [here](https://github.com/intellij-rust/intellij-rust/issues/4608).
- **Replace all occurrences of the extracted expression** - you can either replace only the expression
on which you invoke the refactoring or all identical expressions in the corresponding scope (usually
inside a function):

    {% include gif.html path="/assets/posts/contributing-4/introduce-variable-occurrences" w="100%" %}

    I will call this the *replacement mode*.
- **Specify a name for the newly created variable** - right after the new variable is created, you
can select a name for it. If you replaced multiple occurrences of the extracted expression, all of
them will be renamed:

    {% include gif.html path="/assets/posts/contributing-4/introduce-variable-rename" w="100%" %}

    The original name chosen for the new variable respects names that are already present in the
    corresponding scope. For example, if there already was a local variable called `i`, the new variable
    would be named `i1` instead. 

All of these features are pretty nice and I definitively wanted to include them in the
`Introduce Constant` refactoring.

There will be some differences between introducing a variable and a constant though. Some of them
are rather trivial -- the created constant will use `const` instead of `let`, it will have to specify
an explicit data type (Rust requires that) and its initial name should be in upper case, per
the Rust [naming conventions](https://rust-lang.github.io/api-guidelines/naming.html). There will
also be two additional differences.

#### Constant expressions
The first one is that not all expressions that can be extracted into a variable can be
extracted into a constant. For example, this expression cannot be extracted into a constant, as it
uses a [non-constant value](https://doc.rust-lang.org/stable/error-index.html#E0435):
```rust
fn foo() {
    let x = 5;
    let a = <selection>x + 1</selection>;
}
```
Therefore, the refactoring will have to detect if the extracted expression is actually a constant
expression, and if not, it should fail with an error message.

Constant expressions in Rust can actually contain quite a lot of things, such as calls to constant
functions, instantiation of structs, arithmetic operations between constants etc. As we will see
later in this post, for my initial implementation of the refactoring I decided to stay on the
safe side to avoid potential false negatives that could result in the generated code being invalid.
Therefore the refactoring will only allow the extraction of two types of expressions -- literals
and binary expressions containing literals, as I suspect that these encompass the most common use
cases for constants in Rust (and also other languages).

#### Insertion place
Another important difference from the `Introduce variable` refactoring is that constants can exist
in various scopes, not just inside functions. For example, in the following snippet, you can extract
the specified expression into a constant that could be inserted at any of the marked locations:
```rust
// here
mod foo {
    // here
    fn bar() {
        // here
        fn baz() {
            // here
            let x = /*caret*/5;
        }
    }
}
```
Therefore, the refactoring should offer an additional configuration step (with its own UI) that will
allow the user to select at which scope should the constant be created.

# Bootstrapping the refactoring
To find out how should I actually implement this refactoring, I started examining existing refactoring
actions. We have already talked about `Introduce variable`, so I searched for that in the repository
and found a class named [`RsIntroduceVariableHandler`](https://github.com/intellij-rust/intellij-rust/blob/9d6a43825a49d27dbf49445280bfaa3d7b5e4180/src/main/kotlin/org/rust/ide/refactoring/introduceVariable/RsIntroduceVariableHandler.kt).
To create a similar refactoring to this one, I needed to find out how it is actually registered in
the plugin. So far, we have been registering
[intentions]({% post_url 2020-08-25-contributing-2-subst-assoc-type-int %})
and [inspections]({% post_url 2020-09-04-contributing-3-quick-fix-attach-file-to-mod %}) in the 
[`rust-core.xml`](https://github.com/intellij-rust/intellij-rust/blob/9d6a43825a49d27dbf49445280bfaa3d7b5e4180/src/main/resources/META-INF/rust-core.xml)
file which contains configuration of the plugin. However, when I searched for
`RsIntroduceVariableHandler`, I couldn't find it in any XML file. So how does the plugin know about
its existence?

When I looked at other usages of this class, I found that it is used in something called
[`RsRefactoringSupportProvider`](https://github.com/intellij-rust/intellij-rust/blob/9d6a43825a49d27dbf49445280bfaa3d7b5e4180/src/main/kotlin/org/rust/ide/refactoring/RsRefactoringSupportProvider.kt):
```kotlin
class RsRefactoringSupportProvider : RefactoringSupportProvider() {
    override fun getIntroduceVariableHandler() = RsIntroduceVariableHandler()
    override fun getIntroduceParameterHandler() = RsIntroduceParameterHandler()
    override fun getExtractMethodHandler() = RsExtractFunctionHandler()
}
```
This class itself is indeed registered in `rust-core.xml` and it seems that it creates instances of
refactorings for introducing a variable or a parameter or extracting a method. These are standard
refactorings that are available for many languages in IntelliJ plugins in the standard `Refactoring`
dialog[^1]. Therefore it looks like this is the place where we have to plug in our implementation of
the `Introduce constant` refactoring in order for it to appear in the `Refactoring` dialog!

[^1]:
    For example, in PyCharm you can right click on some Python value and then select
    `Refactor -> Introduce Variable`.

The `RsRefactoringSupportProvider` class implements the `RefactoringSupportProvider` interface.
I tried to examine its methods and sure enough, I found a method called `getIntroduceConstantHandler`,
which sounded exactly like the thing I needed. So I tried to implement it:
```kotlin
override fun getIntroduceConstantHandler() = RsIntroduceConstantHandler()
```
with an empty `RsIntroduceConstantHandler` class that I created at `src/main/kotlin/org/rust/ide/refactoring`
(next to the original handler for introducing variables). The empty handler looks like this:
```kotlin
class RsIntroduceConstantHandler : RefactoringActionHandler {
    override fun invoke(
        project: Project,
        editor: Editor,
        file: PsiFile,
        dataContext: DataContext
    ) {}
}
```
The `invoke` method will be called after you launch the refactoring. Its parameters are pretty much
the same as for the `findApplicableContext` method of intentions, which we have already talked about
[before]({% post_url 2020-08-25-contributing-2-subst-assoc-type-int %}#deciding-when-to-offer-the-intention).

After I implemented the `getIntroduceConstantHandler` method, I fired up CLion and sure enough, suddenly
`Introduce Constant` appeared in the refactoring dialog in Rust code! :tada: Now all that's left
is to actually implement it :)

{% include gif.html path="/assets/posts/contributing-4/introduce-constant-dialog" w="100%" %}

# Writing a failing test
As usually, I like to start with writing a (failing) test. With a test I can step into the function
that I'm trying to implement with a debugger and examine its runtime arguments in order to find out
what am I dealing with. A quick search led me to [`RsIntroduceVariableHandlerTest`](https://github.com/intellij-rust/intellij-rust/blob/9d6a43825a49d27dbf49445280bfaa3d7b5e4180/src/test/kotlin/org/rust/ide/refactoring/RsIntroduceVariableHandlerTest.kt),
which I used as a basis for creating a new test class, the not-so-surprisingly named
`RsIntroduceConstantHandlerTest`.

Let's start with a very simple test:
```kotlin
class RsIntroduceConstantTest : RsTestBase() {
    fun `test insertion local`() = doTest("""
        fn foo() {
            let x = /*caret*/5;
        }
    """, listOf("fn foo", "file"), 0, """
        fn foo() {
            const I: i32 = 5;
            let x = I;
        }
    """)

    ...
}
```
Here we check that we can create a constant inside a function. The constant will be initialized with
the extracted expression and the expression itself will be replaced with an usage of the constant.

> You can ignore the second and third arguments (`listOf("fn foo", "file")`, `0`) for now. They check
> the scopes where the constant can be created, we will use them towards the end of this post, after
> we implement support for it.

To properly test the refactoring, I needed a test function that would enable parametrizing which
expression is selected for extraction, if all of its occurrences should be replaced and also where
should the constant be created. I won't show the implementation of the `doTest` function here,
you can find it in the
[PR](https://github.com/intellij-rust/intellij-rust/pull/4985/files#diff-6438014e8714dd5f85ef84bf4abb6a8271f90b54f2f3a65abb88af292ca641d2R109)
if you want.

Now that we have a test, let's start implementing the basis of the refactoring. Luckily, a large
part of the functionality that we need is shared with the `Introduce variable` refactoring, which
is already implemented. And even better, there is another similar refactoring for introducing parameters
([`RsIntroduceParameterHandler`](https://github.com/intellij-rust/intellij-rust/blob/9d6a43825a49d27dbf49445280bfaa3d7b5e4180/src/main/kotlin/org/rust/ide/refactoring/introduceParameter/RsIntroduceParameterHandler.kt)),
therefore the functionality shared by these two existing refactorings was already extracted into nice
reusable components. We will thus heavily reuse these components to avoid reinventing the wheel. 

# Finding candidate expressions to extract
The first thing that our refactoring has to do is to perform a sanity check to see if it was actually
invoked in a Rust file and find an expression that could be extracted:
```kotlin
override fun invoke(
    project: Project,
    editor: Editor,
    file: PsiFile,
    dataContext: DataContext
) {
        if (file !is RsFile) return
        val exprs = findCandidateExpressionsToExtract(editor, file)
            .filter { it.isExtractable() }
        ...
}
```
The [`findCandidateExpressionsToExtract`](https://github.com/intellij-rust/intellij-rust/blob/9d6a43825a49d27dbf49445280bfaa3d7b5e4180/src/main/kotlin/org/rust/ide/refactoring/extraxtExpressionUtils.kt#L21)
function is an utility function which was already used for introducing variables
and parameters, so I just reused it here. The function checks if the user has some code explicitly
selected and if yes, tries to find an expression in that selection. If the user does not have any
selection, it tries to find expressions that are located near the caret.
Note that the function returns a list of possible expressions. We will leverage this fact in a moment
to let the user select the expression that should be extracted.

After we get the candidate expressions for extraction, we have to keep only the expressions that can
actually be used to initialize a constant. I created an extension function called
[`isExtractable`](https://github.com/intellij-rust/intellij-rust/pull/4985/files#diff-7f006c50a8edbed47c5af65c3c39048a09241d311646e678115179765cfba2cfR54)
for that. As mentioned [above](#constant-expressions), this function is currently pretty conservative,
as it only allow literals and binary expressions containing literals:
```kotlin
private fun RsExpr.isExtractable(): Boolean {
    return when (this) {
        is RsLitExpr -> true
        is RsBinaryExpr ->
            this.left.isExtractable() &&
            this.right?.isExtractable() ?: true
        else -> false
    }
}
```
[`RsLitExpr`](https://github.com/intellij-rust/intellij-rust/blob/9d6a43825a49d27dbf49445280bfaa3d7b5e4180/src/main/kotlin/org/rust/lang/core/psi/ext/RsLitExpr.kt)
represents Rust literals, such as `42`, `1.0`, `true` or `"foo"`. If we see a literal,
we consider it to be "extractable". If we encounter a binary expression (represented by
`RsBinaryExpr`), we recurse into its left and right subexpressions[^2] to see if they are extractable.
If we find anything else, we conservatively assume that the expression is not constant.

[^2]: The right subexpression might be missing, that's why there is a nullability check in the code.

> If you have a use case where you would like to use the refactoring on more complex constant expressions,
> feel free to [create an issue](https://github.com/intellij-rust/intellij-rust/issues/new) and I'll
> try to fix it!

# Selecting the expression to be extracted
Once we have the candidate expressions, we have to decide what to do next, based on their count.
The behaviour here is almost the same as when you introduce a variable, so the following
section of code was shamelessly copied from [`RsIntroduceVariableHandler`](https://github.com/intellij-rust/intellij-rust/blob/9d6a43825a49d27dbf49445280bfaa3d7b5e4180/src/main/kotlin/org/rust/ide/refactoring/introduceVariable/RsIntroduceVariableHandler.kt#L22)[^3]:
```kotlin
when (exprs.size) {
    0 -> {
        val message = RefactoringBundle.message(
            if (editor.selectionModel.hasSelection()
        )
            "selected.block.should.represent.an.expression"
        else
            "refactoring.introduce.selection.error"
        )
        val title = RefactoringBundle.message("introduce.constant.title")
        val helpId = "refactoring.extractConstant"
        CommonRefactoringUtil.showErrorHint(
            project, editor, message,
            title, helpId
        )
    }
    1 -> extractExpression(editor, exprs.single())
    else -> {
        showExpressionChooser(editor, exprs) {
            extractExpression(editor, it)
        }
    }
}
```
There are three situations that might happen (listed here in reverse order w.r.t. the code):
- **Multiple expressions were found** - in this case we have to show the user a UI dialog for selecting
the expression that should be extracted. Luckily, this was already implemented, complete with support
for unit tests and interactive highlighting of the selected expression, so I just reused the
[`showExpressionChooser`](https://github.com/intellij-rust/intellij-rust/blob/9d6a43825a49d27dbf49445280bfaa3d7b5e4180/src/main/kotlin/org/rust/ide/refactoring/extraxtExpressionUi.kt#L21)
function.
- **Exactly one expression was found** - in this case we can skip the expression selection step.
- **No valid expression was found** - in this case we have to show an error to the user. The error
message changes based on the fact if the user had some code selected or not.

    It is clear that the code taken from the introduce variable handler is using some IntelliJ built-in
    error messages referenced by string IDs, so I wanted to follow suit (the original code used
    `introduce.variable.title` and `refactoring.extractVariable`).

    However, I had no idea where to find the corresponding IDs for introducing a constant. After a
    bit of trial and error, I googled the string IDs from the introduce variable handler and found
    some IntelliJ commits that were modifying these IDs in a file called `RefactoringBundle.properties`.
    I thus invoked the mighty `Ctrl + Shift + N` search dialog to find this file, which appeared to
    be hidden inside the resources of the IDEA dependency used to test the plugin. Searching for
    `constant` inside this file led me to the coveted string ID `introduce.constant.title`. I didn't
    find the location of the second string ID, so I just tried to change the word `Variable` to
    `Constant` in the ID and it worked![^4]

[^3]:
    A class or a function could probably be introduced to unify the behaviour of introducing a variable,
    a parameter and a constant, but here it looked like it would needlessly complicate the code for
    a very small gain. The complex behaviour, such as finding candidate expressions and UI dialogs
    for selecting an expression and choosing the replacement mode, is reused between these three
    refactorings. Therefore I didn't consider the small additional duplication here to be a big deal.

[^4]:
    Yes, in retrospect, I could do the same thing for the first string ID :sweat_smile:. But hey,
    at least now I know that there is a file with IntelliJ string IDs if I ever need one again!

# Extracting the constant
Now that we know what expression should be extracted, let's create some basic implementation of the
`extractExpression` function:
```kotlin
private fun extractExpression(editor: Editor, expr: RsExpr) {
    if (!expr.isValid) return
    replaceWithConstant(expr, editor)
}
```
First we just do a basic sanity check that the expression is `valid`, i.e. it has not been removed
from the PSI tree in the meantime or something like that. Then we call the `replaceWithConstant`
function to actually do the replacement.

> Notice the implementation shown above is intentionally simple for now. Later in this post we will
> add support for selecting the replacement mode and the insertion place to this function.

The `replaceWithConstant` function is where the real magic happens. Same as
[before]({% post_url 2020-08-25-contributing-2-subst-assoc-type-int %}#implementing-the-invoke-method),
we must create a `RsPsiFactory`, since we will be constructing new source code (the constant):
```kotlin
private fun replaceWithConstant(expr: RsExpr, editor: Editor) {
    val project = expr.project
    val factory = RsPsiFactory(project)
```
After that, we need to come up with some initial name for the constant. Again, the plugin has our back!
There is a very useful extension method on expressions called
[`suggestedNames`](https://github.com/intellij-rust/intellij-rust/blob/9d6a43825a49d27dbf49445280bfaa3d7b5e4180/src/main/kotlin/org/rust/ide/refactoring/RsNameSuggestions.kt#L42)!
Coming up with a name thus becomes a one-liner. We just have to convert the default suggested name
to upper case to adhere to the Rust naming convention:
```kotlin
    val suggestedNames = expr.suggestedNames()
    val name = suggestedNames.default.toUpperCase()
```
After that, we have to create the constant. The PSI factory did not yet contain a function for creating
constants, so I created it:
```kotlin
// function in RsPsiFactory.kt
fun createConstant(name: String, expr: RsExpr): RsConstant = createFromText(
    "const $name: ${expr.type.renderInsertionSafe(useAliasNames = true,
        includeLifetimeArguments = true)} = ${expr.text};"
) ?: error("Failed to create constant $name from ${expr.text} ")
```
It takes a name and an expression and creates a PSI representation of a Rust constant
([`RsConstant`](https://github.com/intellij-rust/intellij-rust/blob/9d6a43825a49d27dbf49445280bfaa3d7b5e4180/src/main/kotlin/org/rust/lang/core/psi/ext/RsConstant.kt)).
The type of the constant is taken directly from the passed expression.

Using this function, we can finally create the constant and then insert it before the expression
that we are extracting:
```kotlin
val const = factory.createConstant(name, expr)
project.runWriteCommandAction {
    val context = expr.parent
    val insertedConstant =
        context.parent.addBefore(const, context) as RsConstant
```
We need to perform the PSI tree modification itself inside a
[write action]({% post_url 2020-09-04-contributing-3-quick-fix-attach-file-to-mod %}#selecting-a-module-for-attachment-ui).
After we create the constant, we need to replace the original expression with an usage of the new
constant. We can do that using a [path]({% post_url 2020-08-23-contributing-1-nest-use-fix %}#paths)
expression with the name of the created constant:
```kotlin
    val path = factory.createExpression(name)
    expr.replace(path)
```
The
[`createExpression`](https://github.com/intellij-rust/intellij-rust/blob/9d6a43825a49d27dbf49445280bfaa3d7b5e4180/src/main/kotlin/org/rust/lang/core/psi/RsPsiFactory.kt#L85)
method parses an arbitrary string and tries to create an expression out of it.
If we pass it e.g. the string `"I"` (a default name for a created constant), it will parse it as a
`RsPathExpr`, i.e. an expression that references something using a path to it.

For good measure, let's also move the user's caret to the identifier of the created constant:
```kotlin
    editor.caretModel.moveToOffset(
        insertedConstant.identifier?.textRange?.startOffset
        ?: error("Impossible because we just created a constant with a name")
    )
}
```
That was pretty easy! And with this code alone, the [first test](#writing-a-failing-test) already
passes! :tada: Let's also create a test that checks whether we can select the expression to be
extracted:
```kotlin
@ProjectDescriptor(WithStdlibRustProjectDescriptor::class)
fun `test insertion binary expression`() = doTest("""
    fn foo() {
        let x = /*caret*/5 + 5;
    }
""", listOf("fn foo", "file"), 0, """
    fn foo() {
        const I: i32 = 5 + 5;
        let x = I;
    }
""", expression = "5 + 5")
```
The `expression` parameter of the `doTest` function lets us choose which expression should be
extracted. The `ProjectDescriptor` annotation is used to run this test with the Rust `stdlib` present.
The plugin needs access to `stdlib` in order to understand arithmetic operations on built-in number
types (such as `i32`).

Now that we have the basic functionality prepared, let's add shiny new features on top of it.

# Replacing all occurrences
To mirror the behaviour of existing refactorings for introducing variables and parameters, we should
let the user choose to either replace just a single occurrence or all occurrences of the extracted
expression. Again, we do not have to implement this from scratch -- we can just reuse the
[`showOccurrencesChooser`](https://github.com/intellij-rust/intellij-rust/blob/9d6a43825a49d27dbf49445280bfaa3d7b5e4180/src/main/kotlin/org/rust/ide/refactoring/extraxtExpressionUi.kt#L33)
function, which will present a UI dialog to the user and then give us a list of occurrences that
should be replaced. Let's add it to `extractExpression`:
```kotlin
private fun extractExpression(editor: Editor, expr: RsExpr) {
    if (!expr.isValid) return
    showOccurrencesChooser(editor, expr, occurrences) { occurrencesToReplace ->
        replaceWithConstant(expr, occurrencesToReplace, editor)
    }
}
```
Then we just slighty modify `replaceWithConstant` to replace all of the passed occurrences:
```kotlin
private fun replaceWithConstant(
    expr: RsExpr,
    occurrences: List<RsExpr>,
    editor: Editor
) {
    ...
    val replaced = occurrences.map {
        val created = factory.createExpression(name)
        val element = it.replace(created) as RsPathExpr
        element
    }
    ...
```
We will also add support for choosing a name for the new constant, in such a way that the new name
will be mirrored to all replaced occurrences. The plugin again has our back with the wonderful
[`RsInPlaceVariableIntroducer`](https://github.com/intellij-rust/intellij-rust/blob/9d6a43825a49d27dbf49445280bfaa3d7b5e4180/src/main/kotlin/org/rust/ide/refactoring/RsInPlaceVariableIntroducer.kt)
class. We just have to pass it the element that we want to rename, a set of occurrences that should
be renamed along with it and a set of suggested names (which we have already calculated at the
[beginning of the function](#extracting-the-constant)):
```kotlin
    PsiDocumentManager.getInstance(project)
        .doPostponedOperationsAndUnblockDocument(editor.document)
    RsInPlaceVariableIntroducer(insertedConstant, editor, project,
        "Choose a constant name", replaced
    ).performInplaceRefactoring(
        LinkedHashSet(suggestedNames.all.map { it.toUpperCase() })
    )
```
We also have to flush pending PSI operations using `doPostponedOperationsAndUnblockDocument`
before renaming the constant, as I have learned from the existing refactorings.

Now we can confirm that it works with a test:
```kotlin
fun `test replace all`() = doTest("""
    fn foo() {
        let x = /*caret*/5;
        let y = 5;
    }
""", listOf("fn foo", "file"), 0, """
    fn foo() {
        const I: i32 = 5;
        let x = I;
        let y = I;
    }
""", replaceAll = true)
```

> Later it [turned out](https://github.com/intellij-rust/intellij-rust/issues/5844) that the existing
> functions for finding expression occurrences were not prepared for situations that aren't possible
> for variables and parameters, but are possible for constants (i.e. occurrences outside of functions).
> I fixed that in a follow-up [PR](https://github.com/intellij-rust/intellij-rust/pull/5857).

# Selecting the insertion place
At this point, we have a working refactoring for introducing constants that works in a similar
fashion to `Introduce variable` and `Introduce parameter`. However, I wanted to go the extra mile,
so as discussed at the [beginning](#designing-the-refactoring) of this post, we will also add support
for selecting where should the constant be created.

We will need to find potential places where the constant could be inserted and offer them to the user.
To describe a potential insertion place, we will need three things:
- **Context**: a conceptual place of insertion presentable to the user, e.g. a function.
- **Parent**: a specific PSI element into which we will insert the constant, e.g. the block (`{ ... }`)
of some function.
- **Anchor**: an element in `parent` before which we will insert the constant.

> We need to make a distinction between the `context` and the `parent` because of the way Rust
> functions are represented in the PSI structure. You cannot insert an element into a function, you
> have to insert it into its block (therefore the `parent` of a function will be its block). At the
> same time, you want to show the user an informative textual description of the insertion place,
> and for that you need to know the name of the function (therefore the `context` of a function
> will be the function itself).

I created the following class to represent potential insertion places:
```kotlin
data class InsertionCandidate(
    val context: PsiElement,
    val parent: PsiElement,
    val anchor: PsiElement
) {
    fun description(): String = when (val element = this.context) {
        is RsFunction -> "fn ${element.name}"
        is RsModItem -> "mod ${element.name}"
        is RsFile -> "file"
        else -> error("unreachable")
    }
}
```
The `description` method will be used to offer a readable name to the user. As you can see, I decided
to only support functions, modules and files as insertion places (I don't consider other cases, such
as nested blocks inside functions). A proper solution would thus be to represent the `context` with
an [Algebraic Data Type](https://en.wikipedia.org/wiki/Algebraic_data_type) (i.e. a `sealed class`
in Kotlin), but I was too lazy to do that for the sake of a single function :sweat_smile:.

#### Finding potential insertion places
Now we need to find all possible insertion places for a given expression. We can search for potential
candidates by iteratively traversing parents of the given expression until we get to a
[`RsFile`](https://github.com/intellij-rust/intellij-rust/blob/9d6a43825a49d27dbf49445280bfaa3d7b5e4180/src/main/kotlin/org/rust/lang/core/psi/RsFile.kt),
at which point we can stop, since we reached the root of the file. Every time we encounter a
(grand-)parent that is a function, module or a file, we will add it to a list of potential insertion
places. To get the insertion `anchor`, we can take a direct child of the `parent` that is also an
ancestor of the expression. For example here:
```rust
fn foo() {
    let a = /*caret*/5;
}
```
One insertion candidate will have:
- `context` - function `foo`
- `parent` - the block (`{ ... }`) of `foo`
- `anchor` - the `let a = ...;` declaration

Another one might have:
- `context` - file containing `foo`
- `parent` - file containing `foo`
- `anchor` - the function `foo`

In addition to this, we should also stop considering functions once a module has been encountered
to avoid some pathological cases[^5].

I implemented the described algorithm in a function named [`findInsertionCandidates`](https://github.com/intellij-rust/intellij-rust/pull/4985/files#diff-243cd308065e0820a4c1e781c5f32b3a0b88eed5eeac0d6acf358f11ea14274eR104).
You can find its full source code below, but beware, it's a bit of a mouthful.

<details>
<summary>Source code of findInsertionCandidates</summary>
{% highlight kotlin %}
private fun findInsertionCandidates(expr: RsExpr): List<InsertionCandidate> {
    var parent: PsiElement = expr
    var anchor: PsiElement = expr
    val points = mutableListOf<InsertionCandidate>()

    fun getAnchor(parent: PsiElement, anchor: PsiElement): PsiElement {
        var found = anchor
        while (found.parent != parent) {
            found = found.parent
        }
        return found
    }

    var moduleVisited = false
    while (parent !is RsFile) {
        parent = parent.parent
        when (parent) {
            is RsFunction -> {
                if (!moduleVisited) {
                    parent.block?.let {
                        points.add(InsertionCandidate(parent, it, getAnchor(it, anchor)))
                        anchor = parent
                    }
                }
            }
            is RsModItem, is RsFile -> {
                points.add(InsertionCandidate(parent, parent, getAnchor(parent, anchor)))
                anchor = parent
                moduleVisited = true
            }
        }
    }
    return points
}
{% endhighlight %}
</details>

[^5]:
    Yes, you [can](https://play.rust-lang.org/?version=stable&mode=debug&edition=2018&gist=d274376535b8445eaef4db9c496d834e)
    actually create modules inside a function in Rust. Why would you want to do that is beyond me
    though :man_shrugging:.

<br />

#### Selecting an insertion place (tests)
Once we have a way of finding potential candidates for insertion, we can show the user some UI to
choose the target place from them. As in the
[last post]({% post_url 2020-09-04-contributing-3-quick-fix-attach-file-to-mod %}#selecting-a-module-for-attachment-tests),
I first created an interface for selecting the insertion place to allow mocking the UI in tests:
```kotlin
interface ExtractConstantUi {
    fun chooseInsertionPoint(
        expr: RsExpr,
        candidates: List<InsertionCandidate>
    ): InsertionCandidate
}

var MOCK: ExtractConstantUi? = null

@TestOnly
fun withMockExtractConstantChooser(
    mock: ExtractConstantUi,
    f: () -> Unit
) { /* activate mock */}
```
The interface receives an expression and a list of insertion candidates and returns the selected
candidate. In [tests](https://github.com/intellij-rust/intellij-rust/pull/4985/files#diff-6438014e8714dd5f85ef84bf4abb6a8271f90b54f2f3a65abb88af292ca641d2R127),
the interface is mocked with a function that simply returns the selected place from the list of
candidates. If we now go back to the [first test](#writing-a-failing-test):
```kotlin
fun `test insertion local`() = doTest("""
    fn foo() {
        let x = /*caret*/5;
    }
""", listOf("fn foo", "file"), 0, """
    fn foo() {
        const I: i32 = 5;
        let x = I;
    }
""")
```
We can see that the second argument specifies the expected list of offered candidates (in this case
it should be the function `foo` and the containing file) and the third argument specifies which
candidate we want to choose in the test (in this case it's index `0`, so we select the function). 

#### Selecting an insertion place (UI)
Now that we have a function for finding insertion candidates and an interface for selecting them,
we can create a function that will combine both to either create a UI dialog or delegate to a mock
in tests:
```kotlin
fun showInsertionChooser(
    editor: Editor,
    expr: RsExpr,
    callback: (InsertionCandidate) -> Unit
) {
    val candidates = findInsertionCandidates(expr)
    if (isUnitTestMode) {
        callback(MOCK!!.chooseInsertionPoint(expr, candidates))
    } else {
        ...
    }
```
In the `else` branch, we could just use a simple dialog, same as for selecting expressions and the
replacement mode. However, I felt that seeing a list like `function foo`, `mod bar`, `mod baz`, `file`
would not be enough -- we should give the user more information about the place where will the
insertion actually be performed. I experimented with
[two approaches](https://github.com/intellij-rust/intellij-rust/pull/4985#issuecomment-588316134) of
what to show when the user has some insertion candidate selected in the dialog.
The first would insert a placeholder comment which would indicate on which line would the constant
be created. The second would just highlight the full scope of the insertion candidate. I liked the
variant with the placeholder comment better, but it had some implementation issues, so I settled
with the highlight.

I noticed that `RsIntroduceParameterHandler` already has a
[custom dialog](https://github.com/intellij-rust/intellij-rust/blob/9d6a43825a49d27dbf49445280bfaa3d7b5e4180/src/main/kotlin/org/rust/ide/refactoring/introduceParameter/ui.kt#L32)
with some highlighting support. It uses the IntelliJ `JBPopupFactory` class to build a UI dialog, so
we will use that too. What we want to add to it is a listener that will highlight the selected candidate
in the opened editor:
```kotlin
class Highlighter(private val editor: Editor) : JBPopupListener {
    private var highlighter: RangeHighlighter? = null
    private val attributes = EditorColorsManager
        .getInstance()
        .globalScheme
        .getAttributes(EditorColors.SEARCH_RESULT_ATTRIBUTES)

    fun onSelect(candidate: InsertionCandidate) {
        val markupModel: MarkupModel = editor.markupModel

        val textRange = candidate.parent.textRange
        highlighter = markupModel.addRangeHighlighter(
            textRange.startOffset, textRange.endOffset,
            HighlighterLayer.SELECTION - 1, attributes,
            HighlighterTargetArea.EXACT_RANGE
        )
    }
    ...
}
```
Now we just need to create the dialog inside the `showInsertionChooser` function and connect it to
the highlighter (I omitted some cosmetic method calls on the popup factory for brevity):
```kotlin
// showInsertionChooser
...
else {
    val highlighter = Highlighter(editor)
    JBPopupFactory.getInstance()
        .createPopupChooserBuilder(candidates)
        // after a candidate is selected by the user, highlight it
        .setItemSelectedCallback { value: InsertionCandidate? ->
            if (value == null) return@setItemSelectedCallback
            highlighter.onSelect(value)
        }
        .setTitle("Choose scope to introduce constant ${expr.text}")
        .addListener(highlighter)
        .createPopup()
}
```

After the `showInsertionChooser` function is done, we will use it in `extractExpression`:
```kotlin
showOccurrencesChooser(editor, expr, occurrences) { occurrencesToReplace ->
    showInsertionChooser(editor, expr) {
        replaceWithConstant(expr, occurrencesToReplace, it, editor)
    }
}
```
And then use the selected insertion candidate inside `replaceWithConstant` (previously we always
inserted the constant before the extracted expression):
```kotlin
private fun replaceWithConstant(
    expr: RsExpr,
    occurrences: List<RsExpr>,
    candidate: InsertionCandidate, // <- this is new
    editor: Editor
) {
    ...
    project.runWriteCommandAction {
        val context = candidate.parent  // here we use the candidate
        val insertedConstant = context.addBefore(const, candidate.anchor)
            as RsConstant
        ...
```

With all of this in place, the user will be able to see the scope of the insertion candidate:

{% include gif.html path="/assets/posts/contributing-4/introduce-constant-scope" w="100%" %}

#### Importing missing types
After we added support for selecting the insertion place, we have to deal with one last (I promise!),
minor issue. It is demonstrated by the following snippet if we decide to create the constant at the
file level:
```rust
mod a {
    fn foo() {
        let x = /*caret*/5;
    }
}
//^ should turn into v
const I: i32 = 5;

mod a {
    use I;

    fn foo() {
        let x = I;
    }
}
```
Did you notice the use statement (`use I;`)? It is required, otherwise the code wouldn't compile
after the refactoring is performed. Therefore, as a last finishing touch, we should import the name
of the constant at each replaced occurrence if it cannot be resolved:
```kotlin
// `replaceWithConstant` function
...
// replace occurrence with name of the constant
val created = factory.createExpression(name)
val element = it.replace(created) as RsPathExpr

// if the path expression could not be resolved, try to import it
if (element.path.reference?.resolve() == null) {
    RsImportHelper.importElements(element, setOf(insertedConstant))
}
```
We use the mighty
[`RsImportHelper`](https://github.com/intellij-rust/intellij-rust/blob/9d6a43825a49d27dbf49445280bfaa3d7b5e4180/src/main/kotlin/org/rust/ide/utils/import/RsImportHelper.kt)
to do the heavy lifting of importing for us.

> In the original PR, I didn't include the condition which makes sure that the import only happens
> if the reference is unresolved. [`lancelote`](https://github.com/lancelote) later
> [found out](https://github.com/intellij-rust/intellij-rust/issues/5377)
> during testing that this can produce invalid code when the extracted expression is not located inside
> any `mod`, so I fixed it in a follow-up [PR](https://github.com/intellij-rust/intellij-rust/pull/5379).

And that's it! :tada:

# Wrapping it up
We saw that by leveraging a lot of existing plugin functionality, we were able to implement a new
refactoring action relatively easily[^6]. This is how the final refactoring looks like in action:

[^6]: Not counting the tests, the PR added 255 lines of code. Not bad at all.

{% include gif.html path="/assets/posts/contributing-4/introduce-constant-final" w="100%" %}

The refactoring was introduced in this [PR](https://github.com/intellij-rust/intellij-rust/pull/4985).
It took a few months to merge it, but overall it was a pretty smooth process. And as usual, the
maintainers (in this case [`vlad20012`](https://github.com/vlad20012)) helped me to handle various
corner cases and smooth out rough edges.

This post was again pretty long and I couldn't explain the refactoring fully step-by-step, since a
lot of the code was copied from existing refactorings. So if you're reading this, thanks for sticking
with me up until the end of this post! If you have any comments, let me know on [Reddit](https://www.reddit.com/r/rust/comments/jgq9zk/contributing_to_the_intellijrust_plugin_introduce/).

# Footnotes
