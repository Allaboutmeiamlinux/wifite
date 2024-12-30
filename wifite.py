import pywifi
from pywifi import const
import time
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.spinner import Spinner
from rich.prompt import Prompt
import shutil

console = Console()

# Wi-Fi ASCII Art Banner
ASCII_ART = r"""
     █                    ██    
   ███                    ███   
   ██   ██  MR linux   █   ███  
  ██   ██   ████████   ███  ██  
 ███  ██  ███      ███  ██  ███ 
 ██   ██  ██        ██  ███  ██ 
 ██   ██  ██        ██  ███  ██ 
  ██  ██  ███      ███  ██  ███ 
  ██   ██   ████████   ██   ██  
   ██   █      ██      █   ███  
   ███         ██         ███   
     █         ██         █     
               ██               
               ██               
               ██               
"""

def get_encryption_type(network):
    """Returns the encryption type of the network."""
    if const.AKM_TYPE_NONE in network.akm:
        return "None"
    elif const.AKM_TYPE_WPA in network.akm:
        return "WPA"
    elif const.AKM_TYPE_WPA2 in network.akm:
        return "WPA2"
    else:
        return "Unknown"

def scan_wifi():
    """Scans available Wi-Fi networks and returns a generator of network details."""
    wifi = pywifi.PyWiFi()
    iface = wifi.interfaces()[0]
    iface.scan()
    time.sleep(2)  # Allow some time for scanning
    scan_results = iface.scan_results()

    for network in scan_results:
        ssid = network.ssid
        bssid = network.bssid
        signal = network.signal
        frequency = network.freq
        channel = int((frequency - 2407) / 5) if frequency < 2500 else int((frequency - 5000) / 5)
        security = "Open" if network.akm[0] == const.AKM_TYPE_NONE else "Secured"
        encryption = get_encryption_type(network)
        yield {
            "SSID": ssid,
            "BSSID": bssid,
            "Signal": signal,
            "Frequency": f"{frequency} MHz",
            "Channel": str(channel),
            "Security": security,
            "Encryption": encryption
        }

def update_table(networks):
    """Creates a live-updating table."""
    table = Table(title="Wi-Fi Networks", style="bold cyan")
    table.add_column("No.", style="bold white")
    table.add_column("SSID", style="green")
    table.add_column("BSSID", style="cyan")
    table.add_column("Signal Strength", style="yellow")
    table.add_column("Frequency", style="blue")
    table.add_column("Channel", style="magenta")
    table.add_column("Security", style="red")
    table.add_column("Encryption", style="white")

    for i, network in enumerate(networks):
        table.add_row(
            str(i + 1),
            network["SSID"],
            network["BSSID"],
            str(network["Signal"]),
            network["Frequency"],
            network["Channel"],
            network["Security"],
            network["Encryption"]
        )
    return table

def export_results(networks):
    """Exports network details to a file."""
    console.print("[bold cyan]Choose export format: 1) CSV, 2) JSON[/bold cyan]")
    choice = Prompt.ask("[bold green]Enter your choice[/bold green]", choices=["1", "2"], default="1")
    filename = Prompt.ask("[bold yellow]Enter the filename (without extension)[/bold yellow]")

    if choice == "1":
        filepath = f"{filename}.csv"
        with open(filepath, "w") as file:
            file.write("SSID,BSSID,Signal,Frequency,Channel,Security,Encryption\n")
            for network in networks:
                file.write(
                    f"{network['SSID']},{network['BSSID']},{network['Signal']},{network['Frequency']}," 
                    f"{network['Channel']},{network['Security']},{network['Encryption']}\n"
                )
    elif choice == "2":
        import json
        filepath = f"{filename}.json"
        with open(filepath, "w") as file:
            json.dump(networks, file, indent=4)
    
    console.print(f"[bold green]Exported results to {filepath}[/bold green]")

def center_text(text):
    """Centers text in the console based on the terminal width."""
    terminal_width = shutil.get_terminal_size((80, 20)).columns
    return text.center(terminal_width)

def main():
    # Center the ASCII art
    centered_ascii_art = center_text(ASCII_ART)

    console.print(centered_ascii_art, style="cyan")
    console.print("[bold blue]Press Ctrl+C to exit the tool.[/bold blue]\n")
    networks = []

    try:
        with Live(Spinner("dots", text="Scanning for networks..."), refresh_per_second=10) as live:
            while True:
                new_networks = list(scan_wifi())
                filtered_networks = [net for net in new_networks if net["Signal"] > -80]  # Strong signal filter
                
                # Only add new networks if they aren't already in the list
                for network in filtered_networks:
                    if network not in networks:
                        networks.append(network)

                live.update(update_table(networks))
                time.sleep(1)  # Perform the scan more frequently
    except KeyboardInterrupt:
        console.print("\n[bold magenta]Exiting Enhanced Wi-Fi Scanner Tool. Goodbye![/bold magenta]\n")
        export_choice = Prompt.ask("[bold yellow]Do you want to export the results?[/bold yellow] (y/n)", choices=["y", "n"])
        if export_choice == "y":
            export_results(networks)

if __name__ == "__main__":
    main()
