============================================================================
Introduction: Testing Python Web applications using twill and wsgi_intercept
============================================================================

*Originally posted at http://www.advogato.org/article/874.html.*

One of the thorniest problems in GUI application development is how to
test your user interface.  Web applications, as a specific and
somewhat limited example of a GUI, are no exception to this problem.
However, there are several options for testing Web applications now
available.  One of my favorites is twill_, a remote HTTP driver
application that lets you script Web sites.  (Disclaimer: I am the
primary author of twill, so take my recommendation with a grain of
salt ;).

twill implements a simple scripting language and emulates a
command-line browser.  With twill, you can visit URLs, follow links,
fill out forms, log in and log out, deal with cookies, and follow
redirects.  Because twill is written in Python, you can also script it
completely from within Python.  And, because twill accurately emulates
the HTTP behavior of a browser, it's good for both screen-scraping Web
sites you don't control, and testing Web sites that you do control.
Note that twill does have a big flaw in this regard: it cannot
understand JavaScript. This is why "browser drivers" like Selenium_
and PAMIE_ are required for testing AJAX applications.  However, there
are tradeoffs.  One positive tradeoff is that twill can run in a completely
automated manner and has no browser dependencies, which makes it
particularly suitable for unit tests.

Unit tests are a useful type of testing because they're generally
simple, test discrete components of the source code, and are
*automated*.  Because unit tests are automated, there is little
or no cost to running them, which means developers can test their code
after even minor changes.  This can lead to a very fluid style of
development in which major refactorings are thoroughly tested at each
step.

Using twill for unit tests brings in a new problem, however: the setup
and teardown of the Web site.  This is true not just for twill but for
any other HTTP driver, such as urllib2, webtest_, webunit_,
mechanize_, mechanoid_, and zope.testbrowser_: you still have to set
up your development Web site to serve pages, so that it looks and
behaves like your real site.  In practice, this breaks down into
multiple sub-problems:

* you have to start another process; that process has to bind to a
  port and a hostname (usually something like localhost:8080);

* your unit tests have to wait for the Web site to start up, which
  can take a second or two;

* and then you have to shut the Web site down at the end of the unit
  tests.

Each of these is its own tricky problem.  (What if the port is already
bound?  What if your server is slow today?)  Moreover, proper
profiling and code coverage testing of the Web application become
considerably more complicated when you're dealing with multiple
processes and "real, live" Web applications.

This is moderately complex stuff to script, and it's pretty daunting
to get it all working in a unit test framework (at least for
me!). Plus, having a more complicated test setup than most of the
individual tests seems like a bad design choice.  While actually
deploying a test Web site is necessary to properly test a Web app, for
your unit tests it's almost certainly overkill.  But what other
options are there, you might ask?

Well, after `a suggestion`_ from Ian Bicking, I implemented an
in-process test harness for WSGI applications, called wsgi_intercept_.
wsgi_intercept lets you redirect HTTP calls directly into any
`WSGI-compliant`_ application, bypassing the network. With
wsgi_intercept, you don't need to bind any sockets or connect to the
network at all in order to talk to your Web application from
twill. However, because wsgi_intercept acts at a low level -- the
redirection occurs in httplib -- your application looks and feels like
it is actually being called via HTTP. This can considerably simplify
the testing process.  (Testing aficionados may recognize this technique
as building a "mock network interface".)

twill comes with full wsgi_intercept integration, of course -- and you
can find hooks and examples for all of the other Python Web testing
frameworks at `the wsgi_intercept page`_.  So how does it work in practice?

Roughly speaking, you need to do the following:

 * package your application as a WSGI app object;
 * build a function to return that app object;
 * hook that function up to a particular host/port combination;
 * run whatever twill scripts you want to run for the test;
 * teardown (remove the intercept, shut down the server, etc.)

Below, I walk through setting up nose_-based unit testing of two simple
applications -- a Quixote_ application, and a CherryPy_
application.  In both cases most of the complexity is in putting the
start/stop calls in the correct order.

In Practice: Testing a Quixote application using twill and wsgi_intercept
=========================================================================

*You'll need Quixote 2.3 for this, as well as nose 0.8.x and twill 0.8.2.*

For Quixote, let's test the ``mini_demo`` application that
comes with Quixote 2.x.  Unfortunately, Quixote doesn't (yet?) come
with a WSGI interface; however, there's `an adapter available`_
as ``wsgi_server.QWIP``.  So we'll need wsgi_server.py, as well
as Quixote 2.x and nose.



First, create a test file; I'll just call it 'test.py'.  Let's start by
roughing out a nose unit test: ::

   class TestMiniDemo:
      def setUp(self):
         pass

      def tearDown(self):
         pass

Now, the Quixote ``Publisher`` object we want to test is returned
by ``quixote.demo.mini_demo.create_publisher()``.  We need to
dynamically create a function that creates the publisher, wraps it as
a WSGI object, and then returns that same object each time it's
called: ::

       publisher = quixote.demo.mini_demo.create_publisher()
       wsgi_app = wsgi_server.QWIP(publisher)

       fn = lambda : wsgi_app

If we put this in the ``setUp`` function, we have what we need.
The only tricky bit is caching the application object.  Why do we need
to do this?  Well, the function passed into wsgi_intercept is called
once for *each* intercepted connection, but we only want to create
the WSGI app object *once*.  By storing the app object in a dictionary
that persists for the lifetime of the dynamically defined function, we
essentially memoize the WSGI application object.  (I'm not thrilled with
this particular approach: let me know if you have a better way of doing
this.)

OK, once we have this function, we need to install it to handle
requests to ``localhost:8080``, and then we're ready.  Our final
``setUp`` function looks like this: ::

   def setUp(self):
      # create a publisher obj
      publisher = quixote.demo.mini_demo.create_publisher()
   
      # wrap
      wsgi_app = QWIP(publisher)
   
      # install the app at localhost:8080 for wsgi_intercept
      twill.add_wsgi_intercept('localhost', 8080, lambda : wsgi_app)
   
      # while we're at it, stop twill from running off at the mouth...
      self.outp = StringIO()
      twill.set_output(self.outp)

The ``tearDown`` function is much simpler: we just need to remove
the intercept, and then clear the Quixote publisher object. ::

   def tearDown(self):
      # remove intercept
      twill.remove_wsgi_intercept('localhost', 8080)

      # clear out the publisher
      quixote.publish._publisher = None

...and now we're ready for a test or two!  I'll define two: one to test
the main page, and the other to test the link. ::

   def test_welcome(self):
      script = "find 'Welcome to the Quixote demo'\n"
      twill.execute_string(script, initial_url='http://localhost:8080/')
   
   def test_hello(self):
      script = """\
   follow link
   find 'Hello world!'
   """
      twill.execute_string(script, initial_url='http://localhost:8080/')

Briefly, these scripts both go to 'localhost:8080'; the first script
makes sure that it can find specific text on the front page, while the
second script tests the result of following the front page link to
a 'Hello world' page.  (Longer scripts can go in their own file,
and ``execute_file`` can be used to run them.)

Putting it all together with the correct import statements -- you can
download the `final file`_ if you like -- and running
``nosetests``, you get: ::

   % nosetests
   ..
   ----------------------------------------------------------------------
   Ran 2 tests in 0.381s

   OK

So everything works! Huzzah!  (If you want to reassure yourself that
it's actually running the tests through the Web application
break a test by changing the 'find' statements to something else;
see, they really *are* being run. ;)


In Practice: Testing a CherryPy application using twill and wsgi_intercept
==========================================================================



*You'll need CherryPy 2.1.1 for this, along with nose 0.8.x and twill 0.8.2 (the very latest).*

For CherryPy, let's test the "Hello, world!" application that is
included in the tutorial code.  The magic incantations to get a WSGI
app object out of CherryPy are not so tricky: ::

   import cherrypy
   from cherrypy.tutorial.tut01_helloworld import HelloWorld

   # set up the root object
   cherrypy.root = HelloWorld()

   # initialize
   cherrypy.server.start(initOnly=True, serverClass=None)

   # get WSGI app.
   from cherrypy._cpwsgi import wsgiApp

where 'wsgiApp' is the final application object we wanted.

Starting with a 'test.py' containing a simple framework for a nose unit test, ::

   class TestHelloWorld:
      def setUp(self):
         pass

      def tearDown(self):
         pass

we can fill in the ``setUp`` function as before: ::

   def setUp(self):
      # configure cherrypy to be quiet ;)
      cherrypy.config.update({ "server.logToScreen" : False })

      # create root & set up the server.
      cherrypy.root = HelloWorld()
      cherrypy.server.start(initOnly=True, serverClass=None)

      # get WSGI app.
      from cherrypy._cpwsgi import wsgiApp

      # install the app at localhost:8080 for wsgi_intercept
      twill.add_wsgi_intercept('localhost', 8080, lambda : wsgiApp)

      # while we're at it, snarf twill's output.
      self.outp = StringIO()
      twill.set_output(self.outp)

and the ``tearDown`` function is virtually identical to the Quixote
example: ::

   def tearDown(self):
     # remove intercept.
     twill.remove_wsgi_intercept('localhost', 8080)

      # shut down the cherrypy server.
     cherrypy.server.stop()

This application is a bit simpler than the Quixote mini demo, so let's
just build one test function: ::

   def test_hello(self):
      script = "find 'Hello world!'"
      twill.execute_string(string, initial_url='http://localhost:8080/')

and when we run it, voila! it all works: ::

   % nosetests
   .
   ----------------------------------------------------------------------
   Ran 1 test in 0.289s
   
   OK

Conclusions and Caveats
=======================

This code is all still quite young, but it works!  Please remember
that that you *do* need to run some tests on a live site -- twill can
be used for sites without much JavaScript, while Selenium is probably
the way to go for anything more complicated.  Still, using twill and
wsgi_intercept to run tests in-process is relatively simple and
straightforward, and I think it can be a very useful component of your
Web app development process.

It can be very convenient to test Web apps this way.  The biggest
convenience, for me, is that I can avoid all the complicated setup
stuff.  A close second is that code coverage analysis, profiling, and
even debugging can all run within your unit tests, because everything
is in-process.  And a third is that unit tests run this way seem to
run quite a bit faster, perhaps because there's no setup/teardown of
the Web server.

If you have any suggestions, corrections, or explications, please send
them on to me at *titus@caltech.edu*.  I'll acknowledge them
appropriately, I promise!  I would also be interested in examples for
other Python Web frameworks; right now I only use CherryPy and Quixote
myself.  (Note that Michael Twomey has also posted `an example for Django`_.)

--titus

**Software Links**

twill Web browsing language:

  * Web site & docs: http://www.idyll.org/~t/www-tools/twill/
  * download: http://darcs.idyll.org/~t/projects/twill-0.8.2.tar.gz

Quixote Web application framework: 

   * Web site: http://www.mems-exchange.org/software/quixote/
   * download: http://www.mems-exchange.org/software/quixote/Quixote-2.4.tar.gz

CherryPy Web application framework:
   
   * Web site: http://www.cherrypy.org/
   * download: http://prdownloads.sourceforge.net/cherrypy/CherryPy-2.1.1.tar.gz?download

nose unit testing framework:

   * Web site and docs: http://somethingaboutorange.com/mrl/projects/nose/
   * download: http://somethingaboutorange.com/mrl/projects/nose/nose-0.8.6.tar.gz

Mike Orr's WSGI wrapper for Quixote:

   * view source: http://cafepy.com/quixote_extras/rex/wsgi_server.py

(The file itself is included in the source distribution for this article.)

Source distribution for this article:

   * darcs repository: http://darcs.idyll.org/~t/projects/wsgi_intercept-examples/
   * download directly: http://darcs.idyll.org/~t/projects/wsgi_intercept-examples-latest.tar.gz

CTB 3/06

.. _twill: http://www.idyll.org/~t/www-tools/twill/
.. _webtest: http://www.cherrypy.org/file/trunk/cherrypy/test/webtest.py
.. _webunit: http://mechanicalcat.net/tech/webunit/
.. _mechanize: http://wwwsearch.sf.net/
.. _mechanoid: http://www.python.org/pypi/mechanoid/
.. _zope.testbrowser: http://www.python.org/pypi/ZopeTestbrowser

.. _a suggestion: http://blog.ianbicking.org/best-of-the-web-app-test-frameworks.html
.. _wsgi_intercept: http://darcs.idyll.org/~t/projects/wsgi_intercept/README.html
.. _the wsgi_intercept page: http://darcs.idyll.org/~t/projects/wsgi_intercept/README.html
.. _WSGI-compliant: http://www.python.org/peps/pep-0333.html
.. _nose: http://somethingaboutorange.com/mrl/projects/nose/
.. _quixote: http://www.mems-exchange.org/software/quixote/
.. _CherryPy: http://www.cherrypy.org/

.. _Selenium: http://www.openqa.org/selenium/
.. _PAMIE: http://pamie.sourceforge.net/
.. _an example for Django: http://blogs.translucentcode.org/mick/2006/02/26/basic-twill-intercept-testing-django/

.. _final file: http://darcs.idyll.org/~t/projects/wsgi_intercept-examples-latest.tar.gz

.. _an adapter available: http://cafepy.com/quixote_extras/rex/wsgi_server.py
