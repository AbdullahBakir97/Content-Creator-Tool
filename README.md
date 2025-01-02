# Content Creator Tool

A professional Django-based content creation tool that leverages AI for generating and managing multimedia content.

## Features

- AI-powered content generation
- Professional video creation with effects
- Advanced image processing
- Text-to-speech voiceover generation
- Comprehensive file management
- Caching and optimization
- Error handling and logging

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/content_creator_tool.git
cd content_creator_tool
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and settings
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Start the development server:
```bash
python manage.py runserver
```


## Core Components

### Content Generation Service
Handles the creation of content using AI:
- Script generation
- Image selection
- Video creation
- Voiceover generation

### Video Generation Utility
Creates professional videos with:
- Smooth transitions
- Visual effects
- Text overlays
- Audio synchronization

### Image Processing Utility
Processes images with:
- Enhancement filters
- Text overlays
- Optimization
- Format conversion

### File Management Utility
Manages files with:
- Secure operations
- Type validation
- Organization
- Cleanup routines

## API Documentation

Detailed API documentation can be found in the `docs/` directory:
- [API Reference](docs/api-reference.md)
- [Service Documentation](docs/services.md)
- [Utility Documentation](docs/utilities.md)

## Configuration

The project uses environment variables for configuration. Create a `.env` file with:

```env
DEBUG=True
SECRET_KEY=your-secret-key
GEMINI_API_KEY=your-gemini-api-key
ELEVEN_LABS_KEY=your-eleven-labs-key
MEDIA_ROOT=/path/to/media
```

## Development

### Running Tests
```bash
python manage.py test
```

### Code Style
The project follows PEP 8 style guide. Use flake8 for linting:
```bash
flake8 .
```

### Type Checking
The project uses type hints. Run mypy for type checking:
```bash
mypy .
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Google Gemini](https://deepmind.google/technologies/gemini/) for AI content generation
- [ElevenLabs](https://elevenlabs.io/) for text-to-speech
- [MoviePy](https://zulko.github.io/moviepy/) for video processing
- [Pillow](https://python-pillow.org/) for image processing
