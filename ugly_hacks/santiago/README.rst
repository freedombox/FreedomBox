.. -*- mode: rst; fill-column: 80; mode: auto-fill; -*-

==========
 Santiago
==========
----------------------------
Less Discoverable Discovery?
----------------------------

This file is distributed under a Creative Commons Attribution-ShareAlike 3.0
Unported, Version 3 license. This CC-By-SA license is available in both full_
and summarized_ versions from Creative Commons.  This file is also distributed
under the `GNU Free Documentation License`_, version 1.3 or later.

.. _full: http://creativecommons.org/licenses/by-sa/3.0/legalcode
.. _summarized: http://creativecommons.org/licenses/by-sa/3.0/
.. _GNU Free Documentation License: http://www.gnu.org/licenses/fdl.html

Disclaimer
==========

**The following is an incomplete hack.  Beware!**

Santiago's Map
==============

Santiago manages service discovery between FreedomBoxen, coordinating
connections between arbitrary servers and services.  In essence, A requests a
service from B, B replies with the service's location, and A uses that location
for the service.

#. A sends a signed (and encrypted?) message to B's Santiago, requesting
   information, in the form of:

   - Will *X* do *Y* for me?
   - Optional: Reply to my Santiago at *Z*.

#. If B does not recognize A or does not trust A, it stays silent.

#. If B recognizes and trusts A, it replies with a signed (and encrypted?)
   message to A's Santiago, giving the location of A's usable service.  If B
   will not (cannot or won't) provide A the service, B replies with a
   rejection.  This message is in the form of:

   - *X* will (not) do *Y* for *Z*.

In a nutshell, that's the important part.  There are additional details to
manage, but they're implied by and built on the system above.

Our Cheats
----------

Right now, we're cheating.  There's no discovery.  We start by pairing boxes,
exchanging both box-specific PGP keys and Tor Hidden Service IDs.  This allows
boxes to trust and communicate with one another, regardless of any adverserial
interference.  Or, rather, any adverserial interference will be obvious and
ignorable.

Message Exchange
----------------

The Santiago service is running on *B*, waiting for connections.  When it
receives a request message, that message must be signed by a known and trusted
party.  If it is acceptably signed (with a known, and valid ID), *B* will
reply to *A*'s Santiago with an acceptably signed message.

The contents of the request message are as follows:

- I am requesting service *X*.
- I am requesting that the service be performed by *Y*.
- Optional: Reply to this message at *Z*.

The message is signed by *A*, and optionally encrypted (if the message is
proxied, it must contain a "To" header).  If *A* includes a location stanza,
*B* MUST respect that location in its response and update that location for
its Santiago service from *A* going forward.

In this document, I elide the Santiago acknowledgements (because they add a lot
of unnecessary noise - we can assume communication failures are failures of
acknolwedgement receipt).  But, after each message that needs a response, an
acceptably signed acknowledgement message is returned.  Otherwise the sender
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

      0x0928: [ "proxy": "proxy", "wiki": "wiki",
                "drinking buddy": "drinking buddy" ]
      0x7747: [ "wiki": "wiki", "proxy": "restricted_proxy" ]

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
service from *B* and *B* NBKs.  *A* requests that *B* proxy my request
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

:Clarify interactions: Clarify controller/sender/listener interactions.  Who
    knows what and how much?  We need multiple listener ports.

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

Functional Questions
--------------------

:Queuing Messages: Queue actions, dispatching X MB over Y requests per friend
    per unit time, unless the request is preempted by another reply.

:Process Separation: Santiagi should be separated at the process/message-handler
    level, so that trouble in one Santiago doesn't tear down the rest (makes
    queuing harder with multiple listeners).  Services should be recorded and
    messages should be queued at a file-level so that each process who needs
    access can have it.

References
==========

None yet.  How odd ;)
