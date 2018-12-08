============================
Testing WSGI Apps with twill
============================

One of the particularly useful aspects of having a standard interface
to Python Web apps is that it lets you build standard test harnesses,
too.  I've done just that with twill_, using wsgi_intercept_, a
library which lets you "mock" the network interface so that you can
run and test WSGI apps in-process.

twill and basic wsgi_intercept
==============================

For example, this code: ::

   #! /usr/bin/env python
   import twill

   def simple_app(environ, start_response):
      status = '200 OK'
      response_headers = [('Content-type','text/plain')]
      start_response(status, response_headers)
      return ['Hello world!\n']

   if __name__ == '__main__':
      print '*** installing WSGI intercept hook ***\n'
      twill.add_wsgi_intercept('localhost', 80, lambda: simple_app)
      twill.shell.main()

lets you browse a Web app directly: ::

  % ./twill-wsgi-example.py -u http://localhost:80/
  *** installing WSGI intercept hook ***
  ==> at http://localhost:80/

   -= Welcome to twill! =-

  current page: http://localhost:80/
  >> show
  Hello world!

or run a script, for example this script, ``hello-test.twill``, ::

  code 200
  find Hello

produces this output: ::

  % ./twill-wsgi-example.py -u http://localhost:80/ hello-test.twill
  *** installing WSGI intercept hook ***
  >> EXECUTING FILE hello-test.twill
  ==> at http://localhost:80
  --
  1 of 1 files SUCCEEDED.

`[download]`__

.. __: twill-wsgi-example.py

twill and doctest
=================

You should even be able to put twill commands into doctests: ::

    def simple_app(environ, start_response):
        """
        It may even be possible to use wsgi_intercept with doctest.
        For example,

        >>> twill.add_wsgi_intercept('localhost', 80, lambda: simple_app)
        >>> go("http://localhost:80/")
        ==> at http://localhost:80/
	>>> show()
        Hello world!

        Unfortunately this doesn't actually work, for reasons that I'm sure
        Grig will solve.
        """

        status = '200 OK'
        response_headers = [('Content-type','text/plain')]
        start_response(status, response_headers)
        return ['Hello world!\n']

`[download]`__

.. __: twill-wsgi-doctest.py

Now tell me that wouldn't be neat!  (Unfortunately it doesn't *work* just
yet, but I'll figure that out...)

.. _twill: http://www.idyll.org/~t/www-tools/
.. _wsgi_intercept: http://darcs.idyll.org/~t/projects/wsgi_intercept/README.html