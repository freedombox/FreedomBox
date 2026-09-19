require ["vnd.dovecot.pipe", "copy", "imapsieve", "environment"];
if environment "imap.mailbox" "Trash" {
   # Putting spam in Trash mailbox is not significant
   stop;
}
pipe :copy "rspamc" ["learn_ham"];
