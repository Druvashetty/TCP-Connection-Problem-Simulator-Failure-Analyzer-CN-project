# simulation.py - TCP State Machine, Failure Engine & Smart Diagnosis Logic
import time

class TCPSimulator:
    """
    Simulates TCP 3-Way Handshake scenarios and provides 
    rule-based smart diagnostics for network failures.
    """

    SCENARIOS = {
        "normal": "Normal 3-Way Handshake (SYN -> SYN-ACK -> ACK)",
        "syn_lost": "SYN Packet Lost in Transit (Client Timeout)",
        "syn_ack_lost": "SYN-ACK Packet Lost in Transit (Server Waiting / Timeout)",
        "server_not_responding": "Server Not Responding (Unresponsive Service / Silent Drop)",
        "tcp_rst": "TCP Connection Reset (RST Flag Returned / Port Closed)"
    }

    @staticmethod
    def run_simulation(scenario_key):
        """Executes the selected scenario and returns timeline, stats, and diagnosis."""
        if scenario_key not in TCPSimulator.SCENARIOS:
            scenario_key = "normal"

        events = []
        stats = {
            "total_sent": 0,
            "total_received": 0,
            "total_dropped": 0,
            "retransmissions": 0,
            "duration_ms": 0,
            "packet_loss_rate": 0.0,
            "status": "FAILED"
        }

        # Select simulation scenario
        if scenario_key == "normal":
            events, stats = TCPSimulator._sim_normal()
        elif scenario_key == "syn_lost":
            events, stats = TCPSimulator._sim_syn_lost()
        elif scenario_key == "syn_ack_lost":
            events, stats = TCPSimulator._sim_syn_ack_lost()
        elif scenario_key == "server_not_responding":
            events, stats = TCPSimulator._sim_server_not_responding()
        elif scenario_key == "tcp_rst":
            events, stats = TCPSimulator._sim_tcp_rst()

        # Rule-based failure diagnosis
        diagnosis = TCPSimulator._diagnose_failure(scenario_key, events, stats)

        # Baseline comparison
        comparison = TCPSimulator._generate_comparison(scenario_key, stats)

        return {
            "scenario_key": scenario_key,
            "scenario_name": TCPSimulator.SCENARIOS[scenario_key],
            "status": stats["status"],
            "events": events,
            "statistics": stats,
            "diagnosis": diagnosis,
            "comparison": comparison
        }

    # -------------------------------------------------------------------------
    # SCENARIO SIMULATION FLOWS
    # -------------------------------------------------------------------------
    @staticmethod
    def _sim_normal():
        """Successful 3-way handshake: SYN -> SYN-ACK -> ACK."""
        events = [
            {
                "step": 1,
                "timestamp": "0.00s",
                "from_host": "Computer A",
                "to_host": "Computer B",
                "packet_type": "SYN",
                "seq_no": 100,
                "ack_no": 0,
                "flags": ["SYN"],
                "status": "DELIVERED",
                "state_a": "SYN_SENT",
                "state_b": "LISTEN",
                "description": "Computer A initiates connection by sending SYN (Seq=100)."
            },
            {
                "step": 2,
                "timestamp": "0.15s",
                "from_host": "Computer B",
                "to_host": "Computer A",
                "packet_type": "SYN-ACK",
                "seq_no": 300,
                "ack_no": 101,
                "flags": ["SYN", "ACK"],
                "status": "DELIVERED",
                "state_a": "SYN_SENT",
                "state_b": "SYN_RCVD",
                "description": "Computer B acknowledges SYN and responds with SYN-ACK (Seq=300, Ack=101)."
            },
            {
                "step": 3,
                "timestamp": "0.30s",
                "from_host": "Computer A",
                "to_host": "Computer B",
                "packet_type": "ACK",
                "seq_no": 101,
                "ack_no": 301,
                "flags": ["ACK"],
                "status": "DELIVERED",
                "state_a": "ESTABLISHED",
                "state_b": "ESTABLISHED",
                "description": "Computer A sends ACK (Seq=101, Ack=301). Connection successfully ESTABLISHED!"
            }
        ]
        stats = {
            "total_sent": 3,
            "total_received": 3,
            "total_dropped": 0,
            "retransmissions": 0,
            "duration_ms": 300,
            "packet_loss_rate": 0.0,
            "status": "ESTABLISHED"
        }
        return events, stats

    @staticmethod
    def _sim_syn_lost():
        """SYN packet lost in network transit."""
        events = [
            {
                "step": 1,
                "timestamp": "0.00s",
                "from_host": "Computer A",
                "to_host": "Computer B",
                "packet_type": "SYN",
                "seq_no": 100,
                "ack_no": 0,
                "flags": ["SYN"],
                "status": "DROPPED",
                "state_a": "SYN_SENT",
                "state_b": "LISTEN",
                "description": "Computer A sends SYN packet (Seq=100), but packet is dropped in network transit."
            },
            {
                "step": 2,
                "timestamp": "1.00s",
                "from_host": "Computer A",
                "to_host": "Computer A",
                "packet_type": "TIMEOUT",
                "seq_no": 100,
                "ack_no": 0,
                "flags": [],
                "status": "EXPIRED",
                "state_a": "SYN_SENT",
                "state_b": "LISTEN",
                "description": "Retransmission Timeout (RTO) timer expires on Computer A waiting for SYN-ACK."
            },
            {
                "step": 3,
                "timestamp": "1.05s",
                "from_host": "Computer A",
                "to_host": "Computer B",
                "packet_type": "SYN (Retransmission #1)",
                "seq_no": 100,
                "ack_no": 0,
                "flags": ["SYN"],
                "status": "DROPPED",
                "state_a": "SYN_SENT",
                "state_b": "LISTEN",
                "description": "Computer A retransmits SYN (Seq=100), but packet is dropped again."
            },
            {
                "step": 4,
                "timestamp": "3.00s",
                "from_host": "Computer A",
                "to_host": "Computer A",
                "packet_type": "ABORT",
                "seq_no": 100,
                "ack_no": 0,
                "flags": [],
                "status": "CLOSED",
                "state_a": "CLOSED",
                "state_b": "LISTEN",
                "description": "Max SYN retransmissions reached. Connection attempt aborted by client (ETIMEDOUT)."
            }
        ]
        stats = {
            "total_sent": 2,
            "total_received": 0,
            "total_dropped": 2,
            "retransmissions": 1,
            "duration_ms": 3000,
            "packet_loss_rate": 100.0,
            "status": "TIMED_OUT"
        }
        return events, stats

    @staticmethod
    def _sim_syn_ack_lost():
        """SYN-ACK packet lost in transit on return flight."""
        events = [
            {
                "step": 1,
                "timestamp": "0.00s",
                "from_host": "Computer A",
                "to_host": "Computer B",
                "packet_type": "SYN",
                "seq_no": 100,
                "ack_no": 0,
                "flags": ["SYN"],
                "status": "DELIVERED",
                "state_a": "SYN_SENT",
                "state_b": "LISTEN",
                "description": "Computer A sends SYN packet (Seq=100). Received by Computer B."
            },
            {
                "step": 2,
                "timestamp": "0.15s",
                "from_host": "Computer B",
                "to_host": "Computer A",
                "packet_type": "SYN-ACK",
                "seq_no": 300,
                "ack_no": 101,
                "flags": ["SYN", "ACK"],
                "status": "DROPPED",
                "state_a": "SYN_SENT",
                "state_b": "SYN_RCVD",
                "description": "Computer B sends SYN-ACK (Seq=300, Ack=101), but it gets dropped in transit."
            },
            {
                "step": 3,
                "timestamp": "1.15s",
                "from_host": "Computer A",
                "to_host": "Computer A",
                "packet_type": "TIMEOUT",
                "seq_no": 100,
                "ack_no": 0,
                "flags": [],
                "status": "EXPIRED",
                "state_a": "SYN_SENT",
                "state_b": "SYN_RCVD",
                "description": "Computer A timer expires waiting for SYN-ACK. Computer B stays in SYN_RCVD."
            },
            {
                "step": 4,
                "timestamp": "3.15s",
                "from_host": "Computer B",
                "to_host": "Computer B",
                "packet_type": "TIMEOUT / RST",
                "seq_no": 300,
                "ack_no": 0,
                "flags": ["RST"],
                "status": "CLOSED",
                "state_a": "CLOSED",
                "state_b": "CLOSED",
                "description": "Half-open connection cleanup timer expires. Both hosts reset connection to CLOSED."
            }
        ]
        stats = {
            "total_sent": 2,
            "total_received": 1,
            "total_dropped": 1,
            "retransmissions": 0,
            "duration_ms": 3150,
            "packet_loss_rate": 50.0,
            "status": "SYN_ACK_LOST"
        }
        return events, stats

    @staticmethod
    def _sim_server_not_responding():
        """Server ignores SYN or port is blackholed."""
        events = [
            {
                "step": 1,
                "timestamp": "0.00s",
                "from_host": "Computer A",
                "to_host": "Computer B",
                "packet_type": "SYN",
                "seq_no": 100,
                "ack_no": 0,
                "flags": ["SYN"],
                "status": "DELIVERED",
                "state_a": "SYN_SENT",
                "state_b": "LISTEN",
                "description": "Computer A sends SYN packet to Computer B on Port 8080."
            },
            {
                "step": 2,
                "timestamp": "0.10s",
                "from_host": "Computer B",
                "to_host": "Computer B",
                "packet_type": "IGNORED",
                "seq_no": 0,
                "ack_no": 0,
                "flags": [],
                "status": "IGNORED",
                "state_a": "SYN_SENT",
                "state_b": "LISTEN",
                "description": "Computer B received SYN, but server service is frozen or dropping traffic. No reply sent."
            },
            {
                "step": 3,
                "timestamp": "1.00s",
                "from_host": "Computer A",
                "to_host": "Computer B",
                "packet_type": "SYN (Retransmission #1)",
                "seq_no": 100,
                "ack_no": 0,
                "flags": ["SYN"],
                "status": "DELIVERED",
                "state_a": "SYN_SENT",
                "state_b": "LISTEN",
                "description": "Computer A retransmits SYN. Computer B continues to ignore packet."
            },
            {
                "step": 4,
                "timestamp": "3.00s",
                "from_host": "Computer A",
                "to_host": "Computer A",
                "packet_type": "ABORT",
                "seq_no": 100,
                "ack_no": 0,
                "flags": [],
                "status": "CLOSED",
                "state_a": "CLOSED",
                "state_b": "LISTEN",
                "description": "Connection attempt times out on Computer A (Connection Refused / Silent Drop)."
            }
        ]
        stats = {
            "total_sent": 2,
            "total_received": 2,
            "total_dropped": 0,
            "retransmissions": 1,
            "duration_ms": 3000,
            "packet_loss_rate": 0.0,
            "status": "SERVER_UNRESPONSIVE"
        }
        return events, stats

    @staticmethod
    def _sim_tcp_rst():
        """Target port closed; server sends TCP RST flag."""
        events = [
            {
                "step": 1,
                "timestamp": "0.00s",
                "from_host": "Computer A",
                "to_host": "Computer B",
                "packet_type": "SYN",
                "seq_no": 100,
                "ack_no": 0,
                "flags": ["SYN"],
                "status": "DELIVERED",
                "state_a": "SYN_SENT",
                "state_b": "CLOSED",
                "description": "Computer A sends SYN packet to Computer B on a closed target port."
            },
            {
                "step": 2,
                "timestamp": "0.10s",
                "from_host": "Computer B",
                "to_host": "Computer A",
                "packet_type": "RST",
                "seq_no": 0,
                "ack_no": 101,
                "flags": ["RST", "ACK"],
                "status": "DELIVERED",
                "state_a": "SYN_SENT",
                "state_b": "CLOSED",
                "description": "Computer B OS has no process listening on port and responds with TCP RST."
            },
            {
                "step": 3,
                "timestamp": "0.12s",
                "from_host": "Computer A",
                "to_host": "Computer A",
                "packet_type": "RESET_RECEIVED",
                "seq_no": 0,
                "ack_no": 101,
                "flags": ["RST"],
                "status": "CLOSED",
                "state_a": "CLOSED",
                "state_b": "CLOSED",
                "description": "Computer A receives RST packet and immediately resets connection (ECONNREFUSED)."
            }
        ]
        stats = {
            "total_sent": 2,
            "total_received": 2,
            "total_dropped": 0,
            "retransmissions": 0,
            "duration_ms": 120,
            "packet_loss_rate": 0.0,
            "status": "CONNECTION_RESET"
        }
        return events, stats

    # -------------------------------------------------------------------------
    # SMART DIAGNOSIS ENGINE
    # -------------------------------------------------------------------------
    @staticmethod
    def _diagnose_failure(scenario_key, events, stats):
        """Python rule-based logic to analyze failure evidence and suggest fixes."""
        if scenario_key == "normal":
            return {
                "failure_point": "None (Connection Successful)",
                "observed_evidence": [
                    "SYN packet sent and acknowledged.",
                    "SYN-ACK received with matching ACK sequence number.",
                    "Final ACK sent successfully.",
                    "Both endpoints transitioned to ESTABLISHED state."
                ],
                "possible_causes": ["Network operating normally with nominal round-trip latency."],
                "troubleshooting_steps": ["No repair necessary. Connection is fully functional."]
            }

        elif scenario_key == "syn_lost":
            return {
                "failure_point": "Outbound Path / Local Network Infrastructure",
                "observed_evidence": [
                    "SYN packet dispatched by Computer A.",
                    "SYN packet dropped before reaching Computer B.",
                    "Computer A RTO timer expired without SYN-ACK receipt.",
                    "Retransmission attempts failed."
                ],
                "possible_causes": [
                    "Outbound local firewall blocking TCP SYN packets.",
                    "Physical Wi-Fi / Ethernet link drop or signal degradation.",
                    "Misconfigured router default gateway or ARP resolution issue."
                ],
                "troubleshooting_steps": [
                    "Run 'ping <Computer_B_IP>' to verify Layer 3 connectivity.",
                    "Check Windows Defender Firewall outbound rules for TCP port blocking.",
                    "Use 'tracert <Computer_B_IP>' to locate intermediate router drops.",
                    "Verify physical Ethernet cable or Wi-Fi interface status."
                ]
            }

        elif scenario_key == "syn_ack_lost":
            return {
                "failure_point": "Inbound Return Path / Server Local Firewall",
                "observed_evidence": [
                    "Computer A SYN packet reached Computer B successfully.",
                    "Computer B transitioned to SYN_RCVD and sent SYN-ACK.",
                    "SYN-ACK packet dropped in transit during return flight.",
                    "Half-open connection created on Computer B."
                ],
                "possible_causes": [
                    "Computer A inbound firewall blocking incoming SYN-ACK responses.",
                    "Asymmetric network routing dropping return path traffic.",
                    "Network Address Translation (NAT) router table timeout."
                ],
                "troubleshooting_steps": [
                    "Check Computer A inbound firewall rules for returning TCP traffic.",
                    "Examine router NAT state tables for TCP tracking.",
                    "Run packet capture on Computer B to confirm SYN-ACK egress."
                ]
            }

        elif scenario_key == "server_not_responding":
            return {
                "failure_point": "Target Server Application / Socket Layer",
                "observed_evidence": [
                    "Computer A SYN packet arrived at Computer B host OS.",
                    "Computer B OS acknowledged receipt, but no server response was generated.",
                    "Computer A timed out after max SYN retransmissions."
                ],
                "possible_causes": [
                    "Server application process crashed, hung, or overloaded.",
                    "Server firewall configured to silently drop (blackhole) incoming TCP traffic.",
                    "Socket backlog queue full (SYN flooding protection activated)."
                ],
                "troubleshooting_steps": [
                    "Verify target service status on Computer B.",
                    "Check if application process is bound to correct IP interface (0.0.0.0 vs 127.0.0.1).",
                    "Run 'netstat -an | findstr LISTEN' on Computer B to confirm port state."
                ]
            }

        elif scenario_key == "tcp_rst":
            return {
                "failure_point": "Target Host Port / OS Protocol Stack",
                "observed_evidence": [
                    "SYN packet successfully delivered to Computer B.",
                    "Computer B OS immediately replied with TCP RST/ACK packet.",
                    "Computer A connection terminated with Connection Refused error."
                ],
                "possible_causes": [
                    "No application process is actively listening on target port.",
                    "Firewall rule actively rejecting (RST) traffic.",
                    "Connection attempt made before server process completed startup."
                ],
                "troubleshooting_steps": [
                    "Confirm target service port number on Computer A.",
                    "Start or restart server application on Computer B.",
                    "Run 'Test-NetConnection -ComputerName <IP> -Port <Port>' in PowerShell."
                ]
            }

    @staticmethod
    def _generate_comparison(scenario_key, stats):
        """Generates side-by-side comparison with baseline."""
        baseline_ms = 300
        return {
            "current_scenario": scenario_key,
            "baseline_duration_ms": baseline_ms,
            "current_duration_ms": stats["duration_ms"],
            "duration_diff_ms": stats["duration_ms"] - baseline_ms,
            "baseline_loss": 0.0,
            "current_loss": stats["packet_loss_rate"],
            "status_comparison": f"Normal: ESTABLISHED vs Current: {stats['status']}"
        }

    # -------------------------------------------------------------------------
    # DOWNLOADABLE TEXT REPORT GENERATOR
    # -------------------------------------------------------------------------
    @staticmethod
    def generate_text_report(sim_data):
        """Formats simulation results into a clean text report."""
        scenario_name = sim_data.get("scenario_name", "Unknown Scenario")
        status = sim_data.get("status", "N/A")
        stats = sim_data.get("statistics", {})
        diag = sim_data.get("diagnosis", {})
        events = sim_data.get("events", [])

        report = []
        report.append("================================================================================")
        report.append("               TCP CONNECTION PROBLEM SIMULATOR & FAILURE ANALYZER               ")
        report.append("                                DIAGNOSTIC REPORT                               ")
        report.append("================================================================================")
        report.append(f"Timestamp          : {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Selected Scenario  : {scenario_name}")
        report.append(f"Connection Status  : {status}")
        report.append("--------------------------------------------------------------------------------\n")

        report.append("1. PACKET TRANSMISSION STATISTICS")
        report.append("---------------------------------")
        report.append(f" Total Packets Sent     : {stats.get('total_sent', 0)}")
        report.append(f" Total Packets Received : {stats.get('total_received', 0)}")
        report.append(f" Total Packets Dropped  : {stats.get('total_dropped', 0)}")
        report.append(f" SYN Retransmissions    : {stats.get('retransmissions', 0)}")
        report.append(f" Packet Loss Rate       : {stats.get('packet_loss_rate', 0.0)}%")
        report.append(f" Simulation Duration    : {stats.get('duration_ms', 0)} ms\n")

        report.append("2. EVENT TIMELINE LOG")
        report.append("---------------------")
        for ev in events:
            report.append(
                f" [{ev.get('timestamp')}] {ev.get('from_host')} -> {ev.get('to_host')} | "
                f"Type: {ev.get('packet_type')} | Status: {ev.get('status')} | "
                f"State A: {ev.get('state_a')}, State B: {ev.get('state_b')}"
            )
            report.append(f"   Details: {ev.get('description')}\n")

        report.append("3. SMART FAILURE DIAGNOSIS")
        report.append("---------------------------")
        report.append(f" Primary Failure Point : {diag.get('failure_point', 'N/A')}\n")

        report.append(" Observed Evidence:")
        for evd in diag.get("observed_evidence", []):
            report.append(f"  - {evd}")
        report.append("")

        report.append(" Possible Real-World Causes:")
        for cause in diag.get("possible_causes", []):
            report.append(f"  - {cause}")
        report.append("")

        report.append(" Suggested Troubleshooting Actions:")
        for step in diag.get("troubleshooting_steps", []):
            report.append(f"  - {step}")
        report.append("")

        report.append("================================================================================")
        report.append("                            END OF DIAGNOSTIC REPORT                            ")
        report.append("================================================================================")

        return "\n".join(report)

