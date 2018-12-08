===========================================
Setting up supervisor (on a single machine)
===========================================

(for supervisor_ 1.0.6)

.. contents::

Supervisor is a fairly cool tool for starting, stopping, and restarting
long-running processes.  I've mostly been using it for my SCGI_-driven
Web sites, to keep the SCGI backend processes running; it's probably
useful for pretty much any Web site that is proxied via Apache or
lighthttpd.

Incidentally, <plug> I'd suggest using twill_ to make sure that your
Web sites are actually up and running & connected to their databases
At least, that's what I do ;).

supervisor was written by Chris McDonough.

Installation
============

Installation is pretty easy.  Download the tar.gz, unpack it,
go into the resulting directory, run ::

   configure
   make
   make install

and you're done.

This should dump a bunch of files in a bunch of places.  Specifically, it will

  * create supervisord, supervisorctl, supervisord-passwd, and pid-proxy in /usr/local/bin;

  * put supervisord.conf and supervisorctl.conf in /usr/local/etc/supervisor/;

  * dump both the supervisor and ZConfig packages into /usr/local/share/supervisor-1.06/;

Should I run supervisor as root?
--------------------------------

supervisor is definitely *designed* to run as root, but there's no
real problem in running it as a non-root user.  To do so, you have
to make sure that the control socket and all of the log files can be
created and written to by the executing user.   (Configuring the
socket and logfile paths will be discussed in the next section.)

Configuring a simple test program to run under supervisor
=========================================================

Let's start by setting up a little toy program to run under
supervisor.  Create a simple shell script, 'sleep-test': ::

   #! /bin/bash
   echo starting to sleep...
   sleep 10

Make sure to 'chmod +x' the script and put it somewhere you'll remember.
('/tmp/' is fine.)

Now go to /usr/local/etc/supervisor/ and edit supervisord.conf.  At the
top of the file, just below <supervisord>, add ::

   <program test>
     command /tmp/sleep-test
     auto-start false
     auto-restart true
     logfile /tmp/test-output.log
   </program>

(Be sure to replace '/tmp/sleep-test' with the actual location of your shell
script!)

Also comment out the 'passwdfile' line (towards the end of the file) and
(if you're not running as root) make sure that 'logfile' and 'pidfile'
are in directories that are writeable by the user running supervisord.
You should check that 'socket-name' is in a directory writeable by
the user executing supervisord, too.

Save this file & edit 'supervisorctl.conf'.   Make sure that the
'socket-name' file is in a directory writeable by the user, too.

All right -- you're done configuring things!

Run '/usr/local/bin/supervisord'.  It should immediately detach from
the terminal and go into the background; make sure it's still running
by checking with 'ps'.

Now run '/usr/local/bin/supervisorctl'.  (It shouldn't ask you for a password,
because you disabled that in the supervisord.conf, right?)  Type 'status'.
You should see something like this: ::

   socket='/usr/local/var/supervisord.sock'
   supervisord_pid=32519
   up=
   down=test

Type 'start test' and exit supervisor (with CTRL-D or 'quit').

You should now see that 'sleep-test' is running (with ps -- remember,
all of the output is going into /tmp/test-output.log!)  Moreover, it
will *stay* running.  Even though the shell script exits every 10
seconds (after the 'sleep 10'), the 'auto-restart' in the configuration
section for '<program test>' tells supervisor to restart it.  Neat, eh?

OK, now run 'supervisorctl' and type 'stop test'.  It will stop, and
you can verify that with 'ps'.

Configure passwords
-------------------

The next thing you should do, before doing *anything else*, is set up
a password file.  First, uncomment the 'passwdfile' line in the
'supervisord.conf' file.

Next, run 'supervisord-password'.  At the 'SRP>' prompt, type 'add
user'.  It will prompt for a password for user 'user'; enter
something.  Now type 'save' and 'quit'.

This has the effect of creating a password file
'/usr/local/etc/supervisor/passwd'; the usernames/password pairs
in this file will govern communications between supervisorctl and
supervisord.

Now restart 'supervisord' by running 'supervisorctl' and typing
'reload' at the prompt.

Now, if you exit supervisorctl and run it again, you should be
prompted for a username and password.  Hopefully the ones you
just configured should work ;).

A quick tour through supervisorctl
----------------------------------

Most of your interaction with 'supervisord' will be through the supervisorctl
command line.  It only has a few commands, and the help documentation is
pretty good when you forget exactly what something does; here's a quick
tour.

'help' tells you what commands are available; 'help command' gives you
more detailed help on the given command.

'reload' tells supervisord to reload the configuration file.

'shutdown' tells supervisord to die.

'start', 'stop', and 'restart' do the obvious things, e.g.
'start test' will start the program named 'test'.

'list' will list the configured programs.

'open' and 'close' are used when you're connecting to supervisord programs
running on other computers; don't worry about them for now.

'logtail' gives you the last few lines of the 'supervisord' log file.

Configuring real programs
=========================

OK, at this point you're probably ready to try a real program.  Here's
a "real-life" situation on one of my servers, 'woodward.caltech.edu';
it's not much more complicated than the above test situation, though!

Here's the config section I used: ::

   <program woodward-scgi>
     command /disk2/cartwheel/bin/canal-scgi-server
     priority 1
     user t
     auto-start true
     auto-restart true
     logfile /disk2/cartwheel/scgi-server.log
   </program>

This config section tells supervisord how to run the SCGI Web-bish
server for the Cartwheel site running on woodward.caltech.edu.

The only new addition here is 'user t', which specifies that the
program should be run under the account 't' (my personal account).

Once I added this config section, I just typed 'reload' and it all
started up just fine.

The 'program' config directives
-------------------------------

There's not too much more to say, actually, but here, explicitly, are the
config directives that you can put in the <program> sections:

'program' -- necessary; command + arguments, separated by whitespace.
No quoting, so neither the command nor the arguments can contain
whitespace, and shell-special characters like '~' don't get handled.

'priority' -- an integer.  when 'restart all' or 'start all' runs, the higher
priority items are started first.  Probably doesn't matter much unless
you have some things that weight down the machine when they start.

'auto-restart' -- boolean, true/false.  Obvious.  Restart on fail?  (If
'auto-start' is false, this only re-starts the process when it was 'start'ed
to begin with.)

'auto-start' -- boolean, true/false.  Also obvious.  If this isn't set
to true, you'll need to do an explicit 'start' command

'user' -- what user to run the command as.  Only applies if supervisord
is running as root (and therefore has setuid privileges).

'logfile' -- where to dump the stdout/stderr from the executed command.

More Advanced Stuff
===================

supervisord has support for a few things that I haven't needed to use.

For one, you can have it listen on a TCP socket rather than on a UNIX domain
socket.  This would let you control processes remotely.  Use the 'open'
command in supervisorctl to connect to more than one machine.

For another, you can do clever things with exit codes.  You can set
certain program exit codes as signals to supervisord to stop running
this program.  Check out '/usr/local/share/supervisor-1.0.6/supervisor/schema.xml' for details.

Criticisms
==========

What article would be complete without my criticisms!?  Seriously,
supervisor is a very nice, easy-to-use piece of software.  I do wish
that it could be installed entirely with a Python-standard 'setup.py',
because then I could put it all in an egg; and I also wonder why
'supervisord-passwd' exists as a standalone program.  (It should be
possible to make this part of supervisord or supervisorctl and thus
reduce by one the number of programs installed.)  No complaints
apart from those two, so far.

Oh, one additional problem: if you try a 'reload' when the config
file is broken, supervisord will die.

And OK, a Web interface would be nice, but I can write that myself. ;)

--titus Mar 25, 2006.

.. _supervisor: http://www.plope.com/software/supervisor
.. _SCGI: http://www.mems-exchange.org/software/scgi/
.. _twill: http://www.idyll.org/~t/www-tools/twill/
