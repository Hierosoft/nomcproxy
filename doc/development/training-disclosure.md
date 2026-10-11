# Training Disclosure for nomcproxy
This Training Disclosure, which may be more specifically titled above here (and in this document possibly referred to as "this disclosure"), is based on **Training Disclosure version 1.1.4** at https://github.com/Hierosoft/training-disclosure by Jake Gustafson. Jake Gustafson is probably *not* an author of the project unless listed as a project author, nor necessarily the disclosure editor(s) of this copy of the disclosure unless this copy is the original which among other places I, Jake Gustafson, state IANAL. The original disclosure is released under the [CC0](https://creativecommons.org/public-domain/cc0/) license, but regarding any text that differs from the original:

This disclosure also functions as a claim of copyright to the scope described in the paragraph below since potentially in some jurisdictions output not of direct human origin, by certain means of generation at least, may not be copyrightable (again, IANAL):

Various author(s) may make claims of authorship to content in the project not mentioned in this disclosure, which this disclosure by way of omission unless stated elsewhere implies is of direct human origin unless stated elsewhere. Such statements elsewhere are present and complete if applicable to the best of the disclosure editor(s) ability. Additionally, the project author(s) hereby claim copyright and claim direct human origin to any and all content in the subsections of this disclosure itself, where scope is defined to the best of the ability of the disclosure editor(s), including the subsection names themselves, unless where stated, and unless implied such as by context, being copyrighted or trademarked elsewhere, or other means of statement or implication according to law in applicable jurisdiction(s).

Disclosure editor(s): Hierosoft LLC

Project author: Hierosoft LLC

This disclosure is a voluntary of how and where content in or used by this project was produced by LLM(s) or any tools that are "trained" in any way.

The main section of this disclosure lists such tools. For each, the version, install location, and a scope of their training sources in a way that is specific as possible.

Subsections of this disclosure contain prompts used to generate content, in a way that is complete to the best ability of the disclosure editor(s).

tool(s) used:
- Grok

Scope of use: code described in subsections--typically modified by hand to improve logic, variable naming, integration, etc, but in this commit, unmodified.

## AGENTS.md, install.py, nomcproxy.py, README.md, install-on-target-only/*
- https://grok.com/c/c897f443-5e2b-446b-acff-f8d0f9602669?rid=2ecdaf04-895a-4736-a7ee-1ebe7f7e1779
  - shared: https://grok.com/share/c2hhcmQtMg_51cbbc9c-39bd-4206-a702-c9a70ded36a6

What is the bets self-hosted minecraft proxy for Blightfall (modded Minecraft 1.7.10) and what are the recommended specs for 1-8 players? I want to get it on a vps (probably racknerd) preferably, unless a proxy service is less than $10/mo

I don't care about having a huge raid drive. I have that on my home server. The point of the proxy is merely to hide my home server's ip address.

If I have a server with a few small php websites. Would the nginx option show it down significantly (low end racknerd box -- 3 G nvme, 3G RAM)?

write a cron job that will look up the ip address of redacted.example.com, and if the nginx conf file is missing or has a different ip address, write/rewrite the conf in /etc/nginx/conf.d, and reload nginx. If the angie service is running, write to /etc/angie/conf.d/ instead; but if /etc/angie doesn't exist, still write to nginx dir (assume angie has been set up to use that; but use angie conf notation if angie service is running). Use Python.

How can I check the output? Can we make that more standardized?

Make a readme file with all necessary information.

Make an install script in Python which checks for the main python script in the same dir and using that path generates a file in /etc/cron.d/ with the correct permissions and attributes. Assume the main python script will have the right attributes (I can preserve executable bit in git).

Make the main script a reusable module (rename it to nomcproxy). Make the installer require a "--dynamic" or "--static" argument (followed by a space then an address/ip in either case). If static, import the function(s) from the main script and do a one-time generation of the conf (and reload nginx/angie). Don't leak the redacted hostname nor mention it in any files, not even AGENTS.md. Make a folder in canvas (nomcproxy) and put the files in it. Provide an updated AGENTS.md.

I saw you create the files but there were two readmes (one redundant one outside of the folder I said to make) and now the canvas has no files.

Detect if something other than a web address (WAN hostname) is given for --dynamic, and show an error in that case. Allow anything for static except show an error if it ends with any of the dynamic ip address hosts (Make a constant [by convention, all caps] set and function to check if an address is dynamic in the nomcproxy module).

detect the WAN (not LAN) IP of the current server if a hostname or ip (regardless of static or dynamic) matches the current server, show an error explaining the problem and the purpose of the software.

Add a section to the readme explaining how to setup the target server, including saying that for a home server, a dynamic dns service is recommended, but to keep that hostname and ip address hidden and instead provide {detected_this-server_wan_ip} or a domain pointing to it to a user, and not to install nomcproxy on the home server, only Minecraft/mod should go on the home server. Add a install-on-target-only folder that contains modified versions of the included scripts to work on server instead of client, and install the server jar for vanilla in the case of jar.sh and jar-8.sh in the case of blightfall. Rename the scripts to install-and-run-java-latest-mc.sh and install-and-run-java8-blightfall.sh

Download (or check for existing) jars to /opt/minecraft/latest or /opt/minecraft/1.7.10-blightfall respectively for the target script. Put a separate server.md in the target scripts folder, note that it is part of the nomcproxy project (https://github.com/hierosoft/nomcproxy) but that the folder is for the private server and nomcproxy scripts in the repo root should be run on the public proxy which is used to hide the home/other secret IP address (and dynamic hostname, which should be used for home connections since they typically don't have a static IP address). When installing anything in /opt/minecraft, also maintain a list called /opt/minecraft/nomcproxy.list (don't add redundant entries) of minecraft versions/mods (such as latest and/or 1.7.10-blightfall) that were installed by nomcproxy along with a copy of server.md (/opt/minecraft/server.md) and generate an XDG desktop shortcut pointing to the repo root directory (as detected by the installer; usually the parent folder of the server installer since that is in the install-on-target-only subfolder). Convert the target-only scripts to Python for easier maintainability and to more cleanly detect the directory containing the scripts. do sys.path.insert(0, REPO_DIR) where REPO_DIR = os.path.dirname(TARGET_SCRIPTS_DIR), where TARGET_SCRIPTS_DIR = os.path.dirname(os.path.realpath(__file__))

In install.py, if name is __main__ do sys.exit(main()). Make sure main returns 0 only on success. remove the die function and instead use:
```
def echo0(*args, **kwargs) -> None:
    kwargs['file'] = sys.stderr
    print(*args, **kwargs)
```
and return a number. Say "Error: " explicitly instead of in the function.
