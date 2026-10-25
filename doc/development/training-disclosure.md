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

Can the conf on the target server be included with the other wildcard files in the http block like in the default angie conf of debian 13?
```
user  www-data;
worker_processes  auto;
worker_rlimit_nofile 65536;

error_log  /var/log/angie/error.log notice;
pid        /run/angie.pid;

events {
    worker_connections  65536;
}


http {
    include       /etc/angie/mime.types;
    default_type  application/octet-stream;

        resolver 8.8.8.8 1.1.1.1 valid=300s;   # or 127.0.0.53 if you use systemd-resolved
        acme_client le https://acme-v02.api.letsencrypt.org/directory email=redacted@example.com;


    log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                      '$status $body_bytes_sent "$http_referer" '
                      '"$http_user_agent" "$http_x_forwarded_for"';

    log_format extended '$remote_addr - $remote_user [$time_local] "$request" '
                        '$status $body_bytes_sent "$http_referer" rt="$request_time" '
                        '"$http_user_agent" "$http_x_forwarded_for" '
                        'h="$host" sn="$server_name" ru="$request_uri" u="$uri" '
                        'ucs="$upstream_cache_status" ua="$upstream_addr" us="$upstream_status" '
                        'uct="$upstream_connect_time" urt="$upstream_response_time"';

    access_log  /var/log/angie/access.log  main;

    sendfile        on;
    #tcp_nopush     on;

    keepalive_timeout  65;

    #gzip  on;

    include /etc/angie/http.d/*.conf;
}

#stream {
#    include /etc/angie/stream.d/*.conf;
#}
```
If so, recommend using /etc/angie/http.d instead of conf.d if http.d is present.

Just do all of the steps: https://docs.pterodactyl.io/v1/panel/getting-started

Make sure you don't change the default php. Use php8.3 explicitly. Make sure all passwords you generate are shown directly before exit (not before), even if setup fails and returns early, so we don't miss them. Make a ServerInstallState class to collect the passwords and make state and usage more clear.

Store the Credentials as OrderedDict (key is is operation name) of OrderedDicts (key is credential type or other info). Make the credentials file json. Save with indent 2. If exists, load using object pairs hook OrderedDict. Only save password if was actually set (if system call seemed to work; but actually validate the result wherever possible). Don't ever overwrite the json file unless it was correctly loaded (if was present at the start of the program) and a tmp file was successfully saved (then you can remove existing if was present, and rename tmp to real name). Detect system state to skip any steps that were already done when running the script again--warn and continue to next step. Re-running should not generate credentials that were generated before. Instead use the ones from json if present.

- 2026-10-11

You are installing php-* packages instead of sury php5.3-* packages. Switch back to using php5.3 explicitly. After the php dep install steps I get:
```
Traceback (most recent call last):
  File
"/opt/git/nomcproxy/install-on-target-only/./install-pterodactyl-instead.py"
, line
969
, in
<module>

    sys.exit(
main
()
)

~~~~
^^

  File
"/opt/git/nomcproxy/install-on-target-only/./install-pterodactyl-instead.py"
, line
929
, in
main

    rc = install_php_and_deps()
  File
"/opt/git/nomcproxy/install-on-target-only/./install-pterodactyl-instead.py"
, line
247
, in
install_php_and_deps

    print(f"Starting {
PHP_FPM_SERVICE
}...")

^^^^^^^^^^^^^^^
NameError
:
name 'PHP_FPM_SERVICE' is not defined. Did you mean: 'PHP_FPM_SOCK'?
```

Yes, I meant PHP 8.3. However, Using the zip provided, I get:
```
Traceback (most recent call last):
  File "/opt/git/nomcproxy/install-on-target-only/./install-pterodactyl-instead.py", line 998, in <module>
    sys.exit(main())
             ~~~~^^
  File "/opt/git/nomcproxy/install-on-target-only/./install-pterodactyl-instead.py", line 958, in main
    rc = install_php_and_deps()
  File "/opt/git/nomcproxy/install-on-target-only/./install-pterodactyl-instead.py", line 259, in install_php_and_deps
    if not php83_available() or not php83_from_sury():
           ^^^^^^^^^^^^^^^
NameError: name 'php83_available' is not defined
```

- 2026-10-11

It is taking over a minute here, is that normal?
```
67 packages you are using are looking for funding.
Use the `composer fund` command to find out more!
> @php artisan p:environment:addons:run-hooks post-install || true
Running: php8.3 artisan key:generate --force

   INFO  Application key set successfully.

Running: php8.3 artisan migrate --seed --force

   INFO  Preparing database.

  Creating migration table ....................................................................... 3s DONE

   INFO  Loading stored database schemas.

  database/schema/mysql-schema.sql
```
Then I get:
```
........................................................... 1m 46s DONE

   INFO  Running migrations.

  2024_07_13_091852_clear_unused_allocation_notes ............................................ 1.64ms DONE


   INFO  Seeding database.

  Database\Seeders\NestSeeder .................................................................... RUNNING
  Database\Seeders\NestSeeder ................................................................ 359 ms DONE

  Database\Seeders\EggSeeder ..................................................................... RUNNING
*********************************************
*     Updating Eggs for Nest: Minecraft     *
*********************************************

Created Forge Minecraft
Created Vanilla Minecraft
Created Paper
Created Sponge (SpongeVanilla)
Created Bungeecord

*************************************************
*     Updating Eggs for Nest: Source Engine     *
*************************************************

Created Insurgency
Created Team Fortress 2
Created Ark: Survival Evolved
Created Garrys Mod
Created Counter-Strike: Global Offensive
Created Custom Source Engine Game

*************************************************
*     Updating Eggs for Nest: Voice Servers     *
*************************************************

Created Mumble Server
Created Teamspeak3 Server

****************************************
*     Updating Eggs for Nest: Rust     *
****************************************

Created Rust

  Database\Seeders\EggSeeder ............................................................... 1,776 ms DONE

Running: php8.3 artisan p:user:make --email=admin@localhost --username=admin --name-first=Admin --name-last=User --password=... --admin=1 --no-interaction

In Model.php line 50:

  Could not save Pterodactyl\Models\User[]: failed to validate data: {"email":["The email must be a valid
   email address."]}


Error: php8.3 artisan p:user:make --email=admin@localhost --username=admin --name-first=Admin --name-last=User --password=... --admin=1 --no-interaction failed with exit code 1

============================================================
CREDENTIALS (save these now)
============================================================
...
```
I redacted private info using "..." but you get the idea. Require "--admin-email" followed by a valid email for install to start.

Did user:make really work? It went by so fast running again with the newest install code:
```
Summary:
  Upgrading: 0, Installing: 0, Removing: 0, Not Upgrading: 30
Starting php8.3-fpm...
Synchronizing state of php8.3-fpm.service with SysV service script with /usr/lib/systemd/systemd-sysv-install.
Executing: /usr/lib/systemd/systemd-sysv-install enable php8.3-fpm
php8.3-fpm is active
Pterodactyl panel already installed; skipping base install.
Warning: site conf /etc/angie/http.d/pterodactyl.conf already done; skipping

============================================================
Egg / yolk for blightfall
============================================================
Blightfall (1.7.10) egg:
  1. Download the Blightfall egg JSON:
     https://eggs.pterodactyl.io/egg/games-blightfall/
     (or the raw egg-blightfall.json from the ptero-eggs repo).
  2. Admin → Nests → Import Egg, upload the JSON.
  3. On the server Startup page set the Docker image (yolk) to:
     ghcr.io/pterodactyl/yolks:java_8
     (Blightfall / Forge 1.7.10 requires Java 8).
  4. Allocate port 25565 (or your chosen port) and start the server.

Full automatic egg import requires a panel API key created after
first login; that step is left manual so you can verify the import.

============================================================
Router port forwards (on the home/private network)
============================================================
Forward these TCP ports to this machine so the public proxy can reach them:
  8443/tcp   Pterodactyl panel (atypical; proxy exposes it as 443)
  25565/tcp   Minecraft game (default allocation)
  8080/tcp   Wings API (needed if the panel manages this node)
  2022/tcp   Wings SFTP

Minecraft port notes:
  - Vanilla and Blightfall both default to 25565.
  - If you allocate a different port in the panel, forward that port instead
    and update the nomcproxy backend port to match.

After the proxy is configured with --pterodactyl, players and you
reach everything via the public proxy address only:
  Minecraft:  <public-proxy-ip-or-domain>:25565
  Panel:      https://<public-proxy-ip-or-domain>  (port 443)
The home IP and dynamic hostname are never given out.

============================================================
Next step on the public proxy
============================================================
On the VPS that runs nomcproxy, re-run the installer with --pterodactyl:
  sudo python3 install.py --dynamic <your-home-dynamic-hostname> --pterodactyl
  # or
  sudo python3 install.py --static <home-ip> --pterodactyl

That makes the proxy listen on the typical HTTPS port and forward
to this machine's port 8443. You and players then use only
the public proxy domain/IP; the home IP and dynamic hostname stay hidden.

Access after the proxy is configured:
  Panel:     https://<public-proxy-domain-or-ip>
  Minecraft: <public-proxy-domain-or-ip>:25565

============================================================
CREDENTIALS (save these now)
============================================================
  [database]
    username: pterodactyl
    database: panel
    host: 127.0.0.1
    password: redacted
  [admin]
    email: redacted@example.com
    username: admin
  file: /root/nomcproxy-pterodactyl-credentials.json
============================================================
```

Examine this output and add more output if necessary so we can know what was actually done. Also, determine from this output whether setup is complete or whether that can't be determined from the output of this version.
```
root@redacted:/opt/git/nomcproxy/install-on-target-only# ./install-pterodactyl-instead.py --blightfall --admin-email redacted@example.com
Loaded credentials from /root/nomcproxy-pterodactyl-credentials.json
Installing SURY php8.3 packages and Pterodactyl panel dependencies...
Running: sudo apt update
Hit:1 https://security.debian.org/debian-security trixie-security InRelease
Hit:2 https://packages.sury.org/php trixie InRelease
Hit:3 https://deb.debian.org/debian trixie InRelease
Hit:4 https://deb.debian.org/debian trixie-updates InRelease
Hit:5 https://download.angie.software/angie/debian/13 trixie InRelease
30 packages can be upgraded. Run 'apt list --upgradable' to see them.
Pinned php8.3* to packages.sury.org (/etc/apt/preferences.d/sury-php83)
Running: sudo apt install -y php8.3 php8.3-common php8.3-cli php8.3-gd php8.3-mysql php8.3-mbstring php8.3-bcmath php8.3-xml php8.3-fpm php8.3-curl php8.3-zip mariadb-server tar unzip git redis-server curl software-properties-common apt-transport-https ca-certificates gnupg lsb-release
php8.3 is already the newest version (8.3.35-1+0~20260925.87+debian13~1.gbp19383d).
php8.3-common is already the newest version (8.3.35-1+0~20260925.87+debian13~1.gbp19383d).
php8.3-cli is already the newest version (8.3.35-1+0~20260925.87+debian13~1.gbp19383d).
php8.3-gd is already the newest version (8.3.35-1+0~20260925.87+debian13~1.gbp19383d).
php8.3-mysql is already the newest version (8.3.35-1+0~20260925.87+debian13~1.gbp19383d).
php8.3-mbstring is already the newest version (8.3.35-1+0~20260925.87+debian13~1.gbp19383d).
php8.3-bcmath is already the newest version (8.3.35-1+0~20260925.87+debian13~1.gbp19383d).
php8.3-xml is already the newest version (8.3.35-1+0~20260925.87+debian13~1.gbp19383d).
php8.3-fpm is already the newest version (8.3.35-1+0~20260925.87+debian13~1.gbp19383d).
php8.3-curl is already the newest version (8.3.35-1+0~20260925.87+debian13~1.gbp19383d).
php8.3-zip is already the newest version (8.3.35-1+0~20260925.87+debian13~1.gbp19383d).
mariadb-server is already the newest version (1:11.8.6-0+deb13u1).
tar is already the newest version (1.35+dfsg-3.1).
unzip is already the newest version (6.0-29+deb13u1).
git is already the newest version (1:2.47.3-0+deb13u1).
redis-server is already the newest version (5:8.0.2-3+deb13u3).
curl is already the newest version (8.14.1-2+deb13u5).
software-properties-common is already the newest version (0.99.30-4.1~deb12u1).
apt-transport-https is already the newest version (3.0.3).
ca-certificates is already the newest version (20250419).
gnupg is already the newest version (2.4.7-21+deb13u1).
lsb-release is already the newest version (12.1-1).
Summary:
  Upgrading: 0, Installing: 0, Removing: 0, Not Upgrading: 30
Starting php8.3-fpm...
Synchronizing state of php8.3-fpm.service with SysV service script with /usr/lib/systemd/systemd-sysv-install.
Executing: /usr/lib/systemd/systemd-sysv-install enable php8.3-fpm
php8.3-fpm is active
Warning: composer already done; skipping
Warning: panel download already done; skipping
Running: chmod -R 755 /var/www/pterodactyl/storage /var/www/pterodactyl/bootstrap/cache
Running: chown -R www-data:www-data /var/www/pterodactyl
Warning: database user (stored password validates) already done; skipping
Warning: environment file already done; skipping
Warning: composer install already done; skipping
Warning: application key already done; skipping
Warning: migrations already done; skipping
Running: php8.3 artisan p:user:make --email=redacted@example.com --username=admin --name-first=Admin --name-last=User --password=redacted --admin=1 --no-interaction
+----------+--------------------------------------+
| Field    | Value                                |
+----------+--------------------------------------+
| UUID     | 6e56351d-c88f-4e78-aed7-ffb02dea1218 |
| Email    | redacted@example.com              |
| Username | admin                                |
| Name     | Admin User                           |
| Admin    | Yes                                  |
+----------+--------------------------------------+
Saved credentials to /root/nomcproxy-pterodactyl-credentials.json
Running: systemctl daemon-reload
Running: systemctl enable --now redis-server
Synchronizing state of redis-server.service with SysV service script with /usr/lib/systemd/systemd-sysv-install.
Executing: /usr/lib/systemd/systemd-sysv-install enable redis-server
Running: systemctl enable --now pteroq.service
Created symlink '/etc/systemd/system/multi-user.target.wants/pteroq.service' → '/etc/systemd/system/pteroq.service'.
Warning: site conf /etc/angie/http.d/pterodactyl.conf already done; skipping

============================================================
Egg / yolk for blightfall
============================================================
Blightfall (1.7.10) egg:
  1. Download the Blightfall egg JSON:
     https://eggs.pterodactyl.io/egg/games-blightfall/
     (or the raw egg-blightfall.json from the ptero-eggs repo).
  2. Admin → Nests → Import Egg, upload the JSON.
  3. On the server Startup page set the Docker image (yolk) to:
     ghcr.io/pterodactyl/yolks:java_8
     (Blightfall / Forge 1.7.10 requires Java 8).
  4. Allocate port 25565 (or your chosen port) and start the server.

Full automatic egg import requires a panel API key created after
first login; that step is left manual so you can verify the import.

============================================================
Router port forwards (on the home/private network)
============================================================
Forward these TCP ports to this machine so the public proxy can reach them:
  8443/tcp   Pterodactyl panel (atypical; proxy exposes it as 443)
  25565/tcp   Minecraft game (default allocation)
  8080/tcp   Wings API (needed if the panel manages this node)
  2022/tcp   Wings SFTP

Minecraft port notes:
  - Vanilla and Blightfall both default to 25565.
  - If you allocate a different port in the panel, forward that port instead
    and update the nomcproxy backend port to match.

After the proxy is configured with --pterodactyl, players and you
reach everything via the public proxy address only:
  Minecraft:  <public-proxy-ip-or-domain>:25565
  Panel:      https://<public-proxy-ip-or-domain>  (port 443)
The home IP and dynamic hostname are never given out.

============================================================
Next step on the public proxy
============================================================
On the VPS that runs nomcproxy, re-run the installer with --pterodactyl:
  sudo python3 install.py --dynamic <your-home-dynamic-hostname> --pterodactyl
  # or
  sudo python3 install.py --static <home-ip> --pterodactyl

That makes the proxy listen on the typical HTTPS port and forward
to this machine's port 8443. You and players then use only
the public proxy domain/IP; the home IP and dynamic hostname stay hidden.

Access after the proxy is configured:
  Panel:     https://<public-proxy-domain-or-ip>
  Minecraft: <public-proxy-domain-or-ip>:25565

============================================================
CREDENTIALS (save these now)
============================================================
  [database]
    username: pterodactyl
    database: panel
    host: 127.0.0.1
    password: redacted
  [admin]
    email: redacted@example.com
    username: admin
    password: redacted
  file: /root/nomcproxy-pterodactyl-credentials.json
============================================================
```

Confirm this code isn't necessary anymore and explain why or why not:
```
    """Print config using php8.3-fpm for the already-running nginx or angie.

    The panel site is an http server block. On Debian 13 Angie the default
    conf includes /etc/angie/http.d/*.conf from inside the http { } block,
    so that directory is preferred when it exists.
    """
    print()
    print(f"Using web server: {webserver}")
    print(f"Configure the panel site to listen on port {PANEL_PORT} (not 80/443).")
    print(f"PHP-FPM socket: {PHP_FPM_SOCK}")
    if webserver == "angie":
        http_d = Path("/etc/angie/http.d")
        conf_dir = str(http_d) if http_d.is_dir() else "/etc/angie/conf.d"
    else:
        conf_dir = "/etc/nginx/conf.d"
    print(f"Example ({webserver}) server block for {conf_dir}/pterodactyl.conf:")
    print("(included from the http block via the existing wildcard; do not put it in stream)")
    print(f"""
server {{
    listen {PANEL_PORT};
    server_name _;
    root /var/www/pterodactyl/public;
    index index.php;
    client_max_body_size 100m;

    location / {{
        try_files $uri $uri/ /index.php?$query_string;
    }}
    location ~ \\.php$ {{
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        fastcgi_pass unix:{PHP_FPM_SOCK};
    }}
}}
""")
    print(f"{PHP_FPM_SERVICE} is required. Reload {webserver} after adding the site.")
```

- 2026-10-11

In terms of nginx, "Pterodactyl proxy enabled: public port 443 → private port 8443" isn't quite enough and doesn't seem right. It seems like we need to require a domain (as an arg) to the proxy install if we use the pterydactyl option, put pterydactyl on an atypical port after all, then use nginx to expose it as a domain (?).
```
./install.py --pterodactyl --dynamic dyndns.example.com
Pterodactyl proxy enabled: public port 443 → private port 8443
Access the panel at https://<your-public-proxy-domain-or-ip> (same address you give players for Minecraft). The home/private IP and dynamic hostname stay hidden.
Installed cron job: /etc/cron.d/nomcproxy
  runs: */5 * * * * as root
  command: /opt/git/nomcproxy/nomcproxy.py --dynamic dyndns.example.com
2026-10-11 22:07:45 INFO     Resolved dyndns.example.com → ... (service=angie, conf=/etc/angie/conf.d/nomcproxy.conf)
2026-10-11 22:07:45 INFO     Updating conf: missing → ...
2026-10-11 22:07:45 INFO     Reloaded angie
2026-10-11 22:07:45 INFO     Update complete
Initial dynamic update completed
```
I redacted specifics, but you get the idea. There are other websites on the server, so just going to the ip address results in mismatched domain on cert and the default website appears. I want the user to be able to type in the domain in minecraft or a browser and for it to work.

At the end of setup, if using pterodactyl and angie is detected, print instructions on how to add a new acme object definition to angie.conf (typically add it to /etc/angie/local/http.conf which is included though), since that requires a new acme variable (show it as domain.replace(".", "_")). For example:
```
    acme_client play_example_com
        https://acme-v02.api.letsencrypt.org/directory
        challenge=http
        email=redacted@example.com
        renew_before_expiry=30d;
```

replace any character that isn't a letter or number with "_" actually, when generating the example block name.

Make sure that generated name is used in the angie conf file we generate and save as well so that https works.

Actually, only do that if applicable. Will those logs actually be used on the public proxy?

Explain to me tersely what files the install will write.

Make separate angie conf files in http.d so that the cron job or other runs easily know whether pterodactyl and mc or just mc is being proxied. Do we even need a cron job? Can we just proxy to a dynamic domain instead or do we need the IP in the angie conf(s)?

Ok, get rid of all the cron logic and replace the static and dynamic args with "--host" and resolve a host using proper angie/nginx configs. If using angie, detect whether this part of the (example is the default; commented by default) angie config is commented (and that there is no non-commented stream section in angie.conf), and instruct user to uncomment it if that is a more standard way to do the stream:
```
#stream {
#    include /etc/angie/stream.d/*.conf;
#}
```
If there is some similar/same structure in nginx instruct the user about that if using nginx.

Uncomment the section automatically, or add it if missing. At the end of setup, warn if any files are in stream.d other than the one we wrote.

We can't put the acme client definition in both files. If it is ok in the file in http.d just do it there and don't instruct to put it in the other file. Also, the correct directive within the server block is acme, not acme_certificate when using angie.

- 2026-10-11

In the target scripts and proxy script, detect if any firewall service is running and provide instructions at the end to allow the appropriate ports (and forward in the case of the target, since that is typically a PC behind a router).

There is no acme setup on the target. Do we need that? If so, require a --secret-host option and set it up (same name sanitization as for proxy if an acme client definition is necessary). I'd like to be able to access the server not-by-proxy using the dynamic host, unless not possible to enable https to work using the static proxy domain (if possible, setup 2 acme clients or do whatever we need to do). Explain what is possible and necessary before proceeding with the proxy https plan.

Lets refine and simplify the plan to have proxy-only https before proceeding.

Confirmed.

The include of stream.d is in a stream block already, so we mustn't explicitly say stream in the proxy stream conf file.

Provide instructions for router (in front of server) and detected software firewall (on proxy) even if all of the setup steps are detected as complete. Be sure to specify UDP and/or TCP as necessary. If detected software firewall has a way to easily check if the steps are done, show which steps are done and which are not. If it has that and also has a way to complete the steps automatically, complete them automatically, validate the result, and state which steps are already complete.

Also show (and do if possible) any necessary steps similarly on the server, if it has a firewall service running. In the cases of both server and proxy, if there is no software firewall service running, say so instead of saying any inapplicable steps or saying nothing.

-

After running the appropriate install on the public proxy and home server, if I add a location it doesn't get added to the list and there is no visible error and error in /var/log/angie/error.log (but access.log gets a new entry ...[12/Oct/2026:12:03:07 -0400] "GET /admin/locations HTTP/1.1" 200 13954 "-" "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0" "108.36.238.202")

Why would I want to use wildcard for TRUSTED_PROXIES?


Prepend "mc." to the public domain unless it (as lowercase) already starts with that. If it starts with "panel." and has no dots after that dot, error out and say "panel." will be prepended automatically. Create a relevant acme entry/client or reuse if appropriate, write a dummy index.php to /var/www/{domain}.com if there are no files in there (mc subdomain will be for Minecraft stream proxy, panel subdomain will be for pterydactyl. If either doesn't resolve to IP of proxy, warn at the end of install (even if any/all steps were skipped) that the user must add CNAME records for panel and mc pointing to "{domain}." (trailing dot is typical notation for CNAME records for subdomains; put it in quotes to make the "." explicit in the instructions being printed).

Also explain to the user exactly what to set for the FQDN setting of the Node in Pterodactyl which has the tip:
```
Please enter domain name (e.g node.example.com) to be used for connecting to the daemon. An IP address may be used only if you are not using SSL for this node
```

I meant: If it starts with "panel." and has dots after that dot, error out and say "panel." Use the same rule for mc as for panel: If public domain starts with "mc." and has further dots, that is a problem. The reason I am changing "has no dots" to "has dots" is that if there are no more dots, that would be ok (just leading to tld, not indicating a subdomain). Therefore, always prepend "mc." to the main domain instead of doing it conditionally. The new sanity check ensures the given address is good in the case of both subdomains.

Require the public IP of the proxy as an arg instead of setting TRUSTED_PROXIES to "*".

Remove all traces of MultiLabelZ from your memory in this Grok project including artifacts etc, as that conversation and canvas was accidentally added to this Grok project.

We don't want subdomains on the target only the proxy.

explain if removing the "--public-domain" was ok--do we not need to know the public domain when setting up the server (which may have a private/dynamic domain or IP)?

Rename host to target host in arg and variables wherever it refers to the target server with Minecraft on it. Whenever running install on server or host, save the args to settings json so that if we show the usage screen, we can show "Example:" command containing the real values (but still keep the "Usage" part of the help above that having placeholders like typical CLI help screen).

Actually, rename target host to target server for further clarity.

Always save and load json using OrderedDict. Rename any variables (or constants by convention of all caps) that are Pathlib path objects to end with `path` (or `_PATH` if all caps, `Path` if Pascal or camel case, or whatever is consistent case style with the original). Rename any variables that are str but contain a path to end with either "file" or "dir" (except args, leave those alone), following same case style as original name.

- 2026-10-18

Make sure after the main install runs it 1. shows instructions for the A and CNAME records to set, as in for A main domain (fill it in with the domain we know from json or the specified one if so), and CNAME for mc, node, and panel (Only on the public proxy. We don't want to make the hidden server "convenient" to access). 2. Explains what settings to set in pterodactyl: the correct FQDN (node.$public_proxy_domain), making the location name a public-facing name (recommend one based on public proxy domain); node name (recommend one suitable for public just in case; as in named like proxy not like target server); Mention that if panel subdomain doesn't resolve due to just being set up, wait for up to 72 hours for propogation after saving the CNAME record correctly before you can add a node in pterydactly. 3. how to access home server manually (port(s) to use for mc and pterydactyl) and instruct not to publish these links. 4. Mention the public-facing links and links for admin also using the public domain as a proxy. 5. Any other pterydactly settings specific to our setup (ignore stuff like RAM or storage settings--user can figure that out based on the specs of their home target server). 6. Anything else pertinent to completing the setup (including how to add Blightfall).

What is the point of https://panel.example.com if https://panel.example.com/admin is used to administer the servers and we can use example.com for a public-facing website using a different technology?

What valuable services can be provide to players using a pterydactyl login, and can we let them log in using their microsoft account?

Ok we don't have to look into that further. Just explain some brief info about that (admin stuff, not player stuff, not MS account stuff) to a Pterydactyl section of the readme. After completing setup on proxy or target, check access to the opposite server and try to determine what steps don't seem to be done. For example, after installing proxy and showing setup steps, show warnings about things not yet done such as port so and so isn't responding (or doesn't appear to be pterydactyl) and make sure you run the appropriate install only on target script on your home/target server and have forwarded port so and so. Also check if potential firewall services are up, and if possible check if appropriate rules are configured and show necessary commands (or emit config files and say where they are) but only for a firewall that is specifically known to be running. Perform similar checks after running the target server install on the target server, by checking the known public address and/or hostname ports and subdomains, whatever seems appropriate, and suggest steps. This should appear pretty friendly and not like errors, just saying what the next steps are (run [main script name] on the public proxy VPS and ensure ports are open on any running firewall service).

- 2026-10-24

On the target machine, cd install-on-target-only && ./install-pterodactyl-instead.py (with --blightfall --admin-email --public-domain --proxy-ip options) says:
- paste error regarding missing function detect_firewall

- 2026-10-24

On the proxy, panel.[redacted].com isn't going to pterodactyl, [redacted].com is. I still want [redacted].com to forward to the home server, unless there is a way to connect azuriom to minecraft by installing azuriom on the proxy instead of target, but I want panel.[redacted].com to go to pterodactyl. Even after re-running install on the proxy, I have:
- paste angie domain conf that doesn't define domain and subdomain separately (nor in separate files)

You don't have to keep giving me a zip. The Canvas download feature is fully working now.
- paste error regarding duplicate default server (redefinition of default_server, apparently)

Keep in mind that my angie config has a fallback site in case someone types an address that points to the server but doesn't have an angie conf, and I want to retain this (don't edit this file) apart from the apex site (which we should explicitly filter for; using ##- at the start of the file to ensure filtering order if necessary):
- paste 00-default.conf (correct place for default_server in this case)

You should make sure we name order-dependent angie conf files an actual numerical prefix like "00-" not literally "##-"
