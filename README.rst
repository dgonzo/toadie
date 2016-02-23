######
toadie
######

Toadie is a microservices framework that includes everything needed to create microservices using the ambassador pattern to run on a compute cluster (like Elastic Container Service or Kubernetes). Toadie supports the concepts of `service` and `task`.

    * Service: Long-running application or worker
    * Task: Short-running application or worker, which often requires additional compute resorces be added to cluster

Toadie is designed with analytic processes and smaller teams in mind.

Toadie is inspired by django and rails and gummi bears.

.. image:: Toadwart.png
   :target: http://vignette2.wikia.nocookie.net/disney/images/4/4d/Toadwart.png
   :alt: Adventures of the Gummi Bears' "Toadie"

###############
Getting Started
###############

1. Install toadie at the command prompt if you haven't yet using either `pip` or `conda`:

    .. code:: shell

        # using conda
        $ conda install -c https://conda.anaconda.org/gonzo toadie

2. Install required development tools:

    .. code:: shell

       $ toadie ready-system

3. At the command prompt, create a new toadie project and add a `service`:

    .. code:: shell

       $ toadie create-project myproject
       $ cd myproject
       $ toadie create-service myservice

    where "myproject" is the project name and where "myservice" is the name of your service.

4. Start your stack locally:

    .. code:: shell

       $ honcho start up

5. Deploy your stack on your chosen cloud:

    .. code:: shell

       $ toadie deploy

