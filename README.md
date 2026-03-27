 source .venv/bin/activate
 uv init
 conda deactivate
 python --version
 python3 --version
 uv python list
clear
uv python list
uv venv env cpython-3.11.13-macos-aarch64-none
uv venv env --python cpython-3.11.13-macos-aarch64-none
source env/bin/activate
clear
uv pip list
uv add -r requirements.txt
uv pip list