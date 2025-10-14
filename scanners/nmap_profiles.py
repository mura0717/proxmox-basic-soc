#!/usr/bin/env python3
"""
Nmap Scan Profiles
This file contains the configuration for different Nmap scan profiles.
"""

SCAN_PROFILES = {
    # LEVEL 1: Discovery (No root, fastest)
    'discovery': {
        'args': '-sn -PR -T4',
        'use_dns': True,
        'collects_ports': False,
        'description': 'Fast ping sweep with MAC - finds live hosts',
        'frequency': 'hourly',
        'timeout': 300  # 5 minutes
    },

    # LEVEL 2: Quick Check (Basic ports)
    'quick': {
        'args': '-sS --top-ports 100 -T5 --open -PR',
        'use_dns': True,
        'collects_ports': True,
        'description': 'Quick port check - top 100 ports only',
        'frequency': 'daily',
        'timeout': 600  # 10 minutes
    },

    # LEVEL 3: Basic Inventory (Standard scan)
    'inventory': {
        'args': '-sS -O --osscan-limit --top-ports 20 -T4 --open -PR',
        'use_dns': True,
        'collects_ports': True,
        'description': 'Lightweight inventory - gets MAC, OS, and top 20 ports',
        'frequency': 'hourly',
        'timeout': 600  # 10 minutes
    },

    'basic': {
        'args': '-sS -sV --top-ports 1000 -T4',
        'use_dns': False,
        'collects_ports': True,
        'description': 'Basic service detection - top 1000 ports',
        'frequency': 'daily_offhours',
        'timeout': 1800  # 30 minutes
    },

    # LEVEL 4: Detailed Inventory (With OS detection)
    'detailed': {
        'args': '-sS -sV -O --osscan-guess --top-ports 1000 -T4',
        'use_dns': False,
        'collects_ports': True,
        'description': 'Service + OS detection',
        'frequency': 'weekly',
        'timeout': 3600  # 1 hour
    },

    # LEVEL 5: Vulnerability Scan
    'vulnerability': {
        'args': '-sS -sV --script vuln,exploit -T3',
        'use_dns': False,
        'collects_ports': True,
        'description': 'Security vulnerability detection',
        'frequency': 'weekly_weekend',
        'timeout': 7200  # 2 hours
    },

    # LEVEL 6: Full Audit (Comprehensive)
    'full': {
        'args': '-sS -sV -O -A --script default,discovery -p- -T4',
        'use_dns': False,
        'collects_ports': True,
        'description': 'Complete port and service audit - ALL ports',
        'frequency': 'monthly',
        'timeout': 14400  # 4 hours
    },

    # SPECIAL: Web Applications
    'web': {
        'args': '-sV -p80,443,8080,8443 --script http-enum,http-title',
        'use_dns': True,
        'collects_ports': True,
        'description': 'Web application discovery',
        'frequency': 'daily',
        'timeout': 900  # 15 minutes
    },

    # SPECIAL: Network Devices (SNMP/SSH)
    'network': {
        'args': '-sU -sS -p161,22,23 --script snmp-info',
        'use_dns': True,
        'collects_ports': True,
        'description': 'Network device identification',
        'frequency': 'daily',
        'timeout': 1200  # 20 minutes
    }
}