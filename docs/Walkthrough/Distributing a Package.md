Once your package is ready it's time to save and distribute it.

## Building a package locally

To save a package to local disk use `build`.

```python
import t4
p = t4.Package()

top_hash = p.build("username/packagename")
```

Building a package requires providing it with a name. Packages names must follow the `${namespace}/${packagename}` format. For small teams, we recommend using the package author's name as the namespace.

## Pushing a package to a remote registry

To share a package with others via a remote registry, `push` it:

```python
import t4
p = t4.Package()
p.push(
    "username/packagename",
    "s3://your-bucket",
    message="Updated version my package"
)
```

`push` targets a registry. A **registry** is a storage backend&mdash;currently either an S3 bucket (e.g. `s3://my-bucket`) or a local directory path (e.g. `/path/to/somewhere/`). By default the registry is infered from the second argument, `dest`. You can omit `dest` entirely if you configure a default remote registry first:

```python
import t4
t4.config(default_remote_registry='s3://your-bucket')
t4.Package().push("username/packagename")  # this now 'just works'
```

The default remote registry, if set, persists between sessions.

## Distributing a package version

A successful package `build` or `push` returns a **top hash**.

```bash
$ python
>>> t4.Package().build("username/packagename")

'2a5a67156ca9238c14d12042db51c5b52260fdd5511b61ea89b58929d6e1769b'
```

A top hash is a persistent, immutable reference to a specific version of a package. To download this specific version of the package in the future you will need to provide this top hash.

## Delete a package from a registry

To delete a package from a registry:

```python
import t4

# delete from local registry
t4.delete_package("username/packagename")

# delete from remote registry
t4.delete_package("username/packagename", "s3://your-bucket")
```

Only do this if you really need to as this will break the package for anyone relying on it.