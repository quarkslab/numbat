from numbat import SourcetrailDB
from scapy.all import *
import argparse
import re


def get_packet_info(pkt):
    if IP in pkt:
        src = pkt[IP].src
        dst = pkt[IP].dst
        if TCP in pkt:
            sport = pkt[TCP].sport
            dport = pkt[TCP].dport
        elif UDP in pkt:
            sport = pkt[UDP].sport
            dport = pkt[UDP].dport
        else:
            sport = ''
            dport = ''
        return str(src), str(sport), str(dst), str(dport)
    return None, None, None, None


def main():
    parser = argparse.ArgumentParser(
        description="Convert a pcap file to a Sourcetrail database using numbat!"
    )
    parser.add_argument('-i', '--infile', nargs='+', type=str,
                        help="Path to pcap file(s) to convert", required=True
                        )
    parser.add_argument('-o', '--outfile',
                        help='Name of the output file', required=True
                        )
    args = parser.parse_args()

    # Create a new database
    db = SourcetrailDB.open(args.outfile, clear=True)
    nodes = {}
    edges = {}

    for file in args.infile:
        # Open pcap file using scapy
        packets = rdpcap(file)
        for packet in packets:
            # Read packet information
            protocol = packet.lastlayer().name
            src, sport, dst, dport = get_packet_info(packet)
            if not src or not dst:
                continue

            # Update nodes for src/dst
            if src not in nodes:
                id = db.record_class(prefix="Machine", name=src, postfix="")
                nodes.update({src: id})
            if dst not in nodes:
                id = db.record_class(prefix="Machine", name=dst, postfix="")
                nodes.update({dst: id})
            sname = f'{src}:{sport} {protocol}'
            dname = f'{dst}:{dport} {protocol}'

            # Add ports as fields of the class
            if sname not in nodes:
                id = db.record_field(name=f'{sport} {protocol}', parent_id=nodes[src])
                nodes.update({sname: id})
            if dname not in nodes:
                id = db.record_field(name=f'{dport} {protocol}', parent_id=nodes[dst])
                nodes.update({dname: id})

            # Add the edges between nodes
            edge_name = f'{sname}|{dname}'
            if edge_name not in edges:
                # Record a usage between the src port and dst port
                id = db.record_ref_usage(nodes[sname], nodes[dname])
                edges.update({edge_name: id})
    db.commit()
    db.close()


if __name__ == '__main__':
    main()
