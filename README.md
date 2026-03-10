# dotenv

Parse, validate, and diff .env files.

One file. Zero deps. Manages env files.

## Usage

```bash
# Parse
python3 dotenv.py parse .env
python3 dotenv.py parse .env --json

# Get single value
python3 dotenv.py get .env DATABASE_URL

# Diff two env files
python3 dotenv.py diff .env .env.example

# Validate against template
python3 dotenv.py validate .env .env.example

# Merge (second overrides first)
python3 dotenv.py merge .env .env.local

# Shell export statements
eval "$(python3 dotenv.py export .env)"
```

## Requirements

Python 3.8+. No dependencies.

## License

MIT
