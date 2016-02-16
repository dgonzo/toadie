toadie
======

Toadie is a microservices framework that includes everything needed to create task queue based microservices using the ambassador pattern. toadie supports the concepts of `service` and `task`.

    * Service: Long-running application or worker
    * Task: Short-running application or worker

Toadie is designed with analytic processes and smaller teams in mind.

Toadie is inspired by django and rails and gummi bears.

![Adventures of the Gummi Bears' "Toadie"](http://vignette2.wikia.nocookie.net/disney/images/4/4d/Toadwart.png/revision/latest?cb=20110812110754)

# Getting Started

1. Install toadie at the command prompt if you haven't yet using either `pip` or `conda`:

   # using pip
   $ pip install toadie

   # using conda
   $ conda install -c https://conda.anaconda.org/gonzo toadie

2. Install required development tools:

   $ toadie readySystem

3. At the command prompt, create a new toadie project and a `service`:

   $ toadie createProject myproject

   where "myproject" is the project name

   $ cd myproject
   $ toadie createService myservice

   where "myservice" is the name of your service.

4. Start your stack locally:

   $ toadie up

5. Deploy your stack on your chosen cloud:

   $ toadie deploy

