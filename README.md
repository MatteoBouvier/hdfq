# hq

`hq` is a CLI tool for displaying and manipulating hdf5 files.
It uses syntax similar to [jq](https://jqlang.github.io/jq/) although it does not yet support everything `jq` does.
`hq` is written in Python.

## Installation

### with pipx

The recommended way of installing **hq** is trough the pipx installer : 

```shell
pipx install git+ssh://git@gitlab.vidium.fr/vidium/hq.git
pipx inject hq packaging
```
`hq` will be installed in an isolated environment but will be available globally as a shell application.

### from source

You can download the source code from gitlab with :

```shell
git clone git@gitlab.vidium.fr:vidium/hq.git
```

## Usage

### Basics

`hq` requires both a **pattern** (a command to be evaluated) and a **path** to a file saved in `hdf5` format.
A typical hq command would look like :

```shell
hq "." path/to/hdf5/file
```
The pattern argument can be used to :
- read a specific object (stored under the `<name>` identifier) from the file with `.<name>`
- read a specific attribute from an object with `#<attr_name>`
- get the list of identifiers with `keys`, attributes with `attrs` and attribute identifiers with `kattrs`
- set an object's value with `<object>=<value>`
- delete an object with `del(<object>)`

Command can be chained in the pattern argument using a `|` symbol.

### Examples

View all contents in a file :
```shell
hq '.' file.h5
```

Read an object :
```shell
hq '.a.b.c' file.h5
```
Read an object's attribute :
```shell
hq '.a.b#z' file.h5
```

Chain commands :
```shell
hq '.a.b | kattrs' file.h5
```

Update an object's value :
```shell
hq '.a#version = 2' file.h5
```

Delete an object :
```shell
hq 'del(.obj)' file.h5
```


## TODO

- indexing
- better cli help
