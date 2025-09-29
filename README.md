# NewsFast - AI-Powered Article Summarizer

NewsFast is a modern web application that allows users to paste any article URL and get intelligent summaries with key points, keywords, and AI-generated abstracts.

## Features

- **🔗 URL Processing**: Paste any news article, blog post, or webpage URL
- **✨ Extractive Summarization**: Highlights the most important sentences from the original text
- **🏷️ Keyword Extraction**: Identifies and displays key terms and phrases
- **🤖 AI-Powered Summaries**: Generates human-like abstractive summaries using OpenRouter AI
- **📱 Responsive Design**: Works seamlessly on desktop and mobile devices
- **⚡ Fast Processing**: Optimized for quick article processing and summarization

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Frontend  │--->│   FastAPI        │--->│   Article       │
│   (HTML/JS/CSS) │    │   Backend        │    │   Scraper       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   Text           │    │   AI            │
                       │   Summarizer     │    │   Summarizer    │
                       └──────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   Extractive     │    │   OpenRouter    │
                       │   Summary        │    │   API           │
                       └──────────────────┘    └─────────────────┘
```

## Technology Stack

- **Backend**: Python + FastAPI
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **AI Integration**: OpenRouter API (supports multiple AI models)
- **Scraping**: Newspaper3k + BeautifulSoup4 + Custom parsers
- **NLP**: NLTK, scikit-learn, sumy
- **Styling**: Bootstrap 5 + Custom CSS

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd newsfast
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your OpenRouter API key:
   ```
   OPENROUTER_API_KEY=your_api_key_here
   ```

4. **Download NLTK data** (required for NLP features)
   ```bash
   python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"
   ```

## Usage

1. **Start the application**
   ```bash
   python main.py
   ```

2. **Open your browser**
   Navigate to `http://localhost:8000`

3. **Paste an article URL**
   - Copy any news article or blog post URL
   - Paste it in the input field
   - Click "Summarize Article"

4. **View results**
   - **Original Article**: Title, metadata, and link
   - **Key Points**: Extracted important sentences
   - **Keywords**: Important terms and phrases
   - **AI Summary**: AI-generated abstractive summary

## API Endpoints

### POST /summarize
Summarize an article from a URL.

**Request:**
```json
{
  "url": "https://example.com/article"
}
```

**Response:**
```json
{
  "article": {
    "title": "Article Title",
    "text": "Full article text...",
    "authors": ["Author Name"],
    "publish_date": "2024-01-01",
    "url": "https://example.com/article",
    "word_count": 1234
  },
  "extractive_summary": {
    "summary": "Key sentences from the article...",
    "sentences": ["Sentence 1", "Sentence 2"],
    "method": "extractive"
  },
  "keywords": {
    "keywords": [["important", 0.85], ["keyword", 0.72]]
  },
  "ai_summary": {
    "summary": "AI-generated summary...",
    "method": "ai_abstractive"
  },
  "success": true
}
```

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "message": "NewsFast is running"
}
```

## Configuration

### OpenRouter API Setup

1. Visit [OpenRouter.ai](https://openrouter.ai/)
2. Create an account and get your API key
3. Add the key to your `.env` file

**Supported Models:**
- Meta Llama 3.1 8B (free tier available)
- Various other models based on your plan

### Customization Options

- **Summary Length**: Adjust `num_sentences` in extractive summarization
- **Keywords Count**: Modify `num_keywords` parameter
- **AI Summary Length**: Change `max_length` in AI summarization

## Development

### Project Structure
```
newsfast/
├── main.py              # FastAPI application
├── scraper.py          # Web scraping module
├── summarizer.py       # Text summarization logic
├── ai_summarizer.py    # OpenRouter AI integration
├── validation.py       # Input validation and error handling
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variables template
├── templates/
│   └── index.html      # Main web interface
└── static/
    ├── css/
    │   └── style.css   # Custom styling
    └── js/
        └── script.js   # Frontend JavaScript
```

### Adding New Features

1. **Custom Scrapers**: Extend `scraper.py` for specific news sites
2. **New Summarization Methods**: Add algorithms to `summarizer.py`
3. **Additional AI Models**: Extend `ai_summarizer.py`
4. **UI Improvements**: Modify `templates/index.html` and `static/`

## Error Handling

The application includes comprehensive error handling:

- **Invalid URLs**: Clear error messages for malformed URLs
- **Network Issues**: Timeout and connection error handling
- **Content Parsing**: Fallback methods for difficult-to-parse content
- **AI API Failures**: Graceful degradation when AI services are unavailable
- **Input Validation**: Comprehensive validation of user input

## Performance

- **Concurrent Processing**: FastAPI's async capabilities
- **Caching**: Response caching for improved performance
- **Optimized Scraping**: Multiple fallback methods for reliability
- **Responsive UI**: Fast loading and smooth interactions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- Create an issue in the repository
- Check the troubleshooting section below

## Supported Content Types

NewsFast works with various types of content:

### ✅ **Well Supported**
- **News Websites**: CNN, BBC, Reuters, SCMP, etc.
- **Blogs**: Medium, personal blogs, news blogs
- **ArXiv Papers**: Pre-print academic papers
- **Open Access Content**: Publicly available articles

### ⚠️ **Limited Support**
- **Academic Paywalls**: ACM, IEEE, Springer, ScienceDirect (often blocked)
- **Research Databases**: PubMed, Google Scholar (abstracts only)
- **Corporate Sites**: Some company pages with strict access controls

### ❌ **Not Supported**
- **PDF Files**: Direct PDF links (use HTML abstract pages instead)
- **Login-Protected Content**: Sites requiring authentication
- **Video/Audio Content**: Non-text based media

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
2. **NLTK Data**: Run the NLTK download command
3. **OpenRouter API**: Verify your API key is correct
4. **Port Issues**: Make sure port 8000 is available
5. **Memory Usage**: For very long articles, consider chunking

### Academic Content Issues

**Many academic publishers block automated access:**
- ACM, IEEE, Springer often return 403 Forbidden
- Some sites require institutional access
- Use arXiv.org for pre-print papers (works well)
- Check if the content is available as HTML rather than PDF

**Solutions:**
- Try finding the abstract/summary page instead of full paper
- Use arXiv for pre-prints when available
- Consider manual copy-paste for blocked content

### Debug Mode

Run with debug logging:
```bash
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Roadmap

- [ ] User authentication and saved summaries
- [ ] Browser extension
- [ ] Bulk URL processing
- [ ] Export functionality (PDF, DOCX)
- [ ] Multi-language support
- [ ] Advanced filtering options
- [ ] Social media integration