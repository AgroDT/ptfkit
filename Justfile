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

test: codegen::test native::test python::test rust::test
