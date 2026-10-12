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
- 2026-10-11 https://grok.com/c/c897f443-5e2b-446b-acff-f8d0f9602669?rid=2ecdaf04-895a-4736-a7ee-1ebe7f7e1779
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

- 2026-10-11

For the private server add a install-pterodactyl-instead.py script to install pterodactyl instead (detect if angie, nginx, or apache2 is running if applicable/necessary for pterodactyl) in the install-on-target-only folder; run it on an atypical port if possible to script that configuration. Tell the user what ports to forward on their router for pterodactyl and minecraft (may vary depending on whether using 1.7.10* or latest; provide both instructions when installing pterodactyl since that may install any version; but explain how to install the egg for Vanilla or for Blightfall, and the java8 yolk in the latter case. Automate using CLI args for the new script if possible to do the egg and yolk from the CLI; and if that is possible, require --latest or --blightfall arg otherwise do not install anything. Detect if pterodactyl was already installed, and if so, install only the egg, and yolk if applicable, or if can't be automated then explain how. After install, explain to the user they must use the --pterodactyl option when using the proxy install script, and explain to the user they can access pterodactyl through the proxy on the same publicly-shared domain as the public minecraft address without revealing the home/other private IP address or dynamic domain). Add a pterydactyl option to install.py (optional) which will proxy pterydactyl on whatever port the private server will use, but on the proxy server use the typical port. Instruct the user how to access it when done.

Capitalize H in hierosoft in github URLs. Change "latest" to "vanilla" in args, folder names, and documentation. Improve the install pterodactyl instead script to actually run apt update and install php8.3 (that version is required specifically, so update angie and nginx instructions with regard to php-8.3-fpm) and start the php8.3-fpm service or whatever the service is called on debian. Only actually perform the steps if the apt or at least apt-get command is available via shutil.which (prefer apt). Install the required modules and dependencies as per https://docs.pterodactyl.io/v1/panel/getting-started

The install and run can be still called install-and-run-java-latest-mc.py since it runs the latest java as opposed to the latest vanilla minecraft. Look over the scripts and documentation and use the term latest whenever referring to java versions.

- 2026-10-11

If /opt/minecraft/server.md is detected at the start of proxy install, or angie/nginx conf names are detected at the start of the proxy install, explain the correct usage and refuse to install.

I meant: If /opt/minecraft/server.md is detected at the start of proxy install, or angie/nginx conf names are detected at the start of the server install (any scripts in target folder), explain the correct usage and refuse to install. To clarify further, of course proxy conf names are allowed at start of proxy install, and server conf(s) are allowed at start of server install, but all scripts should detect the opposing confs and refuse to continue.

The canvas keeps going inactive then reviving workspaces if I go to Preview then back to canvas, even if I download the files one by one. The problem started today. Also, starting today, if I right-click any folder then click download, it says "Could not download" that folder name, "try again." I can only download one file at a time.

Both symptoms happen in Waterfox and 153.0.8010.52 (Official Build) for Linux Mint (x86_64) starting today and never happened before. Then again I never used Canvas without a project. Nonetheless, if I move this chat to a project, the problem still happens.

- 2026-10-11

On debian 13 I have php8.4 but for the 8.3 install via the script I get:
```
Error: Unable to locate package php8.3
Error: Couldn't find any package by glob 'php8.3'
Error: Package 'php8.3-common' has no installation candidate
Error: Unable to locate package php8.3-cli
Error: Couldn't find any package by glob 'php8.3-cli'
Error: Unable to locate package php8.3-gd
Error: Couldn't find any package by glob 'php8.3-gd'
Error: Unable to locate package php8.3-mysql
Error: Couldn't find any package by glob 'php8.3-mysql'
Error: Unable to locate package php8.3-mbstring
Error: Couldn't find any package by glob 'php8.3-mbstring'
Error: Unable to locate package php8.3-bcmath
Error: Couldn't find any package by glob 'php8.3-bcmath'
Error: Unable to locate package php8.3-xml
Error: Couldn't find any package by glob 'php8.3-xml'
Error: Unable to locate package php8.3-fpm
Error: Couldn't find any package by glob 'php8.3-fpm'
Error: Unable to locate package php8.3-curl
Error: Couldn't find any package by glob 'php8.3-curl'
Error: Unable to locate package php8.3-zip
Error: Couldn't find any package by glob 'php8.3-zip'
Error: package install failed
```

- 2026-10-11

Never install nginx, angie, nor apache2, in case the person has a packaged or compiled angie or other. Make sure install halts if neither nginx nor angie is running. Make sure install halts if any of the system commands return non-zero (excluding apt update, which can have non-fatal issues) unless non-zero return is being used as a sanity check and non-zero is ok. Halt if any condition would make setup invalid instead of proceeding.

provide an updated zip

Instead of using sys.exit more than one place (in if __name__ == "__main__") return nonzero from functions where necessary, and when each of the functions now containing exit are called, instead capture the return in the caller and if non-zero, return early with that code as necessary. Logic should flow all the way back to main every time so that functions are modular. Main can also exit early as necessary if it receives non-zero return codes where that would prevent a successful install. Then provide an updated zip.
