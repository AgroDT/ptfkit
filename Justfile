[windows]
set shell := ["powershell.exe", "-NoLogo", "-Command"]

mod codegen
mod native 'targets/ptfkit-native'
mod python 'targets/ptfkit-py'
mod rust 'targets/ptfkit-rs'

default:
	@{{just_executable()}} --list

[working-directory: 'codegen']
@generate:
    cargo run generate

@version value:
    cargo run --manifest-path codegen/Cargo.toml -- version {{quote(value)}}
    cargo check --manifest-path targets/ptfkit-rs/Cargo.toml --quiet
    uv lock --project targets/ptfkit-py

test: codegen::test native::test python::test rust::test
