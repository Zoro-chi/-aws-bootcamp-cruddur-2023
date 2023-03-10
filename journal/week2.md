# Week 2 — Distributed Tracing

I instrumented the backend flask app with honeycomb. After installing the module, I added my honeycomb api keys to my app and then tested the tracing by hitting the endpoints i tested the honeycomb traces.

I also ran similar tests with Rollbar and AWS-Xray. They all had similar implementations to setting up the environment and observing the logs (traces). I felt Xray was a bit harder to implement due to the daemon.

I also configured Cloudwatch log groups on my AWS account, to test my watchtower custom logger.

I personally found Honeycomb to be the most intuitive and easy to apply.
