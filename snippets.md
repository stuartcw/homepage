# Snippets

## Python cli main

```python
#!/usr/bin/env python3

import click
import logging
from datetime import datetime
from icecream import ic

# Configure logging
def setup_logger():
	log_filename = datetime.now().strftime("log_%Y-%m-%d.log")
	logging.basicConfig(
		filename=log_filename,
		level=logging.INFO,
		format='%(asctime)s - %(levelname)s - %(message)s'
	)
	# Log to console as well
	console_handler = logging.StreamHandler()
	console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
	logging.getLogger().addHandler(console_handler)
	
# Main CLI group
@click.group()
def cli():
	"A CLI application with logging and debugging."
	setup_logger()
	logging.info("Application started.")
	ic("Debugging enabled")
	
# Example command
@cli.command()
@click.argument('name')
@click.option('--greeting', default='Hello', help='Greeting to use.')
def greet(name, greeting):
	"Greet a person with a message."
	message = f"{greeting}, {name}!"
	logging.info(f"Greet command executed with name: {name}, greeting: {greeting}")
	ic(message)
	click.echo(message)
	
# Another example command
@cli.command()
def example():
	"Run an example command."
	logging.info("Example command executed.")
	ic("Example debugging message")
	click.echo("This is an example command.")
	
if __name__ == '__main__':
	cli()
```
