# Server & Workload Protection Tools

This repo hosts tools to help with Server & Workload Protection. Currently there is only one, but more are likely to come.

Abbreviations used:

- SWP: Vision One Server & Workload Protection

Get the code:

```sh
git clone https://github.com/mawinkler/v1-swp-tools.git
cd v1-swp-tools
```

## Preparation of the Scripts

- Set environment variable `API_KEY_SWP` with the API key of the
  Server & Workload Security instance to use.
- Adapt the constants in between
  `# HERE`
  and
  `# /HERE`
  within the scripts to your requirements.
  ```sh
  # HERE
  REGION_SWP = "us-1."  # Examples: de-1. sg-1.
  # /HERE
  ```

Change to the directory of the desired script and install dependencies:

```sh
cd policy-compare

python3 -m venv venv && source venv/bin/activate

pip install -r requirements.txt
```

## Policy Compare

The Python script `policy-compare.py` implements for following functionality:

- Deep comparison of policies
- Listing the differences only

***Options and Examples***

```sh
usage: python3 policy-compare.py [-h] [--policy1 ID] [--policy2 ID]

Compare two Policies and list the differences

options:
  -h, --help    show this help message and exit
  --policy1 ID  policy one
  --policy2 ID  policy two

Examples:
--------------------------------
$ ./policy-compare.py --policy1 ID --policy2 ID
```

```sh
$ ./policy-compare.py --policy1 8 --policy2 265
Identical: False
Differences:
- Path: /name
  Linux Server: Linux Server
  Linux Server_2: Linux Server_2

- Path: /ID
  Linux Server: 8
  Linux Server_2: 265

- Path: /webReputation/state
  Linux Server: on
  Linux Server_2: off

- Path: /webReputation/moduleStatus/status
  Linux Server: active
  Linux Server_2: inactive

- Path: /webReputation/moduleStatus/statusMessage
  Linux Server: On
  Linux Server_2: Off
```

***Bash Magic***

```sh
curl https://workload.us-1.cloudone.trendmicro.com/api/policies/8 \
    -H "Content-type: application/json" -H "api-version: v1" -H "api-secret-key: SWP-API-KEY" > linux-server.json
curl https://workload.us-1.cloudone.trendmicro.com/api/policies/265 \
    -H "Content-type: application/json" -H "api-version: v1" -H "api-secret-key: SWP-API-KEY" > linux-server-2.json
 
jq --argfile a linux-server.json --argfile b linux-server-2.json -n '
  reduce ($a + $b | keys_unsorted[]) as $k ({}; .[$k] =
    if $a[$k] == $b[$k] then null
    else {"file1": $a[$k], "file2": $b[$k]} end
  ) | del(.[] | select(. == null))
'
```

## Support

This is an Open Source community project. Project contributors may be able to help, depending on their time and availability. Please be specific about what you're trying to do, your system, and steps to reproduce the problem.

For bug reports or feature requests, please [open an issue](../../issues). You are welcome to [contribute](#contribute).

Official support from Trend Micro is not available. Individual contributors may be Trend Micro employees, but are not official support.

## Contribute

I do accept contributions from the community. To submit changes:

1. Fork this repository.
2. Create a new feature branch.
3. Make your changes.
4. Submit a pull request with an explanation of your changes or additions.

I will review and work with you to release the code.
