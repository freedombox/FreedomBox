(*
Module: Named
  parses /etc/namedb/named.conf

Author: Mathieu Arnold <mat@FreeBSD.org>

About: Reference
  This lens tries to keep as close as possible to the bind documentation where
  possible. An online source being :
  http://www.freebsd.org/cgi/man.cgi?query=syslog.conf&sektion=5

About: Licence
  This file is licensed under the BSD License.

About: Lens Usage
   To be documented

About: Configuration files
  This lens applies to /etc/namedb/named.conf. See <filter>.

 *)
module Named =
  autoload xfm

    (************************************************************************
     * Group:                 USEFUL PRIMITIVES
     *************************************************************************)

    (* Group: Comments and empty lines *)

    (* Variable: empty *)
        let empty      = Util.empty
    (* Variable: eol *)
        let eol        = Util.eol
    (* Variable: sep_tab *)
        let sep_tab    = Sep.tab
    (* Variable: indent *)
    let indent     = Util.indent


    let chr_blank = /[ \t]/
    let chr_nblank = /[^ \t\n]/
    let chr_any    = /./
    let chr_star   = /\*/
    let chr_nstar  = /[^\* \t\n]/
    let chr_slash  = /\//
    let chr_nslash = /[^\/ \t\n]/
    let chr_nsemicolon = /[^ \t\n;\#\/\*\{\}]/

    let str_no_ip = /[^ \t\n;:\#\/\*\{\}]*[^ \t\n;:\#\/\*\{\}0-9]/
    let boolean = ("yes" | "no")
    let warn_fail_ignore = ( "warn" | "fail" | "ignore" )

    (* Group: single characters macro *)

    (* Variable: semicolon
     Deletes a semicolon and default to it
     *)
    let semicolon  = del /[ \t]*;/ ";"

    let body_start = del /\{([ \t]*\n)?/ "{"

    let body_end = del /[ \t]*\}/ "}"

    let sto_to_eol = store /([^ \t\n].*[^ \t\n]|[^ \t\n])/

    let numbers = /[0-9]+/

    let subnet = Rx.ip | Rx.ip . /\// . numbers

    let del_blank0 = del chr_blank* ""
    let del_blank1 = del chr_blank+ " "

    (************************************************************************
     * Group:                 LENSE DEFINITION
     *************************************************************************)


    (************************************************************************
     *                              COMMENTS
     *************************************************************************)

    let comment_re = chr_nblank
               | ( chr_nblank . chr_any*
               . ( chr_star  . chr_nslash
                 | chr_nstar . chr_slash
                 | chr_nstar . chr_nslash
                 | chr_blank . chr_nblank ) )

    let comment_first_line
               = [ del /([ \t]*\n)?[ \t]*/ ""
             . seq "#comment"
             . store comment_re
              ]
    let comment_other_line
               = [ del /[ \t]*\n[ \t\n]*/ "\n"
             . seq "#comment"
             . store comment_re
              ]
    let comment_end
               = del /[ \t\n]*/ "" . del (chr_star . chr_slash) "*/"

    let comment_extended
             = [ indent
             . del (chr_slash . chr_star) "/*"
             . label "#comment"
             . counter "#comment"
             . ( (comment_first_line . comment_other_line+)
               | comment_first_line?)
             . comment_end
             . eol ]

    let comment_inline
             = [ indent
             . del (chr_slash . chr_slash) "//"
             . label "#inline"
             . indent
             . sto_to_eol
             . eol ]

    let comment      = comment_extended | comment_inline | Util.comment

    (****
     * Generic functions
     *)

    let quoted_string = Util.del_str "\"" . store /[^"]+/ . Util.del_str "\""

    let element (attr:lens) =
      (comment | indent . attr . semicolon) . eol*

    let list0 (attr:lens) =
      (element attr)*

    let list1 (attr:lens) =
      (element attr)+

    let raw_body (attrs:lens) =
      body_start . attrs . body_end

    let body (attr:lens) =
      raw_body (list0 attr)

    let group (name:string) (attr:lens) =
          [ key name
          . del_blank1
          . store /[a-z]+/
          . del_blank0
          . body attr
          ]

    let attr_one (k:regexp) (v:regexp) =
      [key k . del_blank1 . store v]

    let address_match_subnet = [label "ip" . store subnet]
    let address_match_key = [key "key" . del_blank1 . store chr_nsemicolon+]
    let address_match_acl_name = [label "acl" . store /[^ \t\n;:.\#\/\*\{\}]+/]

    let address_match_list = body (address_match_subnet | address_match_key | address_match_acl_name)

    let lns_port_raw (port:regexp) = key "port" . del_blank1 . store port
    let lns_port = lns_port_raw numbers

    let size_spec =
          ( "unlimited"
            | "default"
            | (numbers . (/[KkMmGg]/)?)
          )

    let port_list =
          body [ label "port" . store numbers ]
          | raw_body (
              [ del_blank0
              . key "range"
              . del_blank1
              . [ label "port_low" . store numbers ]
              . del_blank1
              . [ label "port_high" . store numbers ]
              . semicolon ] )

    let string_port_raw (lb:string) (str:lens) (port:lens) =
          [ label lb
          . str
          . [ del_blank1 . port ]? ]

    let string_port (lb:string) (address:regexp) =
      string_port_raw lb (store address) (lns_port)

    let address_port_v46_raw (address:lens) (port:lens) =
      string_port_raw "ip" address port

    let address_port_v46 (address:regexp) =
        address_port_v46_raw (store address) (lns_port)

    (* ACL *)
    (* missing the key possibility *)

    let acl =
        group "acl" address_match_subnet


    (* Control *)


    let controls_inet =
      [ key "inet" . del_blank1 . store ( Rx.ip | "*" )
      . [ del_blank1 . lns_port ]?
      . [ del_blank1 . key "allow" . del_blank1 . address_match_list ]
      . [ del_blank1 . key "keys" . del_blank1 . body [ label "key" . quoted_string ] ] ]

    let controls_unix =
      [ key "unix" . del_blank1 . quoted_string
      . [ del_blank1 . key "perm" . del_blank1 . store numbers ]
      . [ del_blank1 . key "owner" . del_blank1 . store numbers ]
      . [ del_blank1 . key "group" . del_blank1 . store numbers ]
      . [ del_blank1 . key "keys" . del_blank1 . body [ label "key" . quoted_string ] ] ]

    let controls =
      [ key "controls" . del /[ \t]+/ " " . body ( controls_inet | controls_unix ) ]

    (* Include *)

    let include = [ key "include" . del_blank1 . quoted_string ]

    (* Key *)

    let tsig_key =
      [ key "key" . del_blank1 . quoted_string . del_blank0
      . raw_body (
          [ del_blank0 . key "algorithm" . del_blank1 . store ( ( "hmac-md5" | "hmac-sha1" | "hmac-sha224" | "hmac-sha256" | "hmac-sha384" | "hmac-sha512" ) . (/-[0-9]+/)? ) ]
          . semicolon
          . [ del_blank0 . key "secret" . del_blank1 . quoted_string ]
          . semicolon ) ]

    (* Logging *)

    let logging_channel =
      let logging_destination =
        [ del_blank0 . key "file" . del_blank1 . quoted_string
        . [ del_blank0 . key "versions" . del_blank1 . store ( numbers | "unlimited" ) ]?
        . [ del_blank0 . key "size" . del_blank1 . store size_spec ]? ]
        | [ del_blank0 . key "syslog" . del_blank1 . store chr_nsemicolon+ ]
        | [ del_blank0 . key ( "stderr" | "null" ) ] in
      [ key "channel"
      . del_blank1
      . store chr_nblank+
      . del_blank1
      . raw_body (
            logging_destination . semicolon
            . [ del_blank1 . key "severity" . del_blank1 . (
              store ( "critical" | "error" | "warning" | "notice" | "info" | "debug" | "dynamic" )
              | ( store "debug" . [ del_blank1 . label "level" . store numbers ] ) ) . semicolon ]?
            . [ del_blank1 . key ( "print-" . ( "category" | "severity" | "time" ) ) . del_blank1 . store boolean . semicolon ]?
          ) ]

    let logging_category =
      [ key "category"
      . del_blank1
      . store chr_nblank+
      . del_blank1
      . body [ label "channel" . store chr_nsemicolon+ ] ]

    let logging = [ key "logging" . del_blank1 . body (logging_channel | logging_category) ]

    (* lwres *)

    let lwres =
      [ key "lwres"
      . del_blank1
      . raw_body (
          [ del_blank0 . key "listen-on" . del_blank1 . address_port_v46 Rx.ip . semicolon ]?
          . [ del_blank0 . key "view" . del_blank1 . store chr_nsemicolon+ . semicolon ]?
          . [ del_blank0 . key "search" . del_blank1 . body [ label "domain_name" . store chr_nsemicolon+ ] . semicolon ]?
          . [ del_blank0 . key "ndots" . del_blank1 . store numbers . semicolon ]?
          ) ]

    (* masters *)

    let masters_list_name = [ label "masters_list" . store str_no_ip ]

    let masters_list_element =
      [ label "master"
      . store Rx.ip
      . [ del_blank1 . lns_port ]?
      . (del_blank1 . address_match_key)? ]

    let masters =
      let masters_list = (masters_list_name | masters_list_element) in
      [ key "masters"
      . del_blank1
      . store chr_nsemicolon+
      . [ del_blank1 . lns_port ]?
      . del_blank0
      . body masters_list ]

    (* Options *)

    let options_attr_boolean =
      attr_one ( "acache-enable" | "additional-from-auth" | "additional-from-cache" | "auth-nxdomain" | "check-integrity" | "check-sibling" | "check-wildcard" | "deallocate-on-exit" | "dnssec-accept-expired" | "dnssec-dnskey-kskonly" | "dnssec-enable" | "dnssec-must-be-secure" | "dnssec-secure-to-insecure" | "dnssec-validation" | "empty-zones-enable" | "fake-iquery" | "fetch-glue" | "flush-zones-on-shutdown" | "has-old-clients" | "host-statistics" | "maintain-ixfr-base" | "match-mapped-addresses" | "memstatistics" | "minimal-responses" | "multiple-cnames" | "notify-to-soa" | "provide-ixfr" | "querylog" | "recursion" | "request-ixfr" | "rfc2308-type1" | "treat-cr-as-space" | "try-tcp-refresh" | "update-check-ksk" | "use-alt-transfer-source" | "use-id-pool" | "use-ixfr" | "use-queryport-pool" | "zero-no-soa-ttl" | "zero-no-soa-ttl-cache" | "zone-statistics") boolean

    let options_attr_number =
      attr_one ("acache-cleaning-interval" | "cleaning-interval" | "clients-per-query" | "edns-udp-size" | "heartbeat-interval" | "host-statistics-max" | "interface-interval" | "lame-ttl" | "max-cache-ttl" | "max-clients-per-query" | "max-ixfr-log-size" | "max-ncache-ttl" | "max-refresh-time" | "max-retry-time" | "max-transfer-idle-in" | "max-transfer-idle-out" | "max-transfer-time-in" | "max-transfer-time-out" | "max-udp-size" | "min-refresh-time" | "min-retry-time" | "min-roots" | "port" | "queryport-pool-ports" | "queryport-pool-updateinterval" | "recursive-clients" | "reserved-sockets" | "serial-queries" | "serial-query-rate" | "sig-signing-nodes" | "sig-signing-signatures" | "sig-signing-type" | "statistics-interval" | "tcp-clients" | "tcp-listen-queue" | "transfers-in" | "transfers-out" | "transfers-per-ns") numbers


    let options_attr_string =
      [ key ("attach-cache" | "bindkeys-file" | "cache-file" | "directory" | "dump-file" | "hostname" | "key-directory" | "memstatistics-file" | "named-xfer" | "pid-file" | "random-device" | "recursing-file" | "statistics-file" | "tkey-domain" | "tkey-gssapi-credential" | "version")
      . del_blank1
      . quoted_string ]

    let options_dialup =
      attr_one "dialup" ( boolean | "notify" | "refresh" | "passive" | "notify-passive" )

    let options_forwarders =
      [ key "forwarders"
      . del_blank1
      . body (address_port_v46 Rx.ip) ]

    let options_address_match_list =
      [ key ("allow-notify" | "allow-query" | "allow-query-cache" | "allow-query-cache-on" | "allow-query-on" | "allow-recursion" | "allow-recursion-on" | "allow-transfer" | "allow-update" | "allow-update-forwarding" | "allow-v6-synthesis" | "blackhole" | "sortlist" | "topology")
      . del_blank1
      . address_match_list ]

    let options_port_address_match_list =
      let port = [ del_blank1 . lns_port ] in
      let addr = [ del_blank1 . address_match_list ] in
      [ key ("listen-on" | "listen-on-v6")
      . ( port | addr | ( port . addr ) ) ]

    let options_size_spec =
      attr_one ("max-journal-size" | "coresize" | "datasize" | "files" | "stacksize" | "max-cache-size" | "max-acache-size") size_spec

    let options_port_list =
      [ key ("use-v4-udp-ports" | "avoid-v4-udp-ports" | "use-v6-udp-ports" | "avoid-v6-udp-ports")
      . del_blank1
      . port_list ]

    let options_address_port =
      let options_address_port_v46 (k:regexp) (address:regexp) =
        [ key k . del_blank1 . (address_port_v46 (address|"*")) ] in
      options_address_port_v46 ("transfer-source" | "alt-transfer-source" | "notify-source") Rx.ipv4
      | options_address_port_v46 ("transfer-source-v6" | "alt-transfer-source-v6" | "notify-source-v6") Rx.ipv6

    let options_address_port2 =
      let options_address_port_v46 (k:regexp) (address:regexp) =
        [ key k
        . del_blank1
        . (address_port_v46_raw (del /(address[ \t]+)?/ "" . store (address|"*")) (lns_port_raw (numbers|"*"))) ] in
      options_address_port_v46 ("query-source") Rx.ipv4
      | options_address_port_v46 ("query-source-v6") Rx.ipv6

    let options_dnssec_lookaside =
      [ key "dnssec-lookaside"
      . del_blank1
      . ( store "auto"
          | [ label "domain"
            . store chr_nsemicolon+
            . del_blank1 ]
            . [ key "trust-anchor"
            . del_blank1
            . store chr_nsemicolon+ ]) ]

    let options_preferred_glue = attr_one "preferred-glue" ( "A" | "AAAA" | "NONE" )

    let options_check_things =
      attr_one ( "check-dup-records" | "check-mx" | "check-mx-cname" | "check-srv-cname" ) warn_fail_ignore

    let options_check_names =
      [ key "check-names"
      . del_blank1
      . [ key ( "master" | "slave" | "response" )
        . del_blank1
        . store warn_fail_ignore ] ]

    let options_filter_aaaa = attr_one "filter-aaaa-on-v4" ( boolean | "break-dnssec" )

    let options_also_notify =
      [ key "also-notify"
      . del_blank1
      . body (address_port_v46 Rx.ip) ]

    let options_notify = attr_one "notify" (boolean | "explicit" | "master-only" )

    let options_masterfile_format = attr_one "masterfile-format"  ("text"|"raw")

    let options_root_delegation_only =
      [ key "root-delegation-only"
      . [ del_blank1 . key "exclude" . del_blank1
        . body [ label "name" . quoted_string ]
        ]? ]

    let options_forward = attr_one "forward" ( "only" | "first" )

    let options_ixfr_from_differences = attr_one "ixfr-from-differences" (boolean | "master" | "slave" )

    let options_server_id =
      [ key "server-id"
      . del_blank1
      . ( store ( "none" | "hostname" )
          | [ label "name" . quoted_string ] ) ]

    let options_transfer_format = attr_one "transfer-format" ( "one-answer" | "many-answer" )

    let options_disable_algorithms =
      [ key "disable-algorithms"
      . del_blank1
      . [ label "name" . store chr_nblank+ ]
      . del_blank1
      . body [ label "algorithm" . store chr_nsemicolon+ ] ]

      (* Not very proud of the domain_name regexp, as I can't use "- Rx.ipv4"
       because of it's slowness, I have to say that it can't end with a number. *)
    let options_dual_stack_servers =
      [ key "dual-stack-servers"
      . [ del_blank1 . lns_port ]?
      . del_blank1
      . body ( address_port_v46 Rx.ip
             | string_port "domain_name" (str_no_ip) ) ]

    let options_tkey_dhkey =
      [ key "tkey-dhkey"
      . [ del_blank1 . label "key_name" . store chr_nblank+ ]
      . [ del_blank1 . label "key_tag" . store chr_nsemicolon+ ] ]

    let options_empty_stuff =
      [ key ( "empty-contact" | "empty-server" )
      . del_blank1
      . quoted_string ]

    let options_sig_validity_interval =
      [ key "sig-validity-interval"
      . [ del_blank1 . label "expire" . store numbers ]
      . [ del_blank1 . label "resign" . store numbers ]? ]

    let options_notify_delay = attr_one "notify-delay" numbers

    let options_disable_empty_zone = [ key "disable-empty-zone" . del_blank1 . quoted_string ]

    let options_deny_answer_addresses =
      [ key "deny-answer-addresses"
      . del_blank1
      . address_match_list
      . [ del_blank1 . key "except-from" . del_blank1 . body [ label "domain_name" . store chr_nsemicolon+ ] ]? ]

    let options_deny_answer_aliases =
      let label_domain = [ label "domain_name" . store chr_nsemicolon+ ] in
      [ key "deny-answer-aliases"
      . del_blank1
      . body label_domain
      . [ del_blank1 . key "except-from" . del_blank1 . body label_domain ]? ]

    let options_rrset_order =
      let order_spec =
        [ [ key "class" . del_blank1 . store chr_nblank+ . del_blank1 ]?
        . [ key "type" . del_blank1 . store chr_nblank+ . del_blank1 ]?
        . [ key "name" . del_blank1 . quoted_string . del_blank1 ]?
        . key "order" . del_blank1 . store ( "fixed" | "random" | "cyclic" ) ]
      in
      [ key "rrset-order" . del_blank1 . body order_spec ]

    let options_re =
      (   options_attr_boolean
          | options_attr_number
          | options_attr_string
          | options_dialup
          | options_forwarders
          | options_address_match_list
          | options_port_address_match_list
          | options_size_spec
          | options_port_list
          | options_address_port
          | options_address_port2
          | options_dnssec_lookaside
          | options_preferred_glue
          | options_check_things
          | options_check_names
          | options_filter_aaaa
          | options_also_notify
          | options_notify
          | options_masterfile_format
          | options_root_delegation_only
          | options_forward
          | options_ixfr_from_differences
          | options_server_id
          | options_transfer_format
          | options_disable_algorithms
          | options_dual_stack_servers
          | options_tkey_dhkey
          | options_empty_stuff
          | options_sig_validity_interval
          | options_notify_delay
          | options_disable_empty_zone
          | options_deny_answer_addresses
          | options_deny_answer_aliases
          | options_rrset_order
      )

    let options = [ key "options" . del /[ \t]+/ " " . body options_re ]

    (* server *)

    let server_attr_boolean =
      attr_one ( "bogus" | "provide-ixfr" | "request-ixfr" | "edns" | "use-queryport-pool" ) boolean

    let server_attr_numbers =
      attr_one ( "edns-udp-size" | "max-udp-size" | "transfers" | "queryport-pool-ports" | "queryport-pool-updateinterval" ) numbers

    let server_address_port =
      let options_address_port_v46 (k:regexp) (address:regexp) =
        [ key k . del_blank1 . (address_port_v46 (address|"*")) ] in
      options_address_port_v46 ("transfer-source" | "notify-source") Rx.ipv4
      | options_address_port_v46 ("transfer-source-v6" | "notify-source-v6") Rx.ipv6

    let server_keys =
      [ key "keys"
      . del_blank1
      . body [ label "key" . store chr_nsemicolon+ ] ]

    let server_re =
      ( server_attr_boolean
        | server_attr_numbers
        | options_transfer_format
        | options_address_port2
        | server_address_port
        | server_keys
      )

    let server =
      [ key "server"
      . del_blank1
      . store subnet
      . del_blank1
      . body server_re ]

    (* statistics-chanels *)

    let statistics_channels_body =
      [ key "inet" . del_blank1 . store ( Rx.ip | "*" )
      . [ del_blank1 . lns_port ]?
      . [ del_blank1 . key "allow" . del_blank1 . address_match_list ]? ]

    let statistics_channels =
      [ key "statistics-channels"
      . del_blank1
      . body statistics_channels_body ]

    (* trusted-keys *)

    let trusted_keys_key =
      [ label "key"
      . [ label "domain" . store chr_nsemicolon+ ]
      . [ del_blank1 . label "flag" . store numbers ]
      . [ del_blank1 . label "protocol" . store numbers ]
      . [ del_blank1 . label "algorithm" . store numbers ]
      . del_blank1 . quoted_string ]

    let trusted_keys =
      [ key "trusted-keys"
      . del_blank1
      . body trusted_keys_key ]

    (* managed-keys *)

    let managed_keys_key =
      [ label "key"
      . [ label "domain" . store chr_nsemicolon+ ]
      . [ del_blank1 . label "initialization" . store ("initial-key") ]
      . [ del_blank1 . label "flag" . store numbers ]
      . [ del_blank1 . label "protocol" . store numbers ]
      . [ del_blank1 . label "algorithm" . store numbers ]
      . del_blank1 . quoted_string ]

    let managed_keys =
      [ key "managed-keys"
      . del_blank1
      . body managed_keys_key ]

    (* Entries *)

    let entries = list0 (acl | controls | include | tsig_key | logging | lwres | masters | options | server | statistics_channels | trusted_keys | managed_keys )

    (* Group: Top of the tree *)

    (* View: lns
     generic entries then programs or hostnames matching blocs
     *)
    let lns = eol* . entries

    (* Variable: filter
     all you need is /etc/namedb/named.conf
     *)
        let filter = incl "/etc/namedb/named.conf"

        let xfm = transform lns filter
