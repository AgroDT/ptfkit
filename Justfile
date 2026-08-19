set default-list := true

[windows]
set shell := ["powershell.exe", "-NoLogo", "-Command"]

mod codegen
mod native 'targets/ptfkit-native'
mod python 'targets/ptfkit-py'
mod rust 'targets/ptfkit-rs'

# Validate all PTF specifications without generating targets.
[working-directory: 'codegen']
@validate:
    cargo run validate

# Generate target sources from validated PTF specifications.
[working-directory: 'codegen']
@generate:
    cargo run generate

# Set the package version and refresh dependent lockfiles.
@version value:
    cargo run --manifest-path codegen/Cargo.toml -- version {{quote(value)}}
    cargo check --manifest-path targets/ptfkit-rs/Cargo.toml --quiet
    uv lock --project targets/ptfkit-py

# Run the complete test suite for all project components.
[parallel]
test: codegen::test native::test python::test rust::test

# Run the component verification suites in parallel.
[parallel]
verify: codegen::verify native::verify python::verify rust::verify

# Build the documentation site or serve it locally with strict validation.
[arg('command', pattern='build|serve')]
@docs command:
    uv --directory=docs run mkdocs {{command}} --strict
