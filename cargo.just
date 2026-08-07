[windows]
set shell := ["powershell.exe", "-NoLogo", "-Command"]

default:
	@{{just_executable()}} --list

lint:
    cargo clippy --workspace --all-targets -- -D warnings
