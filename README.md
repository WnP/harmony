harmony
=======

Command line CalDAV client, for those of us who hate corporate calendaring.
Harmony aims to be for calendaring what mutt is for email -- simple, powerful
command line goodness.

## To-do

* Everything! (I'm too lazy right now...)
* SQLite database backend
* (n)curses and/or slib UI
* Config file
* iCalendar import/export

### Language features

* Query syntax for looking up events with the CLI
* Line folding for parsing config directives that span multiple lines

### Calendar Sources

Harmony should be able to find calendar data in several locations.

* CalDAV: Pretty much a no brainer, right?
* IMAP: Poll an IMAP server for new messages, looking for those that look like
  event invites.
* Maildir: Same as IMAP, but monitor a Maildir directory.

## Authors

* Eryn Wells (<eryn@erynwells.me>)
