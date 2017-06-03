RASBlite - Lightweight RESTful API Server Builder
=================================================

RASBlite allows you to quickly define a data model that you can interact
with via a RESTful API in a consistent way. Although there are numerous
scenarios when you’d want to do this, it is particularly useful during
the development of REST clients (such as in unit tests and continuous
integration environments).

Imagine you’re working on a client that accesses some remote resource
using a RESTful API. For example, let’s say your client will interact
with a server holding a list of items which includes the name and the
amount of the item. If the server does not yet exist, how will you test
your client? If the server does exist, how can you automatically test
your client consistently without having constant direct access to the
server? For this example, we could easily define a hierarchical model
with RASBlite like so:

.. code:: ini

    [Base]
    url = /api/

    [Model]
    structure = 
        GET,POST         items/
        GET,PUT,DELETE   items/:item_number/
        GET,PUT          items/:item_number/name
        GET,PUT          items/:item_number/amount

With RASBlite, your REST client could now perform a HTTP ``POST`` to
``http://127.0.0.1:8080/api/items/`` with
``{'name': 'Spoon', 'amount': '3'}`` and then verify it worked by
subsequently doing a HTTP ``GET`` to
``http://127.0.0.1:8080/api/items/0/`` and checking the response matched
your earlier ``POST``.

Quickstart
----------

| Install RASBlite using ``pip3`` - ``$ pip3 install rasblite``, this
  will provide the script
| ``rasblite-run``. If you encounter an error during installation, you
  may have to run with elevated privileges using ``sudo`` -
  ``$ sudo pip3 install rasblite``.

Next, create a file containing your model called ``model.txt``. To begin
with you can just fill the contents with the one below which contains a
list of users, their names and any addresses they may have on record:

.. code:: ini

    [Base]
    url = /rest/api/1.0/

    [Model]
    structure = 
        GET,POST         users/
        GET,PUT,DELETE   users/:userID/
        GET,PUT          users/:userID/name
        GET,POST         users/:userID/addresses/
        GET,PUT,DELETE   users/:userID/addresses/:address/
        GET,PUT          users/:userID/addresses/:address/address_lines
        GET,PUT          users/:userID/addresses/:address/post_code
        GET,PUT          users/:userID/age

Now, if we wanted to start off with no initial data on the server you
can simply run:

.. code:: bash

    $ rasblite-run --model model.txt --starting_data DEFAULT

Otherwise if you want start with some example data for this particular
model you can create a file called ``data.json`` with the contents:

::

    {'users': [{'addresses': [{'address_lines': '123 Fake Street', 'post_code': 'AB12 3CD'}], 'age': '21', 'name': 'Bob'}, {'addresses': [{'address_lines': '456 My Street', 'post_code': 'EF45 6GH'}, {'address_lines': '789 Other Street', 'post_code': 'IJ12 3KL'}], 'age': '60', 'name': 'Frank'}]}

and run it with:

.. code:: bash

    $ rasblite-run --model model.txt --starting_data data.json

or

.. code:: bash

    $ rasblite-run -m model.txt -d data.json

Feeling lazy? The above starting data is pre-built into the script so
you can get the same effect without creating the initial data file by
running:

.. code:: bash

    $ rasblite-run -m model.txt -d EXAMPLE

Your HTTP server should now be running and you can easily test it works
by accessing it with your favourite web bowser:

http://127.0.0.1:8080/rest/api/1.0/users/

If all went well you should see your starting data returned. You can
drill down to specific points by following the hierarchy:

http://127.0.0.1:8080/rest/api/1.0/users/1/addresses/0/post_code/

You can now perform all your usual REST functions with HTTP methods such
as ``GET``, ``POST``, ``PUT`` and ``DELETE``. The model you used
specifies which of these HTTP methods are allowed and are determined by
you (more on this below in the **Model Structure** section).

--------------

**NOTE:**

Make sure to set the correct HTTP headers in your client for ``POST``
and ``PUT`` requests. Currently, the only ``content-type`` supported is
``application/json`` and you need to include the correct
``content-length`` too. For example, an example raw ``POST`` request
might look like:

::

    POST /rest/api/1.0/users HTTP/1.1
    HOST: 127.0.0.1:8080
    content-length: 103
    content-type: application/json

    {"name": "Jim", "addresses": [{"post_code": "UR98 7ST", "address_lines": "30 Flat Road"}], "age": "18"}

--------------

Usage
-----

::

    $ rasblite-run --help
    usage: rasblite-run [-h] --model MODEL [--starting_data STARTING_DATA]
                        [--port PORT]

    Lightweight RESTful API Server Builder Command Line Tool

    optional arguments:
      -h, --help            show this help message and exit
      --model MODEL, -m MODEL
      --starting_data STARTING_DATA, -d STARTING_DATA
      --port PORT, -p PORT

Changing the server port
~~~~~~~~~~~~~~~~~~~~~~~~

To use another port other than ``8080``, simply pass the desired port
number to rasblite-run with ``--port`` or ``-p`` argument:

.. code:: bash

    $ rasblite-run --model model.txt --starting_data DEFAULT --port 50000

Initialising without hierarchical data store
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It’s possible to tell RASBlite not to create a hierarchical data store
to match your model structure. To do this, pass ``EMPTY`` for the
``--starting_data`` argument:

.. code:: bash

    $ rasblite-run --model model.txt --starting_data EMPTY

Model Syntax
------------

Base URL
~~~~~~~~

Most REST APIs contain a base url (the part in the url before the
hierarchical structure). i.e.

``http://<host>:<port><base_url><your_model>``

You can set the base url for your API by setting the ``url`` attribute
within the ``[Base]`` section. The path prefix will then be used for
your API.

For example:

.. code:: ini

    [Base]
    url = /rest/api/1.0/
    ...

The above would mean the client must request with ``/rest/api/1.0/``
before their model i.e. ``http://127.0.0.1:8080/rest/api/1.0/some/path``

Model Structure
~~~~~~~~~~~~~~~

To define the structure of your model, you must include the possible
request suffix paths with the ``structure`` attribute under a
``[Model]`` section like so:

.. code:: ini

    ...

    [Model]
    structure = 
        GET,POST         users/
        GET,PUT,DELETE   users/:userID/
        GET,PUT          users/:userID/name
        GET,POST         users/:userID/addresses/
        GET,PUT,DELETE   users/:userID/addresses/:address/
        GET,PUT          users/:userID/addresses/:address/address_lines
        GET,PUT          users/:userID/addresses/:address/post_code
        GET,PUT          users/:userID/age

Each line contains the approved HTTP methods for that entry and the
hierarchical suffix path. The parts need to be separated by whitespace
but this can be spaces or tabs.

Approved HTTP methods
^^^^^^^^^^^^^^^^^^^^^

Each line in the structure must start with the HTTP methods that are
allowed. They have to be comma separated and must be ``GET``, ``POST``,
``PUT`` and/or ``DELETE``. For example, if you only wanted to allow
clients to perform a ``GET``, ``POST`` or ``DELETE`` to
``http://<host>:<port>/base/users/`` your model structure could look
like this:

.. code:: ini

    [Base]
    url = /base/

    [Model]
    structure = 
        GET,POST,DELETE users/

Request path suffix
^^^^^^^^^^^^^^^^^^^

Each line in the structure must end with the path suffix. You can build
a hierarchical tree by including additional paths that contain common
parents. Parts of the path that start with a colon ``:`` such as
item\_number in ``/some/:item_number/path`` denote a list and can be
accessed by an index. For example, you could have a list of cars by
defining a structure like this:

.. code:: ini

    [Base]
    url = /base/

    [Model]
    structure = 
        GET,POST         cars/
        GET,PUT,DELETE   cars/:car_number/
        GET,PUT          cars/:car_number/name
        GET,PUT          cars/:car_number/make
        GET,PUT          cars/:car_number/reg

The lists are zero-indexed which means to access the make of the 5th car
stored by your server, you would perform a ``GET`` on:

http://127.0.0.1:8080/base/cars/4/make

Notice how ``:car_number`` in the path has been replaced by an index.
