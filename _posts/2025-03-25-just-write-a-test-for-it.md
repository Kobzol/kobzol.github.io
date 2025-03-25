---
layout: "post"
title: "Just write a test for it"
date: "2025-03-25 16:00:00 +0100"
categories: rust
reddit_link: https://www.reddit.com/r/rust/comments/1jjm289/just_write_a_test_for_it/
---

> This is a short appreciation post about Rust continuously guiding me towards doing The Right Thing™.

[Google Summer of Code 2025](https://summerofcode.withgoogle.com/) is just around the corner, which means that a bunch of new contributors started sending pull requests to various Rust projects. One of the most popular projects seems to be [bors](https://github.com/rust-lang/bors), a from-scratch implementation of a merge queue bot that we aim to use to manage pull requests in the main [Rust compiler repository](https://github.com/rust-lang/rust).

In the past couple of weeks, I have reviewed and merged tens of PRs in bors. Sadly, soon after I figured out that some of them broke the (staging) deployment of the bot. This was quite annoying, because I was deliberately trying to design the bot, tests and CI so that something like this shouldn't happen. In practice, we would probably detect this issue in the staging environment, so it hopefully wouldn't reach production, but it's still a situation that I would like to avoid as much as possible.

After investigating for a bit, I realized that the issue was in an SQL migration that looked something like this:

```sql
ALTER TABLE foo ADD COLUMN bar NOT NULL;
```

It looked innocent enough at a first glance, until I realized that adding a `NOT NULL` column to an already populated table without providing some `DEFAULT` value for the existing rows is not a good idea. This wasn't caught by the existing test suite (even though it runs almost 200 end-to-end tests), because it always starts from an empty database, applies all migrations and only then runs the test code.

I fixed the bug, but I didn't want to stop there. My programming experience[^matklad] has taught me to (almost) always try to figure out how can I make sure that a specific bug (or ideally a whole class of bugs) won't ever happen again after we first fix it. In this case, it seemed a bit tricky at first though, as the problem was in the structure of arbitrary SQL statements.

[^matklad]: And matklad's [blog posts](https://matklad.github.io/2021/05/31/how-to-test.html).

I started by adding a [warning](https://github.com/rust-lang/bors/pull/251/commits/35b6461cf609eba76fce36e17e667124cb41f90a) to the bors development guide, urging people not to write migrations like this. While this is better than nothing, it's clear that in practice, documentation alone is a very weak protection against similar bugs.

If this was any other technology or language, I would most likely stop there and just call it a day. But with Rust, I somehow feel encouraged (and empowered!) to go the extra mile and try to make sure that I did everything I could to prevent future problems (and urgent pings when something breaks :) ).

But what could we do here? Surely we won't *parse and examine SQL queries* just for a single test?

…Well, after thinking about it for a while, why couldn't we? I knew that there is a crate for parsing SQL called [sqlparser](https://github.com/apache/datafusion-sqlparser-rs). I was worried that it would have hundreds of dependencies and would be overkill for writing a single test, but when I added it as a `dev` dependency, I found out that it only has around three tiny dependencies (that can even be disabled if needed) and compiles pretty quickly.

Standing on the shoulder of giants and armed with a production-grade SQL parser, I started writing an integration test that goes through the `migrations` directory, parses each SQL file and detects situations where a `NOT NULL` column is added without a `DEFAULT` clause. `sqlparser` supports the [Visitor](https://docs.rs/sqlparser/latest/sqlparser/ast/trait.Visitor.html) pattern, which made the implementation quite easy. My solution is probably not bulletproof and there are certainly some cases that it could miss, but it should be enough to find the problematic situation in typical migration queries.

The goal of this blog post isn't to show how to use `sqlparser`, so I won't dig into it, but if you're interested, you can examine the full test code below (it's just ~100 lines of code, excluding imports):

<details markdown="1" style="margin-bottom: 10px;">
<summary>Test code</summary>

```rust
use itertools::Itertools;
use sqlparser::ast::{
    AlterColumnOperation, AlterTableOperation, ColumnOption, Ident, ObjectName,
    Statement, Visit, Visitor,
};
use sqlparser::dialect::PostgreSqlDialect;
use sqlparser::parser::Parser;
use std::collections::{BTreeSet, HashSet};
use std::ffi::OsStr;
use std::ops::ControlFlow;
use std::path::PathBuf;

struct CheckNotNullWithoutDefault {
    error: Option<String>,
    columns_set_to_not_null: HashSet<(ObjectName, Ident)>,
    columns_set_default_value: HashSet<(ObjectName, Ident)>,
}

impl Visitor for CheckNotNullWithoutDefault {
    type Break = ();

    fn pre_visit_statement(&mut self, statement: &Statement) -> ControlFlow<Self::Break> {
        if let Statement::AlterTable {
            operations, name, ..
        } = statement
        {
            for op in operations {
                match op {
                    AlterTableOperation::AddColumn { column_def, .. } => {
                        let has_not_null = column_def
                            .options
                            .iter()
                            .any(|option| option.option == ColumnOption::NotNull);
                        let has_default = column_def
                            .options
                            .iter()
                            .any(|option| matches!(option.option, ColumnOption::Default(_)));
                        if has_not_null && !has_default {
                            self.error = Some(format!(
                                "Column `{name}.{}` is NOT NULL, but no DEFAULT value was configured!",
                                column_def.name
                            ));
                            return ControlFlow::Break(());
                        }
                    }
                    AlterTableOperation::AlterColumn { column_name, op } => match op {
                        AlterColumnOperation::SetNotNull => {
                            self.columns_set_to_not_null
                                .insert((name.clone(), column_name.clone()));
                        }
                        AlterColumnOperation::SetDefault { .. } => {
                            self.columns_set_default_value
                                .insert((name.clone(), column_name.clone()));
                        }
                        _ => {}
                    },
                    _ => {}
                }
            }
        }
        ControlFlow::Continue(())
    }
}

impl CheckNotNullWithoutDefault {
    fn compute_error(self) -> Option<String> {
        if let Some(error) = self.error {
            return Some(error);
        }

        let missing_default = self
            .columns_set_to_not_null
            .difference(&self.columns_set_default_value)
            .collect::<BTreeSet<_>>();
        if !missing_default.is_empty() {
            return Some(format!(
                "Column(s) {} were modified to NOT NULL, but no DEFAULT value was set for them",
                missing_default.iter().map(|v| format!("{v:?}")).join(",")
            ));
        }

        None
    }
}

/// Check that there is no migration that would add a NOT NULL column (or make an existing column
/// NOT NULL) without also providing a DEFAULT value.
#[test]
fn check_non_null_column_without_default() {
    let root = env!("CARGO_MANIFEST_DIR");
    let migrations = PathBuf::from(root).join("migrations");
    for file in std::fs::read_dir(migrations).unwrap() {
        let file = file.unwrap();
        if file.path().extension() == Some(OsStr::new("sql")) {
            let contents =
                std::fs::read_to_string(&file.path()).expect("cannot read migration file");

            let ast = Parser::parse_sql(&PostgreSqlDialect {}, &contents).expect(&format!(
                "Cannot parse migration {} as SQLL",
                file.path().display()
            ));
            let mut visitor = CheckNotNullWithoutDefault {
                error: None,
                columns_set_to_not_null: Default::default(),
                columns_set_default_value: Default::default(),
            };
            ast.visit(&mut visitor);

            if let Some(error) = visitor.compute_error() {
                panic!(
                    "Migration {} contains error: {error}",
                    file.path().display()
                );
            }
        }
    }
}
```

</details>

As is typical with Rust, the test started working on the first try. But what was more amazing to me was the simplicity with which I was able to achieve all of this. It took me around 10 minutes from thinking "could I *actually parse* the SQL?" to getting a working test, using a crate that I haven't ever used before. I didn't even read the documentation apart from copying one line of code that bootstrapped the parsing process; I built the test simply by examining and following autocompletion hints[^autocomplete]. Who needs AI when you can do *vibe coding* using a great type system and a powerful IDE :)

[^autocomplete]: The *old-school* auto-completion, without any AI involved :) Well, IntelliJ does use some machine learning to (re)order the autocompletion results, but that's a far cry from using an actual LLM.

*[LLM]: Large Language Model

If you're curious, the fix and the test was implemented in [this PR](https://github.com/rust-lang/bors/pull/251). Apart from parsing the SQL query, I also considered an alternative testing approach that I might implement in the future: go through each migration one by one, and insert some dummy data into the database before applying it, to make sure that we test each migration being applied on a non-empty database. The data would either have to be generated automatically based on the current database schema, or we could commit some example DB dataset together with each migration, to make sure that we have some representative data sample available.

So, the next time you're wondering "should I write a test or hope that this won't ever happen again?", just try to write the test, even if it sounds annoying at first. With Rust (and some crates), it might not be so difficult after all :)

If you have any comments, let me know on [Reddit]({{ page.reddit_link }}).
