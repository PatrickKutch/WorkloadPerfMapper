#Workload Performance Manager

This tool is designed to mimic a 3-tiered application, where a client communicates with an 'app' via REST API.  The app in turn communicates with services (as in micr-services) via gRPC.

This utility provides all those components and measures the time it takes to process various workloads, and how long the gRPC calls take.  In this way you can do some basic charactorization of what different CPU architectures can do for various workloads, and more importanly, the geographic placment of the client, web app and services are located affects latency.