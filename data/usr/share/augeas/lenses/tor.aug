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
let kc = /[A-Za-z0-9_.,:*]/
let vc = /[-A-Za-z0-9_.,:*\/ ]/
let keyname = kc+
let val = /[[\/]*/ . kc . (vc* . /[]]*/ . vc* . kc . /[\/]*/)?

let entry = [ key keyname . del ws+ " " . store val . eol ]

let lns = (entry|Util.comment|Util.empty_dos)*

let filter = (incl "/etc/tor/torrc")

let xfm = transform lns filter
