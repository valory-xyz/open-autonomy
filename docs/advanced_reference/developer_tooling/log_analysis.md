The {{open_autonomy}} framework provides a log analyser tool for analysing the runtime logs for an agent. Using this tool you apply perform various types filters to the logs to extract the specific types of logs.

To use the tool, place the log files into a folder and make sure the log files follow the `aea_{n}.txt` naming pattern. For example let's say we have logs for 4 agents named `aea_0.txt`, `aea_1.txt`, `aea_2.txt` and `aea_3.txt` placed inside `logs/` folder. You can run following command to retrieve logs for `aea_0`

```
$ autonomy analyse logs --from-dir logs/ -a aea_0
```

When running the command for the first time on a new set of logs the tool will create a database for the logs so it'll run for longer for the first time. 

> **Note** If you want to reset the database use `--reset-db` flag when running the command


This command provides various types of filters to help the user extract the specific set of logs as they require

1. Start time specifier (`--start-time `)
    
    Using this filter you can only keep the logs after a certain timestamp. You will have to provide the time stamp as a string in the `YYYY-MM-DD H:M:S,MS` format. For example

    `$ autonomy analyse logs --from-dir logs/ -a aea_0 --start-time "2023-02-15 10:02:30,199"`

2. End time specifier (`--end-time`)

    Using this filter you can only keep the logs before a certain timestamp. You will have to provide the time stamp as a string in the `YYYY-MM-DD H:M:S,MS` format. For example

    `$ autonomy analyse logs --from-dir logs/ -a aea_0 --end-time "2023-02-15 10:05:30,000"`

3. Period (`--period`)

    Using this filter you can print the logs for a specific period only. For example 

    `$ autonomy analyse logs --from-dir logs/ -a aea_0 --period 0`

4. Round (`--round TEXT`)

    Using this filter you can print the logs for a specific round across various periods. For example 

    `$ autonomy analyse logs --from-dir logs/ -a aea_0 --round round_name`

5. Behaviour (`--behaviour`)

    Using this filter you can print the logs for a specific behaviour across various periods. For example 

    `$ autonomy analyse logs --from-dir logs/ -a aea_0 --behaviour behaviour_name`

6. Include regex filter (`-ir, --include-regex`)

    You can specify regex patterns to include in the result using this filter. For example 

    `$ autonomy analyse logs --from-dir logs/ -a aea_0 -ir ".*Retrieved data from \w+" -ir ".*Couldn't retrieve data from \w+"`

7. Exclude regex filter `-er, --exclude-regex TEXT`

    You can specify regex patterns to exclude from the result using this filter. For example 

    `$ autonomy analyse logs --from-dir logs/ -a aea_0 -er ".*Recieved enevelope" -er ".*current abci time"`


These filters can be used stand-alone or they can be combined to extract a specific set of logs as required. For example if you want logs for a specific time period with a fixed pattern you can use 

```
$ autonomy analyse logs --from-dir logs/ -a aea_0 --start-time START_TIME --end-time END_TIME -ir INCLUDE_REGEX
```