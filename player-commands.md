# Player commands (non-OP)

Commands available to regular players on the Tekkit Classic / Towny server. <br>
These do not require operator status. Some need specific permissions that are granted by default or by group. <br>
Placeholders use `<angle brackets>`.

Admin / OP commands are documented separately in [commands.md](https://github.com/Hierosoft/nomcproxy/blob/main/commands.md). <br>
Plugin settings and GroupManager notes are in [install-on-target-only/plugins.md](https://github.com/Hierosoft/nomcproxy/blob/main/install-on-target-only/plugins.md).

## Jobs (professions)

View available jobs:

```
/jobs browse
```

Join a job (job names are case-sensitive; common ones include Miner, Hunter, Lumberjack, Farmer, Brewer, Weaponsmith):

```
/jobs join <job>
```

Leave a job:

```
/jobs leave <job>
```

See what a job pays for (actions such as break, place, or kill):

```
/jobs info <job>
/jobs info <job> <break|place|kill>
```

View your current job levels and experience:

```
/jobs stats
```

## Towny (basic)

See the map of claims around you:

```
/towny map
```

Check the town or plot you are standing in:

```
/town here
/plot
```

See your own resident information:

```
/res
```

## Lockette

Lock a chest: hold a sign and right-click the chest. The sign becomes:

```
[Private]
<your name>
```

Add another player to an existing lock (right-click the sign first):

```
/lockette <line> <player>
```

`<line>` is 3 or 4 on the first sign (line 2 is the owner). <br>
For more than two extra players, place a second sign (it becomes `[More Users]`) and use the same command on that sign.

Remove a name from a line:

```
/lockette <line>
```

## Other

Many other actions (building in claimed plots, using doors, etc.) depend on Towny permissions and do not require chat commands.
