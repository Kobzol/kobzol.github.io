---
layout: "post"
title: "Investigating and fixing a nasty clone bug"
date: "2025-12-30 15:00:00 +0100"
categories: rust
reddit_link: https://www.reddit.com/r/rust/comments/1pzjj94/investigating_and_fixing_a_nasty_clone_bug/
---

Recently I found myself battling with [another]({% post_url 2025-02-23-tokio-plus-prctl-equals-nasty-bug %}) nasty bug. It took me several hours to understand what is happening, and once I found it, it turned out that the cause of the bug is relevant to the [Ergonomic cloning](https://rust-lang.github.io/rust-project-goals/2025h2/ergonomic-rc.html) initiative that is currently being discussed a lot. So I thought that it would be a good candidate for a blog post.

## Context

I'm currently trying to finally bring the [bors](https://github.com/rust-lang/bors) GitHub merge bot to production, so I spent many days in the past weeks fixing various possible race conditions, making its implementation more robust and improving its test suite.

The `bors` test suite is mostly integration-based; it has very few what you could call "unit tests". In most tests, we spawn the whole bors web application, connect it to a real running instance of Postgres, apply database migrations, send HTTP requests that emulate GitHub webhooks to it, and let it communicate over the network with a fake HTTP server that emulates GitHub endpoints[^bors-testsuite]. The mocked HTTP GitHub endpoints are implemented using the cool [wiremock](https://docs.rs/wiremock/latest/wiremock/) crate. A typical bors test looks something like this:

```rust
#[sqlx::test]
async fn try_build_failed_modify_labels(pool: sqlx::PgPool) {
    let gh = GitHub::default().with_default_config(
        r#"
[labels]
try_failed = ["+foo", "+bar", "-baz"]
"#,
    );
    run_test((pool, gh), async |ctx: &mut BorsTester| {
        ctx.post_comment("@bors try").await?;
        insta::assert_snapshot!(ctx.get_next_comment_text(()).await?, @r"
            :hourglass: Trying commit pr-1-sha with merge merge-0-pr-1…

            To cancel the try build, run the command `@bors try cancel`.
            ");
        ctx.pr(()).await.expect_added_labels(&[]);
        ctx.workflow_full_failure(ctx.try_workflow()).await?;
        ctx.expect_comments((), 1).await;
        ctx.pr(())
            .await
            .expect_added_labels(&["foo", "bar"])
            .expect_removed_labels(&["baz"]);
        Ok(())
    })
    .await;
}
```

[^bors-testsuite]: I recently had a talk about my experiences with Rust testing, inspired primarily by the bors test suite. Since the recording will probably not be available online, I plan to turn that talk into a blog post Soon™. Stay tuned.

## Where's the body?

While doing a particularly big refactoring, a few tests started failing in a very weird way, by panicking in one of the mocked GitHub [endpoints](https://github.com/rust-lang/bors/blob/main/src/tests/mock/repository.rs#L181). It was a `PATCH` endpoint that was trying to deserialize a JSON payload from the request body, but the body was empty, so the deserialization of course failed. That was very weird, because bors only sends a `PATCH` request at one place in its codebase, and there it does fill the request body. Also, the body was empty only *sometimes*, in some situations it was normally present. That's usually the sign of a wonderful bughunt starting.

The receiving endpoint mocked with `wiremock` contained this deserialization code:

```rust
#[derive(serde::Deserialize)]
struct SetRefRequest {
    sha: String,
}

let data: SetRefRequest = req.body_json().unwrap(); // The test panicked here
```

`bors` uses the [octocrab](https://github.com/XAMPPRocky/octocrab) crate for communicating with GitHub. The code that is used to send the `PATCH` request looked like this:

```rust
let res = repo
    .client()
    ._patch(
        url.as_str(),
        Some(&serde_json::json!({
            "sha": sha.as_ref(),
            "force": matches!(force, ForcePush::Yes)
        })),
    )
.await?;
```

Well, *clearly* I was sending a body on the sender side (a JSON object with two fields, `sha` and `force`), and I was trying to deserialize a request type with the correct shape (the `sha` attribute) on the receiving side. But in some tests, and only after a few calls of the endpoint, the body was suddenly empty. That was super weird.

## Investigation

My usual motto when dealing with weird bugs is "the problem is in your code, not in a dependency", which is correct approximately 99% of the time. So I started debugging the failing tests, and the place where the request is sent in bors, but everything looked correct. I always seemed to send the request with a body, but sometimes it arrived without it. So I started suspecting that a problem might be in some dependency. I naturally suspected `wiremock` first, because it is a much less commonly used crate than `octocrab`, so I started digging into it. The issue tracker didn't contain anything that would sound related, so I went back to the good ol' debugger.

Debugging external Rust crates is not actually that easy. Rust is known for being very abstraction heavy (especially in library code), which can be particularly annoying for step-by-step debugging, and even more when it involves `async` code. Furthermore, if you want to modify the debugged code (e.g. to add more logging), it is not so easy as e.g. in Python, where I could just go to a virtual environment and modify the source code of the dependency manually. If I do that in Rust, Cargo won't actually pick up that the source code of a crate in `$HOME/.cargo/registry/src/...` has been modified (and making modifications here is not a good idea anyway). So I `git clone`d `wiremock` and depended on it locally with `wiremock = { path = "..." }`, so that I could add more logging to it to see what's going on[^patch].

[^patch]: If it was a transitive dependency, I could use the [`[patch]`](https://doc.rust-lang.org/cargo/reference/overriding-dependencies.html#the-patch-section) section in `Cargo.toml`.

But again, that did not end up with anything interesting. Once I went up the call stack, I saw that `wiremock` uses the `hyper` crate to create its HTTP server. And indeed, the `hyper` request arrived with an empty body (sometimes). I did not find it very probable that `hyper` would contain a bug that would just randomly remove request bodies, so I decided to take a look elsewhere.

I still wasn't prepared to believe that this could be a bug in `octocrab`, so I pulled up [wireshark](https://www.wireshark.org/), to find a definitive proof whether the problem is in the sender or the receiver side. Luckily, the communication was on localhost via HTTP (without TLS), so investigating it with TCP/IP dumps was quite easy, and I finally found something useful. The HTTP stream looked something like this:

```http
PATCH /repos/a/b/git/refs/heads/main HTTP/1.1
x-github-api-version: 2022-11-28
content-type: application/json
authorization: Bearer foo
user-agent: octocrab
host: localhost:5555
content-length: 27

{"sha":"foo", force":true}
```

```http
HTTP/1.1 500 Internal Server Error
content-length: 0
```

```http
PATCH /repos/a/b/git/refs/heads/main HTTP/1.1
x-github-api-version: 2022-11-28
content-type: application/json
authorization: Bearer foo
user-agent: octocrab
host: localhost:5555
```

```http
HTTP/1.1 500 Internal Server Error
content-length: 0
```

Notice something strange? The body is missing in the second request! So I finally knew for a fact that the sender caused the issue. So at this point, I had three things in mind:

- Something else (other than my code) is somehow sending invalid HTTP requests to my mocked HTTP endpoints.
- My code contains UB.
- The problem is in `octocrab`.

I found it quite hard to believe the first two options (especially since bors contains no `unsafe` code), so I finally set my sights on `octocrab`. I went to the place where I was creating the `PATCH` request and stepped through the internals of `octocrab`, but the body seemed to be there! Although it was not exactly trivial to check, because HTTP bodies are kind of difficult to inspect; in the general case, they can be streamed, so Rust networking APIs are usually built in a way where you can only consume the body once[^foreshawdowing].

[^foreshawdowing]: This is actually kind of foreshadowing the cause of the bug :)

Since I still couldn't find anything weird even in `octocrab`, I went back to the drawing board, and tried to approach the problem from a different viewpoint. After some more thinking, I asked myself: why is the request even being sent multiple times in the first place? Originally, I did not find that weird, because the failing tests were returning a 500 HTTP response from the mocked endpoint, to simulate a problem with GitHub, and bors implements request retrying, so it seemed like it was working as intended. However, after inspecting the test logs[^traced-test] a bit more, I realized that my own retry code was not actually being triggered! That started sounding really suspicious - why was the request retried then?

[^traced-test]: Using the [traced-test](https://crates.io/crates/traced-test) crate.

After taking another look at the `octocrab` codebase, I realized that it actually implements its own mechanism for request retries, which I had no idea about. And it is enabled by [default](https://github.com/XAMPPRocky/octocrab/blob/4ffda40672944f6d56f84113621df987f014b72b/Cargo.toml#L96)! And sure enough, when I disabled the retry mechanism:

```rust
let client = Octocrab::builder()
    ...
    .add_retry_config(RetryConfig::None)
    .build()
```

The problem with the empty body was gone! :tada: So I finally fixed the problem on the bors side, and since bors was (unintentionally) doing double retries before, disabling the octocrab retry mechanism actually fixed two bugs at once.
I think that this was possibly the first time I found an actual bug in a Rust crate dependency that broke my code in ~7 years of using Rust. Pretty good track record for the Rust ecosystem in my experience so far!

But of course, I couldn't just stop there. I *had* to know what is the original cause of the bug, so that I could report it and fix it.

## Origin of the bug

Once I finally knew that the bug was caused by the `octocrab` retry mechanism, creating a minimum reproducible example was relatively easy:

```rust
async fn handler(body: String) -> impl IntoResponse {
    eprintln!("Received data: {body}");
    StatusCode::INTERNAL_SERVER_ERROR
}

#[tokio::main]
async fn main() {
    let port = 5555;
    std::thread::spawn(move || {
        let runtime = tokio::runtime::Builder::new_multi_thread()
            .enable_all()
            .build()
            .unwrap();
        runtime.block_on(async move {
            let app = Router::new().route("/foo", patch(handler));

            let listener = tokio::net::TcpListener::bind(
                format!("127.0.0.1:{port}")
            )
                .await
                .unwrap();
            axum::serve(listener, app).await.unwrap();
        });
    });

    let client = octocrab::OctocrabBuilder::new()
        .personal_token("foo")
        // .add_retry_config(RetryConfig::None) // <- this fixes the issue
        .base_uri(format!("http://localhost:{port}"))
        .unwrap()
        .build()
        .unwrap();

    #[derive(serde::Serialize)]
    struct Request {
        force: bool,
    }
    let response = client
        ._patch(
            "/foo",
            Some(&Request { force: true }),
        )
        .await
        .unwrap();
    eprintln!("Response: {}", response.status());
}
```
This code printed the following:

```
Received data: {"force":true}
Received data: 
Received data: 
Received data: 
Response: 500 Internal Server Error
```

Exactly as in bors. When the request was sent for the first time, the body was correctly sent
over the wire. But when `octocrab` tried to retry the request, suddenly the body disappeared.

Originally, I did not notice this problem when debugging `octocrab`, because I sort of stopped too soon,
at a place where the HTTP request was passed from `octocrab` to a stack of `tower` middleware.
And at that point the request was still fine! But now it became clear that the problem was somewhere inside
that middleware, which is why it was so hard to find originally.

I wasn't aware of how retrying works in `tower`, and if this is a bug in `octocrab`
or in `tower` (although now I suspected the former). After a bit of digging, I found that
retrying is indeed [implemented](https://github.com/XAMPPRocky/octocrab/blob/35f78b5c07a20ea31f4b4648d1ecc65bf6b09863/src/service/middleware/retry.rs#L49) in `octocrab` with a retry [`Policy`](https://docs.rs/tower/0.5.2/tower/retry/trait.Policy.html), which tells `tower` how to retry a given HTTP request. The most important part is the `clone_request` method:

```rust
fn clone_request(&mut self, req: &Request<OctoBody>)
  -> Option<Request<OctoBody>> {
    match self {
        RetryConfig::None => None,
        _ => {
            // `Request` can't be cloned
            let mut new_req = Request::builder()
                .uri(req.uri())
                .method(req.method())
                .version(req.version());
            for (name, value) in req.headers() {
                new_req = new_req.header(name, value);
            }

            let body = req.body().clone();
            let new_req = new_req.body(body).expect(
                "This should never panic,
                 as we are cloning a components from existing request",
            );
            Some(new_req)
        }
    }
}
```

Notice how the code says "Request can't be cloned", yet it clones the request body like it's not a big
deal :thinking: That looked suspicious, so I looked at how the request body type looks like, at which point the
bug became obvious:

```rust
#[derive(Debug)]
pub struct OctoBody(Arc<RwLock<BoxBody>>);
```

Here is the `Clone` impl, if you haven't noticed the issue yet:

```rust
impl Clone for OctoBody {
    fn clone(&self) -> Self {
        OctoBody(Arc::clone(&self.0))
    }
}
```

Yes, cloning the body just performs a shallow clone of an `Arc`, instead of performing a deep copy of
the whole body (!). And since the body is consumed when the request is sent for the first time, the code
simply started sending an empty body when the request was retried.

This is where the relation to the ergonomic cloning initiative comes in. If we had a clearer distinction
between performing a deep copy vs just cloning a (reference-counted) [Handle](https://smallcultfollowing.com/babysteps/blog/2025/10/13/ergonomic-explicit-handles/) to something, it would likely be much more
obvious that there is a problem with the `.clone()` call.

It still seemed suspicious why this was a silent bug though. Shouldn't it panic somewhere if we try to reuse the same body again? :thinking: If we take a look inside the [`Body`](https://docs.rs/http-body/1.0.1/http_body/trait.Body.html) trait [implementation](https://github.com/XAMPPRocky/octocrab/blob/v0.48.1/src/body.rs#L107) of the `OctoBody`, we see that in the `poll_frame` method, it locks the `RwLock` and forwards the `poll_frame` call into its inner boxed body that it abstracts over:

```rust
impl http_body::Body for OctoBody {
    type Data = Bytes;
    type Error = crate::Error;

    #[inline]
    fn poll_frame(
        self: Pin<&mut Self>,
        cx: &mut Context<'_>,
    ) -> Poll<Option<Result<Frame<Self::Data>, Self::Error>>> {
        let inner = Pin::into_inner(self);
        let mut boxed_body = inner.0.write()
            .expect("RwLock write lock failed");
        Pin::new(&mut *boxed_body).poll_frame(cx) // <-- poll forwarding
    }
    ...
}
```

That sounds like it could cause an issue if the body is being polled even after it has been "consumed" while sending the request for the first time. You might think that if `OctoBody` stored an `RwLock<Option<...>>`, which would be replaced by `None` once the body is consumed, it would make this into a noticeable panic. But `OctoBody` actually already mostly does that! It usually stores a [`http_body_util::Full`](https://docs.rs/http-body-util/latest/http_body_util/struct.Full.html) struct as its boxed `Body` implementation, and that does [exactly that](https://docs.rs/http-body-util/0.1.3/src/http_body_util/full.rs.html#13). So why haven't the code panicked, instead of sending an empty body in a retry?

Well, as it turns out, the `poll_frame` method is actually not ever called again once the request is consumed for the first time. When `hyper` [polls the body](https://github.com/hyperium/hyper/blob/v1.8.1/src/proto/h1/dispatch.rs#L339), it first uses the [`Body::is_end_stream`](https://docs.rs/http-body/1.0.1/http_body/trait.Body.html) method to check if the body is at its end, and if it is, it does not ever poll it again. And the `http_body_util::Full` implementation of course [returns `true`](https://docs.rs/http-body-util/0.1.3/src/http_body_util/full.rs.html#47) from this method once its inner body has been consumed. So when the body is consumed for the first time, it will start returning `true` from `is_end_stream`, and when we then try to reuse the same body in another request, `hyper` will just skip reading the body contents and send an empty body instead. Kind of footgunny if bodies are ever reused!

It is interesting to note that this could have caused an issue only because the `Arc` was combined
with interior mutability (`RwLock`). If there was no interior mutability, performing a shallow
(instead of a deep) clone would likely result at most in a performance degradation, but not a logical
bug. Interior mutability is useful, but it also relaxes some of the benefits we are normally
used to when using Rust!

It was also surprising to me that this bug has existed in the `octocrab` crate for more than [two years](https://github.com/XAMPPRocky/octocrab/pull/297),
but it does not seem like anyone noticed it. I suppose that sending a request to the GitHub API that
both has a body (so it is not a simple `GET` request) and that gets retried (so GitHub returned e.g. a 500 error
the first time the request was sent) is just not that common. It seems like my heavy usage of HTTP integration
testing in bors is uncovering all sorts of interesting issues :laughing:

The bug might look obvious in retrospect, but it took me several hours to debug it, and I was getting pretty desperate after that time. I'm certainly not used to spending so much time debugging a single issue when working with Rust! In hindsight, I should have tried to send the `PATCH` request manually, without `octocrab`. That would give me a hint much sooner that the problem is indeed within `octocrab`. I guess avoided it because of my usual thought of "the bug has to be in my code". Well, the next time, I will probably start suspecting dependencies a bit sooner :sweat_smile:.

After finally understanding what was going on, I reported the issue in the octocrab [issue tracker](https://github.com/XAMPPRocky/octocrab/issues/835) and went to sleep. It was a long day :zzz:.

## Fixing the bug

After I rested for a bit and regained enough motivation to take a look at `octocrab` again a few days later, I took a
shot at fixing the actual issue. The root of the issue was in performing a shallow copy, instead of
copying the whole body contents. That is actually easier said than done, as HTTP request bodies are not exactly
known to be easy to clone, as they could be streamed. However, since `octocrab` does not necessarily has
to be the most blazingly fast :rocket: zero-copy :fire: library under the sun, I figured that a bit of
copying in the common case won't hurt that much.

What I did was to add a separate reference-counted copy of the request body, using the venerable [`bytes`](https://docs.rs/bytes/1.11.0/bytes) crate:

```rust
#[derive(Debug)]
pub struct OctoBody {
    body: Arc<RwLock<BoxBody>>,
    // Copy of the whole body, used for retrying requests
    buffered: Option<Bytes>,
}
```

The `buffered` field is an `Option`, because in the most general case, the body might be streamed, in which case I can't easily turn it into `Bytes` outside of an `async` context. However, at that case, we will now at least no longer send an empty body by mistake, but rather do not perform a retry at all.

In cases where the body is available in a buffered way (which I assume will be in 99% of cases when using `octocrab`), we copy the body contents into `Bytes` when wrapping it into `OctoBody`:

```rust
impl From<Vec<u8>> for OctoBody {
    fn from(buf: Vec<u8>) -> Self {
        let buffered: Bytes = Bytes::from(buf.clone());
        Self::create(http_body_util::Full::from(buf), Some(buffered))
    }
}
```

This pessimistically clones the body contents even if we never actually do a retry, but at least it makes the code work as it should. It might be better to only perform this copy if the `retry` feature of `octocrab` is enabled. Could be an interesting follow-up pull request, if you're interested!

The final piece of the puzzle was adding a method for deep copying the body, which I called `try_clone`:

```rust
/// Try to perform a deep clone of this body
pub fn try_clone(&self) -> Option<Self> {
    self.buffered.as_ref().map(|buffered| {
        Self::create(
            http_body_util::Full::from(buffered.clone()),
            Some(buffered.clone()),
        )
    })
}
```

and then using this method in the `clone_request` method:

```rust
fn clone_request(&mut self, req: &Request<OctoBody>)
    -> Option<Request<OctoBody>> {
    match self {
        RetryConfig::None => None,
        _ => {
            let body = req.body().try_clone()?;
            ...
}
```

Notice how `try_clone` returns an `Option`. If the request body cannot be cloned, the `clone_request`
method will also return `None`, and the request simply will not be retried. Which is much better than
sending an invalid request!

My fix was sent in [this](https://github.com/XAMPPRocky/octocrab/pull/842) pull request, which was
merged soon after, and included in the [0.49.1](https://github.com/XAMPPRocky/octocrab/releases/tag/v0.49.1) `octocrab` release. If you use `octocrab` and do not disable the automatic retry mechanism, you might want to update to it.

## Bonus: could LLMs find the bug (sooner)?

While writing this blog post, I wondered if LLMs could actually find this bug sooner, and save me the hours of debugging pain.
I'm not a very skilled vibe-coder, but I do use Claude sometimes, so out of curiosity, I asked it to locate the bug.

First, I showed it the minimal reproducible example from my `octocrab` [issue](https://github.com/XAMPPRocky/octocrab/issues/835). It found out that the problem is with retries pretty much immediately, although with this example that was already quite obvious. After asking it to dig deeper, it also found out the exact cause of the underlying `clone` bug directly in `octocrab`. That was relatively impressive, although it also pointed me to the patched `0.49.1` release, and cited text that was suspiciously similar to my original issue and my PR. So it clearly saw my fix :laughing: And thus it's unclear whether it would be able to find the issue even before I actually fixed it. Well, too late to test that now.

In a more realistic scenario, I reverted `bors` to a commit right before I disabled the retries, and asked Claude to try to find the issue there. At first, it produced some nonsense suggestions, such as claiming that I send an empty string for the `sha` field (which is quite different from sending an empty request body…). Then it kind of forgot that I'm using Rust and not C++ and claimed that the issue is a "subtle temporary lifetime problem with async/await":

```rust
I think I found the issue! It's a subtle temporary lifetime problem
with async/await in Rust.

Look at this code in src/github/api/operations.rs:172-181:

let res = repo
  .client()
  ._patch(
    url.as_str(),
    Some(&serde_json::json!({
      "sha": sha.as_ref(),
      "force": matches!(force, ForcePush::Yes)
    })),
)
.await?;

The problem is that serde_json::json!(...) creates a temporary value,
and you're passing a reference to it (&serde_json::json!(...)).
Even though octocrab's build_request is synchronous and serializes
the body before the .await, there can be subtle issues with temporary lifetime
extension in async contexts, especially across different compiler versions
or optimization levels.

Here's what might be happening:
1. The json! macro creates a temporary serde_json::Value
2. A reference to this temporary is passed to _patch
3. Due to the async context, there's a possibility the temporary
   gets dropped before serialization completes
4. This results in either garbage data or an empty body being sent

The Fix

Store the JSON value in a variable first to ensure it lives long enough:

let body = serde_json::json!({
  "sha": sha.as_ref(),
  "force": matches!(force, ForcePush::Yes)
});

let res = repo
  .client()
  ._patch(url.as_str(), Some(&body))
  .await?;
```

After I patiently explained that this is not the kind of issue that can just happen (without `unsafe`) in Rust, and hinted that the problem might also be in a dependency, it finally started looking at `octocrab`, and actually did find the shallow `clone` problem (although it is again unclear whether that would happen without it knowing about my fix):

```rust
Ah! I found something suspicious. Look at the OctoBody implementation -
it uses Arc<RwLock<BoxBody>> and implements Clone by cloning the Arc:

impl Clone for OctoBody {
  fn clone(&self) -> Self {
    OctoBody(Arc::clone(&self.0))
  }
}

This means when the body is cloned, both clones share the same underlying
body stream! If one clone consumes the body (by polling it), the other clone
will have an empty body!
```

However, even though it found the actual bug, it then started to lose confidence that this bug is the culprit, in a very funny way. It examined my `Cargo.toml`:

```
Wait, I don't see the "retry" feature enabled for octocrab in
bors's Cargo.toml. Let me check if bors has its own retry logic
that might be cloning requests:
```

It failed to realize that `retry` is a *default* feature of `octocrab`, so even if I do not enable it myself, it was actually enabled by default. This was enough for it to stop suspecting `octocrab`, and go on a hunt to find (hopefully fictitious) retry bugs in the logic of bors. At that point I lost my patience with it and stopped it.

I think that this shows both the advantages and disadvantages of debugging using LLMs. They can sometimes find even pretty tricky issues, but they can also get sidetracked, at which point they need *someone else* (either a human that actually understands what is going on, or another LLM :) ) to guide them. I can imagine someone less knowledgeable about Rust wasting quite some time debugging imaginary issues in bors found by Claude, in an attempt to locate what might be causing the empty request bodies.

Anyway, next time I start a similar bughunt, I will probably just start Claude in a terminal and let it run concurrently. Then we can see who can get to the core of the bug sooner :)

## Conclusion

I'm really glad that I managed to find the underlying issue, as it was a satisfying conclusion to
an otherwise pretty maddening debugging experience. And in the end, it helped fix other pre-existing
bugs in bors and its test suite and also fix a nasty bug in a popular Rust crate at the same time.
So, a win-win?

By the way, this post is not taking a shot at `octocrab` in any way. It's a very useful library that
saved me a lot of time over the years! Kudos to [XAMPPRocky](https://github.com/xampprocky) for creating
it and for merging my bugfix PR and releasing a new version so promptly.

If you have similar Rust bug stories, perhaps related to wrong usage of `clone`, I'd be glad to hear them on [Reddit]({{ page.reddit_link }}).
