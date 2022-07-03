# History

**2022.7.3**, Big changes.

- [x] Support for magic expression in config expansion such as `$<1:10:2>` and `$<a|b|c>`.
- [x] Support for easier combination of magic expressions, such as `$<a|b|c>.$<1:10:2>`.
- [x] Make arg reference more readable, change `[-a:1:4:]` to `${-a[1:4]}`.
- [x] Support for passing an argument (or not) to set (or not) a flag.
- [x] Support for multi-gpus per task.
- [x] Re-organize `README`.

**2021.11.8**, Small changes.

- [x] Code refactoring, bugfix, more examples.
- [x] Better support for arg reference (substring, key-based reference).

**2021.10.3**, Big changes. Code refactoring, the architecture changes a lot.

- [x] Better support for log extraction with `yaml` rule file.
- [x] Better support for log analysis with `extract()` from `manytasks.log_extractor`.
- [x] Remove support for extracting results with python scripts.


**2021.9.26**, Big changes.

- [x] Code refactoring.
- [x] Add support for setting timeout for each task.
- [x] Add support for arg reference.
- [x] Add support for showing PID of a task.

**2021.9.13**, Small changes.

- [x] Add support for specifying an output directory.
- [x] Add better support for log analysis.

**2021.6.20**, Big changes.

- [x] Deprecate support for WebUI.
- [x] Add support for resuming from the last running status.
- [x] Add support for factor analysis.

**2021.5.26**, Small changes.

- [x] Add support for yaml rule & Deprecate support for json rule (regex in json is not readable)

**2021.3.16**, Small changes.

- [x] Support for JSON rule.
- [x] Beautify the command line output.

**2021.2.18**, Big changes.

- [x] Support Non-key arguments
- [x] Support for setting latency between two tasks (sometimes task-2 may reuse the cached data generated by task-1, so it is a good idea to let task-2 wait for a few seconds) 
- [x] Remove the arg `runnable` and merge it into `executor`
- [x] Support for result extraction

**2020.12.12**, Big changes! I will submit my paper to ACL 2021 recently (accepted!). Before that, I want to publish this repo to `pypi` so that you can install it by `pip install ...` directly. I rename `alchemist` to `manytasks` to make the name of the tool easier to recognize, and change the description *A toy tool for deep learning, which helps explore different net configurations.* to *A tool for deploying many tasks automatically.*

- [x] Colorize the CLI tools
- [x] Disable the web UI by default
- [x] Support for configuration with python script
- [x] Support for init a config
- [x] Support for showing the results

**2019.12.11**, About one year later, after submitting my ACL 2020 paper (accepted!), I add some new features to the tool. Good luck~

- [x] Use `.hjson` (<https://hjson.org/>) instead of `.json` for configuration, since `.hjson` is more human-readable which allows comments and missing/trailing commas
- [x] Ask the user for overriding existing logs
- [x] Beautify the CLI tools

**2019.1.1**, First version comes out. I wrote the code to enable grid search for my ACL 2019 submission. Unfortunately it was rejected. :(

- [x] Enumerate different configurations
- [x] Specify which GPU card to use
- [x] Specify the number of processes
- [x] Web UI support
- [x] Show the last 100 lines of logs
- [x] Show the GPU overload