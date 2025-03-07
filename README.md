# 🌀 Dreamwave Synthesia

![Banner](docs/banner_vaporwave.png)  
*"Where Neural Impulses Become Virtual Objects"*

A Vaporwave-styled AI pipeline for Unreal Engine 5 that transforms text descriptions into production-ready 3D assets.

## 🌌 Features

| &nbsp; | &nbsp; |
|--------|--------|
| 🎨 **Text-to-Concept Art** | FLUX.1-schnell + ControlNet workflows |
| 📦 **AI-Assisted 3D Conversion** | Hunyuan3D-2 integration |
| ⚡ **UE5 Automation** | Auto-import with material setup |
| 🌐 **Vaporwave Styling** | Retro-cyberpunk texture presets |
| 🔌 **UE5 Integration** | Seamless toolbar and menu integration |
| 🔄 **Robust ComfyUI Integration** | Auto-detection and dependency management |

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

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Unreal Engine 5.3+
- ComfyUI (included in setup)
- FLUX.1-schnell model (download via script)
- About 10GB of disk space for models

The plugin will automatically detect and install required Python packages (PyTorch, YAML) as needed.

### Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/dreamwave-synthesia.git
cd dreamwave-synthesia
```

2. Install the required Python packages:
```bash
pip install -r requirements.txt
```

3. Download the FLUX.1-schnell model:
```bash
python download_flux.py
```

4. Run the ComfyUI cleanup script to optimize disk space (optional):
```bash
python cleanup_comfyui.py
```

### Installing the UE5 Plugin

1. Copy the `Dreamwave-UE5/Plugins/DreamwaveTexGen` folder to your Unreal Engine project's `Plugins` directory
2. Start Unreal Engine and enable the plugin in Edit > Plugins > AI > Dreamwave Texture Generator
3. Restart the Unreal Editor when prompted

After restarting, you'll find:
- A "Dreamwave" entry in the main menu
- A Dreamwave button in the main toolbar for quick access

## 🎛️ Usage

### 1. Generate Concept Art

```python
from dreamwave import miragegen

# Our Hello World test case - the Dreamwave logo
prompt = "Glowing neuron core with VHS artifacts and floating polyhedron, vaporwave style"
styles = ["vaporwave", "retro_future", "neon"]
logo_concepts = miragegen.generate(
    prompt, 
    styles=styles,
    model="FLUX.1-schnell"  # Using FLUX.1-schnell for faster concept generation
)
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

### Using the UE5 Plugin

For quick texture generation directly within Unreal Engine:

1. Click the "Dreamwave" button in the toolbar or use the main menu
2. Use the Texture Generator to create textures from text prompts
3. The plugin automatically imports generated textures into your project

## 🧬 Project Structure

dreamwave-synthesia/
├── miragegen/ # Concept art generation
├── lumeforge/ # 3D conversion core
├── oneiric/ # UE5 automation
├── styles/ # Vaporwave presets
├── mcp-server/ # AI coordination hub
└── Dreamwave-UE5/ # UE5 plugin package

text

## 🌠 Development Roadmap

> **PROJECT STATUS**: Making steady progress! We have successfully completed the model infrastructure setup and UE5 integration, and are now moving into workflow integration.

### Phase 1: Model Infrastructure ✅
- [x] **Model Selection & Integration**
  - [x] Research and select optimal models for concept generation
  - [x] Choose FLUX.1-schnell for faster concept art iteration
  - [x] Setup model download infrastructure with error handling
  - [x] Implement model verification and path normalization
- [x] **Environment Configuration**
  - [x] Setup Python environment with required dependencies
  - [x] Configure ComfyUI with essential extensions and nodes
  - [x] Create disk space optimization scripts
  - [x] Develop workflow templates for consistent generation

### Phase 2: Workflow Integration 🔄
- [ ] **Concept Art Generation System**
  - [x] Configure FLUX.1-schnell for text-to-concept pipeline 
  - [x] Create parameterized workflows for style variations
  - [ ] Build curated prompt library for vaporwave aesthetics
  - [ ] Implement batch processing for concept exploration
- [ ] **3D Asset Generation**
  - [ ] Configure Hunyuan3D-2 API connection
  - [ ] Implement mesh validation and auto-repair
  - [ ] Create texture extraction workflows
  - [ ] Add LOD generation for game-ready assets

### Phase 3: UE5 Integration ✅
- [x] **Asset Import Automation**
  - [x] Develop Python-based UE5 asset importer
  - [x] Create toolbar and menu integration
  - [x] Implement texture generation UI
  - [x] Connect to ComfyUI backend
- [x] **ComfyUI Integration**
  - [x] Automatic detection of ComfyUI installations
  - [x] Dependency management and installation
  - [x] Diagnostic logging and error reporting
  - [x] Multiple launch methods with fallbacks
- [ ] **End-to-End Testing**
  - [ ] Develop pipeline orchestration server
  - [ ] Create automated testing suite
  - [ ] Document performance benchmarks
  - [ ] Optimize for jam-day throughput

### Future Enhancements
- [ ] WebUI for easier interaction with the pipeline
- [ ] Custom node development for specialized workflows
- [ ] Training custom LoRAs for consistent style generation
- [ ] Integration with version control for asset history

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

*© 2025 Dreamwave Synthesia - Made with  in the Neon Grid*