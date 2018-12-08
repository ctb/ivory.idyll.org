#! /usr/bin/env python
import twill

def simple_app(environ, start_response):
    """
    It may even be possible to use wsgi_intercept with doctest.
    For example,
    
    >>> twill.add_wsgi_intercept('localhost', 80, lambda: simple_app)
    >>> twill.execute_string("go http://localhost:80/\\nshow")
    ==> at http://localhost:80/
    Hello world!

    Unfortunately this doesn't actually work, for reasons that I'm sure
    Grig will point out.
    """
    
    status = '200 OK'
    response_headers = [('Content-type','text/plain')]
    start_response(status, response_headers)
    return ['Hello world!\n']

if __name__ == '__main__':
    import doctest
    doctest.testmod()
