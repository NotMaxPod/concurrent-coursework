import argparse
import socket
import os
import sys
import struct
import time
import random
import traceback
import threading

MAX_DATA_RECV = 65535

def setupArgumentParser() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="A collection of Network Applications developed for SCC.231."
    )
    parser.set_defaults(func=ICMPPing, hostname="lancaster.ac.uk")
    subparsers = parser.add_subparsers(help="sub-command help")

    parser_p = subparsers.add_parser("ping", aliases=["p"], help="run ping")
    parser_p.set_defaults(timeout=2, count=10)
    parser_p.add_argument("hostname", type=str, help="host to ping towards")
    parser_p.add_argument(
        "--count",
        "-c",
        nargs="?",
        type=int,
        help="number of times to ping the host before stopping",
    )
    parser_p.add_argument(
        "--timeout",
        "-t",
        nargs="?",
        type=int,
        help="maximum timeout before considering request lost",
    )
    parser_p.set_defaults(func=ICMPPing)

    parser_t = subparsers.add_parser("traceroute", aliases=["t"], help="run traceroute")
    parser_t.set_defaults(timeout=2, protocol="udp")
    parser_t.add_argument("hostname", type=str, help="host to traceroute towards")
    parser_t.add_argument(
        "--timeout",
        "-t",
        nargs="?",
        type=int,
        help="maximum timeout before considering request lost",
    )
    parser_t.add_argument(
        "--protocol",
        "-p",
        nargs="?",
        type=str,
        help="protocol to send request with (UDP/ICMP)",
    )
    parser_t.set_defaults(func=Traceroute)

    parser_m = subparsers.add_parser("mtroute", aliases=["mt"], help="run traceroute")
    parser_m.set_defaults(timeout=2, protocol="udp")
    parser_m.add_argument("hostname", type=str, help="host to traceroute towards")
    parser_m.add_argument(
        "--timeout",
        "-t",
        nargs="?",
        type=int,
        help="maximum timeout before considering request lost",
    )
    parser_m.add_argument(
        "--protocol",
        "-p",
        nargs="?",
        type=str,
        help="protocol to send request with (UDP/ICMP)",
    )
    parser_m.set_defaults(func=MultiThreadedTraceRoute)

    parser_w = subparsers.add_parser("web", aliases=["w"], help="run web server")
    parser_w.set_defaults(port=8080)
    parser_w.add_argument(
        "--port",
        "-p",
        type=int,
        nargs="?",
        help="port number to start web server listening on",
    )
    parser_w.set_defaults(func=WebServer)

    parser_x = subparsers.add_parser("proxy", aliases=["x"], help="run proxy")
    parser_x.set_defaults(port=8000)
    parser_x.add_argument(
        "--port",
        "-p",
        type=int,
        nargs="?",
        help="port number to start web server listening on",
    )
    parser_x.set_defaults(func=Proxy)

    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    return args


class NetworkApplication:
    def checksum(self, dataToChecksum: bytes) -> int:
        csum = 0
        countTo = (len(dataToChecksum) // 2) * 2
        count = 0

        while count < countTo:
            thisVal = dataToChecksum[count + 1] * 256 + dataToChecksum[count]
            csum = csum + thisVal
            csum = csum & 0xFFFFFFFF
            count = count + 2

        if countTo < len(dataToChecksum):
            csum = csum + dataToChecksum[len(dataToChecksum) - 1]
            csum = csum & 0xFFFFFFFF

        csum = (csum >> 16) + (csum & 0xFFFF)
        csum = csum + (csum >> 16)
        answer = ~csum
        answer = answer & 0xFFFF
        answer = answer >> 8 | (answer << 8 & 0xFF00)

        answer = socket.htons(answer)

        return answer

    # Print Ping output
    def printOneResult(
        self,
        destinationAddress: str,
        packetLength: int,
        time: float,
        seq: int,
        ttl: int,
        destinationHostname="",
    ):
        if destinationHostname:
            print(
                "%d bytes from %s (%s): icmp_seq=%d ttl=%d time=%.3f ms"
                % (
                    packetLength,
                    destinationHostname,
                    destinationAddress,
                    seq,
                    ttl,
                    time,
                )
            )
        else:
            print(
                "%d bytes from %s: icmp_seq=%d ttl=%d time=%.3f ms"
                % (packetLength, destinationAddress, seq, ttl, time)
            )

    def printAdditionalDetails(self, host, numPacketsTransmitted, rtts):
        if len(rtts) > 0:
            print(f"--- {host} ping statistics ---")
            lossPercent = int((100.0 - 100.0 * (len(rtts) / numPacketsTransmitted)))
            print(
                f"{numPacketsTransmitted} packets transmitted, {len(rtts)} received, {lossPercent}% packet loss"
            )
            avgRTT = sum(rtts) / len(rtts)
            deviations = [abs(rtt - avgRTT) for rtt in rtts]
            mdev = sum(deviations) / len(deviations)
            minRTT = min(rtts)
            maxRTT = max(rtts)
            print(
                "rtt min/avg/max/mdev = %.3f/%.3f/%.3f/%.3f ms"
                % (1000 * minRTT, 1000 * avgRTT, 1000 * maxRTT, 1000 * mdev)
            )

    # Print one line of traceroute output
    def printMultipleResults(
        self,
        ttl: int,
        pkt_keys: list,
        hop_addrs: dict,
        rtts: dict,
        destinationHostname="",
    ):
        if pkt_keys is None:
            print(str(ttl) + "   * * *")
            return
        # Sort packet keys (sequence numbers or UDP ports)
        pkt_keys = sorted(pkt_keys)
        output = str(ttl) + "   "
        last_hop_addr = None
        last_hop_name = None

        for pkt_key in pkt_keys:
            # If packet key is missing in hop addresses, this means no response received: print '*'
            if pkt_key not in hop_addrs.keys():
                output += "* "
                continue
            hop_addr = hop_addrs[pkt_key]

            # Get the RTT for the probe
            rtt = rtts[pkt_key]
            if last_hop_addr is None or hop_addr != last_hop_addr:
                hostName = None
                try:
                    # Get the hostname for the hop
                    hostName = socket.gethostbyaddr(hop_addr)[0]
                    if last_hop_addr is None:
                        output += hostName + " "
                    else:
                        output += " " + hostName + " "
                except socket.herror:
                    output += hop_addr + " "
                last_hop_addr = hop_addr
                last_hop_name = hostName
                output += "(" + hop_addr + ") "

            output += str(round(1000 * rtt, 3))
            output += " ms  "

        print(output)


class WebServer():
    def __init__(self, args):
        print("Web Server starting on port: %i..." % args.port)

        # 1. Create a TCP socket
        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # 2. Bind the TCP socket to server address and server port
        serverSocket.bind(("", args.port))

        # 3. Continuously listen for connections to server socket
        serverSocket.listen(100)
        print("Server listening on port", args.port)

        while True:
            # 4. Accept incoming connections
            connectionSocket, addr = serverSocket.accept()
            print(f"Connection established with {addr}")

            # 5. Create a new thread to handle each client request
            threading.Thread(
                target=self.handleRequest, args=(connectionSocket,)
            ).start()

        # Close server socket (this would only happen if the loop was broken, which it isn't in this example)
        serverSocket.close()

    def handleRequest(self, connectionSocket):
        try:
            # 1. Receive request message from the client
            message = connectionSocket.recv(MAX_DATA_RECV).decode()

            # 2. Extract the path of the requested object from the message (second part of the HTTP header)
            filename = message.split()[1]

            # 3. Read the corresponding file from disk
            with open(filename[1:], "r") as f:  # Skip the leading '/'
                content = f.read()

            # 4. Create the HTTP response
            response = "HTTP/1.1 200 OK\r\n\r\n"
            response += content

            # 5. Send the content of the file to the socket
            connectionSocket.send(response.encode())

        except IOError:
            # Handle file not found error
            error_response = "HTTP/1.1 404 Not Found\r\n\r\n"
            error_response += (
                "<html><head></head><body><h1>404 Not Found</h1></body></html>\r\n"
            )
            connectionSocket.send(error_response.encode())

        except Exception as e:
            print(f"Error handling request: {e}")

        finally:
            # Close the connection socket
            connectionSocket.close()