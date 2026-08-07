[windows]
set shell := ["powershell.exe", "-NoLogo", "-Command"]

mod cargo
mod python 'crates/ptfkit-py'

default:
	@{{just_executable()}} --list

generate:
    cargo run -p ptfkit-codegen generate
