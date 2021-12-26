# Rate limiter with distributed executor support
=====================================

`nekkar` is a tool for limiting requests to particular service or to particular endpoint of the service.
> The original idea was to create a rate limiter for HTTP APIs. But some kind of wrapper was needed to distinguish the endpoints and in current implementation it uses functions/callables.

> You wrap something in a function and give it a name/identifier with a decorator. All functions with the same name/identifier will share the rate limit.

> You can use it without making HTTP requests, and control the function calls rate limits. Though, I don't know any useful use cases for it.

#### Typical use cases for this tool

- Scheduled process which does lot of requests in the background.

#### Use cases when this tool should be used carefully

- When user is waiting for a response from the server, and this tool locks the process and is waiting for a window to not exceed rate limits.


##### Original use case

There were a process which was processing data in batches, for each record it was doing requests to a third party service(call it Service-S) by HTTP API.
Though it was easy to track the rate at which the process sends requests to the Service-S and control it, it was naive and not scalable.
Naive - because, if for some reason there were another process which works with the Service-S then there could be rate limit violation.
Not scalable - because, if there where another instance that runs similar process then the there could be rate limit violation.


### Prerequisites
- You should have cache installed and accessible from all clients/executors.


## Installation
```bash
$ pip install nekkar
```

## Usage
Lets say rate limit works per endpoint, despite of request method.
Lets say for endpoint '**/a**' it is 100 and for endpoint '**/b**' it is 250.
```python
import requests

from nekkar.core.limiter import Nekkar
from nekkar.core.cache import MemcachedCache


cache = MemcachedCache("localhost", 11211)
limiter = Nekkar(cache=cache)


# Lets say rate limits work per endpoint `/a`.
@limiter(name="some_id_a", rate_limit=100)
def update_a(data):
    return requests.patch("http://localhost:8000/a", json=data, timeout=0.1)


# name="some_id_a" identifies that update_a and get_a will share the same rate limit.
@limiter(name="some_id_a", rate_limit=100)
def get_a():
    return requests.get("http://localhost:8000/a", timeout=0.1)


# get_b will not share rate limit with others because it has another name/identifier.
@limiter(name="another_id_b", rate_limit=250)
def get_b(data):
    return requests.patch("http://localhost:8000/b", json=data, timeout=0.1)


for i in range(100):
    get_a()
```


#### Cache configuration
Any cache could be used for this tool until it implements the `nekkar.core.cache.BaseCache` interface.
`MemcachedCache` is already implemented, but you can derive a class from BaseCache and implement similar for your desired cache.
**Important**: add - method should set the key value only if the value is not already set, otherwise rate limiter will not work properly. To validate this you can add a test case similar to nekkar/tests/integration/test_cache.

#### How does it work and why do you need a cache?
