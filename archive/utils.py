
def patch_sbatch_args(args):
    """
    Takes a list of sbatch command-line arguments and replaces short-form
    options with their long-form equivalents.

    Args:
        args (list): A list of strings representing the command-line arguments,
                     excluding the script name itself (sys.argv[1:]).

    Returns:
        list: A new list of strings with short options patched to long options.
    """
    short_long_map = {
        "-A": "account",
        "-a": "array",
        "-b": "begin",
        "-D": "chdir",
        "-M": "clusters",
        "-C": "constraint",
        "-S": "core-spec",
        "-c": "cpus-per-task",
        "-d": "dependency",
        "-m": "distribution",
        "-e": "error",
        "-x": "exclude",
        "-B": "extra-node-info",
        "-G": "gpus",
        "-h": "help",
        "-H": "hold",
        "-i": "input",
        "-J": "job-name",
        "-k": "no-kill",
        "-L": "licenses",
        "-F": "nodefile",
        "-w": "nodelist",
        "-N": "nodes",
        "-n": "ntasks",
        "-o": "output",
        "-O": "overcommit",
        "-s": "oversubscribe",
        "-p": "partition",
        "-q": "qos",
        "-Q": "quiet",
        "-t": "time",
        "-v": "verbose",
        "-V": "version",
        "-W": "wait",
    }
    options_requiring_arg = {
        "-A",
        "-a",
        "-b",
        "-D",
        "-M",
        "-C",
        "-S",
        "-c",
        "-d",
        "-m",
        "-e",
        "-x",
        "-B",
        "-G",
        "-i",
        "-J",
        "-L",
        "-F",
        "-w",
        "-N",
        "-n",
        "-o",
        "-p",
        "-q",
        "-t",
    }

    patched_args = []
    i = 0
    while i < len(args):
        arg = args[i]

        if arg.startswith("--"):
            # Already a long option, keep it
            patched_args.append(arg)
            i += 1
        elif arg.startswith("-") and len(arg) > 1 and arg[1] != "-":
            # Check if it's potentially a short option (e.g. '-o', not '--output')
            short_opt = arg

            if short_opt in short_long_map:
                long_opt_name = short_long_map[short_opt]

                if short_opt in options_requiring_arg:
                    if i + 1 < len(args):
                        value = args[i + 1]
                        patched_args.append(f"--{long_opt_name}={value}")
                        i += 2
                    else:
                        print(
                            f"Warning: Short option '{short_opt}' requires an argument, but none provided. Keeping original.",
                            file=sys.stderr,
                        )
                        patched_args.append(arg)
                        i += 1
                else:
                    # This option is a flag (doesn't take an argument) [1]
                    patched_args.append(f"--{long_opt_name}")
                    i += 1
            else:
                print(
                    f"Warning: Unknown or unmapped short option '{short_opt}'. Keeping original.",
                    file=sys.stderr,
                )
                patched_args.append(arg)
                i += 1
        else:
            patched_args.append(arg)
            i += 1
    return patched_args





def _parse_option_string(option_str: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parses a Slurm option string (like '--nodes=2' or '--requeue' or '-o output.log')
    into a normalized key and value. Returns (None, None) if invalid.
    Now correctly handles single dash options.
    """
    option_str = option_str.strip()
    if not option_str:
        return None, None

    key = ""
    value = ""

    if "=" in option_str:
        key_part, value_part = option_str.split("=", 1)
        key = key_part.strip().lstrip("-")  # Remove leading dashes and strip
        value = value_part.strip()
    else:
        key = option_str.strip().lstrip("-")  # Flag: key is the whole string
        value = "True"  # Represent flags as True (string)

    # Basic validation: key should not be empty after processing
    if not key:
        return None, None

    return key, value


def parse_sbatch_file_options(filename: str) -> Dict[str, str]:
    """
    Parses #SBATCH options from a file into a dictionary.
    Returns an empty dict if file not found or unreadable.
    """
    sbatch_args = []
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("#SBATCH"):
                    option_part = line[len("#SBATCH") :].split("#", 1)[0].strip()
                    if not option_part:
                        continue
                    if option_part.startswith("-"):
                        sbatch_args.extend(option_part.split(" "))
                    else:
                        sbatch_args.append("--" + option_part)
    except (FileNotFoundError, OSError, UnicodeDecodeError) as e:
        print(
            f"Warning: Could not read or parse file '{filename}': {e}", file=sys.stderr
        )
        return {}

    return parse_sbatch_cli_options(sbatch_args)


def parse_sbatch_cli_options(sbatch_args: List[str]) -> Dict[str, str]:
    """
    Parses command-line sbatch options from a list into a dictionary.
    Includes the filename as 'filename': 'actual_filename' if present.
    Keys are normalized, values are strings.
    """
    options: Dict[str, str] = {}
    filename = None

    # First, extract the filename (if it exists)
    for arg in reversed(sbatch_args):
        if not arg.startswith("-"):
            filename = arg
            break

    if filename:
        options["filename"] = filename

    for arg in sbatch_args:
        if arg != filename and arg.startswith("-"):
            key, value = _parse_option_string(arg)
            if key is not None and value is not None:
                options[key] = value

    return options
