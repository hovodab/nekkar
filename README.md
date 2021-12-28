# Rate limiter with distributed execution support
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

There were a process which was processing data in batches, for each record it was doing requests to a third party service(call it Service-S) by HTTP.
Though it was easy to track the rate at which the process sends requests to the Service-S and control it, it was naive and not scalable.
Naive - because, if for some reason there were another process which works with the Service-S then there could be rate limit violation.
Not scalable - because, if there where another instance that runs similar process then there could be rate limit violation.


### Prerequisites
- You should have cache installed and accessible from all clients/executors.


## Installation
```bash
$ pip install nekkar
```

## Usage
Lets say rate limit works per endpoint, despite of request method.
Lets say for endpoint '**/a**' it is 100, and for endpoint '**/b**' it is 250.
```python
import requests

from nekkar.core.limiter import Nekkar
from nekkar.core.cache import MemcachedCache


cache = MemcachedCache("localhost", 11211)
limiter = Nekkar(cache=cache)


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


#### Basic interface for limiter
TODO: Add graph of execution with different configurations with interval and without.


#### How does it work and why do you need a cache?
The system tracks two "tables". One for storing when the callables was called, and another for locking the access to the first table records.
![Alt text](assets/crt_crt_lock.png?raw=true "CRT and CRT-Lock")

The storage that will be used to store table information should have two main characteristics.
- It should be accessible from different instances, for scalability.
- It should have "test-and-set" operation, to avoid race conditions.

As cache provides those two characteristics - it fits for the purpose. Also caches are quire fast.
Although, any storage could be used if it supports the main two requirements.

##### How the rate limit is controlled
When a callable is being called the system(wrapper function) starts trying to acquire a lock for a CRT record(with corresponding name/id).

When it successfully acquires the lock, it reads the record from CRT table and checks whether there is a "window" for a call.
(We say that there is a window for a call if executing the callable will not exceed the rate limit.)

If there is a window, then CRT record is updated and saved. CRT lock is released and the function/callable finally executes.

If there is no window, then CRT record is leaved unchanged. CRT lock is released and the system starts trying to acquire the lock again after a random sleep time.


#### Examples
Example 1:
2 processes.
Each doing 50 calls.
Rate limit - 60.
Interval - None/Not specified.
Each call takes 100ms approximately.
![Alt text](assets/concurrent_2_50_60_None.png?raw=true "CRT and CRT-Lock")

Example 2:
2 processes.
Each doing 50 calls.
Rate limit - 60.
Interval - 0.
Each call takes 100ms approximately.
![Alt text](assets/concurrent_2_50_60_0.png?raw=true "CRT and CRT-Lock")

Example 3:
3 processes.
Each doing 50 calls.
Rate limit - 600.
Interval - None/Not specified.
Each call takes 100ms approximately.
![Alt text](assets/concurrent_3_50_600_None.png?raw=true "CRT and CRT-Lock")

Example 4:
3 processes.
Each doing 50 calls.
Rate limit - 600.
Interval - 0.
Each call takes 100ms approximately.
![Alt text](assets/concurrent_3_50_600_0.png?raw=true "CRT and CRT-Lock")


#### Known issues
- Complicated interface
- Possible side effects for two functions with the same name/identifier and different rate limits.
- Bad randomisation, non-fair resource distribution.
- Needs cache for processes. On a single instance there could be a another storage rather than a cache.
- Needs cache even for threads. It could be done without cache.
