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

---

## 5. HomeNest Media & Steam Decentralized Node Protocol

### Mission
Eliminate cloud-first media streaming and game delivery delays. A designated local machine (e.g. Steam PC, media server, or Mac Mini) acts as the local media host and game transfer cache for all household clients (tablets, laptops, living-room TV).

### Protocol & Service Registration
All decentralized nodes announce their roles on the LAN via mDNS / ZeroConf:

| Service Type | Port | Purpose | Transport |
| :--- | :--- | :--- | :--- |
| `_homenest-media._tcp.local.` | 8096 | Local media library (films, music, audiobooks) via Jellyfin / uDOS media player | HTTP / WebSocket |
| `_homenest-steam._tcp.local.` | 27036 | Steam Big Picture console, In-Home Streaming, and Local Network Game Transfers | UDP / TCP |
| `_sonic-depot._tcp.local.` | 8088 | Decentralized distro/ISO cache, patch repository, and uCode capsules | HTTP |
| `_udos-portal._tcp.local.` | 8080 | Local Headless WordPress user RBAC, permission store, and document portal | HTTP / REST |
| `_bitchat._tcp.local.` | 8085 | Private LAN P2P messaging and living-room notifications | WebSocket |

### Local Caching & Bandwidth Preservation
1. **Steam Local Network Transfers**:
   - HomeNest operates as a local Steam repository node.
   - When a game or update is downloaded to the HomeNest console, any other PC, laptop, or Steam Deck on the local network pulls game files directly from the HomeNest node over gigabit LAN, requiring zero external internet download.
2. **Local Media & Retro Game Capsules**:
   - Audio, video, and uCode retro game capsules (`.ucapsule`) stream directly from local storage to the living-room display or mobile clients.
   - Preserves complete functionality when the internet connection is offline or degraded.
3. **Controller & Thin-Client Operation**:
   - Thin clients (laptops, phones) can discover the HomeNest node and either trigger playback locally or act as remote controller surfaces via WebSocket events.
