=================================================================
An Introduction to the Python Web Server Gateway Interface (WSGI)
=================================================================

In Brief
========

WSGI is a specification, laid out in `PEP 333`_, for a standardized interface
between Web servers and Python Web frameworks/applications.

The goal is to provide a *relatively simple* yet *comprehensive* interface
capable of supporting all (or most) interactions between a Web server and
a Web framework.  (Think "CGI" but programmatic rather than I/O based.)

An additional goal is to support "middleware" components for pre- and
post-processing of requests: think gzip, recording, proxy, load-balancing.

No mechanism for *deployment* and relatively few mechanisms for
*configuration* are specified in the PEP.  (That's a problem `Python
Paste`_ targets.)

All you really need to know...
------------------------------

Unless you are developing a new Web app framework (admittedly, p > 0.5...)
you don't *care* about WSGI.  Use a Web app framework.  They all support
WSGI at this point, which means you basically need to worry about
configuration and deployment of your app, and nothing else.

Summary of Specification
========================

The PEP specifies three roles: the role of a server, the role of a
framework/app, and the role of a middleware object.

Web server side
---------------

The server must provide two things: an ``environ`` dictionary, and a
``start_response`` function.  The environ dictionary needs to have
the usual things present -- it's similar to the CGI environment.
``start_response`` is a callable that takes two arguments, ``status`` --
containing a standard HTTP status string like ``200 OK`` -- and
``response_headers`` -- a list of standard HTTP response headers.

The Web server dispatches a request to the framework/app by calling
the application: ::

   iterable = app(environ, start_response)
   for data in iterable:
      # send data to client

It's the framework/app's responsibility to build the headers, call
``start_response``, and build the data returned in ``iterable``.  It's
the Web server's responsibility to serve both the headers and the data
up via HTTP.

Web framework/app side
----------------------

The Web framework/app is represented to the server as a Python
callable.  It can be a class, an object, or a function.  The arguments
to ``__init__``, ``__call__``, or the function must be as above:
an ``environ`` object and a ``start_response`` callable.

The Web framework/app must call ``start_response`` before returning or
yielding any data.

The Web framework/app should return any data in an iterable form --
e.g. ``return [ page ]``.

Middleware
----------

Middleware components must obey both the Web server side and the Web
app/framework side of things, plus a few more minor niggling
restrictions.  Middleware should be as transparent as possible.

An example WSGI application
---------------------------

Here's a very simple WSGI application that returns a static "Hello world!"
page. ::

   def simple_app(environ, start_response):
       status = '200 OK'
       response_headers = [('Content-type','text/plain')]
       start_response(status, response_headers)
       return ['Hello world!\n']

Here's a very simple middleware application that uppercases everything sent: ::

   class Upperware:
      def __init__(self, app):
         self.wrapped_app = app

      def __call__(self, environ, start_response):
         for data in self.wrapped_app(environ, start_response):
            return data.upper()

To instantiate/run these from the server's perspective, you just do
the obvious: ::

   serve(simple_app)

or ::

   wrapped_app = Upperware(simple_app)
   serve(wrapped_app)

Yes, it can be that simple: here's my code for running Trac via
``scgiserver``. ::

   #!/usr/bin/env python
   from trac.web.main import dispatch_request as app
   from scgiserver import serve_application

   PREFIX=''
   PORT=4101

   serve_application(app, PREFIX, PORT)

Omitted complexity
------------------

``start_response`` must also return a ``write_fn`` callable that legacy
apps can use as a file-like stream.  This makes it easy to convert old apps
to be "WSGI compliant".  Its use is deprecated because using a file-like
stream puts the reins of execution in the hands of the app object, preventing
intelligent content handling interleaving/asynchrony on the part of the
server.

``start_response`` can take an optional parameter, ``exc_info``, that is
used for error handling when present.

My Opinions
===========

*('cause I'm an opinionated guy, after all...)*

Why I Like It
-------------

I no longer have to worry about making my application run in multiple
Web servers: most servers, and all frameworks, are WSGI compliant.

The WSGI spec is simple enough that if you can't factor your Web app
interface out into a WSGI-compliant interface, you didn't write your
Web app properly.  This exposes lousy design for what it is.

I can also build generic test harnesses for Web apps ;).

What I Don't Like
-----------------

Discussion of WSGI is often entangled with discussion of Paste.  I'm not
sure exactly why, but it confuses the issue quite a bit.

What I Don't Grok
-----------------

People seem to think "loosely-coupled" is good, even when talking about
things like cookies and authentication.  I don't understand how this
simplifies code, or, conversely, I think this approach complicates very
simple matters unnecessarily.

WSGI is Python's Answer to Ruby On Rails
----------------------------------------

Choice is good; WSGI makes choice a matter of *developer opinion*
rather than *technical compatibility*.

(Seriously, that's all I got.)

.. _PEP 333: http://www.python.org/dev/peps/pep-0333/
.. _Python Paste: http://www.pythonpaste.org/
