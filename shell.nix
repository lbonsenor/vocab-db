# shell.nix
{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = [
    pkgs.python3Full
    pkgs.python313Packages.jupyter
    pkgs.python313Packages.psycopg2-binary
    pkgs.python313Packages.stanza
    pkgs.python313Packages.ipykernel
    pkgs.python313Packages.pyzmq
    pkgs.python313Packages.python-dotenv
    pkgs.stdenv.cc.cc.lib # <- provides libstdc++.so.6
  ];
}

# python -m ipykernel install --user --name=.venv --display-name ".venv (Python 3)"
