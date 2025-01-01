# `autonomy hash`

Hashing utilities for packages.

## Usage
```bash
autonomy hash [OPTIONS] COMMAND [ARGS]...
```

## Commands

### `autonomy hash all`
Generate IPFS hashes for all packages.

#### Usage
```bash
autonomy hash all [OPTIONS]
```

#### Options
`--help`
:   Show the help message and exit.

### `autonomy hash hash-file`
Get hash for a specific file.

#### Usage
```bash
autonomy hash hash-file [OPTIONS] PATH
```

#### Arguments
`PATH`
:   Path to the file to hash.

#### Options
`--help`
:   Show the help message and exit.

#### Examples
```bash
# Generate IPFS hashes for all packages
autonomy hash all

# Get hash for a specific file
autonomy hash hash-file path/to/file
```
