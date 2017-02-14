(* Tor lens for Augeas

Author: James Valleroy <jvalleroy@mailbox.org>

About: Reference
  Online Tor configuration manual:
  https://www.torproject.org/docs/tor-manual.html.en

About: License
  This file is licensed under the LGPL v2+.

About: Configuration files
  This lens applies to /etc/tor/torrc. See <filter>.

*)


module Tor =

autoload xfm

let eol = Util.eol

let ws = /[ \t]/
let k = /[A-Za-z0-9_.,:*]+/
let val = /[A-Za-z0-9_.,:*+-=\/]+/

let bracket_val = "[" . val* . "]" . val*
let multi_val = val . (" " . val)+

let simple_entry = [ key k . del ws+ " " . store val . eol ]
let bracket_entry = [ key k . del ws+ " " . store bracket_val . eol ]
let multi_entry = [ key k . del ws+ " " . store multi_val . eol ]

let entry = simple_entry|bracket_entry|multi_entry
let lns = (entry|Util.comment|Util.empty_dos)*

let filter = (incl "/etc/tor/torrc")

let xfm = transform lns filter
