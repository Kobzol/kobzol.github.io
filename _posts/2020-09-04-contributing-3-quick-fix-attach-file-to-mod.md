---
layout: post
title:  "Contributing to Intellij-Rust #3: Quick fix to attach file to a module"
date:   2020-09-04 18:07:00 +0200
categories: rust intellij
reddit_link: https://www.reddit.com/r/rust/comments/inpsiq/contributing_to_the_intellijrust_plugin_quick_fix/
--- 
This post is part of a [series]({% post_url 2020-08-23-contributing-0-setup %}) in which I describe
my contributions to the [IntelliJ Rust](https://github.com/intellij-rust/intellij-rust) plugin.

- Previous post: [#2 Intention to substitute an associated type]({% post_url 2020-08-25-contributing-2-subst-assoc-type-int %})
- Next post: [#4 Introduce constant refactoring]({% post_url 2020-10-19-contributing-4-introduce-constant-refactoring %})

In this post we'll improve an inspection that checks whether a Rust file is included in the
module hierarchy of the current crate. More specifically, we will implement a quick fix that will attach
the file to some existing `mod` so that the user doesn't have to do it by hand. I'll explain what are
inspections and quick fixes and we will also deal with UI for the first time, as we'll build a basic dialog
for selecting the target module.

You can find the original PR that I will go through [here](https://github.com/intellij-rust/intellij-rust/pull/5490) (spoiler alert!).
This functionality was also further improved by [#5766](https://github.com/intellij-rust/intellij-rust/pull/5766)
and [#5937](https://github.com/intellij-rust/intellij-rust/pull/5937).

# Finding an issue
Last year I sent [a PR](https://github.com/intellij-rust/intellij-rust/pull/3826) to the plugin
which added a notification if some opened Rust file is not included in any module of the current
crate. Even though it was nice that a warning was shown to the user, it was still quite annoying that
users had to add the file to a module manually, as was noticed in [this issue](https://github.com/intellij-rust/intellij-rust/issues/5488).
Since this behaviour could easily be automated, I decided to implement a quick fix that would do it. 

# Inspections and quick fixes
First we have to understand what **inspections** are. We have already talked about *intentions*,
simple actions that you can invoke manually on a selected piece of code. Inspections are in contrast
automatic -- they scan the PSI structure of your code after each change and if they find some problem,
they will typically mark the code with an annotation. Their input is a PSI element and their output
is a set of annotations of various levels -- warnings, weak warnings, errors, etc.
Inspections in the plugin use the [Visitor pattern](https://en.wikipedia.org/wiki/Visitor_pattern)
-- they select which types of PSI elements they want to check (usually just a few of them) to avoid
doing too much work after every code change.  

For example, the `RsUnresolvedReferenceInspection` inspection marks unresolved references with an error
annotation:

![Unresolved reference annotation](/assets/posts/contributing-3/annotation.png)

Inspections often offer a set of code actions called **Quick fixes** that can resolve the problematic
situation. Quick fix is basically the same thing as an intention, but it is offered automatically by
inspections on specific PSI elements when they contain some problem. In the above example we can see
that there is a quick fix offered which will import the missing type.

> Currently, the `RsUnresolvedReferenceInspection` only annotates unresolved references if it can
offer some quick fix to solve the problem, otherwise it is turned off to reduce false positives.
You can find more [here](https://github.com/intellij-rust/intellij-rust/issues/3146).

Currently, there are about 30 inspections in the plugin, but there are also other things
that can add annotations to PSI elements, for example annotators. We'll talk about those in a later
blog post.

# Detached file inspection
The `RsDetachedFileInspection` inspection checks whether a Rust file is included in the module hierarchy.
If not, it cannot be properly analyzed by the plugin (and it will not be compiled by `rustc`), so a warning is emitted.
This inspection is slightly special, because it works on a file level. Not that files are not PSI
elements ([they are](https://github.com/intellij-rust/intellij-rust/blob/9071ee1b93f488cf63fa87023b109b2db4b9d6bd/src/main/kotlin/org/rust/lang/core/psi/RsFile.kt#L68)),
but they need a different UI than most other elements. Instead of a squiggly line below an element,
you get a notification panel at the top of the file if the inspection finds some problem:

![Detached file annotation](/assets/posts/contributing-3/annotation2.png)

This inspection was originally implemented with a different IntelliJ API (it actually wasn't an
inspection, but a [notification provider](https://github.com/intellij-rust/intellij-rust/pull/5490/files#diff-751212656c4415e34e7fbf9863d03336))
before this PR, so I had to refactor it to improve testability and add support for quick fixes. I won't talk about this
refactoring here, as it's not very interesting and I mainly want to talk about the quick fix anyway.
Instead, I'll describe how the inspection looked like after the refactoring, but before implementing the
quick fix and then we'll go through the process of implementing the quick fix.

This is the declaration of the inspection along with its most important method:
```kotlin
class RsDetachedFileInspection : RsLocalInspectionTool() {
    override fun checkFile(
        file: PsiFile,
        manager: InspectionManager,
        isOnTheFly: Boolean
    ): Array<ProblemDescriptor>? {
        ...
    }
```

Inspections in the plugin inherit from the `RsLocalInspectionTool` class. If they want to annotate
individual PSI elements, they can override the `buildVisitor` method to build a PSI visitor that
traverses the PSI tree and checks individual elements of interest for possible issues. In this case,
we want to annotate whole files, so this inspection overrides the `checkFile` method. The `file` parameter
contains the file to be checked, while the `manager` is an object that you can use to create annotations
(`ProblemDescriptor`s) that are then returned from this method. The last parameter (`isOnTheFly`) states if
the inspection was invoked "on-the-fly" (automatically after a code change) or if it was invoked
manually (e.g. you can inspect your whole project with the `Analyse -> Inspect Code` action).
I have never used this parameter so far, but I suppose that you can decide to avoid some expensive
checks if it's set to `true` to speed up the analysis.

So, what does this inspection do?

1. First it checks that the given file is actually a Rust file, as you probably don't want to show
a warning about module attachments in e.g. CSS files.

    ```kotlin
val rsFile = file as? RsFile ?: return null
    ```

2. Then it checks if the inspection is enabled (if you're not a fan of some specific inspection,
you can disable it via the UI).

    ```kotlin
if (!isInspectionEnabled(file.project, file.virtualFile)) return null
    ```

3. After that it checks if there is any available Cargo project for the current file. As discussed in the
[last post]({% post_url 2020-08-25-contributing-2-subst-assoc-type-int %}#deciding-when-to-offer-the-intention),
`Project` is an important class that holds the context of the currently opened IntelliJ project. However,
it is not Cargo-specific, therefore to gain information about Cargo, we have to access its extension
attribute `cargoProjects`, which holds an instance of `CargoProjectsService`. This service manages everything
Cargo-related, it finds and attaches `Cargo.toml` files, finds information about the currently installed
Rust toolchain, etc. The plugin's representation of the Cargo project model is non-trivial, so I won't
explain it in detail here, you can find more information about it in the
[architecture documentation](https://github.com/intellij-rust/intellij-rust/blob/master/ARCHITECTURE.md#project-model)
of the plugin.

    If the service is not initialized or if there are no `Cargo.toml` files in the current
    project or if the current Rust file is not inside the `src` directory of any crate in the project
    (`findProjectForFile`), the inspection will bail out. In such case another part of the plugin
    (`NoCargoProjectNotificationProvider`) will show a warning to the user.

    ```kotlin
    val cargoProjects = file.project.cargoProjects
    if (!cargoProjects.initialized) return null
    
    // Handled by [NoCargoProjectNotificationProvider]
    if (cargoProjects.findProjectForFile(file.virtualFile) == null) return null
    ```

4. Now finally comes the main logic of the inspection, which boils down to a single condition,
because the heavy duty is implemented by the rest of the plugin's infrastructure. The `crateRoot`
attribute of a `RsFile` returns the root file of the crate where the file is attached (usually
it is `lib.rs` or `main.rs`). If the attribute is `null` (and we already know that there is some
existing crate where the file could be attached thanks to the earlier checks), the inspection
knows that the file is detached and it should therefore show a warning.

    The `createProblemDescriptor` method is used to create a file-level annotation. We specify what
    file are we talking about, what should be the annotation text and severity (warning, error, etc.).
    The penultimate argument should be an array of quick fixes that will be offered to the user to
    resolve the issue. Currently it is empty[^1], later we will add a new quick fix to it that will
    attempt to attach the file to some existing module.

    ```kotlin
    if (rsFile.crateRoot == null) {
        return arrayOf(
            manager.createProblemDescriptor(
                file,
                "File is not included in module tree, analysis is not available",
                isOnTheFly,
                emptyArray(),
                ProblemHighlightType.WARNING
            )
        )
    }
    ```

The inspection is quite simple and rather useful, but it could be much better if it could not only
warn about the situation, but also resolve it right away. So let's write a quick fix that will do just that.

[^1]: If you look closely at the PR, the array actually contains a quick fix that suppresses the inspection, but that is not very interesting, so I didn't mention it here.

# Writing a passing test
First, let examine the existing tests of the inspection. Its name is `RsDetachedFileInspection`, so we
already know to search for `RsDetachedFileInspectionTest` (or simply press `Ctrl + Shift + T` on the inspection).
The quick fix will be strongly tied to this inspection, so let's put the quick fix tests together with
the inspection's tests. This is an excerpt of how the inspection's tests look like: 

```kotlin
class RsDetachedFileInspectionTest
    : RsInspectionsTestBase(RsDetachedFileInspection::class) {
    fun `test attached file`() = checkByFileTree("""
        //- lib.rs
            mod foo;
        //- foo.rs
        /*caret*/
    """)

    fun `test not included file`() = checkByFileTree("""
        //- foo.rs
        <warning descr="File is not included in module tree, analysis is not available"></warning>/*caret*/
    """)
    ...
}
```

Same as intentions, inspections also have a dedicated test base class (`RsInspectionsTestBase`), which
provides useful functions for testing inspections and their quick fixes. In the earlier posts, we have always
tested behaviour inside a single file, but for this inspection we will need to test how multiple files behave
together. The `checkByFileTree` method allows you to provide the content of multiple files in a single string,
using the `//- <filename>` markers. `test attached file` checks that there is no warning if the file with the caret
(`foo.rs`) is properly attached. The second test checks that a warning is displayed if the file isn't attached
to any module.

Now, as is our tradition in this blog series, let's begin with writing a test. However, this time, we will
start with a test that passes, instead of fails (mindblowing, I know). But how can we write a passing test
if we didn't implement anything yet? By checking that the quick fix is not offered when it
shouldn't be! Since the quick fix *does not even exist* yet, the test *really should pass* (or something
is very wrong). Later, after we implement the fix, the test will check that we did not enable the fix
in too many situations.

Let's add a new test that checks that our future quick fix is not offered if no module exists that could
attach it:

```kotlin
fun `test fix not available if module is not in the same directory`()
    = checkFixIsUnavailableByFileTree("Attach file", """
    //- lib.rs
        fn test() {}
    //- a/foo.rs
    <warning descr="File is not included in ..."></warning>/*caret*/
""")
```

The `checkFixIsUnavailableByFileTree` is used to check that a specific quick fix is not offered. The 
fix is matched by a prefix given in the first argument. Therefore here we check that there is no quick
fix offered that would begin with the text `Attach file`.

The test passes as expected! And we didn't even have to implement anything, so cool.

Now let's also add a first failing test (finally!), so that we can start to implement
the fix. By writing this test, I have to decide how should the fix behave, which should help guide the
actual implementation.

```kotlin
fun `test attach file to library root`()
    = checkFixByFileTree("Attach file to lib.rs", """
    //- lib.rs
        fn test() {}
    //- foo.rs
    <warning descr="File is not included in ..."></warning>/*caret*/
""", """
    //- lib.rs
        /*caret*/mod foo;

        fn test() {}
    //- foo.rs
""")
```

`checkFixByFileTree` ensures that a fix with the specified prefix is offered, then applies it and
checks that the result is equal to the expected text. In `test attach file to library root`, I
check and define several aspects of how should the fix behave:
1. It should find a corresponding target module and use it in its text (`Attach file to lib.rs`).
2. It should insert a `mod` item to beginning of the target module (`mod foo`).
3. It should navigate the user's caret to the inserted `mod` item.
4. After the fix is performed, the warning should disappear from the original file.

Now that we have a test that can check the basic behaviour of our fix, let's start implementing it!

# Bootstrapping the quick fix
If you search for `*Fix`, you will find that existing quick fixes live in the 
`src/main/kotlin/org/rust/ide/inspections/fixes/` directory. We can look at some existing quick fix
(for example `AddRemainingArmsFix`, which adds missing arms to a `match` expression) and copy it to create
a skeleton for our fix. Our quick fix should attach files to modules, so I named it `AttachFileToModuleFix`.
In our failing test, we wanted our fix to contain the name of the target module (if there is only one
candidate for insertion) in its text (`Attach file to lib.rs`), so let's add the optional target module
name to its constructor right away.

```kotlin
class AttachFileToModuleFix(
    file: RsFile,
    private val targetModuleName: String? = null
) : LocalQuickFixOnPsiElement(file) {
    override fun getFamilyName(): String = text
    override fun getText(): String = "Attach file to ${targetModuleName ?: "a module"}"

    override fun invoke(
        project: Project,
        file: PsiFile,
        startElement: PsiElement,
        endElement: PsiElement
    ) { ... }
```

Since quick fixes are created by the plugin's code (and not automatically be the IDE, like intentions),
they receive the element that they should operate on as a constructor argument. Quick fixes must provide
`getFamilyName` and `getText`, which have the same meaning as for
[intentions]({% post_url 2020-08-25-contributing-2-subst-assoc-type-int %}#bootstrapping-an-intention).
In our fix, the `getText` method either includes the target module name if there is only one candidate, or
it returns the generic `Attach file to a module` text if there are multiple candidates.
The main method that needs to be implemented is `invoke`. It receives a `project`, a `file` in which the
fix was invoked, and an element range on which should the fix be performed. Quick fixes are usually invoked
on a single element, so they only care about `startElement`, which should in our case represent a Rust file.

Before the fix attaches a file to some module, it needs to know what are the available candidate modules
that can actually be used to attach the detached file. For that we first need to implement a function
that will find these candidates. This function will be used by `RsDetachedFileInspection` to check
if the fix should be available (if there are no candidates, the fix shouldn't be shown) and also by the
fix itself to decide if a dialog needs to be shown to the user (if there's only a single candidate,
a dialog is not needed). Because it will be used in two places, I decided to implement it as a public
function on a companion object in the quick fix class.

> We cannot just find the modules once in the inspection and pass them to the quick fix in the constructor,
because fixes shouldn't hold PSI elements other than the one they operate on to avoid leaks.

#### Finding candidate modules #1
The function for finding candidate modules for insertion will look like this:
```kotlin
fun findAvailableModulesForFile(project: Project, file: RsFile): List<RsFile> {
    ...
}
```
It receives a detached file and returns a list of potential files where it could be attached.
Why do we return a list of files and not a list of modules? Well, even though it is possible
to do something like this, i.e. attach a file inside another nested module:
```rust
mod item {
    mod bar;
}
```
in my experience this scenario is not common enough, and if we offered all such possible locations
for insertion to the user, she would be overwhelmed. Therefore our fix will only scan for files where
the detached file can be attached at the root level.

So, how do we actually find the candidate files? We need to understand the Rust module system for that.
Even though I will explain the individual cases needed for the quick fix, describing the whole module system
is outside of scope for this article. You can find detailed explanation for example in [this](http://www.sheshbabu.com/posts/rust-module-system/)
blog post.

First, let's get access to the actual file and directory of our detached `RsFile` so that we can examine
its siblings and parents in the filesystem and create a list of files into which we will store the candidates.
```kotlin
val virtualFile = file.virtualFile ?: return emptyList()
val pkg = project.cargoProjects.findPackageForFile(virtualFile) ?: return emptyList()

val directory = virtualFile.parent ?: return emptyList()
val modules = mutableListOf<RsFile>()
```
While `PsiFile` and `RsFile` represent files as PSI elements that contain syntax trees, `VirtualFile`
represents a raw file with some opaque text content that has a specific path inside some (possibly virtual)
filesystem. Apart from the virtual file of the input and its parent directory, we also lookup the corresponding
package for the file, which more or less corresponds to the crate under whose source directory the file lives.

Let's start with the situation from our first test -- we have a file that is in the same directory
as some crate root (`lib.rs` or `main.rs`). We can get all targets from the package and add their
crate root to the candidate list if it is in the same directory as the detached file:
```kotlin
for (target in pkg.targets) {
    val crateRoot = target.crateRoot ?: continue
    if (crateRoot.parent == directory) {
        modules.addIfNotNull(crateRoot.toPsiFile(project)?.rustFile)
    }
}
```

> A target is something that compiles to a binary artifact, for example a library or an executable.

The `crateRoot` variable is a `VirtualFile`, so that we can check its filesystem location (to see
if it matches the detached file's `directory`). If it indeed does, we convert it back to a `RsFile`
with a helper `toPsiFile` method and `rustFile` attribute, both provided by the plugin.

Before we implement support for finding more candidate files, let's add the quick fix to the inspection
and implement basic functionality of the fix so that our first test passes. After that we will add
support for more candidate scenarios and also create UI for selection of the target module if there
are multiple candidates.

# Adding the quick fix to `RsDetachedFileInspection`
Even though our quick fix does not do anything yet, we have the necessary functions in place to add it
to the inspection so that we can stop thinking about it and only focus on the quick fix itself.

As a reminder, this is the current main logic of the inspection:
```kotlin
if (rsFile.crateRoot == null) {
    return arrayOf(
        manager.createProblemDescriptor(file,
            "File is not included in module tree, analysis is not available",
            isOnTheFly,
            emptyArray(),
            ProblemHighlightType.WARNING
        )
    )
}
```
To add the quick fix to it, first use the `findAvailableModulesForFile` function to see if there
are any candidates for attachment:
```kotlin
val availableModules = AttachFileToModuleFix.findAvailableModulesForFile(project, rsFile)
```

Now we can create the fix if there is at least one candidate. We also pass its name to the fix
if there is only a single candidate:
```kotlin
val attachFix = if (availableModules.isNotEmpty()) {
    val moduleLabel = if (availableModules.size == 1) {
        availableModules[0].name
    } else null
    AttachFileToModuleFix(rsFile, moduleLabel)
} else null
```
and finally, we change the created problem descriptor to include the `attachFix` if it's not null:
```kotlin
return arrayOf(
    manager.createProblemDescriptor(file,
        "File is not included in module tree, analysis is not available",
        isOnTheFly,
        listOfNotNull(attachFix).toTypedArray(),
        ProblemHighlightType.WARNING
    )
)
```
With these modifications, the inspection will offer our quick fix if it finds a detached file. We will
not need to modify the inspection further, all other changes will be done in the quick fix.

# Attaching file to a module
Now that the inspection can actually offer our quick fix and we have (at least one) situation in which
we find some candidate module(s), let's implement the attachment of a file to a module so that our
basic test finally passes. Let's add the necessary code to the `invoke` method of the quick fix:
```kotlin
override fun invoke(
    project: Project,
    file: PsiFile,
    startElement: PsiElement,
    endElement: PsiElement
) {
    val rsFile = startElement as? RsFile ?: return
    val availableModules = findAvailableModulesForFile(project, rsFile)
    if (availableModules.isEmpty()) return

    if (availableModules.size == 1) {
        insertFileToModule(rsFile, availableModules[0])
    } else if (availableModules.size > 1) {
        // unimplemented for now
    }
}
```
First we check that the `startElement` is actually a Rust file and we find the candidate modules for it.
For now we will not handle multiple candidate modules, we will solve it later. Let's implement the
`insertFileToModule` function.

```kotlin
private fun insertFileToModule(file: RsFile, targetFile: RsFile) {
    val project = file.project
    val factory = RsPsiFactory(project)
    ...
}
```
It receives two parameters -- `file` which should be attached and `targetFile` into which we should insert
the corresponding `mod` item that will attach `file` to the module structure. We will need to modify the
PSI structure, so I'm creating a PSI factory right away (we have talked about the PSI factory in the
[last post]({% post_url 2020-08-25-contributing-2-subst-assoc-type-int %}#implementing-the-invoke-method)).

As the next step, we need to find out what should be the name after the mod item (`mod <?>`).
If the input `file` is `mod.rs`, it should be the name of its parent directory, since `mod mod`
is not valid Rust syntax. If it's anything else, we just take its filename:
```kotlin
val name = if (file.isModuleFile) {
    file.virtualFile.parent.name
} else {
    file.virtualFile.nameWithoutExtension
}
```
Then we use the factory to create the PSI element representing a `mod` item. It it fails, we show a
fire-and-forget UI notification (called a balloon) to notify the user:
```kotlin
val modItem = factory.tryCreateModDeclItem(name)
if (modItem == null) {
    project.showBalloon("Could not create `mod ${name}`", NotificationType.ERROR)
    return
}
```
and finally, we insert the `mod` item as the first child of the target module:
```kotlin
val child = mod.firstChild
val inserted = if (child == null) {
    mod.add(modItem)
} else {
    mod.addBefore(modItem, child)
} as RsModDeclItem
inserted.navigate(true)
```
PSI manipulation methods (like `add` or `addBefore`) receive a PSI element that they copy, attach
to the PSI structure and return the inserted element. Since the return type of these methods is a generic
`PsiElement`, if we want to get the inserted element with a more specific type, we have to cast it back with
the `as` operator[^2]. After we insert the element, we call the `navigate` method to move the user's
caret to the location of the inserted item.

[^2]: We know the type of the element that we have inserted into the PSI, so the unconditional `as` cast `Should Be Safe™`.

> Astute readers might notice that inserting the `mod` item as the first child might not be a good
idea if the target file contains attributes at its beginning, as they must be the first
children of the file to work. This was later fixed in [this PR](https://github.com/intellij-rust/intellij-rust/pull/5937),
which also tries to insert the `mod` item after existing `mod` items in the target file. Since this
post is already long enough, you can check the PR if you want to learn more. 

And with these changes, the first failing test finally passes! Phew, that was a lot of work. To recap, we:
1. Created a function that finds candidate modules for a given file.
2. Created a quick fix that attaches a file to a given candidate module (so far there must be exactly one candidate).
3. Modified `RsDetachedFileInspection` to offer our new quick fix to the user.

Now we "just" need to add support for finding more candidate modules and finally create a UI dialog
for selecting the target module if there are multiple candidates.

#### Finding candidate modules #2
Right now, we can only attach files to `lib.rs` or `main.rs` that are in the same directory as the detached
file. Now we will add support for more situations. We will check several paths relative to the detached file
to see if there is a valid Rust file that could be used for attaching the detached file. To reuse
this code, let's first create the following helper function:
```kotlin
private fun findModule(
    root: RsFile,
    project: Project,
    file: VirtualFile?
): RsFile? {
    if (file == null) return null
    val module = file.toPsiFile(project)?.rustFile ?: return null
    if (module == root || module.crateRoot == null) return null
    return module
}
```
The `root` parameter contains the detached file and `file` contains some file path. If the file path
exists, contains a valid Rust file that is not equal to `root` and that is itself attached, the
function will return it as a candidate module for insertion.

Now let's go through the individual situations that can occur.

1. You can attach a file by adding it's name to a `mod` item in a `mod.rs` file in the same directory.
This is a test that I wrote to check this situation:
```kotlin
fun `test attach file to a local mod file`()
    = checkFixByFileTree("Attach file to mod.rs", """
    //- lib.rs
        mod a;
    //- a/mod.rs
    //- a/foo.rs
    <warning descr="File is not included in ..."></warning>/*caret*/
""", """
    //- lib.rs
        mod a;
    //- a/mod.rs
        /*caret*/mod foo;
    //- a/foo.rs
""")
```
and here is the code that I added to `findAvailableModulesForFile` to handle it:
```kotlin
modules.addIfNotNull(findModule(file, project,
    directory.findFileByRelativePath(RsConstants.MOD_RS_FILE))
)
```
2. In Rust edition `2018`, you can also attach files from a child directory from any Rust file, as
demonstrated in this test:
```kotlin
@MockEdition(CargoWorkspace.Edition.EDITION_2018)
fun `test attach file to a parent mod file`() 
    = checkFixByFileTree("Attach file to a.rs", """
    //- lib.rs
        mod a;
    //- a.rs
    //- a/foo.rs
    <warning descr="File is not included in ..."></warning>/*caret*/
""", """
    //- lib.rs
        mod a;
    //- a.rs
        /*caret*/mod foo;
    //- a/foo.rs
""")
```
The `@MockEdition` is a test configuration annotation that runs the test in the `2018` edition.

    Handling this situation is simple, we just check if the package uses edition `2018` and then try
    to find a file in the parent directory with the name of the detached file's directory:
    ```kotlin
    if (pkg.edition == CargoWorkspace.Edition.EDITION_2018) {
        modules.addIfNotNull(findModule(file, project,
            directory.parent?.findFileByRelativePath("${directory.name}.rs"))
        )
    }
    ```
    If the detached file is in directory `foo` and there is a `foo.rs` file in the parent directory,
    we add it as a candidate file for insertion.
3. The other two remaining cases occur if the detached file is a module file
(`mod.rs`). In this case we also scan the crate roots and `mod.rs` in a parent directory, so the only
difference is that we check the parent directory of the detached file:

    ```kotlin
    if (file.isModuleFile) {
        // module file in parent directory
        modules.addIfNotNull(findModule(file, project,
            directory.parent?.findFileByRelativePath(RsConstants.MOD_RS_FILE))
        )
    
        // package target roots in parent directory
        for (target in pkg.targets) {
            val crateRoot = target.crateRoot ?: continue
            if (crateRoot.parent == directory.parent) {
                modules.addIfNotNull(crateRoot.toPsiFile(project)?.rustFile)
            }
        }
    }
    ```
    The third case that can happen with the `2018` edition is not really applicable here, as it
    only makes sense for files that are not named `mod.rs`.

Now our quick fix (hopefully) supports all cases where the detached file could be attached and we are
almost at the finish line! But we still haven't solved the situation where there might be multiple
candidates for insertion - in such a case the user should choose where does she want to attach the file.

# Selecting a module for attachment (tests)
Ultimately, we want to show the user a dialog where the target module could be selected. However,
it is quite difficult to use UI in tests (it would also slow them down a lot), so the plugin uses
mocking in situations where a UI element would be otherwise shown to the user.

We thus have to design an interface that will be used for selecting a module. This interface
will then be implemented both by a UI dialog (to be shown in the IDE) and by a mock implementation in tests.
In this case the interface is very simple, it's just a single function that receives a detached file,
a list of candidate modules and returns a module to which should the detached file be attached. Since
it's a single function, I didn't even bother with a proper `interface` and just created an alias for a
function signature in `AttachFileToModuleFix.kt`:
```kotlin
typealias ModuleAttachSelector = (
    file: RsFile,
    availableModules: List<RsFile>
) -> RsFile?
```
Why is the return type nullable? Well, it does not make much sense in tests, but in the UI the user
could always press `Escape` or close the dialog, so we have to deal with the situation where the
attachment is canceled.

Now we need a way to mock this interface during tests. This is usually done by creating a singleton
`MOCK` object that is temporarily set during test execution. The quick fix will then check if it's running
inside a test and if yes, it will use the mocked object instead of opening the UI. This is how the
mock setup function looks like:
```kotlin
private var MOCK: ModuleAttachSelector? = null

@TestOnly
fun withMockModuleAttachSelector(
    mock: ModuleAttachSelector,
    f: () -> Unit
) {
    MOCK = mock
    try {
        f()
    } finally {
        MOCK = null
    }
}
```
We set the mock, execute some action (which will run the quick fix in the test) and then reset it back to
`null`.

> The `@TestOnly` annotation marks that the function should only be called from test code.

In the test class, I created a new method for testing module selection:
```kotlin
private fun checkFixWithMultipleModules(
    @Language("Rust") before: String,
    @Language("Rust") after: String,
    moduleName: String
) {
    withMockModuleAttachSelector({ _, modules ->
        modules.find { it.name == moduleName }
    }) {
        checkFixByFileTree("Attach file to a module", before, after)
    }
}
```
Basically, it simply wraps `checkFixByFileTree` so that during its execution, the `MOCK` will use
an implementation that selects the target module according to the passed `moduleName` argument.
Let's write a basic test using this method:
```kotlin
fun `test attach file to selected module 1`()
    = checkFixWithMultipleModules("""
    //- main.rs
        fn main() {}
    //- lib.rs
        fn test() {}
    //- foo.rs
    <warning descr="File is not included in ..."></warning>/*caret*/
""", """
    //- main.rs
        /*caret*/mod foo;

        fn main() {}
    //- lib.rs
        fn test() {}
    //- foo.rs
""", "main.rs")
```
In this situation `foo.rs` can be attached either to `lib.rs` or to `main.rs`. We use the third argument
to select `main.rs`.

Now that we have a test, let's implement module selection inside the quick fix. If you remember the
`invoke` method, it had an unimplemented case if there were multiple modules. Let's change that:
```kotlin
if (availableModules.size == 1) {
    insertFileToModule(rsFile, availableModules[0])
} else if (availableModules.size > 1) {
    selectModule(rsFile, availableModules)?.let { insertFileToModule(rsFile, it) }
}
```
and implement the `selectModule` function (only for tests now):
```kotlin
private fun selectModule(file: RsFile, availableModules: List<RsFile>): RsFile? {
    if (isUnitTestMode) {
        val mock = MOCK
            ?: error("You should set mock module selector via withMockModuleAttachSelector")
        return mock(file, availableModules)
    }

    // UI will be handled here
}
```
The `isUnitTestMode` is a global variable that can be examined to check if the current code executes
under a unit test. In such case we require the `MOCK` to be set, otherwise there wouldn't be any available
module selection implementation (since we cannot use the UI in tests). Then we simply call the mock and
that's it. This is enough to make our test with multiple candidates pass.

# Selecting a module for attachment (UI)
The last thing that remains is to implement the UI interface. Before we do that, I have to mention
the concept of **write actions**. If you want to perform PSI modifications (add/remove/change source code
elements) inside your plugin actions (intentions, quick fixes, refactorings, etc.), you need to do it
inside a write action. It is an IntelliJ system that allows the IDE to perform transactions (everything
inside a single write action can be rolled back with `Ctrl + Z`) and some optimizations (if you are not
in a write action, the IDE knows that you can only do reads). During a write action, the IDE is in a
"lockdown" state, therefore these actions should be as short as possible. For example, you should not
search for all references of an element inside a project or display UI inside of write actions, since these
things can take a long time to finish.

Maybe you have noticed that in our quick fix we modify PSI like it's no big deal. That's because quick
fixes implicitly run inside a write action for convenience, since most of them do in fact modify PSI.
That is problematic if we want to show UI though, so we have to turn this functionality off and
enable it only for the part of the fix that actually modifies PSI. To do that, we have to override the
`startInWriteAction` method of the quick fix and return `false` from it (by default it returns `true`):
```kotlin
override fun startInWriteAction(): Boolean = false
```
and then we have to wrap the code in the `insertFileToModule` function that actually modifies PSI
by a write action:
```kotlin
WriteCommandAction.runWriteCommandAction(project) {
    val child = mod.firstChild
    val inserted = if (child == null) {
        mod.add(modItem)
    } else {
        mod.addBefore(modItem, child)
    } as RsModDeclItem
    inserted.navigate(true)
}
```

With these changes in place, the quick fix will behave in the same way as before, but now we can actually
use UI elements inside of it. What should the UI look like? We will offer a list of candidate modules to the
user and she has to select one of them. That sounds like a good use case for a select box (also
known as a combo box or a drop-down list in the Java/C# world), so that's what I decided to use. Thanks to Kotlin,
the definition of UI is actually pretty terse. As a reminder, we're adding UI to the `selectModule` function, you
can find its code a few paragraphs above. First, we'll create a combo box containing the candidate modules:
```kotlin
val box = ComboBox<RsFile>()
with(box) {
    for (module in availableModules) {
        addItem(module)
    }
    renderer = SimpleListCellRenderer.create("") {
        val root = it.containingCargoPackage?.rootDirectory
        val path = it.containingFile.virtualFile.pathAsPath
        (root?.relativize(path) ?: path).toString()
    }
}
```
The paths of the candidate module files are rendered relative to the crate root directory to avoid
long absolute paths. After we have our combo box, we put it inside a dialog, which is almost
a one-liner thanks to the `dialog` function from the IntelliJ API:
```kotlin
val dialog = dialog("Select a module", panel {
    row { box(CCFlags.growX) }
}, focusedComponent = box)
```
and finally, we show the dialog and if it finished successfully, we return the selected module:
```kotlin
return if (dialog.showAndGet()) {
    box.selectedItem as? RsFile
} else {
    null
}
```
And that's the final piece of the quick fix! With the UI in place, it looks like this:

{% include gif.html path="/assets/posts/contributing-3/attach" w="100%" %}

# Wrapping it up
After implementing the quick fix, I sent a [PR](https://github.com/intellij-rust/intellij-rust/pull/5490)
named `INSP: add attach file to module quick fix`. As I mentioned in the beginning of this post,
it also included a refactoring of the inspection from a notification provider. In the PR I also added
another quick fix to suppress the inspection, reminded myself about the existence of write actions :smile:
and learned about the useful `navigate` function. Even though this PR was not trivial and it entailed
some discussion with the maintainers, it only took five days to merge it.

Later it was [found](https://github.com/intellij-rust/intellij-rust/issues/5903) [out](https://github.com/intellij-rust/intellij-rust/issues/5934)
by users of the plugin that there are some issues with the fix, so I sent [two](https://github.com/intellij-rust/intellij-rust/pull/5766)
[additional](https://github.com/intellij-rust/intellij-rust/pull/5937) PRs to fix those. I incorporated
these fixes in the text of this post.

If you're reading this, thanks for sticking with me up until the end of this post. If you have any
comments, let me know on [Reddit](https://www.reddit.com/r/rust/comments/inpsiq/contributing_to_the_intellijrust_plugin_quick_fix/).

# Footnotes
