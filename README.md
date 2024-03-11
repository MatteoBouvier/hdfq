# hdfq

`hdfq` is a CLI tool for displaying and manipulating hdf5 files.
It uses syntax similar to [jq](https://jqlang.github.io/jq/) although it does not yet support everything `jq` does.
`hdfq` is written in Python.

## Installation

### with pipx

The recommended way of installing **hdfq** is trough the pipx installer : 

```shell
pipx install git+ssh://git@gitlab.vidium.fr/vidium/hdfq.git
```

`hdfq` will be installed in an isolated environment but will be available globally as a shell application.

### from source

You can download the source code from gitlab with :

```shell
git clone git@gitlab.vidium.fr:vidium/hdfq.git
```

## Usage

### Basics

`hdfq` requires both a **pattern** (a command to be evaluated) and a **path** to a file saved in `hdf5` format.
A typical hdfq command would look like :

```shell
hdfq "." path/to/hdf5/file
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
hdfq '.' file.h5
```

Read an object :
```shell
hdfq '.a.b.c' file.h5
```
Read an object's attribute :
```shell
hdfq '.a.b#z' file.h5
```

Chain commands :
```shell
hdfq '.a.b | kattrs' file.h5
```

Update an object's value :
```shell
hdfq '.a#version = 2' file.h5
```

Delete an object :
```shell
hdfq 'del(.obj)' file.h5
```


## TODO

- indexing
- better cli help
