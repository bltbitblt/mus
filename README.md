rtmus
=====

My music midi thingy. Based on [aiotone](https://github.com/ambv/aiotone).

TODO
----

* Cleanup class structure
* Initialize Metronome proper
* Is sleep(0) correct?
* Register task at Performance and it will cancel the tasks on STOP
* Alternative architectures:
  * Start tasks using position in track-callback
  * Let Bitwig start tasks using midi-messages
