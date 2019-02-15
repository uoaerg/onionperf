
What is OnionPerf
=========
OnionPerf is a utility to track Tor and onion service performance.

OnionPerf uses multiple processes and threads to download random data through
Tor while tracking the performance of those downloads. The data is served and
fetched on localhost using two TGen (traffic generator) processes, and is
transferred through Tor using Tor client processes and an ephemeral Tor Onion
Service. Tor control information and TGen performance statistics are logged to
disk, analyzed once per day to produce a json stats database and files that can
feed into Torperf, and can later be used to visualize changes in Tor client
performance over time.

Measurements
=========

Deployment
=========


Onionperf Components
============
Onionperf is structured around 4 main components: measurement, analysis, monitoring and visualisation.
Alongside this, it provides utilities and tgen graph modelling functions.



util
=========

This documents the utils used by onionperf and mostly contains functionality around paths and opening and closing files.

.. automodule:: onionperf.util
   :members:
   :undoc-members:

analysis
========

This documents the tgen model used by onionperf to conduct downloads.

.. automodule:: onionperf.model
   :members:
   :undoc-members:
