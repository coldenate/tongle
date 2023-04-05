{ pkgs ? import <nixpkgs> {} }:

let
  python = pkgs.python311;
  poetry = pkgs.poetry;
in
pkgs.mkShell {
  buildInputs = [ python poetry ];

  shellHook = ''
    # Set up the virtual environment with Poetry
    export POETRY_VIRTUALENVS_IN_PROJECT=true
    ${poetry}/bin/poetry install

    # Load the .prod.env file
    export $(grep -v '^#' src/.prod.env | xargs)

    # Run the main bot with the correct production environment
    run_bot() {
      . .venv/bin/activate
      python src/main.py
      deactivate
    }
    echo "Run 'run_bot' to start the main bot with the correct production environment."
  '';
}

