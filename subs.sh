#!/usr/bin/env bash

# Function to display usage message
display_usage() {
    echo "Usage:"
    echo "     $0 -d http://example.com"
    echo ""
    echo "Options:"
    echo "  -h               Display this help message"
    echo "  -d               Sub domain finding"
    echo "  -dl              Mass Sub domain finding"
    echo "  -ls              See source list"
    echo "  -i               Check if required tools are installed"
    echo ""
    echo "Required Tools:"
    echo "              https://github.com/projectdiscovery/subfinder
              https://github.com/tomnomnom/anew
              https://github.com/aboul3la/Sublist3r
              https://github.com/projectdiscovery/httpx"
    exit 0
}

# Function to check installed tools
check_tools() {
    tools=("subfinder" "sublist3r" "httpx" "anew")

    echo "Checking required tools:"
    for tool in "${tools[@]}"; do
        if command -v "$tool" &> /dev/null; then
            echo "$tool is installed at $(which $tool)"
        else
            echo "$tool is NOT installed or not in the PATH"
        fi
    done
}


# Check if help is requested
if [[ "$1" == "-h" ]]; then
    display_usage
    exit 0
fi

# Check if tool installation check is requested
if [[ "$1" == "-i" ]]; then
    check_tools
    exit 0
fi


if [[ "$1" == "-d" ]]; then
    domain_Without_Protocol=$(echo "$2" | sed 's,http://,,;s,https://,,;s,www\.,,')

    mkdir -p bug_bounty_report/$domain_Without_Protocol/subdomains/
    subfinder -d "$domain_Without_Protocol" -all -recursive -o bug_bounty_report/$domain_Without_Protocol/subdomains/subfinder.subdomains.txt

    sublist3r -d "$domain_Without_Protocol" -o bug_bounty_report/$domain_Without_Protocol/subdomains/sublist3r.subdomains.txt

    echo """    =========================== Subfinder, sublist3r finished ==================
    ============================================================================"""

    cat bug_bounty_report/$domain_Without_Protocol/subdomains/subfinder.subdomains.txt bug_bounty_report/$domain_Without_Protocol/subdomains/sublist3r.subdomains.txt | anew bug_bounty_report/$domain_Without_Protocol/subdomains/all.subdomains.txt
    echo ""
    echo "Unique subdomains:"
    cat bug_bounty_report/$domain_Without_Protocol/subdomains/all.subdomains.txt | wc -l

    httpx -list bug_bounty_report/$domain_Without_Protocol/subdomains/all.subdomains.txt -mc 200 -o bug_bounty_report/$domain_Without_Protocol/subdomains/alive.subdomains.txt
    echo ""
    echo "Alive subdomains:"
    cat bug_bounty_report/$domain_Without_Protocol/subdomains/alive.subdomains.txt | wc -l

    exit 0
fi


if [[ "$1" == "-dl" ]]; then
    domain_Without_Protocol=$(echo "$2" | sed 's,http://,,;s,https://,,;s,www\.,,')
    # domain_Without_Protocol=$2

    mkdir -p bug_bounty_report/$domain_Without_Protocol/subdomains/
    subfinder -dL "$domain_Without_Protocol" -all -recursive -o bug_bounty_report/$domain_Without_Protocol/subdomains/mass.subfinder.subdomains.txt

    echo """    =========================== Subfinder finished =========================
    ============================================================================"""

    httpx -list bug_bounty_report/$domain_Without_Protocol/subdomains/mass.subfinder.subdomains.txt -mc 200 -o bug_bounty_report/$domain_Without_Protocol/subdomains/mass.alive.subdomains.txt
    echo ""
    echo "Alive subdomains:"
    cat bug_bounty_report/$domain_Without_Protocol/subdomains/mass.alive.subdomains.txt | wc -l

    exit 0
fi




if [[ "$1" == "-ls" ]]; then
    subfinder -ls -silent
    echo """    =========================== sublist3r source list ==========================
    ============================================================================"""
    echo """Baidu..
Yahoo..
Google..
Bing..
Ask..
Netcraft..
DNSdumpster..
Virustotal..
ThreatCrowd..
SSL Certificates..
PassiveDNS..
"""
    exit 0
fi
