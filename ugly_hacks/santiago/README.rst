.. -*- mode: rst; fill-column: 80; mode: auto-fill; -*-

=========================
Person-Focused Networking
=========================
-----------------------
The FreedomBuddy System
-----------------------

:Author: Nick Daly, 2012
:License: This file is distributed under a Creative Commons
    Attribution-ShareAlike 3.0 Unported, Version 3 license. This CC-By-SA
    license is available in both full_ and summarized_ versions from Creative
    Commons.  This file is also distributed under the `GNU Free Documentation
    License`_, version 1.3 or later.

.. _full: http://creativecommons.org/licenses/by-sa/3.0/legalcode
.. _summarized: http://creativecommons.org/licenses/by-sa/3.0/
.. _GNU Free Documentation License: http://www.gnu.org/licenses/fdl.html

Santiago's Map
==============

Santiago manages service discovery between FreedomBoxen, coordinating
connections between arbitrary servers and services.  In essence, A requests a
service from B, B replies with the service's location, and A uses that location
for the service.

#. A requests service information from B with a signed and encrypted message in
   the form of:

   - Will *X* do *Y* for me?
   - Optional: Reply to my Santiago at *Z*.

#. If B does not recognize A or does not trust A, it stays silent.

#. If B recognizes and trusts A, it replies with a signed and encrypted message
   to A's Santiago, giving the location of A's usable service.  If B will not
   (cannot or won't) provide A the service, B replies with a rejection.  This
   message is in the form of:

   - *X* will (not) do *Y* for *Z*.

In a nutshell, that's the important part.  There are additional details to
manage, but they're implied by and built on the system above.

Each Santiago process is responsible for managing a single key and set of
friendships, so multiple Santiagi per box (each with a different purpose or
social circle) is completely possible and intended.

Message Exchange
----------------

The Santiago service is running on *B*, waiting for connections.  When it
receives a request message, that message must be signed by a known and trusted
party.  If it is acceptably signed (with a known and valid ID), *B* will reply
to *A*'s Santiago with an acceptably signed message.

The contents of the request message are as follows:

- I am requesting service *X*.
- I am requesting that the service be performed by *Y*.
- Optional: Reply to this message at *Z*.

The message is signed by *A*, and optionally encrypted (if the message is
proxied, it must contain a "To" header).  If *A* includes a location stanza,
*B* MUST respect that location in its response and update that location for
its Santiago service from *A* going forward.

In this document, I elide the Santiago acknowledgments (because they add a lot
of unnecessary noise - we can assume communication failures are failures of
acknowledgment receipt).  But, after each message that needs a response, an
acceptably signed acknowledgment message is returned.  Otherwise the sender
preferentially moves on to the recipient's next Santiago address after a
sufficient amount of time has passed.  An example of this communication, with
these details specified, follows:

:B -> A: I'll gladly serve *X* for you, at *Z*, my good fellow.
:A -> B: (No response)
:B -> A: *(using a different Santiago address)* I'm serving *X* for *A* at *Z*.
:A -> B: (Acknowledgment)

Storing Service Data and Network Structure
------------------------------------------

How are these data stored, to prevent both A and B from having to dance the
Santiago for each and every request?

Each node contains two dictionaries/hash-tables listing (1) what they serve and
who they serve it to, and (2) what services they use, who from, and where that
service is located.

What I Host and Serve
~~~~~~~~~~~~~~~~~~~~~

I offer these services to others.

These data are stored as pair of dictionaries:

- The GPG ID to Service dictionary.  This lists which service each user is
  authorized for::

      0x0928: { "proxy": "proxy", "wiki": "wiki",
                "drinking buddy": "drinking buddy" }
      0x7747: { "wiki": "wiki", "proxy": "restricted_proxy" }

- The Service to Location dictionary.  This lists the locations each service
  runs on::

      "wiki": [ 192.168.1.1, "superduperwiki.onion" ]
      "proxy": [ 8.8.8.8 ]
      "restricted_proxy": [ 4.4.4.4 ]
      "drinking_buddy": [ "Artopolis, Amsterdam and 114th" ]

Others' Services I Know Of
~~~~~~~~~~~~~~~~~~~~~~~~~~

I consume these services, they are offered by others.

These data are stored as a dual-key dictionary, with the following mappings::

    Service X: { GPG ID1: [ location, location, location ],
                 GPG ID2: [ location, location ], }
    Service Y: { GPG ID2: [ location, location, location ],
                 GPG ID3: [ location, location ], }

This allows fast lookup from the service desired to the users that host the
service, to the actual locations that service is offered.  This allows the user
to quickly decide which service provider to use and to try all locations
controlled by that service provider very quickly and easily.

Data Use
--------

:TODO: Revise to reduce communication to logical minimum number of connections,
       exchanges, and communications.

When *A* is connecting to *B*'s service, it will attempt to connect to that
service, which B will validate before permitting the connection.  If the service
is non-responsive, *A* will query *B* for the service.  If *B* is generally
non-responsive, *A* will move on to *C*.  *A* will ask *C* for the service.  If
*C* cannot provide the service, *A* will ask *C* to request the service from
*B*.  If *C* can reach *B* and *B* authorizes *A*, *B* will respond
affirmatively to *A* with the service's location.

:A -> B: (Connecting to Service!)
:B: (Validating Service and rejecting for some reason, e.x., A hasn't been
    reauthorized for this service recently enough, and because it's Wednesday.)
:B -> A: (No response)
:A -> B: Will you serve X?
:B -> A: (No response, A can't reach B's Santiago.)
:A -> C: Will you serve X?
:C -> A: No!
:A -> C: Will B serve X?
:C -> B: Will you serve X for A?
:B -> A: Hey, buddy, here's X!

Proxied service requesting
--------------------------

The Simple Case
~~~~~~~~~~~~~~~

I'm looking for somebody to provide a service, *X*.

*A* sends a request to *C*, and *C* doesn't respond.  *A* requests the
service from *B* and *B* NAKs.  *A* requests that *B* proxy my request
to *C*, in case *B* can reach *C*.  *C* replies directly to *A*, and
we begin communicating on that service:

:A -> C: Will you serve X?
:C -> A: (No response)
:A -> B: Will you serve X?
:B -> A: No!
:A -> B: Will C serve X?
:B -> C: Will you serve X for A?
:C -> A: Hey, buddy, here's X!  Let's go out for beer later.

More Complicated Cases
~~~~~~~~~~~~~~~~~~~~~~

I know *D* offers a service, *X*, but I can't get in touch with it.

*A* requests *X* from *D*, and *D* never responds.  *A* requests that *B* find
*D*.  *B* doesn't know *D* and forwards the request to a friend *C*.  *C* knows
*D* and sends the message along.  *D* tries to respond directly to *A*, but
can't, so it sends replies back up the chain.

:A -> D: Will you serve X?
:D -> A: (No response)
:A -> B: Will D serve X for me?
:B -> C: Will D serve X for A?
:C -> D: Will you serve X for A?
:D -> A: Hey, buddy, here's X!
:A -> D: (No response)
:D -> C: I'm serving X for A.
:C -> B: D's serving X for A.
:B -> A: D's serving X for you.

Each message is signed, but only the first message (A's message) is inviolable.
Each client then passes the message, stripping off intermediary signatures, and
then signing the message for each of its friends.

A message looks like::

    ---- A's Signed Message Starts Here ----
        To: D's GPG key.
        ---- D's Encrypted Message Starts Here ----
            Hey *D*, will you serve *X* for me?
            Please reply to 5.onion.
        ---- D's Encrypted Message Ends Here ----
    ---- A's Signed Message Ends Here ----

A forwarded message, from B to C, looks like::

    ---- B's Signed Message Starts Here ----
    ---- A's Signed Message Starts Here ----
        To: D's GPG key.
        ---- D's Encrypted Message Starts Here ----
            Hey *D*, will you serve *X* for me?
            Please reply to 5.onion.
        ---- D's Encrypted Message Ends Here ----
    ---- A's Signed Message Ends Here ----
    ---- B's Signed Message Ends Here ----

When forwarded over again, from C to D, it looks like::

    ---- C's Signed Message Starts Here ----
    ---- A's Signed Message Starts Here ----
        To: D's GPG key.
        ---- D's Encrypted Message Starts Here ----
            Hey *D*, will you serve *X* for me?
            Please reply to 5.onion.
        ---- D's Encrypted Message Ends Here ----
    ---- A's Signed Message Ends Here ----
    ---- C's Signed Message Ends Here ----

Note that:

- The original message is unchanged.
- Irrelevant signatures (intermediate links in the WOT) are stripped, hiding the
  WOT's structure from friends.

Anachronisms
~~~~~~~~~~~~

It's odd because this has a potential for a number of irrelevant communications.

It's possible for A to send multiple requests to B and for B to receive multiple
requests before A acknowledges responses.  Removing these oddly timed messages
requires A and B to exchange more information (acknowledgments and replies would
need to include the service location that responded).  I'm not sure whether
sending more messages or identifying the active service to friends is the better
option.  Probably the latter, because it allows for communication to take fewer
messages (an order of magnitude less, if proxying is involved).

Code/Object Structure
---------------------

So, listeners receive responses and pass them up to the controller that queues
it for the sender.  Up to one listener and sender per protocol.

Our Cheats
----------

Right now, we're cheating.  There's no discovery.  We start by pairing boxes,
exchanging both box-specific PGP keys and Tor Hidden Service IDs.  This allows
boxes to trust and communicate with one another, regardless of any adverserial
interference.  Or, rather, any adverserial interference will be obvious and
ignorable.

Unit Tests
==========

These buggers are neat.  We need to fake known and pre-determined communications
to verify the servers and clients are correctly and independently responding
according to the protocol.

Attacks
=======

Of *course* this is vulnerable.  It's on the internet, isn't it?

Concepts
--------

Discovery
~~~~~~~~~

A discovered box is shut down or compromised.  It can lie to its requestors and
not perform its functions.  It can also allow connections and expose
connecting clients.  If the client is compromisable (within reach), it also can
be compromised.  We can try, but every service that isn't run directly over Tor
identifies one user to another.

What attacks can an adversary who's compromised a secret key perform?  The same
as any trusted narc-node.  As long as you don't have any publicly identifiable
(or public-facing) services in your Santiago, then not much.  If you're
identifiable by your Santiago, and you've permitted the attacker to see an
identifiable service (including your Santiago instances), that service and all
co-located services could be shut down.  If the service identifies you (and not
just your box), you're vulnerable.  Any attacker will shortly identify all the
services you've given it access to.

An attacker can try to identify your friends, though will have trouble if you
send your proxied requests with non-public methods, or you don't proxy at all.

Deception
~~~~~~~~~

This is probably the largest worry, where B fakes A's responses or provides
invalid data.  Because we rely on signed messages, B can fake only B's services.
B can direct A to an adversary, so A's boned, but only insofar as A uses B's
services.  If A relies primarily on C's services, A isn't very boned at all.

Methods
-------

:TODO: I'll need to think about all these a lot more.  I'm really far from
       exhaustive logical proof at this point.

Out of Order
~~~~~~~~~~~~

How vulnerable are we to out-of-order responses?  Not very, *at this point*,
because there isn't too much going on.  However, I'll need to think further
about the vulnerabilities.

The dangerous message is the service response.  If B can send A any response, B
could modify A's service table at a whim.  Therefore, A should accept service
updates only for services it expects an update for.

Flood
~~~~~

Since messages are signed and/or encrypted many huge, invalid, requests could
easily overwhelm a box.  The signature verification alone could overheat one of
the buggers.  We need a rate-limiter to make sure it tries to never handle more
than X MB of data and Y requests per friend at one time.  Data beyond that limit
could be queued for later.

Network Loops
~~~~~~~~~~~~~

Look into how BATMAN and its ilk handle network loops.  Each box could keep a
list of recently-proxied-requests so that no box sends the same request to its
friends within a time-range.  Might we need to look into other request proxying
methods when the DHT comes up?

False Flags / False Friends
~~~~~~~~~~~~~~~~~~~~~~~~~~~

:TODO: Add unit tests for these behaviors.

Since we allow request proxying, an attacker (C) who knows where my Santiago (B)
is located and has captured a real request from a trusted party (A) can later
forward that request to me, again, for the fun of it.  However, requiring both
the proxier and client to be trusted means that such falsely forwarded requests
will go unanswered.

However, if the key is compromised, an attacker could modify the message's
"reply-to" header to allow communication with an untrusted third party.
Santiago cannot protect against this manner of attack because the data we use to
validate the request (the key) is compromised.  We can't enforce a reverse-DNS
style callback very well, because there's no guarantee we can reach the client
in the first place.  We could try, but I don't know how much trust it would add
to the system beyond that which we can guarantee by signed messages alone.

Mitigations
===========

We gain a lot by relying on the WOT, and only direct links in the WOT.  We also
gain a lot by requiring every communication to be signed (and maximally
encrypted).

Outstanding Questions
=====================

Sure, there's been a lot of work so far, but there's a lot more to do.

Design Questions
----------------

:Really weird proxies: Email, Twitter, bit.ly, paste buckets, etc.
    This implies listener polling.

:Add Expiry: Add both service and proxy (search) hop expiry.

:Moar Unit Testing!: Add real Unit Testing.  Spec out the system through test
    harnesses.  If the tests can run the system, it's complete.

:Clarify Actions: Actions probably aren't necessary with hop expiry, since each
    Santiago sender sends two messages: "Will X serve Y for Z? Please respond at
    W.", and "X will (not) serve Y for Z at U."

:Fucking-with-you Replies: An urban legend: During World War II, the RAF
    confused the German air force by alternating the altitudes of their fighters
    and bombers (doing it wrong, flying the fighters *beneath* the bombers).
    Apparently the Germans were most confused when the RAF did it wrong once
    every seven flights.  Whether or not it's true, it implies a lesson:

    Confuse adversaries by intentionally doing it wrong, sometimes.  We could
    answer a bum Santiago request with garbage, irrelevant HTTP codes, or
    silence.

:Onion Routing: What can we learn from Tor itself?  Maybe not a lot.  Maybe a
    bit.  That we don't allow untrusted connections is an incredible limitation
    on the routing system.

    However, we can reinterpret the onion concept, by permitting the signed and
    encrypted parts of messages to conflict.  A's signed message is to B, but
    the encrypted part is to C.  B, named as an intermediate destination, reads
    the encrypted message and forwards it on to C, as it's own message.  This
    allows users to force messages through specific hops in the system.

    I don't know if that's a good thing or not.  It lets a trusted attacker (A)
    validate that specific nodes are part of a trust-web (that B and C can
    communicate), but it also allows nodes to control their routing, while
    revealing some aspects of their communication to the named intermediates.
    Also, it implies network loops, which could be minimized by rate-limiting.

    This also implies infinite named intermediates.  There's nothing in this
    setup preventing A also using C as a proxy for D through J.

    I'm still not sure whether the benefits outweigh the costs, but that's still
    an interesting question.

:Reverse DNS: Should we check with the original requester before replying?  What
    if we can't reach that requester outside of the reply-to address they sent?
    Verifying the requester's identity by their self-reported address seems to
    add little confidence to the requester's identity.

Functional Questions
--------------------

:Queuing Messages: Queue actions, dispatching X MB over Y requests per friend
    per unit time, unless the request is preempted by another reply.

:Process Separation: Santiagi should be separated at the process/message-handler
    level, so that trouble in one Santiago doesn't tear down the rest (makes
    queuing harder with multiple listeners).  Services should be recorded and
    messages should be queued at a file-level so that each process who needs
    access can have it.

:Santiago Updates: Updates are tricky things.  They're when we're most
    vulnerable.  The question becomes: since both boxes need to know where they
    are to communicate successfully, but at least one box may have changed its
    location (even its Santiago), how do we handle those updates, while reducing
    the vulnerability as much as possible?  Let's assume that A (the requester)
    changes its locations frequently, while B (the server) does not.  A requests
    a service from B and B then needs to reply.  How does B know where to reply?
    It has a few old Santiago ports left over in the database.  A might also
    have sent Santiago updates with the request message.  How does B handle
    those updates?

    Does B queue those Santiagi last in the update queue, are they checked
    first, or is appending Santiagi not allowed?  Each creates a different
    vulnerability.

    If A's key is compromised, but his box is not, then the request is fake and
    so are the new Santiagi.  The old ones are still valid.

    If A's box is compromised, then his key is probably compromised too, and all
    existing Santiagi are compromised.  This could be A trying to transition to
    a new box without changing keys, though, so the new Santiagi are valid.

    If A NAKs B's update message when A didn't ask for it, causing B to consider
    that request from A (and the related Santiago) compromised, then that too
    could be used by adversaries with a compromised key to deny A service.

    What a bloody circle.  Both options are bad, but some worse than others?

    Well, if we prevent Santiagi updates in messages altogether, B might never
    find A again, if A moved.  So that sucks.  But, that's also overloading
    messages and implicitly allowing push-updating.  If we allow pull-updating
    only, then both boxes need to be accessible to one another at all times.
    More secure, but a *lot* less useful.

    Is it meaningful to consider some forms of signed communication more
    vulnerable than others, or are we just saying that if the communication is
    successfully signed, then it must be valid, damn the consequences?  I think
    so, actually.  Otherwise, we start jumping at shadows.  There's no way to
    know whether a key's been compromised until the revocation certificate is
    deployed, and I can't verify anybody else's security measures.  Perhaps your
    definition of security is "this key I share between me, my wife, our three
    kids, and the dog's neighbor."  If I happen to trust the dog's neighbor
    (but, oddly, not the dog itself), then I might trust the key.  If I don't
    trust the second of three kids, then why am I trusting the key?  Trust is an
    annoyingly deep subject, and one of the few good uses of the word "faith."

:Encryption Keys: So, being able to sign and encrypt messages is necessary
    functional requirement.  However, that implies that the Santiago process
    always has access to the public key's secret key.  That's right, it's an
    always-on web service that has access to a secret key, in Python.  That's
    bad, Python makes it (slightly) worse.

    So, how do we make the system less vulnerable?  The first step is to avoid
    storing the secret key (or the key's password) in memory whenever possible.
    The system should pick up and then put down the password as quickly as
    possible.  There are two ways we can do this:

    #. Using gpg-agent.  We pass the agent the password, once, and the agent
       takes care of it from then on.  This is what I'll use unless something
       goes terribly wrong with the setup.
    #. Read the password from a file, shoveling it into the GnuPG request
       whenever required.  Not particularly secure, unless the Santiago service
       is running as a custom user, reading from an only-owner-readable file.
       However, then any other Santiago-user-owned process could harvest
       passwords from files.

    The second allows for un-attended startup, because the passwords can be read
    from files, but I don't trust it.  It feels like I'm going out on a limb
    enough before this point.

    Going to the other extreme, we can make un-passworded secret keys, so that
    no hard-coded passwords or gpg-agents are required.  Then, it's just
    plug-and-play.  That might be an acceptable option in some circumstances.

Using Santiago
==============

The Santiago service is mostly working now.

First, you'll need to create a certificate to serve Santiago over HTTPS::

    # make-ssl-cert generate-default-snakeoil
    # make-ssl-cert /usr/share/ssl-cert/ssleay.cnf santiago.crt
    # chgrp 1000 santiago.crt
    # chmod g+r santiago.crt

Next, you'll need to open up ``start.sh`` and update the system path to locate
the "gnupg_" and "cfg" modules.

.. _gnupg: https://code.google.com/p/python-gnupg/

Finally, start the Santiago process in a console with ``start.sh``.  Test it out
by navigating to:

    https://localhost:8080/query?host=b&service=santiago

You should see three requests appear in the console.

Tasks
-----

- |TODO| TODOs and FIXMEs.

- |TODO| add unit tests and doctests

- |TODO| allow multiple listeners and senders per protocol (with different
  proxies?)

.. |TODO| unicode:: U+2610
.. |DONE| unicode:: U+2611

References
==========

None yet.  How odd ;)
