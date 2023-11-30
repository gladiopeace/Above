#!/usr/bin/env python3

from scapy.all import *
from scapy.layers.l2 import *
from scapy.contrib.ospf import *
from scapy.contrib.eigrp import *
from scapy.contrib.cdp import *
from scapy.contrib.dtp import *
from scapy.layers.ipsec import *
from scapy.layers.vrrp import *
from scapy.layers.hsrp import *
from colorama import Fore, Style
import threading
import shutil
import argparse
import signal
import sys

# The design of the code leaves a lot to be desired.
# First of all, I wrote the code in such a way that it would work as intended.


# This section is code for displaying the logo and author information
text = r"""
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@&   &@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@   @   @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@   @@@   @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@   @@@@@   @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%  @@@@@@@@@  %@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@   @@@@@@@@@@@   @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@   @@@@@@@@@@@@@   @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@   @@@@@@@@@@@@@@@   @@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@                                     @@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@                                     @@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@   @@@@@@@@@@@@@@@@@@@@@@@@@   @@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@%  @@@@@@@@@@@@@@@@@@@@@@@@@@@@@  %@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@                                     @@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
"""

terminal_width = shutil.get_terminal_size().columns

for line in text.split("\n"):
    padding = " " * ((terminal_width - len(line)) // 2)
    print(Fore.LIGHTWHITE_EX + Style.BRIGHT + padding + line)


def centered_text(text, color=Fore.WHITE, style=Style.BRIGHT):
    terminal_width = shutil.get_terminal_size().columns
    padding = " " * ((terminal_width - len(text)) // 2)
    return f"{color}{style}{padding}{text}"


print(centered_text("Network Sniffer for Finding Vulnerabilities", Fore.WHITE))
print(centered_text("Version 2.1, Codename: Vivid", Fore.YELLOW))
print(centered_text("Author: Caster, @wearecaster, <casterinfosec@gmail.com>", Fore.WHITE))


# CDP & DTP Scan
def detect_ciscoprotocols(interface, timer):
    cdp_frame = sniff(filter="ether dst 01:00:0c:cc:cc:cc", count=1, timeout=timer, iface=interface)
    if not cdp_frame:
        return 0
    snapcode = cdp_frame[0][SNAP].code
    # For CDP Protocol
    if snapcode == 0x2000:
        print(Fore.WHITE + Style.BRIGHT + '-' * 50)
        print(Fore.WHITE + Style.BRIGHT + "[+] Detected CDP Protocol")
        print(Fore.GREEN + Style.BRIGHT + "[*] Impact: " + Fore.YELLOW + Style.BRIGHT + "Information Gathering, DoS")
        print(Fore.GREEN + Style.BRIGHT + "[*] Tools: " + Fore.WHITE + Style.BRIGHT + "Yersinia, Wireshark")
        cdphostname = cdp_frame[0][CDPMsgDeviceID].val
        print(
            Fore.GREEN + Style.BRIGHT + "[*] System Hostname: " + Fore.WHITE + Style.BRIGHT + str(cdphostname.decode()))
        cdphardwareversion = cdp_frame[0][CDPMsgSoftwareVersion].val
        print(Fore.GREEN + Style.BRIGHT + "[*] Target Version: " + Fore.WHITE + Style.BRIGHT + str(
            cdphardwareversion.decode()))
        cdphardwareplatform = cdp_frame[0][CDPMsgPlatform].val
        print(Fore.GREEN + Style.BRIGHT + "[*] Target Platform: " + Fore.WHITE + Style.BRIGHT + str(
            cdphardwareplatform.decode()))
        cdpportid = cdp_frame[0][CDPMsgPortID].iface
        print(Fore.GREEN + Style.BRIGHT + "[*] Port ID: " + Fore.WHITE + Style.BRIGHT + str(cdpportid.decode()))
        if cdp_frame[0].haslayer(CDPAddrRecordIPv4):
            cdpaddr = cdp_frame[0][CDPAddrRecordIPv4].addr
            print(Fore.GREEN + Style.BRIGHT + "[*] IP Address: " + Fore.WHITE + Style.BRIGHT + cdpaddr)
    # For DTP Protocol       
    if snapcode == 0x2004:
        print(Fore.WHITE + Style.BRIGHT + '-' * 50)
        print(Fore.WHITE + Style.BRIGHT + "[+] Detected DTP Protocol")
        dtp_neighbor = cdp_frame[0][DTPNeighbor].neighbor
        print(Fore.GREEN + Style.BRIGHT + "[*] Impact: " + Fore.YELLOW + Style.BRIGHT + "VLAN Segmentation Bypass")
        print(Fore.GREEN + Style.BRIGHT + "[*] Tools: " + Fore.WHITE + Style.BRIGHT + "Yersinia, Scapy")
        print(Fore.GREEN + Style.BRIGHT + "[*] DTP Neighbor MAC: " + Fore.WHITE + Style.BRIGHT + str(dtp_neighbor))


# 802.1Q Tags Scan
def vlan_sniffer(interface, timer):
    # To search for unique IDs without duplication
    vlan_ids = set()

    # Custom Filter
    def sniff_dot1q(pkt):
        if pkt.haslayer(Dot1Q):
            vlan_ids.add(pkt[Dot1Q].vlan)

    sniff(iface=interface, prn=sniff_dot1q, timeout=timer)
    if len(vlan_ids) == 0:
        return
    print(Fore.WHITE + Style.BRIGHT + '-' * 50)
    print(Fore.WHITE + Style.BRIGHT + "[+] Detected 802.1Q Frames")
    print(
        Fore.GREEN + Style.BRIGHT + "[+] Found VLAN IDs:" + Fore.WHITE + Style.BRIGHT + f" {', '.join(str(vlan_id) for vlan_id in vlan_ids)}")
    print(Fore.GREEN + Style.BRIGHT + "[*] Impact: " + Fore.YELLOW + Style.BRIGHT + "VLAN Segmentation Bypass")
    print(
        Fore.YELLOW + Style.BRIGHT + "[!] Using the IDs found, create the necessary virtual interfaces using Linux tools")


# OSPF Scan
def detect_ospf(interface, timer):
    ospfpacket = sniff(filter="ip dst 224.0.0.5 and ip proto 89", count=1, iface=interface, timeout=timer)
    if not ospfpacket:
        return 0

    # For display cleartext string (simple OSPF auth)
    def hex_to_string(hex):
        if hex[:2] == '0x':
            hex = hex[2:]
        string_value = bytes.fromhex(hex).decode('utf-8')
        return string_value
    
    areaID = ospfpacket[0][OSPF_Hdr].area
    authtype = ospfpacket[0][OSPF_Hdr].authtype
    ospfkeyid = ospfpacket[0][OSPF_Hdr].keyid
    authdatalength = ospfpacket[0][OSPF_Hdr].authdatalen
    authseq = ospfpacket[0][OSPF_Hdr].seq
    hellosource = ospfpacket[0][OSPF_Hdr].src
    print(Fore.WHITE + Style.BRIGHT + '-' * 50)
    print(Fore.WHITE + Style.BRIGHT + "[+] Detected OSPF Protocol")
    print(
        Fore.GREEN + Style.BRIGHT + "[+] Impact: " + Fore.YELLOW + Style.BRIGHT + "Subnets Discovery, Blackhole, Evil Twin")
    print(Fore.GREEN + Style.BRIGHT + "[*] Tools: " + Fore.WHITE + Style.BRIGHT + "Loki, Scapy, FRRouting")
    print(Fore.GREEN + Style.BRIGHT + "[*] OSPF Area ID: " + Fore.WHITE + Style.BRIGHT + str(areaID))
    print(Fore.GREEN + Style.BRIGHT + "[*] OSPF Neighbor: " + Fore.WHITE + Style.BRIGHT + str(hellosource))
    # No Auth
    if authtype == 0x0:
        print(Fore.YELLOW + Style.BRIGHT + "[!] Authentication: " + Fore.WHITE + Style.BRIGHT + "No")
    # Simple Auth (cleartext string)
    if authtype == 0x1:
        raw = ospfpacket[0][OSPF_Hdr].authdata
        hex_value = hex(raw)
        string = hex_to_string(hex_value)
        print(
            Fore.YELLOW + Style.BRIGHT + "[!] Authentication: " + Fore.YELLOW + Style.BRIGHT + "Plaintext Phrase: " + string)
    # Crypt Auth (MD5)
    if authtype == 0x02:
        print(Fore.YELLOW + Style.BRIGHT + "[!] Authentication: " + Fore.WHITE + Style.BRIGHT + "MD5")
        print(Fore.YELLOW + Style.BRIGHT + "[*] Tools for bruteforce: Ettercap, John the Ripper")
        print(Fore.GREEN + Style.BRIGHT + "[*] OSPF Key ID: " + Fore.WHITE + Style.BRIGHT + str(ospfkeyid))
        print(Fore.GREEN + Style.BRIGHT + "[*] Crypt Data Length: " + Fore.WHITE + Style.BRIGHT + str(authdatalength))
        print(Fore.GREEN + Style.BRIGHT + "[*] Crypt Auth Sequence Number: " + Fore.WHITE + Style.BRIGHT + str(authseq))


# EIGRP Scan
def detect_eigrp(interface, timer):
    eigrppacket = sniff(filter="ip dst 224.0.0.10 and ip proto 88", count=1, timeout=timer, iface=interface)
    if not eigrppacket:
        return 0
    else:
        print(Fore.WHITE + Style.BRIGHT + '-' * 50)
        print(Fore.WHITE + Style.BRIGHT + "[+] Detected EIGRP Protocol")
        print(
            Fore.GREEN + Style.BRIGHT + "[*] Impact: " + Fore.YELLOW + Style.BRIGHT + "Subnets Discovery, Blackhole, Evil Twin")
        print(Fore.GREEN + Style.BRIGHT + "[*] Tools: " + Fore.WHITE + Style.BRIGHT + "Loki, Scapy, FRRouting")
    asnumber = eigrppacket[0][EIGRP].asn
    if eigrppacket[0].haslayer("EIGRPAuthData"):
        print(Fore.YELLOW + Style.BRIGHT + "[!] There is EIGRP Authentication")
        if eigrppacket[0]["EIGRP"]["EIGRP Authentication Data"].authtype == 2:
            print(Fore.YELLOW + Style.BRIGHT + "[!] Authentication: " + Fore.WHITE + Style.BRIGHT + "MD5")
            print(Fore.YELLOW + Style.BRIGHT + "[*] Tools for bruteforce: eigrp2john.py, John the Ripper")
    else:
        print(Fore.YELLOW + Style.BRIGHT + "[!] Authentication: " + Fore.WHITE + Style.BRIGHT + "No")
    eigrpneighborip = eigrppacket[0][IP].src
    print(Fore.GREEN + Style.BRIGHT + "[*] AS Number: " + Fore.WHITE + Style.BRIGHT + str(asnumber))
    print(Fore.GREEN + Style.BRIGHT + "[*] EIGRP Neighbor: " + Fore.WHITE + Style.BRIGHT + str(eigrpneighborip))


# HSRP Scan
def detect_hsrp(interface, timer):
    # This is HSRPv1
    hsrp_detected = False  # Flag to track if HSRP packet with state 16 has been detected
    while True:
        hsrpv1_packet = sniff(count=1, filter="ip dst 224.0.0.2 and udp port 1985", iface=interface, timeout=timer)
        if not hsrpv1_packet:
            return 0
        if hsrpv1_packet[0][HSRP].state == 16 and hsrpv1_packet[0][HSRP].priority < 255 and not hsrp_detected:
            hsrp_detected = True  # Set the flag to True to indicate that HSRP packet with state 16 has been detected
            hsrpv1senderip = hsrpv1_packet[0][IP].src
            hsrpv1sendermac = hsrpv1_packet[0][Ether].src
            hsrpv1group = hsrpv1_packet[0][HSRP].group
            hsrpv1vip = hsrpv1_packet[0][HSRP].virtualIP
            print(Fore.WHITE + Style.BRIGHT + '-' * 50)
            print(Fore.WHITE + Style.BRIGHT + "[+] Detected HSRPv1 Protocol")
            print(
                Fore.YELLOW + Style.BRIGHT + "[*] HSRP ACTIVE Vulnerable Priority Value: " + Fore.WHITE + Style.BRIGHT + str(
                    (hsrpv1_packet[0].priority)))
            print(Fore.GREEN + Style.BRIGHT + "[+] Impact: " + Fore.YELLOW + Style.BRIGHT + "MITM")
            print(Fore.GREEN + Style.BRIGHT + "[*] Tools: " + Fore.WHITE + Style.BRIGHT + "Loki, Scapy, Yersinia")
            print(Fore.GREEN + Style.BRIGHT + "[*] HSRP Group Number: " + Fore.WHITE + Style.BRIGHT + str(hsrpv1group))
            print(Fore.GREEN + Style.BRIGHT + "[+] HSRP Virtual IP Address: " + Fore.WHITE + Style.BRIGHT + str(
                hsrpv1vip))
            print(Fore.GREEN + Style.BRIGHT + "[*] HSRP Speaker IP: " + Fore.WHITE + Style.BRIGHT + hsrpv1senderip)
            print(Fore.GREEN + Style.BRIGHT + "[*] HSRP Speaker MAC: " + Fore.WHITE + Style.BRIGHT + hsrpv1sendermac)
            if hsrpv1_packet[0].haslayer(HSRPmd5):
                print(Fore.YELLOW + Style.BRIGHT + "[!] Authentication: " + Fore.WHITE + Style.BRIGHT + "MD5")
                print(Fore.YELLOW + Style.BRIGHT + "[*] Tools for bruteforce: hsrp2john.py, John the Ripper")
            else:
                if hsrpv1_packet[0][HSRP].auth:
                    hsrpv1_plaintext = hsrpv1_packet[0][HSRP].auth
                    simplehsrppass = hsrpv1_plaintext.decode("UTF-8")
                    print(
                        Fore.YELLOW + Style.BRIGHT + "[!] Authentication: " + Fore.WHITE + Style.BRIGHT + "Plaintext Phrase: " + simplehsrppass)
        


# VRRP Scan
def detect_vrrp(interface, timer):
    # This is VRRPv2
    vrrppacket = sniff(filter="ip dst 224.0.0.18 or ip proto 112", count=1, timeout=timer, iface=interface)
    if not vrrppacket:
        return 0
    else:
        print(Fore.WHITE + Style.BRIGHT + '-' * 50)
        print(Fore.WHITE + Style.BRIGHT + "[+] Detected VRRPv2 Protocol")
        if vrrppacket[0].haslayer(AH):
            print(Fore.YELLOW + Style.BRIGHT + "[!] Authentication: " + Fore.WHITE + Style.BRIGHT + "AH")
            print(Fore.YELLOW + Style.BRIGHT + "[*] If this router is running RouterOS and AH is active - at this time, bruteforcing AH hashes from RouterOS is considered impossible")
            print(Fore.YELLOW + Style.BRIGHT + "[*] If it is keepalived, there is no problem with bruteforcing the AH hash")
            print(Fore.YELLOW + Style.BRIGHT + "[+] Skipping...")
            return 0
        vrrppriority = vrrppacket[0][VRRP].priority
        vrrpgroup = vrrppacket[0][VRRP].vrid
        vrrpauthtype = vrrppacket[0][VRRP].authtype
        ipsrcpacket = vrrppacket[0][IP].src
        vrrpmacsender = vrrppacket[0][Ether].src
        vrrpvip = vrrppacket[0][VRRP].addrlist
        # The problem is that usually the configuration does not allow you to set the priority to 255 on the hardware, only 254.
        if vrrppriority <= 255:
            print(
                Fore.YELLOW + Style.BRIGHT + "[*] VRRP Master Vulnerable Priority Value: " + Fore.WHITE + Style.BRIGHT + str(
                    vrrppriority))
            print(Fore.GREEN + Style.BRIGHT + "[*] Impact: " + Fore.YELLOW + Style.BRIGHT + "MITM")
            print(Fore.GREEN + Style.BRIGHT + "[*] Tools: " + Fore.WHITE + Style.BRIGHT + "Scapy, Loki")
        # VRRP Null Auth    
        if vrrpauthtype == 0:
            print(Fore.YELLOW + Style.BRIGHT + "[!] Authentication: " + Fore.WHITE + Style.BRIGHT + "No")
        # VRRP Plaintext Auth    
        if vrrpauthtype == 0x1:
            print(
                Fore.YELLOW + Style.BRIGHT + "[!] Authentication: " + Fore.WHITE + Style.BRIGHT + "Plaintext. Look at the password in Wireshark")
        # VRRP Cryptographic Auth    
        if vrrpauthtype == 254:
            print(Fore.YELLOW + Style.BRIGHT + "[!] Authentication: " + Fore.WHITE + Style.BRIGHT + "MD5")
        print(Fore.GREEN + Style.BRIGHT + "[*] VRRP Virtual IP Address: " + Fore.WHITE + Style.BRIGHT + str(vrrpvip))
        print(Fore.GREEN + Style.BRIGHT + "[*] VRRP Group Number: " + Fore.WHITE + Style.BRIGHT + str(vrrpgroup))
        print(Fore.GREEN + Style.BRIGHT + "[*] VRRP Speaker IP: " + Fore.WHITE + Style.BRIGHT + ipsrcpacket)
        print(Fore.GREEN + Style.BRIGHT + "[*] VRRP Speaker MAC: " + Fore.WHITE + Style.BRIGHT + vrrpmacsender)


# STP Scan
def detect_stp(interface, timer):
    stp_frame = sniff(filter="ether dst 01:80:c2:00:00:00", count=1, timeout=timer, iface=interface)
    if not stp_frame:
        return 0
    print(Fore.WHITE + Style.BRIGHT + '-' * 50)
    print(Fore.WHITE + Style.BRIGHT + "[+] Detected STP Protocol")
    print(Fore.GREEN + Style.BRIGHT + "[*] Impact: " + Fore.YELLOW + Style.BRIGHT + "Partial MITM")
    print(Fore.GREEN + Style.BRIGHT + "[*] Tools: " + Fore.WHITE + Style.BRIGHT + "Yersinia, Scapy")
    stp_root_mac = stp_frame[0][STP].rootmac
    stp_root_id = stp_frame[0][STP].rootid
    stp_root_pathcost = stp_frame[0][STP].pathcost
    print(Fore.GREEN + Style.BRIGHT + "[*] STP Root MAC: " + Fore.WHITE + Style.BRIGHT + str(stp_root_mac))
    print(Fore.GREEN + Style.BRIGHT + "[*] STP Root ID: " + Fore.WHITE + Style.BRIGHT + str(stp_root_id))
    print(Fore.GREEN + Style.BRIGHT + "[*] STP Root Path Cost: " + Fore.WHITE + Style.BRIGHT + str(stp_root_pathcost))


# LLMNR Scan
def detect_llmnr(interface, timer):
    llmnr_packet = sniff(filter="ip dst 224.0.0.252 and udp port 5355", count=1, timeout=timer, iface=interface)
    if not llmnr_packet:
        return 0
    else:
        print(Fore.WHITE + Style.BRIGHT + '-' * 50)
        print(Fore.WHITE + Style.BRIGHT + "[+] Detected LLMNR Protocol")
        print(
            Fore.GREEN + Style.BRIGHT + "[*] Impact: " + Fore.YELLOW + Style.BRIGHT + "LLMNR Spoofing, Credentials interception")
        print(Fore.GREEN + Style.BRIGHT + "[*] Tools: " + Fore.WHITE + Style.BRIGHT + "Responder")
        llmnr_sender_mac = llmnr_packet[0][Ether].src
        llmnr_sender_ip = llmnr_packet[0][IP].src
        print(Fore.GREEN + Style.BRIGHT + "[*] LLMNR Sender IP: " + Fore.WHITE + Style.BRIGHT + str(llmnr_sender_ip))
        print(Fore.GREEN + Style.BRIGHT + "[*] LLMNR Sender MAC: " + Fore.WHITE + Style.BRIGHT + str(llmnr_sender_mac))

# NBT-NS Scan
def detect_nbns(interface, timer):
    nbns_packet = sniff(filter="ether dst ff:ff:ff:ff:ff:ff and udp port 137", count=1, timeout=timer, iface=interface)
    if not nbns_packet:
        return 0
    else:
        print(Fore.WHITE + Style.BRIGHT + '-' * 50)
        print(Fore.WHITE + Style.BRIGHT + "[+] Detected NBT-NS Protocol")
        print(
            Fore.GREEN + Style.BRIGHT + "[*] Impact: " + Fore.YELLOW + Style.BRIGHT + "NBT-NS Spoofing, Credentials interception")
        print(Fore.GREEN + Style.BRIGHT + "[*] Tools: " + Fore.WHITE + Style.BRIGHT + "Responder")
        nbns_packet_mac = nbns_packet[0][Ether].src
        nbns_packet_ip = nbns_packet[0][IP].src
        print(Fore.GREEN + Style.BRIGHT + "[*] NBT-NS Sender IP: " + Fore.WHITE + Style.BRIGHT + str(nbns_packet_ip))
        print(Fore.GREEN + Style.BRIGHT + "[*] NBT-NS Sender MAC: " + Fore.WHITE + Style.BRIGHT + str(nbns_packet_mac))


# MDNS Scan
def detect_mdns(interface, timer):
    mdns_packet = sniff(filter="ip dst 224.0.0.251 and udp port 5353", count=1, timeout=timer, iface=interface)
    if not mdns_packet:
        return 0
    else:
        print(Fore.WHITE + Style.BRIGHT + '-' * 50)
        print(Fore.WHITE + Style.BRIGHT + "[+] Detected MDNS Protocol")
        print(
            Fore.GREEN + Style.BRIGHT + "[*] Impact: " + Fore.YELLOW + Style.BRIGHT + "MDNS Spoofing, Credentials interception")
        print(Fore.GREEN + Style.BRIGHT + "[*] Tools: " + Fore.WHITE + Style.BRIGHT + "Responder")
        mdns_packet_mac = mdns_packet[0][Ether].src
        mdns_packet_ip = mdns_packet[0][IP].src
        print(Fore.GREEN + Style.BRIGHT + "[*] MDNS Sender IP: " + Fore.WHITE + Style.BRIGHT + str(mdns_packet_ip))
        print(Fore.GREEN + Style.BRIGHT + "[*] MDNS Sender MAC: " + Fore.WHITE + Style.BRIGHT + str(mdns_packet_mac))


# DHCPv6 Scan
def detect_dhcpv6(interface, timer):
    dhcpv6_packet = sniff(filter="udp and port 546 and port 547", count=1, iface=interface, timeout=timer)
    if not dhcpv6_packet:
        return 0
    else:
        print(Fore.WHITE + Style.BRIGHT + '-' * 50)
        print(Fore.WHITE + Style.BRIGHT + "[+] Detected DHCPv6 Protocol")
        print(Fore.GREEN + Style.BRIGHT + "[*] Impact: " + Fore.YELLOW + Style.BRIGHT + "DNS IPv6 Spoofing")
        print(Fore.GREEN + Style.BRIGHT + "[*] Tools: " + Fore.WHITE + Style.BRIGHT + "mitm6")
        dhcpv6_mac_address_sender = dhcpv6_packet[0][Ether].src
        dhcpv6_packet_sender = dhcpv6_packet[0][IPv6].src
        print(Fore.GREEN + Style.BRIGHT + "[*] DHCPv6 Sender IP: " + Fore.WHITE + Style.BRIGHT + dhcpv6_packet_sender)
        print(
            Fore.GREEN + Style.BRIGHT + "[*] DHCPv6 Sender MAC: " + Fore.WHITE + Style.BRIGHT + dhcpv6_mac_address_sender)


exit_flag = False


# To interrupt the code by pressing CTRL + C
def signal_handler(sig, frame):
    global exit_flag
    print("\n[!] Sniffing interrupted. Exiting...")
    exit_flag = True
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


# Main func, arguments processing, threads processing
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--interface", dest="interface", type=str, required=True, help="Specify the interface")
    parser.add_argument("--timer", dest="timer", type=int, required=True, help="Specify the timer value (seconds)")

    args = parser.parse_args()
    if args.interface and args.timer:
        print(Fore.WHITE + Style.BRIGHT + "\n[+] Start Sniffing...")
        print(Fore.WHITE + Style.BRIGHT + "\n[+] Searching for L2/L3 Protocols...")
        print(Fore.WHITE + Style.BRIGHT + "[*] The specified timer applies to all protocols")
        print(
            Fore.GREEN + Style.BRIGHT + "[*] After the protocol is detected - all necessary information about it will be displayed")

    cdp_thread = threading.Thread(target=detect_ciscoprotocols, args=(args.interface, args.timer))
    dot1q_thread = threading.Thread(target=vlan_sniffer, args=(args.interface, args.timer))
    ospf_thread = threading.Thread(target=detect_ospf, args=(args.interface, args.timer))
    eigrp_thread = threading.Thread(target=detect_eigrp, args=(args.interface, args.timer))
    hsrp_thread = threading.Thread(target=detect_hsrp, args=(args.interface, args.timer))
    vrrp_thread = threading.Thread(target=detect_vrrp, args=(args.interface, args.timer))
    stp_thread = threading.Thread(target=detect_stp, args=(args.interface, args.timer))
    llmnr_thread = threading.Thread(target=detect_llmnr, args=(args.interface, args.timer))
    nbns_thread = threading.Thread(target=detect_nbns, args=(args.interface, args.timer))
    mdns_thread = threading.Thread(target=detect_mdns, args=(args.interface, args.timer))
    dhcpv6_thread = threading.Thread(target=detect_dhcpv6, args=(args.interface, args.timer))

    cdp_thread.daemon = True
    dot1q_thread.daemon = True
    ospf_thread.daemon = True
    eigrp_thread.daemon = True
    hsrp_thread.daemon = True
    vrrp_thread.daemon = True
    stp_thread.daemon = True
    llmnr_thread.daemon = True
    nbns_thread.daemon = True
    mdns_thread.daemon = True
    dhcpv6_thread.daemon = True

    cdp_thread.start()
    dot1q_thread.start()
    ospf_thread.start()
    eigrp_thread.start()
    hsrp_thread.start()
    vrrp_thread.start()
    stp_thread.start()
    llmnr_thread.start()
    nbns_thread.start()
    mdns_thread.start()
    dhcpv6_thread.start()

    cdp_thread.join()
    dot1q_thread.join()
    ospf_thread.join()
    eigrp_thread.join()
    hsrp_thread.join()
    vrrp_thread.join()
    stp_thread.join()
    llmnr_thread.join()
    nbns_thread.join()
    mdns_thread.join()
    dhcpv6_thread.join()


if __name__ == "__main__":
    main()