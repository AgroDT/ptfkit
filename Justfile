[windows]
set shell := ["powershell.exe", "-NoLogo", "-Command"]

mod codegen
mod python 'targets/ptfkit-py'
mod rust 'targets/ptfkit-rs'

default:
	@{{just_executable()}} --list

[working-directory: 'codegen']
@generate:
    cargo run generate

test: codegen::test python::test rust::test
