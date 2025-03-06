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

> **🔑 Pipeline Test Case**: The Logo Concept serves as our "Hello World" test for the pipeline. Each step of development will be verified using this concept. When the pipeline can successfully generate a 3D model of the logo with proper materials and import it into UE5, the tool will be considered ready for Game Development use.

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

```python
from dreamwave import miragegen

# Our Hello World test case - the Dreamwave logo
prompt = "Glowing neuron core with VHS artifacts and floating polyhedron, vaporwave style"
styles = ["vaporwave", "retro_future", "neon"]
logo_concepts = miragegen.generate(prompt, styles=styles)
```

### 2. Convert to 3D Asset

```python
from dreamwave import lumeforge

selected_concept = logo_concepts[0]  # Choose preferred concept rendering
logo_asset = lumeforge.convert(
    selected_concept,
    texture_style="vaporwave",
    poly_limit=50000,
    material_channels=["diffuse", "emission", "normal"]
)
```

### 3. Import to UE5

```python
from dreamwave.unreal import oneiric_importer

# Import to special showcase location for verification
oneiric_importer.import_asset(
    logo_asset,
    destination="/Game/Dreamwave/Logo",
    auto_materials=True,
    nanite=True,
    create_showcase_scene=True  # Creates a test scene with proper lighting
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

> **NOTICE**: This is a rapid prototype built in 2 days for an upcoming game dev jam! The project serves as a "dogfooding" exercise to identify practical GenAI workflows for indie game developers.

### Day 1: Core Pipeline Setup (8 hours)
- [ ] **Morning**: Text-to-Concept System
  - Set up ComfyUI with SDXL-Turbo
  - Implement basic vaporwave style preset
  - Create minimal selection interface
- [ ] **Afternoon**: 3D Asset Generation
  - Configure Hunyuan3D-2 API connection
  - Implement basic mesh validation
  - Optimize for single GPU workflow

### Day 2: UE5 Integration & Testing (8 hours)
- [ ] **Morning**: UE5 Import System
  - Implement Python-based asset importer
  - Create basic vaporwave material templates
  - Set up automatic collision generation
- [ ] **Afternoon**: End-to-End Testing
  - Build MCP coordination server
  - Create example workflow documentation
  - Test full pipeline with sample assets

### Post-Jam: Community Contributions
- [ ] Gather feedback from jam participants
- [ ] Document encountered workflow issues
- [ ] Create improvement roadmap based on real usage

## 🔬 Dogfooding Goals

This project explores practical workflows for indie devs integrating GenAI into game development:

1. **Time Efficiency**: How much can GenAI accelerate asset creation under jam conditions?
2. **Technical Barriers**: What minimum technical setup is needed for effective AI integration?
3. **Workflow Gaps**: Where do current GenAI tools fall short in game dev pipelines?
4. **Cost Analysis**: What are the real resource requirements for indie developers?

Results and findings will be shared openly to benefit the indie game development community.

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

*© 2025 Dreamwave Synthesia - Made with �� in the Neon Grid*