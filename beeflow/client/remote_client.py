@app.command()
def connection(ssh_target: str = typer.Argument(..., help='the target to ssh to'):
    """Check the connection to Beeflow client via REST API"""



