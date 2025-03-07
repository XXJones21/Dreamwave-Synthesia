# 🌀 Dreamwave Synthesia

![Banner](../docs/banner_vaporwave.png)  
*"Where Neural Impulses Become Virtual Objects"*

A Vaporwave-styled AI pipeline for Unreal Engine 5 that transforms text descriptions into production-ready assets.

## 🚀 Current Focus: Texture Generation

We are currently focusing on building the texture generation component of the pipeline. This allows technical artists to generate high-quality textures directly within Unreal Engine 5 using AI models.

### Features

- Text-to-texture generation using FLUX.1-schnell model
- ComfyUI integration for powerful AI workflows
- Unreal Engine 5 plugin for in-editor texture creation
- Vaporwave aesthetic presets for consistent style

## 📦 Components

The project is organized into the following components:

- **texture_gen**: Core Python module for texture generation via ComfyUI
- **UnrealPlugin/DreamwaveTexGen**: Unreal Engine 5 plugin for in-editor texture generation

## 🛠️ Setup Instructions

### Prerequisites

- Python 3.10+
- ComfyUI with FLUX.1-schnell model
- Unreal Engine 5.3+

### Installation

1. Install Python dependencies:
```bash
pip install -r texture_gen/requirements.txt
```

2. Ensure ComfyUI is properly set up with the FLUX.1-schnell model

3. For UE5 integration, follow the instructions in the [texture_gen README](texture_gen/README.md)

## 📋 Development Roadmap

### Current Phase: Texture Generation
- [x] ComfyUI bridge implementation
- [x] Basic text-to-texture generation
- [x] UE5 plugin structure
- [ ] UE5 plugin UI implementation
- [ ] Style preset management
- [ ] Material auto-generation

### Next Phases
1. **3D Asset Generation**
   - Integration with Hunyuan3D-2
   - Mesh validation and optimization
   - Texture mapping and material creation

2. **UE5 Pipeline Automation**
   - Asset import automation
   - Material template application
   - Showcase scene generation

## 🎮 Usage Examples

See the [texture_gen README](texture_gen/README.md) for detailed usage examples and API documentation.

## 🧪 Testing

To test the texture generation functionality:

```bash
python -m texture_gen.test_bridge --prompt "vaporwave grid with neon glow, cyberpunk, retro"
```

## 🤝 Contributing

Contributions are welcome! Please check out our contributing guidelines for details on how to get involved.

## 📜 License

**Dreamwave Non-Commercial License**  
Free for personal/artistic use. Commercial licenses available.

---

*© 2025 Dreamwave Synthesia - Made with ❤️ in the Neon Grid* 