import os
import sys
from typing import Optional
from fwa import oracle_manager
from fwa.utils import helper, payloads, webserver
from fwa.utils.helper import FWA_PREFIX, fwa_default_analyzers_path, fwa_init, fwa_list_sessions, fwa_package_path, fwa_session
from fwa.utils import mitm
import typer
import fwa.fuzzer as fuzzer

import fwa.analyzer_manager  as am



## Con poetry 
typer_app = typer.Typer(add_completion=False, context_settings={"help_option_names": ["-h", "--help"]})


@typer_app.command()
def record(url: str, session_name: str, quiet: bool = typer.Option(False, help="Quiet mode"), background : bool = typer.Option(False, help="If mitmdump should run in background")):
    """ Records a sessions and store in ~/.fwa folder
    """
    fwa_init()
    mitm.start_record(url, session_name, quiet, background)

    # -s repeater.py  -k -q)

@typer_app.command()
def list():
    """List the sessions """
    fwa_init()
    for s in fwa_list_sessions():
        print(s)

@typer_app.command()
def replay(session_name: str, proxy: str = typer.Option("", help="proxy (<host>:<port>)")):
    """Resend a session

    Args:
        session_name (str): The session name
        proxy (str, optional): The proxy in form http://<host>:<port>
    """
    fuzzer.send_from_har(session_name, proxy)

@typer_app.command()
def stop_record():
    mitm.stop_record()
    pass


@typer_app.command()
def fuzz(session_name: str = typer.Argument(..., help="The session name, taken from ~/.fwa/sessions folder"),
    payload_file: str = typer.Option("payloads.csv", help="The csv payload in the form <payload>,<payload_type>"), 
    cookies: bool = typer.Option(False, help="If set, fuzz the cookies"),
    querystring: bool = typer.Option(False, help="If set, fuzz the params in the query string"),
    body: bool = typer.Option(False, help="If set, fuzz the params in the body "),
    headers: bool = typer.Option(False, help="If set, fuzz the headers"),
    threads: int = typer.Option(1, help="The number of threads")
    ):
    """ 
    Fuzz a session obtained with the record command
    """
    if session_name not in fwa_list_sessions():
        helper.err("Session \"{}\" not found, run \"fwa list\" to show availabe sessions.".format(session_name))
    fuzzer.fuzz_from_har(session_name, payload_file, querystring, body, cookies, headers, threads)


@typer_app.command()
def analyze(session_name: str = typer.Argument(..., help="The base session name"), fuzz_session_name: Optional[str] = typer.Argument("", help="The fuzzing session name"), payload_file: str = typer.Argument("payloads.csv", help="The csv payload in the form <payload>,<payload_type>"), analyzers = typer.Option("", help="The analyzers' folder"), output = typer.Option('observations.csv', help="Detected observations")):
    """ The command analyzes the session name and generate a csv containing the list of observations.

    Args:
        session_name (str, optional): _description_. Defaults to typer.Argument(..., help="The base session name").
        fuzz_session_name (Optional[str], optional): _description_. Defaults to typer.Argument("", help="The fuzzing session name").
        payload_file (str, optional): _description_. Defaults to typer.Argument("payloads.csv", help="The csv payload in the form <payload>,<payload_type>").
        analyzers (_type_, optional): _description_. Defaults to typer.Option("", help="The analyzers' folder").
        output (_type_, optional): _description_. Defaults to typer.Option('observations.csv', help="Detected observations").
    """
    fwa_init()
    if not fuzz_session_name: 
        fuzz_session_name = "{}{}".format(FWA_PREFIX, session_name)
    if not analyzers: 
        analyzers = fwa_default_analyzers_path()
    ploads = payloads.load(payload_file)
    webserver.start_webserver()
    am.run(session_name, fuzz_session_name, analyzers, ploads, "observations.csv")
    webserver.stop_webserver()

@typer_app.command()
def oracle(observation_file: str = typer.Argument(..., help="The observation file"), rules_path: Optional[str] = typer.Argument("", help="The path containing the list of Oracle rules") ):
    """ The command receives the observations_file and detects vulenrabilities through the "oracle" 

    Args:
        analyzer_file (str, optional): _description_. Defaults to typer.Argument(..., help="The observation file").
    """
    # TODO: extract as variables
    output_file = 'vulnerabilities.csv'
    save_no_vulns = True
    if not rules_path: 
        rules_path = oracle_manager.get_default_oracle_path()
    oracle_manager.oracle(observation_file, rules_path, output_file, save_no_vulns)
        



def run():
    command = typer.main.get_command(typer_app)
    result = command(standalone_mode=False)
    return result
    # typer_app()
    