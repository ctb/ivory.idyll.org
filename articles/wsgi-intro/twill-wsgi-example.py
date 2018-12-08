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
