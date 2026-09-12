# uCore-Network Specification (2026)

Status: Active Specification  
Date: 12 September 2026  
Authority: uCore Ecosystem Architecture  
Lanes Replaced: Former Portal / Beacon / MeshCore research  

---

## 1. Mission and Boundaries

`uCore-Network` provides local-first networking, private communication, and network-level security for the uDos ecosystem. It grounds previously speculative "Beacon/Mesh" ideas in mature, deployable technology:

1. **Local Content Portals**: Serving compiled markdown editions, document libraries, and Kiwix ZIM collections over the home LAN without internet connectivity.
2. **BitChat P2P**: Zero-cloud, local-first chat over WebSockets and mDNS for household members and LAN peers, with direct export into uDos project Binders.
3. **Network-Level Privacy & Defense**:
   - Network-wide ad, tracker, and telemetry blocking via **AdGuard Home** / **Pi-hole**.
   - Encrypted DNS-over-HTTPS (DoH) upstream resolution via privacy-focused providers (**Quad9**, **Mullvad**).
   - Secure, zero-trust remote mesh access via **WireGuard** / **Tailscale** (**Headscale** / **NetBird**) without opening firewall ports.
   - Router-level guest network isolation recipes on **OpenWrt**.

### What uCore-Network is NOT
- It is **not** an attempt to build a global replacement internet or custom hardware protocol.
- LoRa radio mesh (MeshCore) is deferred to long-term hardware research; it does not block software releases.
- It does not bypass host firewall policies or auto-open router ports.

---

## 2. Architecture & Service Topology

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            HOME NETWORK / LAN                               │
│                                                                             │
│  ┌─────────────────────────┐           ┌─────────────────────────────────┐  │
│  │ uCore Host (Local Node) │           │ Client Devices (Phones, Laptops)│  │
│  │                         │           │                                 │  │
│  │ • Local Portal (HTTP)   │◄─────────►│ • Obsidian Vault / Web Browser  │  │
│  │ • BitChat Hub / mDNS    │           │ • BitChat Client UI             │  │
│  │ • Bounded Task Receipts │           │ • HomeNest Console              │  │
│  └────────────┬────────────┘           └────────────────┬────────────────┘  │
│               │                                         │                   │
│               ▼                                         ▼                   │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                 LOCAL NETWORK PRIVACY LAYER (DNS & MESH)              │  │
│  │                                                                       │  │
│  │ • AdGuard Home / Pi-hole: Network-wide ad & tracker blocking          │  │
│  │ • Upstream: Encrypted DoH to Quad9 (9.9.9.9) / Mullvad DNS            │  │
│  │ • WireGuard / Tailscale (Headscale): Encrypted point-to-point mesh    │  │
│  │ • OpenWrt Router: Guest Wi-Fi isolated from Private Vault Subnet      │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ (Encrypted WireGuard Mesh)
                                       ▼
                     [Remote Laptop / Phone on Public Wi-Fi]
                     (Accesses home vaults securely; no open ports)
```

---

## 3. BitChat: Local-First Private Communication

### Purpose
BitChat provides private, real-time messaging between household members or co-located teams without relying on third-party servers, telephone numbers, or cloud accounts.

### Protocol & Discovery
1. **Discovery**: Devices on the same subnet discover the uCore BitChat endpoint via **mDNS / Bonjour** service advertisement (`_bitchat._tcp.local.`).
2. **Transport**: Lightweight WebSocket connection (`/api/network/bitchat/ws`).
3. **Identity**: Ephemeral or profile-based public-key identity (derived from `app.identity`).
4. **Encryption**: End-to-end encrypted message frames using standardlibs (NaCl / TweetNaCl / AES-GCM).

### uDos Integration: "Save to Binder"
* Discussions regarding project briefs, decisions, or research can be saved with one click.
* The selected chat thread is formatted as Markdown evidence and committed to the active binder under `evidence/chats/YYYY-MM-DD-thread.md`.

---

## 4. Network Privacy Stack Recipes

### A. AdGuard Home / Pi-hole DNS Sinkholing
* **Deployment**: Packaged as an optional container or service recipe managed via SonicScrewdriver or system services.
* **Standard Policy**:
  - Block known telemetry, ad networks, and behavioral tracking lists.
  - Enforce encrypted upstream DNS queries via **DNS-over-HTTPS (DoH)** or **DNS-over-TLS (DoT)**.
  - Zero logging of local queries unless explicitly requested by the administrator for debugging.

### B. WireGuard & Tailscale (Headscale) Zero-Trust Remote Mesh
* **Deployment**: Point-to-point WireGuard mesh network.
* **Security Posture**:
  - Eliminates universal port-forwarding (UPnP is disabled by default).
  - Outside devices connect via an encrypted WireGuard tunnel directly to the user's home node.
  - Allows full access to offline-published editions, BitChat, and HomeNest media while traveling on untrusted Wi-Fi.

### C. OpenWrt Router Isolation
* **Policy Recipe**:
  - Separate VLANs/SSIDs for **Main LAN**, **Guest Wi-Fi**, and **IoT Devices**.
  - **Guest Wi-Fi**: Granted WAN internet access and read-only access to the public uCore portal; strictly blocked from internal file shares, vaults, and camera streams.
  - Provisioning recipes authored in Sonic for compatible router hardware.
