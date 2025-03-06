# 🌀 Dreamwave Synthesia

![Banner](docs/banner_vaporwave.png)  
*"Where Neural Impulses Become Virtual Objects"*

A Vaporwave-styled AI pipeline for Unreal Engine 5 that transforms text descriptions into production-ready 3D assets.

## 🌌 Features

| &nbsp; | &nbsp; |
|--------|--------|
| 🎨 **Text-to-Concept Art** | SDXL-Turbo + ControlNet workflows |
| 📦 **AI-Assisted 3D Conversion** | Hunyuan3D-2 integration |
| ⚡ **UE5 Automation** | Auto-import with material setup |
| 🌐 **Vaporwave Styling** | Retro-cyberpunk texture presets |

## 🌈 Visual Identity

**Color Scheme**  

```
/* CSS variables for UI theming */
--neon-cyan: #6BD6EB;
--retro-coral: #FF6B6B;
--nanite-black: #2A2A2A;
```

**Logo Concept**  
![Logo Sketch](docs/logo_concept.png)  
*Glowing neuron core with VHS artifacts and floating polyhedron*

## 🖥️ System Requirements

### Minimum Spec

GPU: NVIDIA RTX 3090 (24GB VRAM)
RAM: 64GB DDR4
Storage: PCIe 4.0 NVMe (1TB)

### Recommended

GPU: NVIDIA RTX 6000 Ada (48GB VRAM)
RAM: 128GB DDR5
Storage: RAID 0 NVMe (2TB)

## 🛠️ Installation

Clone with vaporwave aesthetic

```
git clone https://github.com/yourhandle/dreamwave-synthesia --branch vaporwave
```

### Install dependencies

```
conda env create -f environment.yml
conda activate dreamwave
```

### Launch MCP server

```
python -m dreamwave.mcp --gpu 0 --style vapor95
```

## 🎛️ Usage

### 1. Generate Concept Art

from dreamwave import miragegen

prompt = "Neon samurai sword with glowing kanji"
styles = ["vaporwave", "cyberpunk", "retro_future"]
concepts = miragegen.generate(prompt, styles=styles)

### 2. Convert to 3D Asset

```
from dreamwave import lumeforge

selected_concept = concepts
asset = lumeforge.convert(
selected_concept,
texture_style="vaporwave",
poly_limit=50000
)
```

### 3. Import to UE5

```
from dreamwave.unreal import oneiric_importer

oneiric_importer.import_asset(
asset,
destination="/Game/AI_Assets",
auto_materials=True,
nanite=True
)
```

## 🧬 Project Structure

dreamwave-synthesia/
├── miragegen/ # Concept art generation
├── lumeforge/ # 3D conversion core
├── oneiric/ # UE5 automation
├── styles/ # Vaporwave presets
└── mcp-server/ # AI coordination hub

text

## 🌠 Development Roadmap

### Phase 1: Core Synthesis (Q3 2025)
- [ ] Vaporwave texture presets
- [ ] Basic MCP server
- [ ] UE5 material auto-setup

### Phase 2: Style Expansion (Q4 2025)
- [ ] Cyberpunk neon shaders
- [ ] Retro CRT filter bank
- [ ] AI-assisted UV unwrapping

### Phase 3: Dreamwave Architect (Q1 2026)
- [ ] Standalone desktop app
- [ ] VFX graph templates
- [ ] Community asset library

## 🧬 Contributing

1. Clone the `vaporwave` branch
2. Create feature branch with style prefix:

```
git checkout -b style/retro-crt-filters
```

3. Follow our [Vaporwave Design Guidelines](docs/STYLE_GUIDE.md)

## 📜 License

**Dreamwave Non-Commercial License**  
Free for personal/artistic use. Commercial licenses available.

---

[![Discord](https://img.shields.io/badge/Join%20Discord-%235865F2.svg?logo=discord)](https://discord.gg/yourlink) 
[![UE5 Marketplace](https://img.shields.io/badge/UE5-Marketplace-%232F3136)](https://unrealengine.com/marketplace)

*© 2025 Dreamwave Synthesia - Made with 💜 in the Neon Grid*
