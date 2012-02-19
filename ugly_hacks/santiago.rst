.. -*- mode: rst; fill-column: 80; mode: auto-fill; -*-

==========
 Santiago
==========
----------------------------
Less Discoverable Discovery?
----------------------------

Disclaimer
==========

**The following is an ugly hack.  Beware!**

Santiago's Map
==============

Santiago manages service discovery between FreedomBoxen, coordinating
connections between arbitrary servers and services.  In essence, A requests a
service from B, B replies with the service's location, and A uses that location
for the service.

#. A sends a signed (and encrypted?) message to B's Santiago, requesting
   information, in the form of:

   - Will *X* do *Y* for me?
   - (By the way I'm at *Z*)
#. If B does not recognize A or does not trust A, it stays silent.
#. If B recognizes and trusts A, it replies with a signed (and encrypted?)
   message to A's Santiago, giving the location of A's usable service.  If no
   service is available, it reples with a rejection.

In a nutshell, that's the important part.  There are additional details to
manage, but they're implied and build on the system above.

Message Exchange
----------------

The Santiago service is running on ``B``, waiting for connections.  When it
receives a request message, that message must be signed by a known and trusted
party.  If it is acceptably signed (with a known, and valid ID), ``B`` will
reply to ``A``'s Santiago with an acceptably signed message.

The contents of the request message are as follows:

- I am requesting service *X*.
- I am requesting that the service be performed by *Y*.
- Optional: I am located at *Z*.

The message is signed by ``A``, and optionally encrypted (if the message is
proxied, it must contain a "To" header).

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

Others' Services I Know Of
~~~~~~~~~~~~~~~~~~~~~~~~~~

I consume these services, they are offered by others.

These data are stored as a triple-key dictionary, with the following mappings::

    Service -> [ GPG, ID ]
    GPG ID -> [ Location, location, location ]

This allows fast lookup from the service desired to the users that host the
service, to the actual locations that service is offered.  This allows the user
to quickly decide which service provider to use and to try all locations
controlled by that service provider very quickly and easily.

Data Use
--------

:TODO: Revise to reduce communication to logical minimum number of connections,
       exchanges, and communications.

When ``A`` is connecting to ``B``'s service, it will attempt to connect to that
service (and verify ``B``'s identity with a signed handshake before using the
service?).  If the service is non-responsive, ``A`` will query ``B`` for the
service.  If ``B`` is generally non-responsive, ``A`` will move on to ``C``.
``A`` will ask ``C`` for the service.  If ``C`` cannot provide the service,
``A`` will ask ``C`` to request the service from ``B``.  If ``C`` can reach
``B`` and ``B`` authorizes ``A``, ``B`` will respond affirmatively to ``A`` with
the service's location.

Our Cheats
----------

Right now, we're cheating.  We start by pairing boxes, exchanging both
box-specific PGP keys and Tor Hidden Service IDs.  This allows boxes to trust
and communicate with one another, regardless of any adverserial interference.
Or, rather, any adverserial interference will be obvious and ignorable.

Next Steps
==========

Proxied service requesting
--------------------------

``Me`` sends a request to ``B``, and ``B`` doesn't respond.  ``Me`` requests the
service from ``A`` and ``A`` NAKs.  ``Me`` requests that ``A`` proxy my request
to ``B``, in case ``A`` can reach ``B``.  ``B`` replies directly to ``Me``, and
we begin communicating on that service.

:TODO: What is the maximum number of hops that we can securely achieve from this
       system while keeping intermedia hops secret?  One?  More?

Unit Tests
==========

These buggers are neat.  We need to fake known and pre-determined communications
to verify the servers and clients are correctly and independently responding
according to the protocol.

Attacks
=======

Of *course* this is vulnerable.  It's on the internet, isn't it?

Discovery
---------

A discovered box is shut down or compromised.  It can lie to its requestors and
not perform its functions.  It can also allow connections and expose
connecting clients.  If the client is compromisable (within reach), it also can
be compromised.  We can try, but every service that isn't run directly over Tor
identifies one user to another.

Deception
---------

This is probably the largest worry, where B spoofs A's responses.
