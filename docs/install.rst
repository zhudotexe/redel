Installation
============

TL;DR: ReDel requires Python 3.10+. You can install ReDel though pip:

.. code-block:: console

    $ pip install "redel[all]"

.. warning::
    The default installation without any extras defined is a "thin" configuration - it contains only what's needed to
    run a ReDel system, without the web interface or bundled tools. This can be useful to avoid dependency pollution,
    but we recommend installing the ``all`` or ``web`` extra if it's your first time using the library.

Extras
------
To use the bundled web viewer and/or bundled example tools, you'll need to install a few additional packages. ReDel
provides these dependencies as extras, which you can specify with your installation command
(e.g. ``pip install "redel[all]"``). ReDel provides the following extras:

* ``all``: All extras included below.
* ``web``: All the dependencies needed to run the web interface (an HTTP server, ASGI, and websockets)
* ``bundled``: The dependencies needed to use the bundled :class:`.Browsing` tool.

If you plan to use the bundled browsing tool, you will also need to run ``playwright install chromium``.

Installing on Conda
-------------------
You may need to install pip in your conda environment first:

.. code-block:: console

    $ conda install pip

Then, follow the instructions for installing with pip above.

.. caution::

    In certain cases when using a conda venv, the ``pip`` binary may
    `reference a different environment <https://stackoverflow.com/questions/41060382/using-pip-to-install-packages-to-anaconda-environment>`_,
    and ReDel may appear to be uninstalled even if pip assures that it is. Using ``python -m pip install`` in place of
    ``pip install`` may mitigate this issue.

Virtual Environment
-------------------
If you're not using conda, we recommend using a virtual environment to manage your project dependencies. This will
help you prevent polluting your global Python installation with all sorts of packages.

.. tab:: macOS/Linux

    .. code-block:: console

        $ python -m venv ./venv
        $ ./venv/bin/activate
        $ pip install "redel[all]"

.. tab:: Windows

    .. code-block:: console

        $ python -m venv venv
        $ venv\Scripts\activate.bat
        $ pip install "redel[all]"

Development Version
-------------------
If you'd like to install the development version of ReDel, you can install it from GitHub directly:

.. code-block:: console

    $ pip install 'redel[all] @ git+https://github.com/zhudotexe/redel.git@main'

This will install the latest version of ReDel.

.. note::
    You may need to use ``pip install --upgrade --no-deps --force-reinstall ...`` to force pip to re-fetch the
    latest ReDel from GitHub.

.. caution::
    Development versions of ReDel may be unstable! Do not use development ReDel in production or in final research
    experiments; pin a released version of ReDel instead.

Requirements File
-----------------
If you're running experiments using ReDel, we recommend pinning the version of ReDel to ensure your runs are reproducible.
To do this, we recommend storing all your Python requirements in a ``requirements.txt`` file.

.. code-block:: text

    redel[all]==x.y.z
    # ... other dependencies

You can automatically generate this file too, by running ``pip freeze > requirements.txt``.

Later, anyone else running your code can install the same dependency versions by simply running
``pip install -r requirements.txt``.
