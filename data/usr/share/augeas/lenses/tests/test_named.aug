module Test_Named =

    test (Named.address_port_v46 Rx.ipv4) get "1.2.3.4" = { "ip" = "1.2.3.4" }
    test (Named.address_port_v46 Rx.ipv6) get "::1" = { "ip" = "::1" }

    test (Named.address_port_v46 Rx.ipv4) get "1.2.3.4 port 53" = { "ip" = "1.2.3.4" { "port" = "53" } }

    test (Named.string_port "dom" /[a-z]+/) get "foobar port 22" = { "dom" = "foobar" { "port" = "22" } }

    test Named.address_match_subnet get "1.2.3.4" = { "ip" = "1.2.3.4" }
    test Named.address_match_subnet get "1.2.3.4/32" = { "ip" = "1.2.3.4/32" }
    test Named.address_match_subnet get "::1" = { "ip" = "::1" }
    test Named.address_match_subnet get "::1/128" = { "ip" = "::1/128" }

    test Named.address_match_key get "key foobar" = { "key" = "foobar" }

    test Named.address_match_acl_name get "foobar" = { "acl" = "foobar" }

    test Named.address_match_list get "{ 1.2.3.4; key foo; bar;\n }" = { "ip" = "1.2.3.4" } { "key" = "foo" } { "acl" = "bar" }

    test [Named.lns_port] get "port 123" = { "port" = "123" }

    test Named.controls_inet get "inet 1.2.3.4 allow { 1.2.3.4; } keys { \"tata\"; }" =
      { "inet" = "1.2.3.4"
        { "allow" { "ip" = "1.2.3.4" } }
        { "keys" { "key" = "tata" } } }
    test Named.controls_inet get "inet * port 953 allow { 1.2.3.4; } keys { \"tata\"; }" =
      { "inet" = "*"
        { "port" = "953" }
        { "allow" { "ip" = "1.2.3.4" } }
        { "keys" { "key" = "tata" } } }

    test Named.controls_unix get "unix \"/foo/bar\" perm 644 owner 123 group 234 keys { \"tutu\"; }" =
      { "unix" = "/foo/bar"
        { "perm" = "644" } { "owner" = "123" } { "group" = "234" }
        { "keys" { "key" = "tutu" } } }

    test Named.controls get "controls {inet 1.2.3.4 allow { 1.2.3.4; } keys { \"tata\"; }; }" =
      { "controls"
        { "inet" = "1.2.3.4"
          { "allow" { "ip" = "1.2.3.4" } }
          { "keys" { "key" = "tata" } } } }

    test Named.include get "include \"foo/bar\"" = { "include" = "foo/bar" }

    test Named.tsig_key get "key \"foo\" { algorithm hmac-sha1-80; secret \"foobar\"; }" =
      { "key" = "foo"
        { "algorithm" = "hmac-sha1-80" }
        { "secret" = "foobar" } }

    test Named.logging_channel get "channel foo { file \"foo\"; }" =
      { "channel" = "foo"
        { "file" = "foo" } }

    test Named.logging_channel get "channel foo { file \"foo\" versions 3 size 2G; }" =
      { "channel" = "foo"
        { "file" = "foo"
          { "versions" = "3" }
          { "size" = "2G" } } }

    test Named.logging_channel get "channel foo { syslog local0; }" =
      { "channel" = "foo"
        { "syslog" = "local0" } }

    test Named.logging_channel get "channel foo { stderr; }" =
      { "channel" = "foo"
        { "stderr" } }

    test Named.logging_channel get "channel foo { null; }" =
      { "channel" = "foo"
        { "null" } }

    test Named.logging_channel get "channel foo { stderr; severity warning; print-time yes; }" =
      { "channel" = "foo"
        { "stderr" }
        { "severity" = "warning" }
        { "print-time" = "yes" } }

    test Named.logging_channel get "channel foo { stderr; severity debug 4; }" =
      { "channel" = "foo"
        { "stderr" }
        { "severity" = "debug"
          { "level" = "4" } } }

    test Named.logging_category get "category default { null; }" =
      { "category" = "default" { "channel" = "null" } }

    test Named.logging get "logging { channel stderr { stderr; print-time yes; }; category dnssec { stderr; }; }" =
      { "logging"
        { "channel" = "stderr"
          { "stderr" }
          { "print-time" = "yes" } }
        { "category" = "dnssec"
          { "channel" = "stderr" } } }

    test Named.lwres get "lwres { }" = { "lwres" }
    test Named.lwres get "lwres { listen-on ::1 port 21; view tata; search { example.org; }; ndots 0; }" =
      { "lwres"
        { "listen-on" { "ip" = "::1" { "port" = "21" } } }
        { "view" = "tata" }
        { "search" { "domain_name" = "example.org" } }
        { "ndots" = "0" } }

    test Named.masters_list_name get "foo" = { "masters_list" = "foo" }
    test Named.masters_list_element get "1.2.3.4" = { "master" = "1.2.3.4" }
    test Named.masters_list_element get "1.2.3.4 port 1 key foo" =
      { "master" = "1.2.3.4" { "port" = "1" } { "key" = "foo" } }

    test Named.masters get "masters bar { }" = { "masters" = "bar" }
    test Named.masters get "masters bar port 1 { foo; 1.2.3.4; }" =
      { "masters" = "bar"
        { "port" = "1" }
        { "masters_list" = "foo" }
        { "master" = "1.2.3.4" } }

    test Named.options_attr_boolean get "querylog no" = { "querylog" = "no" }

    test Named.options_attr_number get "port 12" = { "port" = "12" }

    test Named.options_attr_string get "pid-file \"/var/run/named.pid\"" = { "pid-file" = "/var/run/named.pid" }

    test Named.options_dialup get "dialup no" = { "dialup" = "no" }

    test Named.options_forwarders get "forwarders {\n 1.2.3.4; \n::2;  }" =
    { "forwarders"
        { "ip" = "1.2.3.4" }
        { "ip" = "::2" } }

    test Named.options_address_match_list get "allow-query { 1.2.3.4; }" = { "allow-query" { "ip" = "1.2.3.4" } }

    test Named.options_port_address_match_list get "listen-on port 53" = { "listen-on" { "port" = "53" } }

    test Named.options_port_address_match_list get "listen-on { 1.2.3.4; }" = { "listen-on" { { "ip" = "1.2.3.4" } } }

    test Named.options_port_address_match_list get "listen-on port 5353 { 1.2.3.4; }" =
      { "listen-on" { "port" = "5353" } { { "ip" = "1.2.3.4" } } }

    test Named.options_size_spec get "files default" = { "files" = "default" }
    test Named.options_size_spec get "files unlimited" = { "files" = "unlimited" }
    test Named.options_size_spec get "files 1234" = { "files" = "1234" }
    test Named.options_size_spec get "files 12M" = { "files" = "12M" }

    test Named.port_list get "{ range 1 5; }" = { "range" { "port_low" = "1" } { "port_high" = "5" } }
    test Named.port_list get "{ 1; 2; }" = { "port" = "1" } { "port" = "2" }

    test Named.options_port_list get "use-v4-udp-ports { 1; 2; }" =
      { "use-v4-udp-ports"
        { "port" = "1" }
        { "port" = "2" }
      }

    test Named.options_address_port get "transfer-source 1.2.3.4" = { "transfer-source" { "ip" = "1.2.3.4" } }
    test Named.options_address_port get "transfer-source *" = { "transfer-source" { "ip" = "*" } }
    test Named.options_address_port get "transfer-source 1.2.3.4 port 53" = { "transfer-source" { "ip" = "1.2.3.4" { "port" = "53" } } }
    test Named.options_address_port get "transfer-source-v6 2a01::" = { "transfer-source-v6" { "ip" = "2a01::" } }

    test Named.options_address_port2 get "query-source-v6 2a01::" = { "query-source-v6" { "ip" = "2a01::" } }
    test Named.options_address_port2 get "query-source * port *" = { "query-source" { "ip" = "*" { "port" = "*" } } }
    test Named.options_address_port2 get "query-source address 1.2.3.4 port 1" = { "query-source" { "ip" = "1.2.3.4" { "port" = "1" } } }

    test Named.options_dnssec_lookaside get "dnssec-lookaside auto" = { "dnssec-lookaside" = "auto" }
    test Named.options_dnssec_lookaside get "dnssec-lookaside . trust-anchor dlv.isc.org." = { "dnssec-lookaside" { "domain" = "." } { "trust-anchor" = "dlv.isc.org." } }

    test Named.options_preferred_glue get "preferred-glue A" = { "preferred-glue" = "A" }

    test Named.options_check_things get "check-mx fail" = { "check-mx" = "fail" }

    test Named.options_check_names get "check-names master fail" = { "check-names" { "master" = "fail" } }

    test Named.options_filter_aaaa get "filter-aaaa-on-v4 no" = { "filter-aaaa-on-v4" = "no" }

    test Named.options_also_notify get "also-notify { ::1; 1.2.3.4 port 900; }" =
      { "also-notify" { "ip" = "::1" } { "ip" = "1.2.3.4" { "port" = "900" } } }

    test Named.options_notify get "notify explicit" = { "notify" = "explicit" }

    test Named.options_masterfile_format get "masterfile-format raw" = { "masterfile-format" = "raw" }

    test Named.options_root_delegation_only get "root-delegation-only" = { "root-delegation-only" }
    test Named.options_root_delegation_only get "root-delegation-only exclude { \"fr\"; \"en\"; }" =
      { "root-delegation-only"
        { "exclude"
          { "name" = "fr" }
          { "name" = "en" }
        }
      }

    test Named.options_ixfr_from_differences get "ixfr-from-differences master" = { "ixfr-from-differences" = "master" }

    test Named.options_forward get "forward first" = { "forward" = "first" }

    test Named.options_server_id get "server-id none" = { "server-id" = "none" }
    test Named.options_server_id get "server-id \"foo.bar\"" = { "server-id" { "name" = "foo.bar" } }

    test Named.options_disable_algorithms get "disable-algorithms foo.org { 7; }" =
      { "disable-algorithms" { "name" = "foo.org" } { "algorithm" = "7" } }
    test Named.options_disable_algorithms get "disable-algorithms foo.org { NSEC3RSASHA1; }" =
      { "disable-algorithms" { "name" = "foo.org" } { "algorithm" = "NSEC3RSASHA1" } }

    test Named.options_dual_stack_servers get "dual-stack-servers { 1.2.4.5; }" =
      { "dual-stack-servers" { "ip" = "1.2.4.5" } }
    test Named.options_dual_stack_servers get "dual-stack-servers port 52 { foo.bar port 55; }" =
      { "dual-stack-servers" { "port" = "52" } { "domain_name" = "foo.bar" { "port" = "55" } } }

    test Named.options_tkey_dhkey get "tkey-dhkey foo bar" =
      { "tkey-dhkey" { "key_name" = "foo" } { "key_tag" = "bar" } }

    test Named.options_empty_stuff get "empty-contact \"foo\"" = { "empty-contact" = "foo" }

    test Named.options_sig_validity_interval get "sig-validity-interval 3" =
      { "sig-validity-interval" { "expire" = "3" } }
    test Named.options_sig_validity_interval get "sig-validity-interval 3 2" =
      { "sig-validity-interval" { "expire" = "3" } { "resign" = "2" } }

    test Named.options_notify_delay get "notify-delay 12" = { "notify-delay" = "12" }

    test Named.options_disable_empty_zone get "disable-empty-zone \"foo.bar\"" = { "disable-empty-zone" = "foo.bar" }

    test Named.options_deny_answer_addresses get "deny-answer-addresses { 1.2.3.4; }" =
      { "deny-answer-addresses" { "ip" = "1.2.3.4" } }
    test Named.options_deny_answer_addresses get "deny-answer-addresses { 1.2.3.4; } except-from { foo.org; }" =
      { "deny-answer-addresses" { "ip" = "1.2.3.4" } { "except-from" { "domain_name" = "foo.org" } } }

    test Named.options_deny_answer_aliases get "deny-answer-aliases { foo.org; }" =
      { "deny-answer-aliases" { "domain_name" = "foo.org" } }
    test Named.options_deny_answer_aliases get "deny-answer-aliases { foo.org; } except-from { bar.org; }" =
      { "deny-answer-aliases" { "domain_name" = "foo.org" } { "except-from" { "domain_name" = "bar.org" } } }

    test Named.options_rrset_order get "rrset-order { order cyclic; }" =
      { "rrset-order" { "order" = "cyclic" } }
    test Named.options_rrset_order get "rrset-order { class IN order cyclic; }" =
      { "rrset-order" { "order" = "cyclic" { "class" = "IN" } } }
    test Named.options_rrset_order get "rrset-order { type A order cyclic; }" =
      { "rrset-order" { "order" = "cyclic" { "type" = "A" } } }
    test Named.options_rrset_order get "rrset-order { name \"example.org\" order cyclic; }" =
      { "rrset-order" { "order" = "cyclic" { "name" = "example.org" } } }
    test Named.options_rrset_order get "rrset-order { class IN type A name \"example.org\" order cyclic; }" =
      { "rrset-order" { "order" = "cyclic" { "class" = "IN" } { "type" = "A" } { "name" = "example.org" } } }

    test Named.server_attr_boolean get "edns no" = { "edns" = "no" }

    test Named.server_attr_numbers get "edns-udp-size 12" = { "edns-udp-size" = "12" }

    test Named.server_address_port get "transfer-source 1.2.3.4" = { "transfer-source" { "ip" = "1.2.3.4" } }

    test Named.server_keys get "keys { tata; tutu; }" =
      { "keys"
        { "key" = "tata" }
        { "key" = "tutu" } }

    test Named.server get "server ::4/120 { }" = { "server" = "::4/120" }
    test Named.server get "server ::4/120 { bogus no; keys { foo; }; }" =
      { "server" = "::4/120"
        { "bogus" = "no" }
        { "keys"
          { "key" = "foo" } } }

    test Named.statistics_channels_body get "inet *" = { "inet" = "*" }
    test Named.statistics_channels_body get "inet ::1 port 1 allow { 1.2.3.4; }" =
      { "inet" = "::1"
        { "port" = "1" }
        { "allow"
          { "ip" = "1.2.3.4" } } }

    test Named.statistics_channels get "statistics-channels { inet 1.2.3.4; }" = { "statistics-channels" { "inet" = "1.2.3.4" } }

    test Named.trusted_keys_key get "dlv.isc.org. 257 3 5 \"FoO\nBar\"" =
      { "key" = "FoO\nBar"
        { "domain" = "dlv.isc.org." }
        { "flag" = "257" }
        { "protocol" = "3" }
        { "algorithm" = "5" } }

    test Named.trusted_keys get "trusted-keys { bar 1 2 3 \"foo\"; bam 2 3 4 \"baz\"; }" =
      { "trusted-keys"
        { "key" = "foo" { "domain" = "bar" } { "flag" = "1" } { "protocol" = "2" } { "algorithm" = "3" } }
        { "key" = "baz" { "domain" = "bam" } { "flag" = "2" } { "protocol" = "3" } { "algorithm" = "4" } } }

    test Named.managed_keys_key get "dlv.isc.org. initial-key 257 3 5 \"FoO\nBar\"" =
      { "key" = "FoO\nBar"
        { "domain" = "dlv.isc.org." }
        { "initialization" = "initial-key" }
        { "flag" = "257" }
        { "protocol" = "3" }
        { "algorithm" = "5" } }

    test Named.managed_keys get "managed-keys { bar initial-key 1 2 3 \"foo\"; }" =
      { "managed-keys"
        { "key" = "foo" { "domain" = "bar" } { "initialization" = "initial-key" } { "flag" = "1" } { "protocol" = "2" } { "algorithm" = "3" } } }

    let full="
# foo
// $FreeBSD: src/etc/namedb/named.conf,v 1.6.2.4 2001/12/05 22:10:12 cjc Exp $
  /**/
/* */
/* bar */
/*
 * bar
 */

acl friends {   192.0.2.0/25; # foo
        127.0.0.1;
};

options {
    dnssec-enable yes;
        request-ixfr yes;
    tcp-clients 1234;
    port 53;
    version \"9.1\";
    dialup refresh;
    forwarders {
      1.2.3.4;
      2.3.4.5 port 5353;
    };
    blackhole { 4.5.6.7; polom; };
    allow-update { key toto; };
    listen-on port 53;
    listen-on-v6 { ::1; };
    listen-on port 5353 { 127.0.0.1; };
    datasize 12M;
    use-v6-udp-ports { range 1024 65000; };
    avoid-v4-udp-ports { 1; };
    avoid-v6-udp-ports { };
    notify-source * port 93;
    query-source-v6 address 2a01:: port *;
    dnssec-lookaside . trust-anchor dlv.isc.org.;
    preferred-glue AAAA;
    check-srv-cname warn;
    check-names response warn;
    filter-aaaa-on-v4 break-dnssec;
    also-notify { ::2; };
    notify master-only;
    masterfile-format text;
    root-delegation-only exclude { \"fr\"; };
    forward first;
    ixfr-from-differences master;
    server-id none;
    transfer-format one-answer;
    disable-algorithms foo.org { NSEC3RSASHA1; };
    dual-stack-servers port 52 { 1.2.3.4 port 55; };
    tkey-dhkey foo bar;
    empty-server \"foo\";
    sig-validity-interval 3 2;
    notify-delay 12;
    disable-empty-zone \"foo.bar\";
    deny-answer-addresses { 1.2.3.4; } except-from { foo.org; };
    deny-answer-aliases { foo.org; } except-from { bar.org; };
    rrset-order {
      class IN type A name \"example.org\" order random;
      order cyclic;
    };
};"

    test Named.lns get full =
      { "#comment" = "foo" }
          { "#inline" = "$FreeBSD: src/etc/namedb/named.conf,v 1.6.2.4 2001/12/05 22:10:12 cjc Exp $" }
      { "#comment" }
      { "#comment" }
      { "#comment"
        { "1" = "bar" }
      }
      { "#comment"
        { "1" = "* bar" }
      }
      { "acl" = "friends"
        { "ip" = "192.0.2.0/25" }
        { "#comment" = "foo" }
        { "ip" = "127.0.0.1" }
      }
      { "options"
        { "dnssec-enable" = "yes" }
        { "request-ixfr" = "yes" }
        { "tcp-clients" = "1234" }
        { "port" = "53" }
        { "version" = "9.1" }
        { "dialup" = "refresh" }
        { "forwarders"
            { "ip" = "1.2.3.4" }
            { "ip" = "2.3.4.5" { "port" = "5353" } } }
        { "blackhole"
          { "ip" = "4.5.6.7" }
          { "acl" = "polom" }
        }
        { "allow-update" { "key" = "toto" } }
        { "listen-on" { "port" = "53" } }
        { "listen-on-v6" { { "ip" = "::1" } } }
        { "listen-on" { "port" = "5353" } { { "ip" = "127.0.0.1" } } }
        { "datasize" = "12M" }
        { "use-v6-udp-ports"
          { "range" { "port_low" = "1024" } { "port_high" = "65000" } }
        }
        { "avoid-v4-udp-ports" { "port" = "1" } }
        { "avoid-v6-udp-ports" }
        { "notify-source" { "ip" = "*" { "port" = "93" } } }
        { "query-source-v6" { "ip" = "2a01::" { "port" = "*" } } }
        { "dnssec-lookaside" { "domain" = "." } { "trust-anchor" = "dlv.isc.org." } }
        { "preferred-glue" = "AAAA" }
        { "check-srv-cname" = "warn" }
        { "check-names" { "response" = "warn" } }
        { "filter-aaaa-on-v4" = "break-dnssec" }
        { "also-notify" { "ip" = "::2" } }
        { "notify" = "master-only" }
        { "masterfile-format" = "text" }
        { "root-delegation-only" { "exclude" { "name" = "fr" } } }
        { "forward" = "first" }
        { "ixfr-from-differences" = "master" }
        { "server-id" = "none" }
        { "transfer-format" = "one-answer" }
        { "disable-algorithms" { "name" = "foo.org" } { "algorithm" = "NSEC3RSASHA1" } }
        { "dual-stack-servers" { "port" = "52" } { "ip" = "1.2.3.4" { "port" = "55" } } }
        { "tkey-dhkey" { "key_name" = "foo" } { "key_tag" = "bar" } }
        { "empty-server" = "foo" }
        { "sig-validity-interval" { "expire" = "3" } { "resign" = "2" } }
        { "notify-delay" = "12" }
        { "disable-empty-zone" = "foo.bar" }
        { "deny-answer-addresses" { "ip" = "1.2.3.4" } { "except-from" { "domain_name" = "foo.org" } } }
        { "deny-answer-aliases" { "domain_name" = "foo.org" } { "except-from" { "domain_name" = "bar.org" } } }
        { "rrset-order"
          { "order" = "random" { "class" = "IN" } { "type" = "A" } { "name" = "example.org" } }
          { "order" = "cyclic" }
        }
      }
