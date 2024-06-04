Scheduling a Regular Backup
---------------------------
On linux you can add gphotos-sync to your cron schedule easily. See https://crontab.guru/
for tips on how to configure regular execution of a command. You will need a script that
looks something like this::

    #!/bin/bash
    <PATH TO VENV>/bin/python gphotos-sync <PATH TO TARGET> $@ >> <PATH TO TARGET>/gphotos_full.log --logfile /tmp 2>&1

gphotos-sync uses a lockfile so that if a cron job starts while a previous one
is still running then the 2nd instance will abort.

Note that cron does not have access to your profile so none of the usual 
environment variables are available.